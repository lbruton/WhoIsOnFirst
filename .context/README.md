# `.context/`: WhoIsOnFirst foundation docs

These tracked docs are the source of truth for the architecture, the standards and the workflow.
They travel with the code to every mirror, including the corporate GitLab.

Foundation docs for agents live here. Product material and long-term research live in the in-repo
`DocVault/`. Security reviews and infrastructure detail live in the private companion
`Devops/DocVault/Projects/WhoIsOnFirst/`.

## Documents

| File | Purpose | Read before… |
| --- | --- | --- |
| [architecture.md](architecture.md) | System design: FastAPI app, APScheduler jobs, SQLite/SQLAlchemy data layer, Twilio integration, 8-page frontend. | Touching `src/` structure, scheduler, or data model. |
| [technical-stack.md](technical-stack.md) | Stack decisions and rationale: FastAPI, APScheduler, SQLAlchemy, Tabler.io/Bootstrap 5, Docker. | Adding a dependency or evaluating a stack change. |
| [code-patterns.md](code-patterns.md) | Recurring implementation patterns: ORM/transaction conventions, phone masking, validation, error handling. | Writing any new `src/` code. |
| [authentication.md](authentication.md) | Auth system design: Argon2id hashing (OWASP 2025 params), session model. | Touching auth, sessions, or password handling. |
| [voice.md](voice.md) | Prose dials: audience, register, docstring format, UI and SMS copy rules, exemptions. | Writing comments, docstrings, UI copy or SMS text. |
| [rpi-process.md](rpi-process.md) | The project's Research → Plan → Implement workflow (override of the global spec-workflow). | Starting any non-trivial feature, `/spec` or quick-fix work. |

## Conventions

- These docs describe the intended design. The context-drift skill audits them against the code.
  Check the named source before you rely on a claim.
- Update the relevant doc in the same PR as a behavior change to the area it covers.
