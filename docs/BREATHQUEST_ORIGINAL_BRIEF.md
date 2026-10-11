# BreathQuest
## Clinical Skills Adventure

A web-based formative learning game for second-year nursing students reviewing:

1. Suctioning
2. Oxygen Therapy
3. Nebulization
4. Integrated Respiratory Care

---

# 1. PRODUCT PURPOSE

BreathQuest is designed for second-year nursing students who have already learned the relevant theoretical content in class.

The application is NOT intended to replace lecture teaching.

Its purpose is to help students:

- retrieve previously learned knowledge,
- recall procedural sequences,
- recognize patient-safety issues,
- practice basic clinical reasoning,
- connect assessment findings with nursing actions,
- observe simulated patient responses,
- learn safely from mistakes,
- prepare for hands-on skill-lab practice.

The overall experience should feel like:

**Clinical simulation + casual learning game**

and should NOT feel like:

**LMS + online examination**

---

# 2. LEARNING PRINCIPLES

The game must be:

- formative,
- exploratory,
- low-stakes,
- replayable,
- immediate-feedback oriented,
- focused on patient safety,
- focused on reasoning rather than memorization alone.

Do not use:

- numeric grades,
- percentages,
- pass/fail labels,
- rankings,
- leaderboards.

Wrong actions should produce meaningful feedback and opportunities to retry.

Use progress, completion states, badges, patient responses, and reflection instead of scores.

---

# 3. TARGET USERS

Primary users:

Second-year nursing students.

Typical devices:

- smartphones,
- tablets,
- laptops,
- desktop computers.

The application must be mobile-first.

---

# 4. CORE GAME WORLD

The student enters a simulated respiratory ward.

Main environment:

## RESPIRATORY WARD

Four rooms are available.

### Room 501
**CLEAR THE AIRWAY**  
Suctioning Mission

### Room 502
**SUPPORT THE BREATH**  
Oxygen Therapy Mission

### Room 503
**OPEN THE AIRWAY**  
Nebulization Mission

### Room 504
**RESPIRATORY RESCUE**  
Integrated Clinical Mission

Room 504 remains locked until the first three missions are completed.

Students may complete Rooms 501–503 in any order.

---

# 5. BADGES

Mission completion badges:

- Room 501: Airway Explorer
- Room 502: Oxygen Guardian
- Room 503: Nebulizer Navigator
- Room 504: Respiratory Ready

Badges represent completion and learning progress, not competency certification.

---

# 6. TECHNOLOGY STACK

Backend:

- Python 3
- Flask
- Flask-SQLAlchemy
- SQLAlchemy
- Flask-Migrate / Alembic
- Waitress

Frontend:

- HTML5
- Jinja templates
- Tailwind CSS
- Vanilla JavaScript
- SortableJS

Database V1:

- SQLite

Future production database:

- PostgreSQL

Web server:

- Apache / XAMPP reverse proxy
- Waitress
- Flask

Architecture:

Browser  
→ Apache  
→ Reverse Proxy  
→ Waitress  
→ Flask  
→ SQLAlchemy  
→ SQLite

Future:

SQLAlchemy  
→ PostgreSQL

Do not make the application dependent on cloud services.

---

# 7. PORTABILITY REQUIREMENTS

Use environment-based configuration.

Example:

DATABASE_URL

Development:

sqlite:///instance/breathquest.db

Future production:

postgresql://...

Do not hard-code:

- credentials,
- absolute Windows paths,
- IP addresses,
- server names,
- drive letters.

The same codebase should be portable between Windows and Linux.

---

# 8. CORE SOFTWARE ARCHITECTURE

Frontend responsibilities:

- rendering UI,
- interaction,
- drag/drop,
- animations,
- patient-monitor presentation,
- responsive layout.

Backend responsibilities:

- activity evaluation,
- progress management,
- patient-state simulation,
- feedback selection,
- session handling,
- badge logic.

Clinical content:

primarily stored in the database.

Game mechanics:

implemented in reusable Python services.

---

# 9. PROJECT STRUCTURE

Recommended structure:

breathquest/

- run.py
- config.py
- requirements.txt
- package.json
- tailwind.config.js
- .env.example
- .gitignore

app/

