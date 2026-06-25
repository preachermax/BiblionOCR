# 🧠 AI-Assisted Development Workflow — Commit Protocol

## 📌 Source

Conversation between Max and ChatGPT — 2026-06-22

---

## ❓ Developer Question

A summary of my current role and usage is:

* Use ChatGPT as a foremost development tool
* Use OpenAI (Continue.dev) for codebase checking after changes are made here
* Use Copilot to sync up remote commits after all branches have been committed locally

Any platform that generates a commit will:

1. Review the developer notebook
2. Update the notebook regarding the committed changes

---

## 🤖 ChatGPT Response (Refined Workflow)

### 🧠 System Roles

```
ChatGPT → primary reasoning engine (architecture + debugging truth)

OpenAI (Continue.dev) → codebase-aware validation after changes

Copilot → local implementation + commit assistance

Git → state tracking + rollback safety

Developer Notebook → single source of truth (project memory)
```

---

## 🔁 Commit Protocol (Corrected)

### ✅ Core Rule

> The notebook records **state changes**, not activity.

---

### 🔹 Update the Developer Notebook When:

* A bug is **actually fixed**
* A system boundary is clarified
* A behavior becomes stable
* A new issue is discovered
* A design decision is made

---

### ❌ Do NOT Update the Notebook For:

* Minor refactors
* Formatting changes
* Debug prints
* Small UI tweaks

---

## 🔄 Development Loop

```
1. ChatGPT → define change (reasoning)
2. Implement locally (manual or Copilot)
3. Run targeted runtime test
4. Validate with Continue.dev (codebase awareness)
5. Commit locally
6. IF behavior/state changed → update notebook
```

---

## 🔒 Critical Guardrail

### “Single Commit Authority” Rule

> Only the developer (Max) triggers final commits.

* AI tools may suggest or prepare changes
* Only the developer decides when changes become history

---

## 🧭 Role of the Developer Notebook

The notebook is not just notes. It is:

* 🧠 Project memory
* 🧭 Architectural intent
* ⚠️ Stability guardrail

It explains:

* Why things are done a certain way
* What must not be broken
* What has already been solved

---

## ⚠️ Workflow Refinement

### Preferred Order

```
ChatGPT → Implement → Test → Commit → THEN Validate with tools
```

### Rationale

* Tools validate **stable states**
* Not in-progress edits

---

## 🏷️ Commit Message Strategy

Use structured commit messages:

```
stabilize: MyPixler standalone load confirmed
fix: crop preview updates right panel only
debug: add thread lifecycle prints
wip: zoom slider investigation
```

---

## 🎯 Guiding Principle

> Code changes are cheap.
> Stable behavior is valuable.
> The notebook records value—not activity.

---

## 🧠 System Insight

This workflow represents:

> A controlled multi-AI development loop with human authority

---

## 🚀 Next Evolution (Planned)

* Formalize **MyServer → MyPixler parameter contract**
* Maintain commit discipline during integration phase

---

## 📅 Entry Timestamp

2026-06-22

---
