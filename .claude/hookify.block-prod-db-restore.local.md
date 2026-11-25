---
name: block-prod-db-restore
enabled: true
event: bash
pattern: Nextcloud/Backups/who(se|is)onfirst|docker\s+(--context\s+\S+\s+)?cp.*\.db.*who(se|is)onfirst-dev|backups/who(se|is)onfirst.*\.db.*who(se|is)onfirst-dev
action: block
---

BLOCKED: Restoring production backups to dev environment is prohibited (WHO-49 guardrail).

The Opus incident showed AI agents will overwrite dev data with production backups if not blocked.

Correct procedure:

- Let first-boot auto-seed (admin/Admin123!, viewer/User123!)
- Or import sanitized seed: `~/whoisonfirst-dev-data/backups/dev-seed-sanitized.stvault`
- NEVER use files from `~/Nextcloud/Backups/whoseonfirst/`, `~/Nextcloud/Backups/whoisonfirst/` or production `.db` files
- This applies to the hosted `whoisonfirst-dev` stack too: it sends real SMS (WOF-42).

Both slugs are matched until the WOF-40 cleanup (2026-11-30); after that, keep `whoisonfirst` only.
