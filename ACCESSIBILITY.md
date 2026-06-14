# ACCESSIBILITY.md
# YGGDRASIL CHRONICLES
# Accessibility Standard
Version: 2.0 -- Enterprise Edition
Status: Normative
Last reviewed: 2026-06-13

---

## 1. TARGET

Player-facing web interfaces target WCAG 2.2 Level AA. Where Phaser/canvas content cannot expose equivalent semantics directly, the game must provide an accessible DOM-based alternative for critical information and actions.

---

## 2. REQUIRED BEHAVIOR

- All menus and critical gameplay actions are keyboard operable.
- Pointer input may supplement but never replace keyboard operation.
- Controller/gamepad support is post-MVP unless promoted into an approved release scope; when provided, remapping and a complete keyboard path remain required.
- Focus order is logical, visible, and restored after dialogs close.
- Controls have accessible names, roles, states, and error associations.
- Text and meaningful UI graphics meet AA contrast requirements.
- Color is never the only carrier of state.
- Text can scale to 200% without loss of critical content or operation.
- Animation, flashing, screen shake, and auto-motion respect reduced-motion settings.
- Timed interactions provide adjustment unless timing is essential to deterministic gameplay.
- Audio has independent volume controls; narrative speech requires text equivalents.
- Save, load, settings, combat choices, inventory, equipment, quests, and NPC dialogue have accessible interaction paths.

---

## 3. GAME-SPECIFIC REQUIREMENTS

- Combat turn order, HP/MP, status effects, selected target, and action results must be available as text.
- Maps require a navigable location list with adjacency and discovery status.
- Item comparisons must not rely only on arrows, color, or hover.
- Dialogue choices must be reachable without pointer input.
- Error messages must explain recovery actions without relying only on transient toast notifications.

Accessibility options are player settings and must be included in save compatibility and regression tests.

---

## 4. TESTING

Each release candidate requires:

- automated semantic and contrast checks;
- keyboard-only testing of critical user journeys;
- screen-reader smoke tests for authentication, character creation, save/load, combat, inventory, quests, and dialogue;
- reduced-motion verification;
- zoom/reflow verification;
- documented manual findings, owners, and remediation dates.

Automated tools cannot be the sole evidence of conformance.

---

## 5. EXCEPTIONS

An inaccessible critical journey blocks release. Non-critical exceptions require severity, affected users, workaround, owner, expiry, and Product plus Accessibility approval.

---

## 6. FINAL RULE

A browser game is not playable when essential information or actions are available only through one sense or input method.
