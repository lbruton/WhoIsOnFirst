---
tags: []
doc_type: overview
project: whoisonfirst
source: manual
aliases: ["WhoIsOnFirst Overview", "WhoIsOnFirst"]
created: "2026-03-11"
updated: "2026-11-25"
---

# WhoIsOnFirst

> Public copy. The private companion `Devops/DocVault/Projects/WhoIsOnFirst/Overview.md` (`vault-path private`) holds the hosts, addresses and deploy detail.

WhoIsOnFirst is an on-call rotation and SMS notification system. It assigns shifts to a team, keeps the schedule weeks ahead and texts the person on call through Twilio each morning.

## At a glance

| Field | Value |
| --- | --- |
| Repo | [lbruton/WhoIsOnFirst](https://github.com/lbruton/WhoIsOnFirst) |
| Language | Python 3.12 (FastAPI backend), vanilla JavaScript frontend (Tabler) |
| Branches | `dev` is the default branch and the PR target. `main` is production and deploys through Portainer GitOps. Both branches require a PR. |
| Version | 2.0.0 ([CHANGELOG](../CHANGELOG.md)). The project has no version lock. |
| Issues | [Plane](https://plane.lbruton.cc/lbruton/), prefix `WOF` |

## Features

- Circular rotation over 24-hour and 48-hour shifts. Schedule generation starts the first member on the chosen start date and never creates entries before it.
- A daily SMS at 8:00 AM Central from an editable template.
- Two fixed escalation contacts behind the rotation.
- A Monday digest of the week's schedule. It goes to members who opt in, to escalation contacts whose digest flag is on and to up to 10 digest-only recipients. Digest-only recipients get no shift SMS and do not appear on the dashboard. Each phone number gets one copy.
- Shift overrides for vacation, sick leave and swaps, with a history.
- Admin and viewer roles with session authentication.
- Backup and restore through `.stvault` files. A restore is atomic.
- A progressive web app with dark mode and layouts for phones and tablets.

## How it is deployed

Production runs as a Docker container on the [Portainer](/Volumes/DATA/GitHub/Devops/DocVault/KnowledgeBase/Infrastructure/Portainer.md) VM behind the [NPM](/Volumes/DATA/GitHub/Devops/DocVault/KnowledgeBase/Infrastructure/NPM.md) reverse proxy. It is reachable on the home LAN and over the VPN only. No Cloudflare tunnel serves it.

| Component | Detail |
| --- | --- |
| Stack | `whoisonfirst` in the [Stack Registry](/Volumes/DATA/GitHub/Devops/DocVault/KnowledgeBase/Infrastructure/Stack%20Registry.md), from the `main` branch with 5-minute GitOps polling |
| Port | 8900 on the host, 8000 in the container |
| Database | SQLite at `/app/data/whoisonfirst.db` on the [named volume](/Volumes/DATA/GitHub/Devops/DocVault/KnowledgeBase/Infrastructure/Named%20Volumes.md) `whoisonfirst_whoseonfirst-data`. The compose volume key stays `whoseonfirst-data` on purpose. |
| Health check | `GET /health` every 30 seconds |
| Backups | The [db-backup](/Volumes/DATA/GitHub/Devops/DocVault/KnowledgeBase/Infrastructure/Backups.md) container copies the database with `sqlite3 .backup` every 6 hours |
| Dev stack | `whoisonfirst-dev` tracks `dev`. It sends real SMS only to the numbers in `SMS_ALLOWED_NUMBERS`. |

### Corporate deployment (planned)

| Component | Detail |
| --- | --- |
| Source sync | GitHub to the corporate GitLab mirror |
| Deploy | The corporate server admin deploys from GitLab to Kubernetes |
| Secrets | The production Twilio keys live in the Kubernetes environment, not in the repo |
| Dev safety | Development uses dummy Twilio keys and 555 phone numbers |

A development environment never holds live Twilio credentials, so it cannot send a duplicate SMS.

## Architecture

FastAPI with the SQLAlchemy ORM and Alembic migrations.

| Component | Technology |
| --- | --- |
| Framework | FastAPI 0.162 and Uvicorn |
| Database | SQLAlchemy 2.1 and Alembic on SQLite. PostgreSQL is a later option. |
| Scheduling | APScheduler 3.11 |
| Admin seed | The first start on an empty database creates `admin` with the password `Admin123!` |
| SMS | Twilio SDK 9.12 |
| Auth | Argon2id through argon2-cffi |
| Validation | Pydantic 2.14 |
| Frontend | Tabler 1.6.1 (Bootstrap 5), vanilla JavaScript, no build step |
| Testing | pytest, Playwright for the frontend specs |

### Development workflow

The project uses RPI (Research, Plan, Implement), a three-phase process lighter than the spec workflow. The repo holds it in `.context/rpi-process.md`.

## Architecture decisions

- **FastAPI over Express:** Python has the better scheduling (APScheduler) and SMS (Twilio) libraries.
- **SQLite first:** one instance needs no database server. PostgreSQL waits for a multi-instance deploy.
- **Tabler frontend:** Bootstrap 5, a 16-color WCAG AA palette for members and no build step.
- **LAN-only access:** the app needs no inbound internet traffic, because Twilio SMS is outbound only.
- **RPI over the spec workflow:** a lighter process suits a project with one developer.

## Documentation

The foundation docs (architecture, stack, code patterns, authentication, RPI) live in the repo under `.context/`, so they travel with the code to the GitLab mirror. Start at `.context/README.md`. Product and research material lives here in DocVault.

| Doc | Notes |
| --- | --- |
| [[PRD]] | Product requirements |
| [[Roadmap]] | Planned work |
| [[Runbooks/real-sms-test]] | Send a real SMS from the dev stack |
| [[Research/research-notes]] | Framework and library research |
| [[Research/memento-taxonomy]] | Memento knowledge-graph taxonomy |
| `Sprints/` | Archived sprint logs, one file for each sprint |

## Related

- [Plane issues](https://plane.lbruton.cc/lbruton/): open and closed `WOF` issues
- [Portainer](/Volumes/DATA/GitHub/Devops/DocVault/KnowledgeBase/Infrastructure/Portainer.md): the Docker host
- [Stack Registry](/Volumes/DATA/GitHub/Devops/DocVault/KnowledgeBase/Infrastructure/Stack%20Registry.md): the prod and dev stacks
- [Named Volumes](/Volumes/DATA/GitHub/Devops/DocVault/KnowledgeBase/Infrastructure/Named%20Volumes.md): the database volume
- [Backups](/Volumes/DATA/GitHub/Devops/DocVault/KnowledgeBase/Infrastructure/Backups.md): the SQLite backup job
