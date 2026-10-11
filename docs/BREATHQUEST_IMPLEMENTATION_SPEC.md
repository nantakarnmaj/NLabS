# BreathQuest — Implementation specification v1.1

Status: ready for Checkpoint A development; not clinical approval or production certification.

This specification accompanies `BREATHQUEST_ORIGINAL_BRIEF.md`. Read both. Preserve the original product, mission narratives, technology stack, and learning principles. Where implementation details conflict, this specification takes precedence. Future-phase requirements describe design constraints; they do not authorize implementing those phases now.

## 1. Product contract

Build a mobile-first, web-based formative respiratory-care game for second-year nursing students who have already studied the relevant theory. Use a simulated ward, patient responses, immediate feedback, retry opportunities, reflection, completion states, and badges.

- No numeric grades, performance percentages, pass/fail labels, rankings, leaderboards, or competency certificates.
- Clinical measurements such as SpO₂ percentages are allowed. Activity counts and time are allowed; do not frame them as performance scores.
- Wrong actions must support learning and recovery. Do not label the learner as a failure.
- Badges acknowledge participation and completion, not clinical competence.
- Use synthetic patients only. Do not collect real patient identifiers or clinical records.
- No cloud service is required to run the application.
- Student accounts, CMS, SSO, LMS integration, AI chatbot, voice, multiplayer, and 3D remain out of scope.

## 2. Delivery boundaries

### Checkpoint A — implement now

Deliver the application factory, configuration, database foundation, migration baseline, idempotent mission seed, anonymous server-side session, read-only progress presentation, compiled Tailwind styles, home and ward pages, automated tests, and deployment instructions.

The ward must show these exact product states:

| Room | Title | State | Behavior |
|---|---|---|---|
| 501 | Clear the Airway | Ready | Open an honest preview page explaining that the playable mission arrives in Checkpoint B |
| 502 | Support the Breath | Coming Soon | Informational card; no start action |
| 503 | Open the Airway | Coming Soon | Informational card; no start action |
| 504 | Respiratory Rescue | Locked | Explain the three prerequisite missions; no start action |

“Ready” at Checkpoint A means the room entry and technical foundation are ready, not that a learner can complete the mission. Show “Mission preview — gameplay coming in Checkpoint B” beside the Room 501 action. The action label must be “View mission preview,” not “Start mission.” This distinction must remain visible on mobile.

Do not create placeholder quizzes, fake completion, simulated earned badges, or a clickable path that appears to complete a mission. Room 501 preview does not create a mission attempt or mark progress as started.

### Later checkpoints — do not implement yet

- B: complete Room 501 and validate reusable activity evaluation, patient state, retries, progress, badge award, and debrief end to end.
- C: Room 502, including setup, device matching, and trend monitoring.
- D: Room 503, including medication checks, assembly, and troubleshooting.
- E: Room 504, accepted action sets, branching, deterioration, escalation, and action timeline.
- F: refinement, accessibility, performance, content review, deployment rehearsal, and operational readiness.

Do not proceed beyond A without a new instruction. A technical demonstration is not a student pilot. A pilot requires complete playable content and faculty approval for the included missions.

## 3. Stack and project layout

Keep Python 3, Flask, Flask-SQLAlchemy, SQLAlchemy, Flask-Migrate/Alembic, Waitress, Jinja, Tailwind CSS, vanilla JavaScript, SortableJS, and SQLite. PostgreSQL is a future migration target. No SPA framework or new backend framework.

Use one importable package:

```text
run.py
config.py
requirements.txt
requirements-dev.txt
package.json
package-lock.json
.env.example
.gitignore
app/
  __init__.py
  extensions.py
  models/
  routes/
  services/
  templates/
    activities/
  static/
    css/app.css
    js/
    images/
  assets/css/input.css
migrations/
seed/
tests/
docs/
instance/                 # runtime data; never commit its contents
```

All Python models/routes/services live under `app/`; do not create competing root packages. Add files when used, not empty modules for every future feature. Select and document a supported Tailwind version. Use that version’s correct build configuration; a `tailwind.config.js` is required only if that version/workflow needs it.

Pin tested Python dependency versions and commit the npm lockfile. Record the tested Python and Node versions. Node is build-time only. Install SortableJS locally when its first activity is implemented. Serve runtime JavaScript, CSS, fonts, and images locally; no CDN dependency.