- __init__.py
- extensions.py

models/

- mission.py
- scenario.py
- activity.py
- session.py
- progress.py
- badge.py

routes/

- main.py
- mission.py
- api.py

services/

- game_engine.py
- patient_engine.py
- feedback_engine.py
- progress_service.py
- badge_service.py

templates/

- base.html
- home.html
- ward.html
- mission.html
- debrief.html

activities/

- intro.html
- clinical_cues.html
- equipment.html
- medication_check.html
- assembly.html
- safety_check.html
- sequence.html
- decision.html
- troubleshooting.html
- spot_risk.html
- aftercare.html
- outcome.html

static/

- css
- js
- images

instance/

- breathquest.db

seed/

- suction_seed.py
- oxygen_seed.py
- nebulization_seed.py
- final_mission_seed.py

tests/

docs/

---

# 10. DATABASE MODEL

Use generic reusable content architecture.

## Mission

Fields:

- id
- slug
- title
- subtitle
- description
- icon
- room_number
- display_order
- is_active
- created_at
- updated_at

## Scenario

Fields:

- id
- mission_id
- title
- patient_name
- patient_age
- patient_gender
- clinical_summary
- initial_state_json
- image_path
- difficulty
- is_active

## Activity

Fields:

- id
- scenario_id
- activity_type
- title
- instruction
- content_json
- display_order
- is_required
- is_active

Supported activity types:

- intro
- clinical_cues
- equipment_select
- medication_check
- assembly
- safety_check
- sequence
- decision
- troubleshooting
- spot_risk
- aftercare
- outcome
- debrief
- multi_action_priority
- branching_scenario

## ActivityOption

Fields:

- id
- activity_id
- label
- description
- image_path
- option_key
- is_correct
- display_order
- metadata_json

## ProcedureStep

Fields:

- id
- activity_id
- step_key
- step_text
- correct_order
- rationale
- critical_step
- image_path

## Feedback

Fields:

- id
- activity_id
- trigger_type
- trigger_key
- feedback_type
- title
- message
- clinical_rationale
- hint
- patient_effect_json

Feedback types:

- positive
- guidance
- caution
- critical

## StudentSession

Fields:

- id
- session_token
- nickname
- started_at
- last_active_at
- completed_at

## MissionProgress

Fields:

- id
- session_id
- mission_id
- status
- current_activity_id
- activities_completed
- started_at
- completed_at

Statuses:

- not_started
- in_progress
- completed

## ActivityAttempt

Fields:

- id
- session_id
- activity_id
- attempt_number
- response_json
- result_type
- duration_seconds
- created_at

## Badge

Fields:

- id
- name
- description
- icon
- rule_key

---

# 11. CLINICAL CONTENT RULES

Clinical values must remain editable.

Do not hard-code uncertain institution-specific values such as:

- exact suction pressure,
- suction duration,
- catheter size,
- oxygen flow range,
- medication dose,
- nebulizer volume,
- procedural timing.

If values have not yet been faculty-approved, use:

[Faculty-approved value required]

or place them in configurable seed/database content.

Do not present unverified values as authoritative.

---

# 12. PATIENT SIMULATION ENGINE

Use deterministic rule-based simulation.

Do not use generative AI for patient-state changes.

Possible patient-state variables:

- spo2
- rr
- hr
- distress
- secretions
- wheezing
- breath_sound
- consciousness
- comfort

Effects are database-configurable.

Example:

{
  "spo2_delta": -4,
  "distress_delta": 1
}

or:

{
  "spo2_set": 92,
  "distress_delta": -1
}

Patient engine responsibilities:

- apply effects,
- validate values,
- prevent nonsensical state,
- return normalized state,
- remain independent from UI animation.

---

# 13. GAME ENGINE PRINCIPLES

Do not build mission-specific logic throughout Python.

Avoid:

if mission == "suction"

Prefer reusable functions such as:

- evaluate_equipment_selection()
- evaluate_sequence()
- evaluate_decision()
- evaluate_hotspot()
- evaluate_assembly()
- evaluate_priority_actions()
- apply_feedback()
- apply_patient_effect()
- save_attempt()
- update_progress()

Mission content should drive behavior.

---

# 14. VISUAL DESIGN

