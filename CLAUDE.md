# WhoIsOnFirst

Renamed from WhoseOnFirst (WOF-36 epic). Old slug `whoseonfirst` survives on purpose in a few places: the `_LEGACY_SALT` bytes (never change), legacy `.stvault` imports, and prod infra until the WOF-39 cutover.

Automated on-call rotation + SMS notification system for a 7-person technical team. FastAPI + APScheduler + Twilio + SQLite. 8-page frontend (Tabler.io / Bootstrap 5). Docker-containerized; Portainer GitOps on prod.

## Docs

- **In-repo (`.context/`):** `architecture.md`, `technical-stack.md`, `code-patterns.md`, `authentication.md`, `rpi-process.md`. Foundation source of truth — tracked, travels with the code. Start at `.context/README.md`.
- **Voice:** [`.context/voice.md`](.context/voice.md) sets the audience, register and prose dials for comments, docstrings, UI copy and SMS text. Read it with `.claude/rules/prose-core.md` before writing any of those.
- **DocVault (in-repo, `DocVault/`):** `Overview.md`, PRD, Roadmap, research notes, sprint archives, runbooks. Human/product-facing + long-term research; edits ride the feature PR (DEVS-78). Security reviews and deploy/infra detail live in the **private companion** `Devops/DocVault/Projects/WhoIsOnFirst/` (`vault-path private`) — this repo is public and mirrored. Run `/vault-update` after behavior-affecting changes.

## Branch & Push Policy (overrides global)

**Default branch is `dev`** — both locally and as PR target. `main` is production. The Portainer GitOps stack auto-deploys from `main`, so any push to `main` fires real SMS at real coworkers on the next scheduler tick (WHO-49). A second stack, `whoisonfirst-dev`, GitOps-tracks `dev` with live Twilio limited to `SMS_ALLOWED_NUMBERS` (WOF-42), so merges to `dev` are live within ~5 min too.

- All work on `dev` or worktrees off `dev`.
- Both `main` AND `dev` require PRs — direct push blocked by GitHub rules. Always worktree + PR targeting `dev`.
- `dev → main` PRs only opened on explicit user "ship" or "release".
- Before any code change: verify you are on `dev` (or worktree off `dev`), not `main`. If on `main`, stop and switch.
- No version lock. main's ruleset gates on the Codacy check AND requires linear history (squash merge only) — verify with `gh api repos/{o}/{r}/rules/branches/main`, don't trust this file.

### Shipping dev → main

- dev and main accumulate conflicts (.gitignore, requirements, CLAUDE.md): build `release/vX.Y.Z` off dev, merge origin/main into it resolving dev-side, verify `git diff origin/dev release/vX.Y.Z` is EMPTY (proves shipped tree = tested tree), PR that to main.
- Codacy "new issues" on release PRs are baseline artifacts (pre-existing dev code). Dismiss true false positives per-alert, then `codacy pull-request ... --reanalyze-and-wait`.
- CodeRabbit re-reviews after every reply batch and re-sets CHANGES_REQUESTED — one reply+resolve pass, then dismiss its review and merge. Don't iterate.
- Post-merge: tag `vX.Y.Z` on the squash commit + publish GitHub Release.

## DEV DB — DO NOT RESTORE FROM PROD

Dev uses **sanitized data only**. Production DBs contain real names and phone numbers.

- **NEVER** copy from `~/Nextcloud/Backups/whoseonfirst/`, `~/Nextcloud/Backups/whoisonfirst/`, the VM backup dirs, or any production `.stvault` into dev (local or the hosted dev stack).
- **Correct restore:** `~/whoisonfirst-dev-data/backups/dev-seed-sanitized.stvault`, or let first-boot auto-seed handle it.
- `docker-compose.dev.yml` enforces rails: `SMS_MOCK_MODE=true`, no shared `.env` with prod.
- Hosted dev stack sends real SMS, so its rail is in code: with `APP_ENV=dev` and live Twilio, `SMSService` sends only to `SMS_ALLOWED_NUMBERS` and blocks everything when that is empty. Never unset it there.
- **Why this exists:** an AI agent once restored prod DB over dev, exposing real PII to a local container with mock security. Must not recur.

