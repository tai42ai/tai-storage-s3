# Contributing to tai42-storage-s3

`tai42-storage-s3` is the S3 **Storage** backend for the TAI ecosystem: it stores
text, binary, and media content in an S3 bucket, implementing the full
`tai42_contract.storage.Storage` surface. Because S3 stores bytes natively, the
binary methods (`load_bytes` / `upload_bytes`) are true reads/writes rather than
a text bridge. The hard rule (the plugin rule): **it depends on `tai42-contract` +
`tai42-kit` only and never imports the skeleton** — beyond those it depends only on
its S3 driver, `aioboto3`. Importing the `tai42_storage_s3` package fires the
`@tai42_app.storage.register_storage` decorator on `S3Storage` as a side-effect, so
naming the package in a manifest's `storage_module` activates it — there is no
import edge to the skeleton in either direction.

## Ground rules

- **No skeleton import — ever.** The package is contract-facing; the ban is
  enforced by ruff (`flake8-tidy-imports`), so a stray import fails lint:
  ```bash
  grep -rn "tai42_skeleton" src/   # must be empty
  ```
- **Loud errors, no metadata leaks.** A missing object (404) maps to
  `FileNotFoundError`; a raw `ClientError` or bucket metadata never surfaces to
  the caller.
- **Typed package** (`py.typed`). Pyright runs clean.

## Layout

- `storage.py` — `S3Storage` (the `Storage` impl) and its registration.
- `client.py` — the pooled S3 (`aioboto3`) client.
- `settings.py` — the `STORAGE_S3_` settings.

## Naming

PyPI is a flat namespace with no owner in the path, so distributions carry the
`tai42-` prefix. GitHub repositories keep their `tai-` names, because the
`tai42ai` organisation already namespaces them. Import packages follow the
distribution.

| Surface | Form |
| --- | --- |
| Distribution — PyPI, `pip install`, dependency pins | `tai42-<name>` |
| Import package | `tai42_<name>` |
| GitHub repository and sibling checkout directory | `tai-<name>` |

So a dependency is declared as `tai42-<name>` but resolved from `../tai-<name>`
during local development, and both spellings are correct in their own context.

Some surfaces are deliberately neither, and must not be renamed: the `tai` CLI
command (`tai42` is an alias), the Prometheus metric namespace (`tai_tool_*`),
`TAI_*` environment variables, and the `tai-plugin.yml` descriptor filename.

## Dev

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

For local cross-repo work, `make dev` editable-installs the sibling `tai-*`
checkouts this package builds on into the venv. While `[tool.uv.sources]` pins
those siblings to local paths, `uv sync` already installs them editable and
`make dev` changes nothing; once the lock resolves them from the registry,
`uv sync` / `uv run` installs the published builds instead, so re-run
`make dev` afterward to restore the editable links.

Before any commit, run a secret scan over `src/` and `tests/` (e.g.
`detect-secrets scan`).

## License

By contributing you agree your contributions are licensed under Apache-2.0.
