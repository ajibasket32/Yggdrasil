# Release Process

Version: 1.0
Status: Normative
Last reviewed: 2026-06-13

## Purpose

This process makes development incremental and release-based. One user prompt
may complete at most one release.

## Mandatory Preflight

Before planning or changing any release, read these files in this order:

1. `PRODUCT_VISION.md`
2. `MVP_ROADMAP.md`
3. `TASKS.md`
4. `AGENTS.md`
5. `RELEASE_CHECKLIST.md`

Before generating code, also read `CODING_STANDARDS.md`, `ARCHITECTURE.md`, and
the contracts relevant to the selected release.

## Select the Release

1. Inspect release statuses in `MVP_ROADMAP.md` from top to bottom.
2. Select the first release whose status is not `DONE`.
3. Confirm that it is also the current release in `RELEASE_STATUS.md`.
4. Work only on tasks assigned to that release in `TASKS.md`.
5. If the two status files disagree, correct the planning records before
   implementing features.

## Execution Rules

- Implement only the selected release.
- Never implement future releases early.
- Do not broaden the release because a later feature appears convenient.
- Do not rewrite unrelated documentation.
- Respect all architecture, engine authority, save, security, test, and AI
  boundaries.
- Set a task to `IN_PROGRESS` only while it is actively being worked.
- Set a task to `DONE` only when its acceptance criteria have objective
  evidence.
- Use `BLOCKED` only when the task cannot progress and record the blocker in
  its notes and in `RELEASE_STATUS.md`.

## Release Completion

A release is complete only when:

1. Every task assigned to it is `DONE`.
2. Every release acceptance criterion in `MVP_ROADMAP.md` passes.
3. Required unit, integration, and regression tests pass.
4. Save compatibility and architecture boundaries are verified where
   applicable.
5. Relevant release and documentation checklist items have evidence.

Do not mark a release complete based on partial implementation or intent.

## Required Closeout Updates

After completing a release:

1. Set its roadmap status to `DONE`.
2. Update every task status and note in `TASKS.md`.
3. Move completed changes into the versioned section of `CHANGELOG.md`.
4. Create or update `RELEASE_NOTES.md`.
5. Update `RELEASE_STATUS.md`.
6. Record what is done, what is not done, known limitations, risks, technical
   debt, and the next release recommendation.
7. Retain test and release-gate evidence required by project contracts.

## Mandatory Stop Condition

Stop after one release is completed. Do not start, prepare, scaffold, or
implement the next release in the same run. Continue only after the user gives
a new prompt that authorizes the next first unfinished release.
