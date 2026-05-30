from __future__ import annotations

from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_USER_AGENT = "katala-web-research/0.1 (+local research tool)"


@dataclass(slots=True)
class HttpResponse:
    url: str
    status: int
    headers: dict[str, str]
    body: bytes

    @property
    def text(self) -> str:
        content_type = self.headers.get("content-type", "")
        charset = "utf-8"
        if "charset=" in content_type:
            charset = content_type.split("charset=", 1)[1].split(";", 1)[0].strip()
        try:
            return self.body.decode(charset or "utf-8", errors="replace")
        except LookupError:
            return self.body.decode("utf-8", errors="replace")


class FetchError(RuntimeError):
    pass


def fetch_url(url: str, *, headers: dict[str, str] | None = None, timeout: int = 20) -> HttpResponse:
    merged = {"User-Agent": DEFAULT_USER_AGENT}
    if headers:
        merged.update(headers)
    request = Request(url, headers=merged)
    try:
        with urlopen(request, timeout=timeout) as response:
            return HttpResponse(
                url=response.geturl(),
                status=getattr(response, "status", 200),
                headers={k.lower(): v for k, v in response.headers.items()},
                body=response.read(),
            )
    except HTTPError as exc:
        body = exc.read()
        raise FetchError(f"HTTP {exc.code} for {url}: {body[:200]!r}") from exc
    except URLError as exc:
        raise FetchError(f"fetch failed for {url}: {exc.reason}") from exc

