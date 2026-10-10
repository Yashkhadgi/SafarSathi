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

## Testing rule (mandatory)
- A feature is NOT done until you have run it and seen it work: start backend and frontend, and run the flow end to end.
- Add Playwright e2e tests (npm run test:e2e). A USE_FAKE_LLM=true mode returns canned replies so tests cost nothing.
- Every task ends with the actual command output of the tests, not a claim.
- Raw exceptions must never reach the UI. Log the real error server side with a request id; show the user a short friendly message and a retry button.
- If you could not test something, say so explicitly.

