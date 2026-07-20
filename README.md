# tai-storage-s3

[![CI](https://github.com/tai42ai/tai-storage-s3/actions/workflows/ci.yml/badge.svg)](https://github.com/tai42ai/tai-storage-s3/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

An S3 `Storage` backend for the TAI ecosystem. It stores text, binary, and media
content in an S3 bucket, implementing the full `tai_contract.storage.Storage`
surface — the five text methods (`load` / `list` / `upload` / `delete` /
`delete_dir`) plus the binary/media methods (`load_bytes` / `upload_bytes` /
`stat`). S3 stores bytes natively, so the binary methods are true reads/writes
rather than the text bridge.

## The TAI ecosystem

TAI is an open-source runtime for MCP tools, agents, and workflows. A `Storage`
backend is "where content physically lives" — a pluggable provider the runtime's
`ResourceManager` loads and renders content over. This package is one such
provider (S3); siblings back the same contract with GitHub or the local
filesystem. The ecosystem is open-ended: any package can back the same contract,
so this repo is this provider's own full doc home, and the documentation site
covers the platform-level story:

- Storage & resources concept: https://tai42.ai/concepts/storage-and-resources
- Build a storage provider (author guide): https://tai42.ai/guides/authors/storage-provider
- Ecosystem catalog: https://tai42.ai/reference/catalog

Its only tai-* dependencies are `tai-contract` (the `Storage` ABC, `ObjectStat`,
`assert_not_root`, and the `tai_app` handle) and `tai-kit` (`PooledClient`,
`TaiBaseSettings`, and the settings cache). Beyond those it depends on its S3
driver (`aioboto3`, `botocore`) and `pydantic` / `pydantic-settings`.

## Install

Requires **Python 3.13+**. Nothing is on PyPI yet, so install from source — clone
this repo alongside your `tai-skeleton` checkout and add it as an editable
dependency of the environment that runs the server:

```bash
git clone https://github.com/tai42ai/tai-storage-s3
cd tai-skeleton   # or your own app checkout
uv add --editable ../tai-storage-s3   # once published: uv add tai-storage-s3
```

## Discovery

The skeleton discovers this backend by **importing its package** — importing
`tai_storage_s3` fires the `@tai_app.storage.register_storage` decorator on
`S3Storage` as a side-effect (there is no entry-point). Name the package in your
manifest's `storage_module` field so the runtime imports it at startup:

```yaml
storage_module: tai_storage_s3
```

## Configuration

Settings are read from the `STORAGE_S3_` environment group (see
`S3Settings`):

| Env var | Default | Purpose |
| --- | --- | --- |
| `STORAGE_S3_BUCKET` | — | Target bucket (required) |
| `STORAGE_S3_ENDPOINT` | — | Custom endpoint (e.g. MinIO); scheme inferred from `SECURE` if omitted |
| `STORAGE_S3_ACCESS_KEY` | — | AWS access key id |
| `STORAGE_S3_SECRET_KEY` | — | AWS secret access key |
| `STORAGE_S3_SECURE` | `true` | Use HTTPS |
| `STORAGE_S3_REGION` | `us-east-1` | AWS region |
| `STORAGE_S3_VERIFY_SSL` | `true` | Verify TLS certificates |
| `STORAGE_S3_CONNECT_TIMEOUT` | `5` | Connect timeout (seconds) |
| `STORAGE_S3_READ_TIMEOUT` | `30` | Read timeout (seconds) |
| `STORAGE_S3_ADDRESSING_STYLE` | `auto` | `path` / `virtual` / `auto` |
| `STORAGE_S3_REQUEST_CHECKSUM_CALCULATION` | — | `when_supported` / `when_required` |

## Content-type behavior

- `upload` (text) stores `ContentType: application/jinja2` — a template reads
  back as its authoring format, not an inferred `text/*`.
- `upload_bytes` stores the parametrized `content_type` as the object's
  `ContentType` (omitted when `None`).
- `stat` returns the object's stored `ContentType` via `head_object`, mapping a
  missing object (404) to `FileNotFoundError` — no raw `ClientError` or metadata
  leaks. Because text uploads store `application/jinja2`, `stat` on a text
  template reports that type; it reads as non-media, which is the only thing the
  content-type gates.

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv run pyright
```

## License

Apache-2.0. See `LICENSE` and `NOTICE`.
