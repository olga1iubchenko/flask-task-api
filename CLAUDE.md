# Flask Task API

A simple REST API for task management. Used as a demo project for Claude Code CI/CD knowledge transfer sessions.

## Tech Stack
- Python 3.11
- Flask 3.x with Flask-SQLAlchemy
- SQLite (dev), PostgreSQL (prod)
- pytest for testing

## Code Standards
- Follow PEP8. Max line length: 88 characters.
- Type hints are required on all function signatures.
- Use `logger.error()` / `logger.info()` — never `print()`.
- All routes must return proper HTTP status codes (400 for bad input, 404 for not found, etc.).

## Review Checklist
When reviewing PRs, always check for:
1. **Input validation** — all POST and PUT routes must validate required fields and reject empty/None values with HTTP 400.
2. **Error handling** — routes must handle missing resources gracefully.
3. **No raw SQL** — use SQLAlchemy ORM only.
4. **Tests** — new routes must have corresponding tests in `tests/test_app.py`.
5. **Logging** — significant actions (create, delete) should be logged at INFO level.

## Do NOT modify
- `migrations/` folder — handled separately by DBA team.
- `config/production.py` — production config is managed via environment variables.

## Running locally
```bash
pip install -r requirements.txt
python app.py
```

## Running tests
```bash
pytest tests/ -v
```