## 4. Application and configuration

- Implement `create_app(config_override=None)` and extension initialization through `init_app`.
- Importing modules or starting the server must not create tables, seed data, run migrations, or modify existing content.
- Use separate development, test, and production configuration. Production is the documented deployment mode, never Flask debug mode.
- Read `SECRET_KEY`, `DATABASE_URL`, deployment mode, and cookie policy from the environment. Environment variables override optional local development `.env` values. Document whether and how `.env` is loaded; Waitress must not silently depend on Flask CLI dotenv behavior.
- Require a nonempty secret outside tests. Reject known example/default secrets in production. Provide a command to generate a secret, never commit one.
- With Flask-SQLAlchemy, use `sqlite:///breathquest.db` for a database relative to Flask’s instance directory. The original `sqlite:///instance/breathquest.db` example risks a nested instance path and is superseded.
- Resolve the instance directory from the application location, not the process working directory. Create the directory if absent, but never delete or replace its contents.
- Use portable path handling. No hard-coded user directories, drive letters, host IPs, credentials, or deployment hostnames.
- Use timezone-aware UTC application timestamps and a documented serialization convention. Test database round trips; SQLite does not preserve timezone information automatically.
- Provide `/health/live` for process health and `/health/ready` for database/schema readiness. Return 503 when the database or required schema is unavailable, with no stack trace, path, or credentials in the response.
- Health checks must not create learner sessions or application data. Schema readiness can be checked using a read-only query against a required table; liveness must not depend on the database.

## 5. Data model and migrations

Use the original entities, with the following corrections and additions. Implement only the A subset now.

### A subset

**Mission:** original fields plus `availability` (`preview`, `coming_soon`, `playable`). Unique `slug` and `room_number`; non-null display order and timestamps. `is_active` controls visibility. Availability is distinct from learner completion and prerequisite locking.

**MissionPrerequisite:** `mission_id`, `prerequisite_mission_id`, unique pair, no self-reference. Seed Room 504 prerequisites as 501, 502, and 503. Content validation must reject cycles when authoring tools are introduced.

**StudentSession:** original lifecycle fields plus `token_hash`, `expires_at`. Store a digest of the token, never the raw token. The original plaintext `session_token` field is superseded. Nickname is optional and omitted from A UI. Anonymous records are pseudonymous data, not proof that no privacy obligations exist.

**MissionProgress:** session/mission foreign keys; unique `(session_id, mission_id)`; constrained status; timestamps. In A, no row means `not_started`. Do not create an Activity table merely to support an unused `current_activity_id`: add that foreign key in B. Completed activity count is derived from normalized records in B, not an authoritative client-supplied integer.

Do not implement Badge, attempts, or clinical content tables in A unless required by a demonstrated dependency. Mission metadata is enough for ward rendering.

### B and later additions

- Preserve Scenario, Activity, ActivityOption, ProcedureStep, Feedback, ActivityAttempt, and Badge from the original brief.
- Add **ActivityProgress** with unique `(mission_progress_id, activity_id)`, completion timestamp, and required completion evidence. Retries do not create duplicate completion records.
- Add **SessionBadge** with unique `(session_id, badge_id)`, mission reference, and awarded timestamp. A badge definition alone cannot record earned badges.
- Add **MissionRun** for a replayable mission: session, mission, scenario/content version, lifecycle, current activity, patient state JSON, state revision, and timestamps. Tie attempts and activity completion to the run. Adjust ActivityProgress uniqueness to `(mission_run_id, activity_id)` when introduced.
- MissionProgress summarizes lasting mission completion; MissionRun holds each playthrough. Replay starts a new run without erasing earlier attempts, badges, or completion.
- ActivityAttempt records the run, activity, attempt number, bounded response JSON, result type, server timestamps, and request idempotency key. Uniqueness must prevent duplicate attempt numbers and duplicate request application within a run.
- Resolve `current_activity_id` within the run’s scenario. Do not allow an activity from another mission to become current.
- Add a stable `content_key` and version where seeded clinical content needs repeatable updates. Existing runs must retain a stable approved content version. Do not silently change the meaning of historical attempts.

