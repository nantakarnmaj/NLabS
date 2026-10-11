# Prompt for Antigravity

Develop BreathQuest in this repository. First read:

1. `docs/BREATHQUEST_IMPLEMENTATION_SPEC.md`
2. `docs/BREATHQUEST_ORIGINAL_BRIEF.md`
3. Any applicable `AGENTS.md` instructions.

The implementation specification takes precedence over conflicting details in the original brief. Preserve its learning goals and specified technology stack.

Inspect the repository before making changes. At the last readiness check it was empty apart from the handoff documents; recheck its actual state. Preserve all existing work. Do not refactor unrelated code, delete persistent files, clear databases, drop tables, or overwrite production data.

Implement **Checkpoint A only**:

- Flask application factory and environment configuration.
- SQLAlchemy and Flask-Migrate with an explicit migration baseline.
- Correct instance-relative SQLite configuration.
- Mission, MissionPrerequisite, StudentSession, and MissionProgress foundation.
- Explicit idempotent seed command for four rooms and prerequisites.
- Secure anonymous session start with CSRF and hashed server-side tokens.
- Home, Respiratory Ward, and an honest Room 501 preview.
- Compiled Tailwind and local runtime assets.
- Health checks, isolated automated tests, and setup/deployment documentation.

Required ward states:

- Room 501 — Clear the Airway — Ready. Label the action “View mission preview” and explain that gameplay comes in Checkpoint B.
- Room 502 — Support the Breath — Coming Soon.
- Room 503 — Open the Airway — Coming Soon.
- Room 504 — Respiratory Rescue — Locked.

Do not implement full missions, generate clinical treatment rules, invent faculty approval, award fake badges, or introduce student scores. Do not install or configure cloud services. Do not modify Apache/XAMPP settings automatically.

Make minimal, incremental changes. Run relevant automated tests in temporary databases, build CSS, run the application, and inspect layouts at 360, 390, 768, 1024, and 1440 CSS pixels. Check keyboard navigation, focus, and zoom. Record actual evidence; clearly state any check that could not be performed.

Deliver the implementation report required by section 13 of the specification. Highlight potential side effects and architectural deviations. Recommend Checkpoint B, then **STOP**. Do not automatically continue into gameplay development.
