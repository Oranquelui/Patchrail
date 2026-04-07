from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from patchrail.core.exceptions import PatchrailError


def post_json(
    *,
    url: str,
    headers: dict[str, str],
    body: dict[str, Any],
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    request = Request(
        url=url,
        data=json.dumps(body, ensure_ascii=True).encode("utf-8"),
        headers={"content-type": "application/json", **headers},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace").strip()
        except Exception:
            detail = ""
        if detail:
            raise PatchrailError(f"Provider API HTTP {exc.code}: {detail}") from exc
        raise PatchrailError(f"Provider API HTTP {exc.code}") from exc
    except URLError as exc:
        reason = exc.reason if getattr(exc, "reason", None) else str(exc)
        raise PatchrailError(f"Provider API connection error: {reason}") from exc
    except Exception as exc:
        raise PatchrailError("Provider API request failed") from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PatchrailError("Provider API returned non-JSON response") from exc
    if not isinstance(payload, dict):
        raise PatchrailError("Provider API response must be an object")
    return payload