Use portable database types, explicit foreign keys, unique constraints, indexes for session/progress lookups, and application validation for JSON payloads. Enable SQLite foreign key enforcement on every connection. Do not promise PostgreSQL compatibility until migration and integration tests have run against it.

### Migration and seed safety

- Use reviewed Alembic migrations. No `drop_all`, automatic `create_all` at startup, database deletion, or schema recreation.
- Run upgrade commands explicitly. Test upgrade from an empty temporary database and a second upgrade with no changes.
- Seed via an explicit CLI command and a transaction. Use stable keys. First run inserts missing definitions; repeated execution leaves existing definitions and all learner data intact.
- Do not overwrite existing edited content by default. Report conflicting definitions. Future explicit content updates require a separate versioned workflow.
- Never run tests against the development or production database. Fixtures must select a temporary database before creating the app.
- Database migrations that remove data or alter meaning need a separate reviewed plan. Do not generate destructive downgrade instructions as routine recovery.

## 6. Anonymous session contract

- Start with an informational home page. `POST /session/start` creates the learner session, protected by CSRF and followed by a redirect to `/ward`.
- GET routes do not create a learner or change learning progress. An anonymous CSRF bootstrap cookie on the home page is permitted.
- Use a cryptographically secure opaque token with at least 256 bits of randomness. Store its hash server-side and set the raw token in an HttpOnly cookie. Never include it in URLs, HTML, analytics, or logs.
- Set `SameSite=Lax`; set `Secure` in HTTPS production. Development over localhost HTTP may disable `Secure` explicitly. Cookie lifetime must not exceed server-side expiry.
- Default absolute lifetime: 30 days, configurable. Refreshing does not reset this absolute expiry. Missing, malformed, expired, or unknown tokens prompt a fresh session; never reconnect to an unrelated record.
- Repeated start requests with a valid existing session reuse it. Invalid browser cookies are replaced only when a new session is explicitly started.
- Server-side lookup determines ownership. Never accept a client-provided session ID as authority.
- Explain that resuming works on the same browser/device until expiry, and clearing cookies loses access. No cross-device recovery is promised in V1.
- Session expiry is not a deletion policy. No automatic data purge. Before a pilot, the owner must document retention, backup retention, access, and an approved deletion process.

## 7. Progress, locking, and transactions

- The server decides room availability and prerequisite completion. Disabling a button is not access control.
- In A, only Room 501 preview is accessible. Direct access to Rooms 502–504 must not start a run or bypass restrictions. Return an accessible explanation and an appropriate non-success response for protected mission endpoints.
- Later, Room 504 can start only when all three prerequisite missions are completed for the current session and its content is published as playable.
- `not_started → in_progress → completed` is the normal mission lifecycle. Incorrect attempts do not revert lasting completion. Replay has its own run lifecycle.
- Required activities must have server-recorded completion evidence before finishing a run. Opening an outcome page is not completion.
- Evaluating an attempt, saving patient effects, updating activity/run progress, and awarding a badge must be one transaction. Roll back the whole operation on failure.
- Use a request idempotency key and run revision to handle double-clicks, network retries, and multiple tabs. Return a recoverable conflict for stale state; never apply patient effects twice.
- Refresh restores current activity and patient state from the server. Do not derive authoritative progress from localStorage.
- For free-text reflection, accept completion without grading the text. Bound length and render as escaped text. Informational activities require an explicit acknowledge action.

## 8. Clinical content and game contracts — B onward

Keep clinical rules in versioned database content, not mission-specific Python branches. Reusable evaluators dispatch on supported activity type. Unknown types or invalid schemas fail closed with a recoverable message and an internal diagnostic.

Add `matching` as a supported activity type for the Oxygen Device Match Challenge. Matching is not equivalent to choosing a single option.

Each activity content schema must define:

- renderable prompt/assets/options with stable keys;
- accepted response shape and allowed keys;
- server-only evaluation rules and targeted feedback triggers;
- completion criteria, retry behavior, and any critical safety handling;
- any patient effects, allowed transitions, and content approval metadata.

Sequence evaluators support partial-order constraints or multiple accepted sequences where appropriate. Priority evaluators support accepted sets and precedence constraints. Do not force one arbitrary order when several clinically acceptable actions exist. Branching transition rules must be explicit and deterministic, with escalation available when clinically appropriate.

