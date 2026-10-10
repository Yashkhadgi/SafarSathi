- Python 3.11, no new heavy dependency without asking.
- Never edit .env. Never hardcode API keys.
- New code goes in new files; keep old agents working behind a feature flag.
- Every tool function must NEVER raise: return {"error": "..."} or empty value.
- Add a test or smoke check for every feature.
- After finishing, list changed files and how to test manually.

## Phase 2 rules
- Stack: FastAPI + PostgreSQL (SQLAlchemy 2, Alembic) + React (Vite, TypeScript, Tailwind).
- All UI work must follow docs/DESIGN_RULES.md. Run scripts/design_lint.sh before finishing any UI task.
- Never store secrets in code. Never read or edit .env.
- Auth cookies: httpOnly, Secure, SameSite. Passwords: argon2id. Rate-limit every auth endpoint.
- Every endpoint that returns user data must check ownership. Add a test for it.
- Never show fake data, fake metrics, seeded demo numbers or placeholder testimonials. Use honest empty states.
- No booking and no payment features.
- Tool/API wrappers never raise; return {"error": "..."}.
- After each task: list changed files, new env keys (add to config/.env.example), and the manual checkpoint steps. Then STOP.
