"""An unreachable database must fail fast, not hang the request.

asyncpg's default connect timeout is 60 seconds. A teammate whose PostgreSQL is
absent or misconfigured does not get an error -- they get a page that sits there
for a minute and then quietly serves the CSV fallback. On a demo screen that
reads as a broken product.
"""
import time

import pytest

from app.core.database import build_engine


@pytest.mark.asyncio
async def test_unreachable_database_gives_up_quickly():
    # 203.0.113.1 is TEST-NET-3 (RFC 5737): reserved for documentation and not
    # routed, so the connection hangs rather than being refused -- which is what
    # a firewalled or wrong-host PostgreSQL actually does.
    engine = build_engine("postgresql+asyncpg://u:p@203.0.113.1:5432/db")
    started = time.monotonic()
    with pytest.raises(Exception):
        async with engine.connect():
            pass
    elapsed = time.monotonic() - started
    await engine.dispose()

    assert elapsed < 15, f"took {elapsed:.1f}s to give up; the connect timeout is not being applied"
