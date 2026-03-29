from __future__ import annotations

import secrets
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
import typer
from rich.console import Console

from ..config.settings import Settings
from .token_store import TokenStore

console = Console()

XERO_AUTH_URL = "https://login.xero.com/identity/connect/authorize"
XERO_TOKEN_URL = "https://identity.xero.com/connect/token"
XERO_CONNECTIONS_URL = "https://api.xero.com/connections"


def login(settings: Settings, tenant: str | None = None) -> dict[str, Any]:
    """Run the OAuth2 authorization flow and return saved token data."""
    if not settings.client_id or not settings.client_secret:
        console.print(
            "[red]Error:[/red] XERO_CLIENT_ID and XERO_CLIENT_SECRET must be set.\n"
            "Copy [bold].env.example[/bold] to [bold].env[/bold] and fill in your credentials."
        )
        raise typer.Exit(1)

    state = secrets.token_hex(16)
    auth_code: list[str] = []
    error_msg: list[str] = []

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/callback":
                params = parse_qs(parsed.query)
                if "error" in params:
                    error_msg.append(params["error"][0])
                elif "code" in params and params.get("state", [""])[0] == state:
                    auth_code.append(params["code"][0])
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                if auth_code:
                    self.wfile.write(
                        b"<h1>Authentication successful!</h1>"
                        b"<p>You can close this tab and return to the terminal.</p>"
                    )
                else:
                    self.wfile.write(b"<h1>Authentication failed.</h1><p>Please try again.</p>")

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            pass  # suppress server logs

    server = HTTPServer(("localhost", 8080), CallbackHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    params = {
        "response_type": "code",
        "client_id": settings.client_id,
        "redirect_uri": settings.redirect_uri,
        "scope": " ".join(settings.scopes),
        "state": state,
    }
    auth_url = f"{XERO_AUTH_URL}?{urlencode(params)}"

    console.print("\n[bold]Opening browser for Xero authentication...[/bold]")
    console.print(f"If the browser doesn't open, visit:\n[cyan]{auth_url}[/cyan]\n")
    webbrowser.open(auth_url)

    timeout = 120
    start = time.time()
    while not auth_code and not error_msg and time.time() - start < timeout:
        time.sleep(0.1)

    server.shutdown()

    if error_msg:
        console.print(f"[red]Authentication error:[/red] {error_msg[0]}")
        raise typer.Exit(1)

    if not auth_code:
        console.print("[red]Authentication timed out.[/red] Please try again.")
        raise typer.Exit(1)

    token_data = _exchange_code(auth_code[0], settings)
    selected = _select_tenant(token_data["access_token"], tenant=tenant)
    token_data["tenant_id"] = selected["tenantId"]
    token_data["tenant_name"] = selected["tenantName"]

    TokenStore().save(token_data)
    return token_data


def refresh_token(token_data: dict[str, Any], settings: Settings) -> dict[str, Any]:
    """Exchange a refresh token for a new access token."""
    response = httpx.post(
        XERO_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": token_data["refresh_token"],
        },
        auth=(settings.client_id, settings.client_secret),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response.raise_for_status()
    new_token = response.json()
    new_token["expires_at"] = time.time() + new_token.get("expires_in", 1800)
    new_token["tenant_id"] = token_data["tenant_id"]
    new_token["tenant_name"] = token_data["tenant_name"]
    return new_token


def _exchange_code(code: str, settings: Settings) -> dict[str, Any]:
    response = httpx.post(
        XERO_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.redirect_uri,
        },
        auth=(settings.client_id, settings.client_secret),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response.raise_for_status()
    data = response.json()
    data["expires_at"] = time.time() + data.get("expires_in", 1800)
    return data


def _select_tenant(access_token: str, tenant: str | None = None) -> dict[str, Any]:
    response = httpx.get(
        XERO_CONNECTIONS_URL,
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
    )
    response.raise_for_status()
    connections: list[dict] = response.json()

    if not connections:
        console.print("[red]No Xero organizations found for this account.[/red]")
        raise typer.Exit(1)

    if tenant is not None:
        lower = tenant.lower()
        match = next(
            (
                c
                for c in connections
                if lower in c["tenantName"].lower() or lower == c["tenantId"].lower()
            ),
            None,
        )
        if match is None:
            names = ", ".join(c["tenantName"] for c in connections)
            console.print(f"[red]No tenant matching '{tenant}' found.[/red] Available: {names}")
            raise typer.Exit(1)
        return match

    if len(connections) == 1:
        return connections[0]

    console.print("\n[bold]Multiple Xero organizations found:[/bold]")
    for i, conn in enumerate(connections, 1):
        console.print(f"  {i}. {conn['tenantName']}")
    choice = typer.prompt("Select organization number", type=int, default=1)
    return connections[max(0, min(choice - 1, len(connections) - 1))]
