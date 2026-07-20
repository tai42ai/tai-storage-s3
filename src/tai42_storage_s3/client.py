"""The pooled aioboto3 S3 client.

``S3Client`` subclasses ``tai42_kit.clients.PooledClient`` — one connected S3 client
per event loop, reached through ``tai42_app.clients.client_ctx(S3Client)``. It reads
its connection from the cached ``s3_settings`` singleton, so the pool key stays
empty (a single configured client per loop).
"""

from __future__ import annotations

from typing import Any

import aioboto3
from botocore.config import Config
from botocore.exceptions import ConnectionError as BotocoreConnectionError
from botocore.exceptions import HTTPClientError
from tai42_kit.clients.base import PooledClient, is_loop_bound_runtime_error, reject_unknown_connection_kwargs

from tai42_storage_s3.settings import s3_settings

# The S3 client reads its entire connection from the cached settings singleton,
# so it accepts no connection kwargs — anything passed is a typo that would
# silently split the pool key and is rejected loudly.
_ALLOWED_KWARGS: frozenset[str] = frozenset()


class S3Client(PooledClient[Any]):
    async def _create(self, **kwargs: Any) -> Any:
        reject_unknown_connection_kwargs("S3 client", kwargs, _ALLOWED_KWARGS)
        settings = s3_settings()

        endpoint = settings.endpoint
        if endpoint and not endpoint.startswith(("http://", "https://")):
            protocol = "https" if settings.secure else "http"
            endpoint = f"{protocol}://{endpoint}"

        session = aioboto3.Session()
        context = session.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=settings.access_key.get_secret_value() if settings.access_key else None,
            aws_secret_access_key=settings.secret_key.get_secret_value() if settings.secret_key else None,
            region_name=settings.region,
            verify=settings.verify_ssl,
            use_ssl=settings.secure,
            config=Config(
                connect_timeout=settings.connect_timeout,
                read_timeout=settings.read_timeout,
                s3={"addressing_style": settings.addressing_style},
                request_checksum_calculation=settings.request_checksum_calculation,
            ),
        )
        # Enter the aioboto3 client context and return the live client. The pool
        # closes it via ``_close`` (``client.close()``), so no per-instance state
        # is kept — a fresh ``S3Client()`` built by the pool's shutdown sweep can
        # close any client it is handed.
        return await context.__aenter__()

    async def _close(self, client: Any) -> None:
        await client.close()

    def _disconnection_exceptions(self) -> tuple[type[Exception], ...]:
        # botocore signals a dead connection through its own exception tree, not
        # the builtin ConnectionError: botocore's ConnectionError covers the
        # endpoint/connect failures and HTTPClientError the transport-level HTTP
        # failures (closed connections, read timeouts). A ClientError — an API
        # error carried over a healthy connection — matches neither, so it never
        # evicts the pooled client.
        return (BotocoreConnectionError, HTTPClientError)

    def _is_disconnection_error(self, exc: BaseException) -> bool:
        # The aiohttp transport underneath aiobotocore is loop-bound and surfaces
        # use after its event loop closed as a plain RuntimeError ("Event loop is
        # closed" / "... attached to a different loop"); match those by message so
        # an unrelated RuntimeError raised by caller code never tears down the
        # pool.
        return super()._is_disconnection_error(exc) or is_loop_bound_runtime_error(exc)
