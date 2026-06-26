# PROJECT_CREATION_ARCHITECTURE.md

## Version: 1.1 (Full-Fidelity Execution Spec)
Status: Canonical Runtime Contract  
Scope: MyServer / MyPixler Project Creation Engine  
Mode: Implementation-Ready Specification (NOT descriptive only)

---

# 1. System Definition

A project creation is a **state-driven, RIS-enforced transactional workflow** that produces a deterministic filesystem artifact with immutable provenance.

A project is invalid unless:

- RIS exists
- RIS is captured BEFORE filesystem write
- State machine reaches COMPLETE
- Event log is fully emitted

---

# 2. Hard Constraints (Runtime-Enforced)

These are not guidelines. They are **execution blockers**:

### C1 — RIS Before Write
No filesystem write may occur before:

---

### C2 — Immutability Lock
Once RIS is captured:

- It becomes read-only
- Any change requires FORK operation

---

### C3 — No Silent Execution
Every transition MUST emit an event.

If event emission fails → system must abort.

---

### C4 — Deterministic Output
Same inputs → identical:

- folder structure
- RIS metadata (except timestamps)
- registry state

---

# 3. Execution State Machine (Formal)

---

## 3.1 State Transition Contract

Each state transition MUST satisfy:

Failure at any step triggers:

---

## 4. State Definitions (Executable Semantics)

---

### INIT

**Input:**
- create_project request

**Output:**
- session context initialized

**Allowed actions:**
- none (no filesystem access)

Event: project_init
---

### VALIDATE_INPUT

**Checks:**

- project_name not null
- project_name regex valid
- project_name not exists
- permissions OK

Failure → TERMINATE

Event: validation_failed
---

### PROVENANCE_REQUIRED

System enters blocking capture mode.

Allowed inputs:

- UI dialog payload
- API-provided RIS
- template-derived RIS

No transition allowed without valid RIS payload.

Event: provenance_required
---

### PROVENANCE_CAPTURED

RIS payload is:

- validated
- normalized
- locked (immutable)

System computes:

Event: provenance_captured
---

### RIS_GENERATION

System writes:
Rules:

- must match locked RIS
- must include system fields
- must embed ris_hash

Event: ris_generated
---

### FILESYSTEM_WRITE

Creates:
Atomic requirements:

- write temp dir first
- validate structure
- rename atomic commit

Failure → full rollback

Event: filesystem_written
---

### REGISTRATION

Registers project in:

- MyServer registry
- project index
- UI cache

Event: project_registered
---

### COMPLETE

Final state reached only if:

- all previous states succeeded
- no pending rollback flag

Event: project_created
---

# 5. RIS SPECIFICATION (Immutable Contract)

## 5.1 Core Schema

```json
{
  "ris_version": "1.0",
  "project_name": "",
  "timestamp_created": "",
  "creator": "Max",
  "environment": {
    "platform": "MyPixler",
    "server": "MyServer"
  },
  "creation_context": {
    "trigger": "",
    "source_context": "",
    "user_intent_summary": ""
  },
  "dependencies": [],
  "linked_files": [],
  "audit_trail": [
    {
      "event": "created",
      "timestamp": ""
    }
  ],
  "ris_hash": ""
}

user/Max/Projects/<ProjectName>/
│
├── project.ris.json
├── project_config.json
├── /src
├── /assets
├── /logs
└── /output
``` id="fs_exec_v11"

Atomic creation requirement:

- staging directory required
- commit rename required
- partial writes forbidden

---

# 7. Event System (Required Runtime Bus)

All transitions emit structured events:

```json
{
  "event": "event_name",
  "timestamp": "",
  "state": "",
  "project_name": "",
  "metadata": {}
}

| Event               | Trigger              |
| ------------------- | -------------------- |
| project_init        | request received     |
| validation_passed   | input OK             |
| validation_failed   | input rejected       |
| provenance_required | RIS needed           |
| provenance_captured | RIS locked           |
| ris_generated       | metadata written     |
| filesystem_written  | disk commit complete |
| project_registered  | indexed              |
| project_created     | success              |
| project_failed      | failure              |

# 8. Rollback System
Trigger conditions:
filesystem write failure
event emission failure
invalid RIS detected post-capture
state inconsistency
Rollback behavior:
delete temp directories
invalidate session
emit:
project_failed


# 9. Component Responsibilities
# 9.1 MyServer.py (Execution Engine)

Must implement:

run_state_machine()
transition_state()
validate_project_name()
capture_provenance()
freeze_ris()
write_project_atomic()
register_project()
emit_event()
rollback()

9.2 0-MainUI (Control Surface)

Responsibilities:

collect RIS input
enforce blocking dialog
submit structured payload
display state (optional debug mode)


# 10. Forking Model (Reserved Extension)

Future behavior:

new project inherits RIS lineage pointer
new RIS hash always generated
original RIS remains immutable

# 11. Audit Guarantees

System guarantees:

full origin traceability
deterministic reconstruction of creation
event-level audit replay capability

# 12. Philosophy (Enforcement-Level)

This system enforces:

No artifact exists without origin, and no origin exists without proof.

END OF EXECUTION SPEC

---

If you want the next real upgrade step, I recommend one of these (all now directly implementable):

1. **:contentReference[oaicite:0]{index=0}**
2. **:contentReference[oaicite:1]{index=1}**
3. **:contentReference[oaicite:2]{index=2}**
4. **:contentReference[oaicite:3]{index=3}**

Just tell me which layer you want to make real first.