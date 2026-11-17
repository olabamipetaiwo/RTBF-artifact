"""Turn a Cookie-Editor export into a Playwright session the pipeline can load.

Most agents block logins performed by an automated browser, so log in in your
everyday Chrome instead and export that browser's cookies with the
Cookie-Editor extension. Step-by-step instructions: docs/sessions.md.

    python scripts/import_cookies.py <agent>                    # sessions/cookies_<agent>.json -> sessions/<agent>.json
    python scripts/import_cookies.py <agent> --account LABEL    # sessions/cookies_<agent>__LABEL.json -> sessions/<agent>__LABEL.json
    python scripts/import_cookies.py <agent> --merge DOMAIN     # add sessions/cookies_<agent>_DOMAIN.json to an existing session

Copilot and DeepSeek also keep part of the login in localStorage; paste it into
sessions/localstorage_<agent>.json and it is attached automatically.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repository root

from didr import config  # noqa: E402

_SAMESITE = {"no_restriction": "None", "unspecified": "None", "none": "None", "lax": "Lax", "strict": "Strict"}

# Origin the localStorage belongs to, per agent.
_ORIGINS = {
    "chatgpt": "https://chatgpt.com",
    "claude": "https://claude.ai",
    "gemini": "https://gemini.google.com",
    "copilot": "https://copilot.com",
    "perplexity": "https://www.perplexity.ai",
    "deepseek": "https://chat.deepseek.com",
}


def _read_json(path: Path) -> object | None:
    """Return the parsed file, or None when the placeholder is still empty."""
    if not path.exists():
        return None
    text = path.read_text().strip()
    # Ignore a leftover placeholder ("[]" or "{}") left above a pasted export.
    for placeholder in ("[]", "{}"):
        if text.startswith(placeholder) and text[len(placeholder):].strip():
            text = text[len(placeholder):].strip()
    if text in ("", "[]", "{}"):
        return None
    return json.loads(text)


def _cookies(path: Path) -> list[dict]:
    raw = _read_json(path)
    if raw is None:
        raise SystemExit(f"{path} is empty: paste the Cookie-Editor export into it first (docs/sessions.md).")
    if isinstance(raw, dict) and "cookies" in raw:
        raw = raw["cookies"]
    cookies = []
    for c in raw:
        expires = -1 if c.get("session") else c.get("expirationDate", -1)
        cookies.append({
            "name": c["name"],
            "value": c["value"],
            "domain": c["domain"],
            "path": c.get("path", "/"),
            "expires": -1 if expires is None else expires,
            "httpOnly": bool(c.get("httpOnly", False)),
            "secure": bool(c.get("secure", False)),
            "sameSite": _SAMESITE.get(str(c.get("sameSite", "lax")).lower(), "Lax"),
        })
    return cookies


def _local_storage(path: Path, origin: str) -> list[dict]:
    raw = _read_json(path)
    if raw is None:
        return []
    items = raw.items() if isinstance(raw, dict) else raw
    return [{"origin": origin, "localStorage": [{"name": k, "value": v} for k, v in items]}]


def _report(cookies: list[dict], origins: list[dict], out: Path) -> None:
    auth = [c["name"] for c in cookies if any(m in c["name"].lower() for m in ("session", "auth", "token", "sid"))]
    print(f"Saved {out} ({len(cookies)} cookies, {sum(len(o['localStorage']) for o in origins)} localStorage entries)")
    if not auth:
        print("Warning: no cookie name looks like a login token. Check that you exported while logged in.")


def convert(agent: str, account: str | None = None) -> None:
    suffix = f"__{account}" if account else ""
    cookies = _cookies(config.SESSIONS_DIR / f"cookies_{agent}{suffix}.json")
    origins = _local_storage(config.SESSIONS_DIR / f"localstorage_{agent}{suffix}.json", _ORIGINS[agent])
    out = config.session_path(agent, account)
    out.write_text(json.dumps({"cookies": cookies, "origins": origins}, indent=2))
    _report(cookies, origins, out)


def merge(agent: str, domain: str, account: str | None = None) -> None:
    out = config.session_path(agent, account)
    if not out.exists():
        raise SystemExit(f"{out} does not exist yet: run `python scripts/import_cookies.py {agent}` first.")
    state = json.loads(out.read_text())
    merged = {(c["name"], c["domain"], c["path"]): c for c in state.get("cookies", [])}
    for c in _cookies(config.SESSIONS_DIR / f"cookies_{agent}_{domain}.json"):
        merged[(c["name"], c["domain"], c["path"])] = c
    state["cookies"] = list(merged.values())
    out.write_text(json.dumps(state, indent=2))
    _report(state["cookies"], state.get("origins", []), out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("agent", choices=list(config.PLATFORMS))
    parser.add_argument("--account", metavar="LABEL", help="a separate account, saved as sessions/<agent>__LABEL.json")
    parser.add_argument("--merge", metavar="DOMAIN", help="add a second domain's cookies to the existing session")
    args = parser.parse_args()
    config.SESSIONS_DIR.mkdir(exist_ok=True)
    if args.merge:
        merge(args.agent, args.merge, args.account)
    else:
        convert(args.agent, args.account)


if __name__ == "__main__":
    main()