Feedback must include what happened, why it matters, and a next action or targeted hint. Do not reveal the entire answer on the first incorrect sequence unless the approved content explicitly requires it.

Patient engine:

- Input: validated state and approved effect specification. Output: normalized next state and an event record.
- Whitelist state fields and effect operations; reject unknown fields, invalid types, nonfinite numbers, and contradictory operations.
- Define per-variable data types, enum values, and allowed bounds in a reviewed schema. Clamp approved numeric deltas to schema bounds; reject invalid configured absolute values during content validation.
- Define deterministic effect ordering. The same state, version, and action must produce the same result.
- Patient monitor animation represents persisted events; browser animation must not determine clinical outcome.
- Prototype patient measurements in the original brief are synthetic scenario data, not treatment thresholds or general clinical advice.

Add clinical review metadata to publishable scenario versions: `approval_status` (`draft`, `reviewed`, `approved`), reviewer reference, approval date, source/reference text, and revision notes. Do not fabricate faculty approval. Only approved content may be published for student use.

Unapproved treatment values use `[Faculty-approved value required]` in authoring/preview views. Activities that depend on missing values cannot become playable. Do not simply show this placeholder inside an otherwise actionable medication activity.

Faculty review must cover all accepted actions, unsafe-action feedback, simulated effects, timing, medication/device parameters, escalation paths, and completion criteria. No teacher CMS is required; versioned seed/content files are sufficient for V1.

## 9. HTTP, validation, and security

For A use server-rendered routes: `GET /`, `POST /session/start`, `GET /ward`, `GET /missions/<slug>`, and the two health routes. Introduce JSON gameplay endpoints only in B.

- Protect state-changing form and JSON requests with CSRF. Use a maintained Flask-compatible CSRF implementation and include it in dependency documentation.
- Enforce ownership, room access, payload size, allowed fields, option membership, and activity/run relationship on the server.
- Keep answer flags, accepted sequences/sets, feedback trigger rules, and patient-effect rules out of initial browser payloads. Return only the feedback/state appropriate after submission.
- Escape Jinja output. Do not use `|safe` or `innerHTML` for untrusted content. Use SQLAlchemy parameterized operations.
- Bound request bodies and user strings. Do not expose stack traces in production.
- Use a self-hosted asset-compatible Content Security Policy, `X-Content-Type-Options: nosniff`, and a restrictive referrer policy. Personalized ward/game responses use `Cache-Control: no-store`.
- Add bounded abuse controls before a public pilot; document behavior without blocking ordinary shared-campus traffic. Do not claim a service is protected by a limiter that has not been implemented and tested.
- Trust proxy headers only with an explicitly configured trusted proxy topology. Do not enable broad ProxyFix defaults.
- Operational logs may contain event IDs and error categories, but no cookies, raw tokens, secrets, or reflection text. Learning events stay in the protected application database.
- JSON errors, once introduced, use a stable shape such as `{ "error": { "code": "stale_state", "message": "Reload to continue." } }`; do not return internal exception strings.

## 10. UI, accessibility, and content language

Use the original navy/cyan/aqua direction with clear typography and restrained motion. A does not require generated clinical illustrations. Use local lightweight assets and do not misrepresent decorative images as clinically accurate equipment.

Default interface copy for A is English to match the original brief. Keep copy centralized enough for later Thai localization; multilingual UI is not required in A. This is an implementation default, not a claim that English is approved for the student cohort.

- Semantic landmarks, heading order, explicit form labels, keyboard navigation, visible focus, and meaningful link/button names.
- Meet WCAG 2.2 AA contrast targets: 4.5:1 for normal text, 3:1 for large text and applicable UI boundaries/focus indicators.
- Aim for touch targets at least 44 × 44 CSS pixels. Do not communicate status by color alone.
- At 360, 390, 768, 1024, and 1440 CSS pixel widths: no horizontal page overflow, clipped text, overlapping controls, or hidden room-state explanations.
- Check zoom/reflow at 200% and keyboard-only operation. Respect `prefers-reduced-motion`.
- Later drag-and-drop activities require Move Up/Move Down or equivalent keyboard/touch controls, readable order, and announcements after changes.
- Screen reader announcements should summarize meaningful patient events; do not announce every animation frame.
- Locked and coming-soon cards must have readable explanations. Avoid disabled controls whose purpose is available only via a hover tooltip.

