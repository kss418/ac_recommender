"""HTTP fetching and response-type helpers."""

from __future__ import annotations

import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request

from atcoder_editorials.models import FetchResult


def fetch_url(
    url: str,
    *,
    timeout: float,
    retries: int,
    user_agent: str,
    verify_tls: bool = True,
) -> FetchResult:
    last_error: Exception | None = None
    context = None if verify_tls else ssl._create_unverified_context()
    for attempt in range(retries + 1):
        request = urllib.request.Request(url, headers={"User-Agent": user_agent})
        try:
            with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
                return FetchResult(
                    url=response.geturl(),
                    status=response.status,
                    content_type=response.headers.get("Content-Type", ""),
                    body=response.read(),
                )
        except urllib.error.HTTPError:
            raise
        except urllib.error.URLError as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(min(2**attempt, 8))
    assert last_error is not None
    raise last_error


def decode_html(result: FetchResult) -> str:
    charset_match = re.search(r"charset=([\w.-]+)", result.content_type, re.IGNORECASE)
    charset = charset_match.group(1) if charset_match else "utf-8"
    return result.body.decode(charset, errors="replace")


def is_pdf(result: FetchResult, url: str) -> bool:
    content_type = result.content_type.lower()
    return "application/pdf" in content_type or urllib.parse.urlparse(url).path.lower().endswith(".pdf")


def is_tls_certificate_error(exc: BaseException) -> bool:
    if isinstance(exc, ssl.SSLCertVerificationError):
        return True

    reason = getattr(exc, "reason", None)
    if isinstance(reason, ssl.SSLCertVerificationError):
        return True

    return "CERTIFICATE_VERIFY_FAILED" in str(exc)