Visual style:

- modern healthcare game,
- academically appropriate,
- friendly,
- clean,
- not childish.

Suggested palette:

- deep navy,
- cyan,
- aqua,
- soft sky tones.

Patient status:

- emerald = stable/positive,
- amber = caution,
- rose/red = genuine patient-safety concern.

Do not use red simply to indicate a wrong answer.

Use:

- rounded cards,
- large touch targets,
- subtle shadows,
- purposeful animation,
- clear typography,
- generous spacing.

---

# 15. ACCESSIBILITY

Support:

- keyboard navigation,
- visible focus,
- semantic HTML,
- sufficient contrast,
- ARIA labels where needed.

Any drag-and-drop interaction must also provide an accessible alternative such as:

- Move Up
- Move Down

---

# 16. MISSION 01 — CLEAR THE AIRWAY

Room 501

Topic:

Suctioning

Estimated duration:

8–12 minutes.

Flow:

Ward  
→ Meet Patient  
→ Clinical Cues  
→ Gear Up  
→ Safety Check  
→ Put It in Order  
→ Critical Moment  
→ Patient Monitor Challenge  
→ Spot the Risk  
→ After Care  
→ Patient Outcome  
→ Shift Reflection  
→ Airway Explorer

Prototype patient:

Mr. Somchai  
68 years old

Initial simulated state:

- SpO₂ 91%
- RR 26
- HR 96
- copious secretions
- weak cough
- coarse breath sounds
- alert

Signature mechanics:

- procedural sequencing,
- critical suction timing,
- deterioration during procedure,
- safety recognition.

No numeric score.

---

# 17. SUCTION — CORE ACTIVITIES

## Clinical Cues

Students identify relevant assessment findings.

Provide rationale rather than score.

## Gear Up

Students select required equipment.

Use visual equipment cards.

## Safety Check

Students review preparation, patient assessment, positioning, PPE, and monitoring.

## Put It in Order

Students reorder procedural steps.

Use SortableJS.

Provide targeted hints rather than immediately revealing the entire answer.

## Critical Moment

Student chooses when suction should be applied.

Unsafe action triggers simulated patient change.

## Monitor Challenge

Example simulated decline:

SpO₂ 91 → 89 → 86

Student must recognize deterioration and respond safely.

## Spot the Risk

Use configurable image hotspots.

## After Care

Student selects reassessment and aftercare actions.

## Patient Outcome

Show before/after simulated state.

## Shift Reflection

Summarize what was practiced.

Unlock:

Airway Explorer.

---

# 18. MISSION 02 — SUPPORT THE BREATH

Room 502

Topic:

Oxygen Therapy

Flow:

Meet Patient  
→ Clinical Cues  
→ Choose My Oxygen  
→ Set It Up  
→ Safety Check  
→ Start Oxygen  
→ Watch the Monitor  
→ Device Match Challenge  
→ Clinical Decision  
→ Spot the Risk  
→ Comfort & Communication  
→ Reassess  
→ Patient Outcome  
→ Shift Reflection  
→ Oxygen Guardian

Prototype patient:

Ms. Anong  
62 years old

Simulated initial state:

- SpO₂ 88%
- RR 28
- HR 104
- dyspnea
- anxiety
- alert

Signature mechanics:

- oxygen-device selection,
- setup,
- trend monitoring,
- device matching,
- patient comfort and safety.

All device parameters must remain faculty-configurable.

---

# 19. OXYGEN — CORE ACTIVITIES

## Choose My Oxygen

Student chooses the most appropriate oxygen-delivery approach for the scenario.

The activity should support:

- device,
- indication,
- flow range,
- concentration range,
- precautions.

Do not expose unapproved exact values.

## Set It Up

Student follows oxygen path from source to patient.

## Watch the Monitor

Display trends rather than isolated numbers.

## Device Match Challenge

Students match mini-patient scenarios to appropriate devices.

## Clinical Decision

Student responds when patient status or oxygen delivery changes.

## Spot the Risk

Examples:

- poor fit,
- disconnected tubing,
- oxygen-source problem,
- unsafe environment,
- lack of reassessment.

## Comfort & Communication

Include patient-centered care.

Unlock:

Oxygen Guardian.

---

