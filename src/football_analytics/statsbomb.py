"""Download StatsBomb open data files, keeping a local copy of each file exactly as served."""

import json
import logging
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
RETRYABLE_STATUS = {429, 500, 502, 503, 504}

log = logging.getLogger(__name__)


class StatsBombClient:
    """Fetches files such as `matches/43/106.json` by their path in the open-data repository.

    With a cache directory, each file is saved on first download and read from disk afterwards,
    so reruns do not download the same files again.
    """

    def __init__(self, cache_dir: Path | None = None, attempts: int = 3, timeout: float = 60):
        self.cache_dir = cache_dir
        self.attempts = attempts
        self.timeout = timeout

    def fetch(self, path: str) -> Any:
        cached = self.cache_dir / path if self.cache_dir else None
        if cached and cached.exists():
            return json.loads(cached.read_bytes())

        raw = self._download(f"{BASE_URL}/{path}")
        if cached:
            cached.parent.mkdir(parents=True, exist_ok=True)
            cached.write_bytes(raw)
        return json.loads(raw)

    def _download(self, url: str) -> bytes:
        request = urllib.request.Request(url, headers={"User-Agent": "football-analytics"})
        for attempt in range(1, self.attempts + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return response.read()
            except urllib.error.HTTPError as err:
                if err.code not in RETRYABLE_STATUS or attempt == self.attempts:
                    raise
                log.warning("HTTP %s for %s, retrying (attempt %s)", err.code, url, attempt)
            except urllib.error.URLError as err:
                if attempt == self.attempts:
                    raise
                log.warning("%s for %s, retrying (attempt %s)", err.reason, url, attempt)
            time.sleep(2**attempt)
        raise AssertionError("unreachable")