## 11. Deployment and operations

Document both local development and Windows Server deployment with Apache/XAMPP → Waitress → Flask. Do not edit the user's Apache configuration automatically.

- Document virtual environment setup, dependency installation, secret generation, database URL semantics, explicit migration/seed commands, CSS build, test commands, and start commands.
- Compile Tailwind to `app/static/css/app.css`. Include the compiled artifact in the release procedure and prove production runtime works without npm/Node or internet asset access.
- Production Waitress binds to loopback behind Apache. Publish a reviewed reverse-proxy example, with placeholders, HTTPS/cookie settings, timeout considerations, and exact trusted forwarded headers.
- Keep the SQLite database outside publicly served directories. Restrict filesystem permissions to the service account and approved operators.
- Document service startup/restart and logs on Windows. A deployment example does not demonstrate that the target Windows host has been tested.
- Use a consistent SQLite backup mechanism, such as its backup API, or stop writes before a file copy. Do not copy only the main live database file while ignoring transaction/WAL state.
- Back up before production migrations. Restore rehearsal uses a separate path and environment. Never overwrite the active database as a test.
- Code rollback is safe only if compatible with the migrated schema. Otherwise use a reviewed recovery procedure; do not automatically run destructive downgrades.
- SQLite is the V1 choice. Record expected class size before a pilot and test representative simultaneous writes. Do not invent a supported concurrency guarantee. Reassess PostgreSQL if measured contention exceeds the agreed operating target.

## 12. Checkpoint A verification matrix

Run meaningful automated tests against isolated temporary data:

| Test | Required evidence |
|---|---|
| Application factory | Test config overrides work; import/startup does not create application tables or seed data |
| Configuration | Missing required secret is rejected; production debug is off; SQLite resolves inside the intended instance directory |
| Migrations | Empty test DB upgrades; repeated upgrade preserves a sentinel record |
| Seed | Exactly four stable room definitions and three prerequisites; rerun creates no duplicates and preserves existing edits and learner data |
| Session start | Valid CSRF creates a hashed-token record; valid existing session is reused; refresh retains the same learner |
| Session rejection | Missing/invalid CSRF rejected; expired/malformed tokens cannot access another learner's records |
| Cookies | HttpOnly/SameSite and environment-appropriate Secure/expiry behavior |
| Ward | All four required labels and explanations; Room 501 preview explicitly marked; no fabricated completion or earned badge |
| Access | Direct requests cannot start unavailable or locked rooms; preview does not change progress |
| Isolation | Two independent browser clients do not share learner state |
| Health | Liveness does not write data; readiness returns 503 on absent schema and succeeds after migration |
| Rendering | Escaping verified with a representative untrusted string; missing rooms return a safe 404 |
| Assets | CSS build succeeds; rendered pages use local assets with no required CDN calls |

Also run the app and inspect all five target widths. Record screenshots and a brief keyboard/focus/zoom/reduced-motion checklist. If browser automation is unavailable, report the missing checks honestly; do not mark them as passed based on code inspection alone.

Do not create fake gameplay implementations merely to test future contracts. Record future tests for B–E: incorrect/correct/retry paths, required activity enforcement, deterministic patient changes, accepted alternative sequences, refresh/resume, duplicate submissions, stale tabs, replay preservation, unique badge award, and Room 504 unlock/bypass prevention.

## 13. Definition of done and handoff

Checkpoint A is complete only when its implemented scope, relevant automated tests, app startup, compiled assets, and requested responsive checks have evidence. Missing external environment checks must be listed separately from verified local results.

The final implementation report must include:

1. Completed scope and exact files created/modified.
2. Commands run and actual test results, including failures or skipped checks.
3. Local preview/start instructions and responsive evidence paths.
4. Data safety checks and any dependency/schema side effects.
5. Known limitations: no playable missions yet, no clinical approval yet, and any untested deployment environment.
6. Architectural deviations with reasons, or explicitly “none.”
7. Recommended next checkpoint: B; then stop.

Before a student pilot, confirm faculty-approved content, cohort language, retention/access ownership, HTTPS deployment, backup restoration, accessibility checks, full mission acceptance tests for included rooms, and representative concurrency results. These are later release gates, not reasons to block isolated Checkpoint A development.