# 20. MISSION 03 — OPEN THE AIRWAY

Room 503

Topic:

Nebulization

Flow:

Meet Patient  
→ Clinical Cues  
→ Check Medication Order  
→ Gear Up  
→ Assemble It Right  
→ Prepare Medication  
→ Safety Check  
→ Position Patient  
→ Start Nebulization  
→ Monitor Patient  
→ Why No Mist?  
→ Clinical Decision  
→ Spot the Risk  
→ After Care  
→ Patient Outcome  
→ Shift Reflection  
→ Nebulizer Navigator

Prototype patient:

Ms. Mali  
55 years old

Initial simulated state:

- SpO₂ 93%
- RR 24
- HR 92
- wheezing
- chest tightness
- alert

Signature mechanics:

- nebulizer assembly,
- medication preparation,
- troubleshooting,
- patient monitoring.

---

# 21. NEBULIZATION — CORE ACTIVITIES

## Medication Check

Present a medication order.

Students verify safe medication administration concepts.

## Assemble It Right

Students connect:

interface  
→ nebulizer chamber  
→ tubing  
→ source.

## Prepare Medication

Medication and diluent content must remain configurable.

## Position Patient

Use visual positioning choices.

## Start Nebulization

Display simulated mist and patient monitor.

## Why No Mist?

Troubleshooting game.

Possible causes:

- tubing disconnected,
- kinked tubing,
- cup positioning issue,
- source problem,
- medication absent.

## Clinical Decision

Student responds to discomfort, new symptoms, or deterioration.

## Spot the Risk

Use configurable visual hotspots.

## After Care

Reassessment, cleaning/disposal, comfort, documentation.

Unlock:

Nebulizer Navigator.

---

# 22. FINAL MISSION — RESPIRATORY RESCUE

Room 504

Unlocked when Missions 01–03 are completed.

This mission integrates:

- assessment,
- prioritization,
- oxygen therapy,
- nebulization,
- suctioning,
- reassessment,
- escalation,
- patient safety.

Do not identify which intervention should be used in advance.

The student must reason from patient findings.

---

# 23. FINAL MISSION CASE

Prototype patient:

Mr. Prasert  
70 years old

Current problems:

- shortness of breath,
- wheezing,
- copious secretions,
- weak cough,
- anxiety.

Initial simulated state:

- SpO₂ 87%
- RR 30
- HR 108
- distress high
- secretions high
- wheezing high

---

# 24. FIRST LOOK CHALLENGE

Student inspects:

- patient appearance,
- monitor,
- breathing,
- secretions/cough.

Then chooses the most concerning findings.

---

# 25. PRIORITIZE YOUR ACTIONS

Present action cards such as:

- assess airway,
- position patient,
- check oxygen delivery,
- provide oxygen support,
- prepare nebulization,
- prepare suction,
- reassess,
- call for assistance,
- continue observation.

Student chooses first actions.

Do not require one rigid sequence if multiple safe approaches are acceptable.

Support accepted action sets.

---

# 26. BRANCHING CLINICAL STATE

Example conceptual flow:

State A  
Hypoxemia + wheezing + secretions

→ oxygen

State B  
oxygenation improves but wheezing and secretions persist

→ nebulization

State C  
wheezing improves but retained secretions remain

→ suction

State D  
airway and breathing improve

Unsafe action may temporarily move the patient to a deterioration state.

---

# 27. DETERIORATION EVENT

Include one patient-safety event.

Example:

SpO₂ 92 → 89 → 85

Patient becomes restless.

Student must respond.

Do not display failure.

Use:

Patient Safety Alert

and allow recovery.

---

# 28. CALL FOR HELP MECHANIC

Include escalation as an available action.

Students should understand that clinical support may be appropriate.

Do not imply that the student must manage all deterioration independently.

---

# 29. FINAL DEBRIEF

Use:

Clinical Reflection

not:

Score or Result.

Sections:

What happened?

Why did it matter?

What would you watch next?

Show a timeline of the student's major clinical actions.

If a safety issue occurred, display:

Worth reviewing:

followed by the relevant concept.

No numeric score.

Unlock:

Respiratory Ready.

---

# 30. PROGRESS AND SESSION LOGIC

For V1:

