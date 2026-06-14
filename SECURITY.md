# Security Policy

Version: 2.0 -- Enterprise Edition
Status: Operational
Last reviewed: 2026-06-13

## Supported Versions

Once production releases exist, security fixes are provided for the current production release. Additional supported versions, if any, must be listed in the applicable release notes.

## Reporting a Vulnerability

Do not disclose suspected vulnerabilities in a public issue, discussion, or chat.

Use the repository host's private vulnerability-reporting feature. If that service is unavailable, report to `security@yggdrasil.game`.

Before production release, the project owner must verify that both the private reporting feature and fallback mailbox are monitored by the Security Owner. A release is blocked when no verified private channel is available.

Include:

- affected version or source revision;
- reproduction steps;
- expected and observed impact;
- whether player data, saves, credentials, or game-state integrity may be affected;
- suggested mitigation, if known.

## Response Targets

- Acknowledge reports within 2 business days.
- Triage suspected critical issues immediately.
- Provide status updates at least every 5 business days until resolution.
- Coordinate disclosure after a fix or mitigation is available.

## Scope Priorities

Highest priority includes:

- authentication or authorization bypass;
- account or secret exposure;
- save corruption or cross-player access;
- manipulation of deterministic gameplay state;
- direct AI influence over gameplay authority;
- remote code execution, injection, or supply-chain compromise.

Operational severity and incident handling follow `SECURITY_GUIDELINES.md` and `OPERATIONS_RUNBOOK.md`.
