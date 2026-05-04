# Always Near

Always Near is an MVP for a parent-approved AI comfort helper. Parents create a helper label, child profile, avatar, voice, and comfort scripts; children use a simplified child mode to receive short comfort responses. The app includes safety classification, parent alerts, an admin portal, and privacy/data-rights controls.

Always Near is not an emergency service, medical service, therapy service, or replacement for a real grown-up. High-risk child messages direct the child to find a real grown-up immediately and create a parent alert.

## Monorepo Layout

- `apps/api` - FastAPI backend, SQLAlchemy async models, Alembic migrations, tests.
- `apps/web` - Next.js 14 frontend with parent, child, admin, and privacy pages.
- `package.json` and `turbo.json` - root scripts for building and checking both apps.

## Environment Setup

Copy `.env.example` to `.env` in the repo root or provide the same variables in your deployment environment.

Required local variables:

```env
DATABASE_URL=sqlite+aiosqlite:///./always_near.db
NEXT_PUBLIC_API_URL=http://localhost:8000
JWT_SECRET=replace-with-a-long-random-secret
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
```

Provider defaults use local mocks:

```env
STORAGE_PROVIDER=local
STORAGE_LOCAL_PATH=./storage
VOICE_PROVIDER=local
OPENAI_API_KEY=
ELEVENLABS_API_KEY=
```

Production provider options:

- Storage: set `STORAGE_PROVIDER=s3` or `r2`, plus bucket, region, endpoint, access key, and secret key.
- Voice: set `VOICE_PROVIDER=elevenlabs`, `ELEVENLABS_API_KEY`, and optionally `ELEVENLABS_MODEL_ID`.
- Safety/comfort generation: set `OPENAI_API_KEY` and optionally `OPENAI_MODEL`. Without an OpenAI key, deterministic test-friendly fallbacks are used.
- LiveAvatar rendering: set `HEYGEN_LIVEAVATAR_ENABLED=true`, `HEYGEN_LIVEAVATAR_API_KEY`, and `HEYGEN_LIVEAVATAR_BASE_URL` after creating an approved LiveAvatar in the LiveAvatar platform. The frontend flag is `NEXT_PUBLIC_LIVEAVATAR_ENABLED=true`.

Do not hardcode secrets in source files. Keep API keys and JWT secrets in environment variables.

## Install

```bash
npm install
```

Install Python dependencies using the environment expected by `apps/api`. The current workspace uses Python packages directly, including FastAPI, SQLAlchemy, Alembic, Pydantic v2, python-jose, bcrypt/passlib, structlog, slowapi, and pytest.

## Database

From `apps/api`:

```bash
python -m alembic upgrade head
```

If the `alembic` executable is not on PATH, use `python -m alembic`.

## Run Locally

Backend:

```bash
npm run api:dev
```

Frontend:

```bash
npm run web:dev
```

Open the frontend at `http://localhost:3000`.

## Admin Portal

The admin portal lives at `/admin`. Backend admin endpoints require a JWT for a user with `role="admin"`. Parent users are blocked by backend role checks and by the frontend `RequireAdmin` guard.

Admin pages include:

- `/admin` - dashboard
- `/admin/alerts` - alert summaries only, no child transcripts
- `/admin/audit-logs` - audit event summaries
- `/admin/users` - basic user list

## Testing and QA

Run backend tests:

```bash
cd apps/api
python -m pytest
```

Run frontend checks from the repo root:

```bash
npm run typecheck
npm run lint
npm run build
```

The test suite covers authentication, models, avatars, voices, safety classification, response checking, helper labels, conversation flows, alerts, admin routes, data export/deletion, and forbidden phrase safety sweeps.

## Safety Rules

Runtime copy and generated responses must follow these rules:

- The helper identifies as `[Parent label]'s Always Near helper`.
- The helper must not claim to be the real parent.
- The helper must not discourage the child from getting a real grown-up.
- High-risk messages trigger the emergency flow and parent alert path.
- Admin alert views show summaries only, not full child transcripts.

Child mode is isolated from parent/admin navigation and includes a fixed emergency button on every child page.

## Data Rights and Privacy

Parents can:

- Export their own data via `GET /data/export`.
- Request deletion via `POST /data/delete-request`.
- Delete avatar and voice assets.
- Delete their account with the exact confirmation phrase.

Exports omit password hashes, raw files, signed URLs, and storage keys. Voice and avatar deletes mark records deleted and revoke/remove stored files where supported by the storage provider.

## Known Limitations

- Local providers are mocks intended for development and tests.
- Production voice/avatar providers require real credentials and provider review.
- Avatar animation is a simple frontend presentation, not real-time lip sync.
- HeyGen LiveAvatar support is isolated behind provider adapters. Local development uses mock behavior unless LiveAvatar credentials and flags are configured.
- Token revocation is represented by account deactivation; a dedicated token denylist is not implemented.
- Notifications are recorded as alerts but real push/email delivery is not implemented.
