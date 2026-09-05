# Contributing

## Development

1. Create a Python 3.11+ environment in `backend`.
2. Install dependencies with `uv sync`.
3. Copy `backend/.env.example` to `backend/.env` and configure local services.
4. Run the API with `uv run uvicorn app.main:app --reload`.

## Before Opening a Pull Request

- Keep comments focused on non-obvious decisions and security boundaries.
- Do not commit `.env` files, API keys, local databases, generated indexes, caches, or uploaded PDFs.
- Run `python -m compileall -q backend/app backend/*.py`.
- Update the README when setup or runtime behavior changes.
