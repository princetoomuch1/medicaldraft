# Medical Draft

Backend scaffolding for a medical-data application. Early-stage — module skeletons in place, implementation pending.

## Structure

```
backend/
  api/      # HTTP route handlers (FastAPI planned)
  db/       # Database layer + migrations
  engine/   # Domain logic / processing core
  models/   # Pydantic/ORM models
```

## Planned Stack

- Python 3.11+
- FastAPI
- PostgreSQL (or SQLite for dev)
- Pydantic v2

## Status

Skeleton only. Modules are empty placeholders awaiting design decisions on:
- exact medical domain scope
- HIPAA/data-handling requirements
- frontend pairing

## Frontend Prototype

A minimal React-based UI skeleton has been added under `frontend/` with a star-rating component and notes form for early concept validation.

## Next Steps

1. Pin domain scope (one specialty / use case).
2. Define core data models in `backend/models/`.
3. Stand up minimal API + DB connection in `backend/api/` and `backend/db/`.
4. Integrate `frontend/` with backend endpoints and add real medical workflows.

## License

MIT (placeholder — to be confirmed once scope is set).
