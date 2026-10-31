"""Prepare a fresh SonarQube Community server for one CI scan.

The password and token exist only for this process. They are not GitHub
secrets and must not be printed.
"""

from __future__ import annotations

import argparse
import base64
import json
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PROJECT_KEY = "Astroimage"
PROJECT_NAME = "Astroimage"
TOKEN_NAME = "ci-scan"


def ephemeral_password() -> str:
    return "Aa1!" + secrets.token_urlsafe(18)


def basic_header(user: str, password: str) -> str:
    token = base64.b64encode(f"{user}:{password}".encode()).decode("ascii")
    return f"Basic {token}"


def request(
    method: str,
    url: str,
    *,
    user: str | None = None,
    password: str | None = None,
    form: dict[str, str] | None = None,
    timeout: float = 30,
) -> tuple[int, bytes]:
    data = urllib.parse.urlencode(form).encode() if form is not None else None
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if user is not None and password is not None:
        headers["Authorization"] = basic_header(user, password)
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as caught:
        return caught.code, caught.read()


def wait_until_up(base_url: str, *, attempts: int = 60, pause_seconds: float = 2) -> None:
    status_url = f"{base_url.rstrip('/')}/api/system/status"
    last_detail = "no response"
    for _ in range(attempts):
        try:
            code, body = request("GET", status_url)
        except (urllib.error.URLError, TimeoutError, OSError) as caught:
            last_detail = str(caught.reason) if isinstance(caught, urllib.error.URLError) else str(caught)
            time.sleep(pause_seconds)
            continue
        if code == 200:
            payload = json.loads(body.decode("utf-8"))
            if payload.get("status") == "UP":
                return
            last_detail = str(payload.get("status"))
        else:
            last_detail = f"HTTP {code}"
        time.sleep(pause_seconds)
    raise RuntimeError(f"SonarQube did not become UP: {last_detail}")


def require_ok(code: int, body: bytes, action: str) -> bytes:
    if code not in (200, 204):
        detail = body.decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"{action} failed with HTTP {code}: {detail}")
    return body


def post_form(url: str, *, user: str, password: str, form: dict[str, str], action: str) -> bytes:
    last_error = f"{action} was not attempted"
    for _ in range(30):
        try:
            code, body = request("POST", url, user=user, password=password, form=form)
        except (urllib.error.URLError, TimeoutError, OSError) as caught:
            last_error = str(caught.reason) if isinstance(caught, urllib.error.URLError) else str(caught)
            time.sleep(2)
            continue
        if code in (200, 204):
            return body
        if code in (401, 500, 502, 503):
            last_error = f"HTTP {code}"
            time.sleep(2)
            continue
        return require_ok(code, body, action)
    raise RuntimeError(f"{action} failed: {last_error}")


def bootstrap(base_url: str, token_file: Path) -> None:
    root = base_url.rstrip("/")
    password = ephemeral_password()
    wait_until_up(root)
    post_form(
        f"{root}/api/users/change_password",
        user="admin",
        password="admin",
        form={"login": "admin", "previousPassword": "admin", "password": password},
        action="change admin password",
    )
    post_form(
        f"{root}/api/projects/create",
        user="admin",
        password=password,
        form={"project": PROJECT_KEY, "name": PROJECT_NAME},
        action="create project",
    )
    body = post_form(
        f"{root}/api/user_tokens/generate",
        user="admin",
        password=password,
        form={"name": TOKEN_NAME, "type": "USER_TOKEN"},
        action="generate token",
    )
    payload = json.loads(body.decode("utf-8"))
    token = payload.get("token")
    if not isinstance(token, str) or not token:
        raise RuntimeError("generate token returned no token")
    token_file.write_text(token, encoding="utf-8")
    token_file.chmod(0o600)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--token-file", required=True, type=Path)
    args = parser.parse_args()
    try:
        bootstrap(args.url, args.token_file)
    except (RuntimeError, urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as caught:
        print(str(caught), file=sys.stderr)
        return 1
    print("SonarQube project ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
