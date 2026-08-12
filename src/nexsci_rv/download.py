"""Parallel FITS download.

Archive-agnostic: callers supply a function that turns a result-table row
into ``(filename, url)``. We do the rest:

- bounded thread pool
- atomic writes via ``.partial`` rename
- exponential-backoff retry on transient HTTP/network errors
- 401/403 → :class:`AuthExpired` immediately (no retry)
- tqdm progress bar
- partial-failure aggregation into :class:`DownloadError`
- filename sanitization (no path traversal, no absolute paths)
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING

import requests
from tqdm import tqdm

from .config import Conf
from .config import conf as default_conf
from .exceptions import AuthExpired, DownloadError

if TYPE_CHECKING:
    from astropy.table import Table

logger = logging.getLogger("nexsci_rv.download")

RowToUrl = Callable[[dict[str, object]], tuple[str, str]]
"""Callable that maps a row dict to ``(filename, full_download_url)``."""


def parallel_download(
    rows: Table,
    row_to_url: RowToUrl,
    outdir: Path,
    session: requests.Session,
    *,
    workers: int | None = None,
    resume: bool = True,
    progress: bool = True,
    conf: Conf | None = None,
) -> list[Path]:
    """Download all files referenced by ``rows`` into ``outdir``.

    Args:
        rows: Astropy result table.
        row_to_url: Per-archive callable that returns ``(filename, url)`` for a
            row. The filename will be sanitized before joining with ``outdir``.
        outdir: Destination directory; created if missing.
        session: HTTP session (typically supplied by ``SessionManager``).
        workers: Concurrency. Defaults to :attr:`Conf.download_workers`.
        resume: If True and a destination file already exists, skip when sizes
            match the remote ``Content-Length``.
        progress: Show a tqdm bar to stderr.
        conf: Process configuration.

    Returns:
        List of paths to successfully downloaded files (in input row order
        where possible).

    Raises:
        DownloadError: If any file failed. ``err.failures`` lists
            ``(filename, underlying_exception)`` for failures.
        AuthExpired: If the server returned 401/403 on any file.
    """
    conf = conf if conf is not None else default_conf
    workers = workers if workers is not None else conf.download_workers
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    plan: list[tuple[str, str]] = []
    for row in rows:
        row_dict = {col: row[col] for col in rows.colnames}
        filename, url = row_to_url(row_dict)
        plan.append((filename, url))

    successes: list[Path] = []
    failures: list[tuple[str, Exception]] = []
    auth_expired: AuthExpired | None = None

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(
                _fetch_one,
                session,
                url,
                outdir,
                filename,
                resume=resume,
                retries=conf.download_retries,
                timeout=conf.timeout,
            ): filename
            for filename, url in plan
        }

        bar = tqdm(total=len(futures), disable=not progress, unit="file", desc="downloading")
        try:
            for fut in as_completed(futures):
                fname = futures[fut]
                try:
                    successes.append(fut.result())
                except AuthExpired as exc:
                    auth_expired = exc
                    # Cancel everything still pending. Note: future.cancel()
                    # cannot interrupt tasks that have already started running
                    # — those will finish before the AuthExpired surfaces.
                    # Each running fetch will also raise AuthExpired itself on
                    # its 401/403, so the worst case is we wait for ~workers
                    # in-flight requests to complete before the user sees the
                    # error.
                    for other in futures:
                        other.cancel()
                except Exception as exc:
                    failures.append((fname, exc))
                finally:
                    bar.update(1)
        finally:
            bar.close()

    if auth_expired is not None:
        raise auth_expired

    if failures:
        raise DownloadError(
            f"{len(failures)} of {len(plan)} files failed to download",
            failures,
        )

    return successes


def _fetch_one(
    session: requests.Session,
    url: str,
    outdir: Path,
    filename: str,
    *,
    resume: bool,
    retries: int,
    timeout: float,
) -> Path:
    safe_name = _sanitize_filename(filename)
    dest = outdir / safe_name

    if resume and dest.exists() and _remote_size_matches(session, url, dest, timeout=timeout):
        logger.info("skipping (already present): %s", safe_name)
        return dest

    partial = dest.with_suffix(dest.suffix + ".partial")
    backoff = 1.0

    for attempt in range(retries + 1):
        try:
            with session.get(url, stream=True, timeout=timeout) as response:
                if response.status_code in (401, 403):
                    raise AuthExpired(
                        f"Download rejected (HTTP {response.status_code}) for {safe_name}. "
                        "Re-run .login()."
                    )
                response.raise_for_status()
                with partial.open("wb") as handle:
                    for chunk in response.iter_content(chunk_size=1024 * 64):
                        if chunk:
                            handle.write(chunk)
            partial.replace(dest)
            return dest
        except AuthExpired:
            raise
        except (requests.RequestException, OSError) as exc:
            if attempt == retries:
                if partial.exists():
                    partial.unlink(missing_ok=True)
                raise
            logger.warning(
                "download attempt %d/%d for %s failed: %s; retrying in %.1fs",
                attempt + 1,
                retries + 1,
                safe_name,
                exc,
                backoff,
            )
            time.sleep(backoff)
            backoff *= 2

    # Unreachable — loop above always returns or raises.
    raise RuntimeError("unreachable")


def _remote_size_matches(
    session: requests.Session, url: str, dest: Path, *, timeout: float
) -> bool:
    try:
        head = session.head(url, timeout=timeout, allow_redirects=True)
    except requests.RequestException:
        return False
    if head.status_code >= 400:
        return False
    length = head.headers.get("Content-Length")
    if length is None:
        return False
    try:
        remote_size = int(length)
    except ValueError:
        return False
    return dest.stat().st_size == remote_size


def _sanitize_filename(name: str) -> str:
    """Reject any filename that could escape the destination directory.

    Defense-in-depth: rather than silently stripping path components, we
    refuse any input that isn't already a plain filename. If the server ever
    returns a path-laden value where we expect a bare filename, that's a bug
    worth seeing rather than papering over.
    """
    if not isinstance(name, str) or not name:
        raise ValueError(f"Invalid filename: {name!r}")
    if any(c in name for c in "/\\") or "\x00" in name:
        raise ValueError(f"Unsafe filename (contains path separator or null): {name!r}")
    if name in (".", ".."):
        raise ValueError(f"Filename resolves to nothing useful: {name!r}")
    base = Path(name).name
    if base != name:
        raise ValueError(f"Unsafe filename (basename mismatch): {name!r}")
    return base


__all__ = ["RowToUrl", "parallel_download"]