## Development

Docker-first. Port 8900.

```bash
docker-compose -f docker-compose.dev.yml up -d
# rebuild after code changes:
docker-compose -f docker-compose.dev.yml down && \
  docker-compose -f docker-compose.dev.yml build && \
  docker-compose -f docker-compose.dev.yml up -d
```

Dev DB seed (at start of session if `~/whoisonfirst-dev-data/whoisonfirst.db` missing/empty):
```bash
cp ~/whoisonfirst-dev-data/backups/dev-seed-sanitized.stvault \
   ~/whoisonfirst-dev-data/whoisonfirst.db
docker restart whoisonfirst-dev
```

Tests (local): `source venv/bin/activate && pytest --cov=src --cov-report=html`. Baseline 467+ tests. Target 80%+ coverage. Rotation algorithm + critical paths at 100%.

## Production Debugging

Prod runs on Portainer VM `192.168.1.81`, LAN-only behind NPM (the Cloudflare tunnel is being retired, WOF-39). The container is `whoseonfirst` (stack #12) until the WOF-39 cutover, then `whoisonfirst` — substitute below. Use `docker --context portainer <cmd>` for remote ops — no SSH needed. Claude never creates, stops, starts or redeploys stacks or containers (Devops `Portainer.md` HARD BLOCK); read-only only.

- **Healthcheck noise** (~99% of output): `docker --context portainer logs whoseonfirst --since 24h 2>&1 | grep -v "GET /health"`.
- **Requests missing from filtered logs** (e.g. a save fails with "NetworkError") = the request never reached FastAPI. Over the old Cloudflare tunnel this is an edge problem, not a code change (WOF-43); use the LAN hostname.
- **Production admin password is undocumented anywhere.** Dev container credentials live in auto-memory (`MEMORY.md`) — local dev only, never against production.
- **Backups:** `db-backup` container on the VM snapshots prod every 6h to `/home/infrastructure/backups/whoseonfirst/` (→ `whoisonfirst/` after the cutover edits `backup.sh`; 7-day retention, on-VM only, plus Proxmox nightly VM backups). The stvault export (`GET /api/v1/admin/export`) is NOT a backup — omits `users` + `notification_log` by design. Full backup: sqlite3 `.backup` API + `docker cp` off-host.

## Important Constraints

1. Timezone: `America/Chicago` (CST/CDT) via `pytz`. Daily SMS 8am, auto-renewal 2am, both CST.
2. Phone: E.164 only (`^\+1\d{10}$`). Pydantic validates all inputs.
3. Shift config: default 6 shifts, Shift 2 is 48h double (Tue–Wed).
4. Schedule gen: minimum 4 weeks advance. Regenerate from change date forward only — never the entire schedule.
5. DB: SQLAlchemy ORM exclusively, no raw SQL. Explicit transactions with rollback on errors.
6. Logs: mask phone numbers (last 4 digits only). All credentials in `.env`, never committed.
7. Scheduling: APScheduler (project standard), not system cron.
8. Schedule regeneration cascade-deletes ALL override history (`ondelete=CASCADE`, WOF-24) — a blank schedule-overrides page after a rebuild is expected, not a regression.

## RPI Workflow

Project-specific lightweight alternative to `/spec`: **Research → Plan → Implement** (3 phases). Full process: `.context/rpi-process.md`.

## Issue Tracking

Prefix `WOF`. Plane workspace `https://plane.lbruton.cc/lbruton/`. Create via `/issue` or `mcp__plane__workitem` (`action: "create"`).

## Hooks

- **gitleaks** (pre-commit, OPS-116, 2026-04-14) — scans for `github-pat`, `aws`, `stripe`, etc. via the `pre-commit` framework.