- anonymous student session,
- secure random session token,
- browser cookie,
- progress saved server-side,
- resume after refresh.

Track:

- mission started,
- current activity,
- completed activities,
- retries,
- duration,
- mission completed,
- badge unlocked.

Do not calculate grades.

---

# 31. LEARNING ANALYTICS

ActivityAttempt may later support faculty analytics such as:

- commonly confused steps,
- commonly selected unsafe choices,
- activities requiring many retries,
- average time by activity.

These analytics must not automatically become student grades.

---

# 32. SECURITY REQUIREMENTS

Use:

- environment secret key,
- secure session handling,
- server-side validation,
- CSRF protection where appropriate,
- safe template rendering,
- SQLAlchemy,
- no concatenated raw SQL,
- no credentials in repository.

Do not send answer keys or patient-effect rules to the browser before submission unless necessary.

---

# 33. DATABASE SAFETY

Never:

- drop tables automatically,
- recreate the database on startup,
- clear student progress,
- delete persistent files,
- overwrite existing production data.

Use migrations.

Seed scripts should be idempotent where practical.

---

# 34. TAILWIND BUILD

Development may use:

npm run dev

Production build:

npm run build

Compile to:

app/static/css/app.css

Production runtime must not require Node.js.

---

# 35. DEPLOYMENT

Target initial environment:

Windows Server  
XAMPP  
Apache

Use:

Apache  
→ reverse proxy  
→ Waitress  
→ Flask.

Provide deployment documentation.

Do not automatically modify the user's Apache/XAMPP configuration.

Do not overwrite httpd.conf.

---

# 36. DEVELOPMENT ROADMAP

## Phase 1 — Core

Build:

- Flask application,
- SQLAlchemy,
- SQLite,
- migrations,
- Tailwind,
- anonymous sessions,
- ward screen.

## Phase 2 — Suction

Build Room 501 completely.

Use it to validate the core game engine.

## Phase 3 — Oxygen

Add oxygen-specific game mechanics.

## Phase 4 — Nebulization

Add assembly and troubleshooting mechanics.

## Phase 5 — Integrated Mission

Add branching clinical state and prioritization.

## Phase 6 — Refinement

Improve:

- responsive UX,
- accessibility,
- visual assets,
- animations,
- analytics.

Teacher CMS remains a future phase.

---

# 37. OUT OF SCOPE FOR INITIAL BUILD

Do not build yet:

- full Teacher CMS,
- student accounts,
- institutional SSO,
- LMS integration,
- AI chatbot,
- voice recognition,
- multiplayer,
- leaderboard,
- grades,
- certificates,
- 3D simulation.

---

# 38. ACCEPTANCE CRITERIA

A successful complete BreathQuest build eventually allows a student to:

1. enter the Respiratory Ward,
2. play Room 501,
3. complete Room 502,
4. complete Room 503,
5. unlock Room 504,
6. complete the integrated clinical mission,
7. receive all mission badges,
8. refresh the browser without losing progress.

No numeric student score appears anywhere.

---

# 39. ANTIGRAVITY IMPLEMENTATION INSTRUCTION

Inspect the existing BreathQuest repository before modifying anything.

Preserve all working code.

Do not refactor unrelated files.

Do not change the agreed technology stack.

Implement incrementally.

Current implementation priority:

## Checkpoint A

Build or verify:

- Flask application factory,
- configuration,
- SQLAlchemy,
- Flask-Migrate,
- SQLite configuration,
- Tailwind setup,
- anonymous session creation,
- mission data model foundation,
- Respiratory Ward UI.

At this checkpoint, display:

Room 501 — Clear the Airway — Ready

Room 502 — Support the Breath — Coming Soon

Room 503 — Open the Airway — Coming Soon

Room 504 — Respiratory Rescue — Locked

Do not implement the full missions yet.

Run automated tests relevant to Checkpoint A.

Run the application.

Verify responsive layouts at approximately:

360px  
390px  
768px  
1024px  
1440px

After completing Checkpoint A, report:

- completed work,
- files created or modified,
- tests run,
- test results,
- known limitations,
- any architectural deviation,
- next recommended checkpoint.

Then STOP.

Do not continue automatically into Checkpoint B.