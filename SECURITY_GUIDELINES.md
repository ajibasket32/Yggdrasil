# SECURITY_GUIDELINES.md
# YGGDRASIL CHRONICLES
# Security Guidelines & Threat Model
Version: 2.0 -- Enterprise Edition
Status: Normative
Last reviewed: 2026-06-13

---

## 1. SECURITY PHILOSOPHY

Security is not an afterthought. It is a **design requirement** embedded into every layer of the system.

The primary assets to protect:
1. **Player accounts** -- credentials, session data
2. **Player game data** -- characters, saves, progression
3. **AI provider credentials** -- API keys, billing exposure
4. **World state integrity** -- preventing manipulation of game outcomes

---

## 2. THREAT MODEL

### 2.1 Primary Threats

| Threat | Risk Level | Mitigation |
|---|---|---|
| Account takeover via credential stuffing | High | Rate limiting, Argon2id, MFA-ready controls, token rotation |
| API manipulation to gain in-game advantage | High | Server-side validation, engine authority |
| AI prompt injection via NPC dialogue | Medium | Output validation, context sanitization |
| Secret exposure in source code or Docker images | High | Environment variables, secrets scanning |
| SQL injection | High | SQLAlchemy ORM, parameterized queries only |
| XSS in player-generated content (names, text) | Medium | Output escaping, CSP headers |
| Session hijacking | Medium | HTTPS-only, HttpOnly cookies, short token lifetime |
| AI API cost abuse | Medium | Rate limiting, per-user token budgets |
| Replay attacks on save endpoints | Medium | Idempotency keys, transaction validation |

### 2.2 Out of Scope (Single-Player MVP)

- DDoS protection (handled at infrastructure level, not application level)
- Multi-player cheating (no multiplayer at MVP)
- Reverse engineering of client-side code (acceptable for browser games)

---

## 3. SECRETS MANAGEMENT

### 3.1 Absolute Rules

```
RULE 1: No secrets in source code -- EVER.
RULE 2: No secrets in Docker images -- EVER.
RULE 3: No secrets in git history -- EVER.
RULE 4: No secrets in log output -- EVER.
```

### 3.2 Environment Variable Structure

```bash
# .env.example -- committed to repo with non-secret sample values only
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/yggdrasil
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333
SECRET_KEY=REPLACE_WITH_RANDOM_64_CHAR_HEX_STRING

# AI Providers
OPENAI_API_KEY=REPLACE_WITH_OPENAI_KEY
GEMINI_API_KEY=REPLACE_WITH_GEMINI_KEY
ANTHROPIC_API_KEY=REPLACE_WITH_ANTHROPIC_KEY
GROQ_API_KEY=REPLACE_WITH_GROQ_KEY

# Never commit .env -- only .env.example
```

### 3.3 Docker Secrets (Production)

In production, use Docker secrets or a secrets manager (HashiCorp Vault, AWS Secrets Manager, etc.) instead of `.env` files:

```yaml
# docker-compose.prod.yml
secrets:
  db_password:
    external: true
  openai_key:
    external: true

services:
  backend:
    secrets:
      - db_password
      - openai_key
```

### 3.4 Secret Detection in CI

Every PR is scanned by `gitleaks` before merge. A PR containing a secret pattern fails automatically and cannot be merged.

```yaml
# .github/workflows/security.yml
- name: Detect secrets
  uses: gitleaks/gitleaks-action@v2
  with:
    config: .gitleaks.toml
```

Secret scanning must also run before every release candidate. If a secret is detected, rotation is mandatory even if the secret is believed to be unused.

---

## 4. AUTHENTICATION & AUTHORIZATION

### 4.1 JWT Implementation

```python
# Token structure
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "EdDSA"
# Signing key is loaded from a secret manager; verification keys rotate by `kid`.

# Claims structure
{
  "sub": "player_uuid",
  "roles": ["player"],        # or ["player", "admin"]
  "jti": "unique_token_id",  # for revocation
  "iat": 1705000000,
  "exp": 1705000900
}
```

### 4.2 Token Refresh Policy

- Access tokens expire after **15 minutes**
- Refresh tokens expire after **7 days**
- On password change: all existing refresh tokens invalidated
- On logout: current refresh token blacklisted in Redis
- Token blacklist checked on every refresh attempt

### 4.3 Password Security

```python
# Argon2id parameters must be benchmarked on production-class hardware.
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

Passwords must allow at least 64 characters, require a minimum of 12 characters, reject known-compromised values when the deployment can do so without disclosing the password, and must not impose composition rules that discourage passphrases.

### 4.4 Authorization Levels

| Role | Access |
|---|---|
| `player` | Own character data, public world data |
| `admin` | Admin endpoints, world simulation control |
| `internal` | AI orchestration endpoints (service-to-service only) |

No player may access another player's character data except through explicitly shared world APIs.

---

## 5. INPUT VALIDATION

### 5.1 Pydantic Schema Enforcement

Every API endpoint uses a Pydantic schema that explicitly defines:
- Field types
- Field length limits
- Allowed value ranges
- Regex patterns where applicable

```python
class CreateCharacterRequest(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=32, pattern=r"^[a-zA-Z0-9 '_-]+$")]
    race_id: UUID
    gender: Literal["male", "female", "nonbinary", "unspecified"]
    alignment: Literal["lawful_good", "neutral_good", "chaotic_good",
                       "lawful_neutral", "true_neutral", "chaotic_neutral",
                       "lawful_evil", "neutral_evil", "chaotic_evil"]
    starting_job_id: UUID
```

### 5.2 Server-Side Game Validation

Player-provided values are never used directly for gameplay calculations. The client cannot:
- Declare their own damage
- Report their own XP gain
- Self-report loot
- Transition their own quest status

All of these must be calculated server-side by the relevant engine.

### 5.3 NPC Dialogue Input Sanitization

Player messages sent to NPC dialogue endpoint:
- Maximum 500 characters
- Treated as untrusted data, not instructions
- Escaped on output according to rendering context
- Isolated from system instructions through structured prompt/message roles
- Excluded from gameplay-state mutation inputs
- Embedded in a structured system prompt where user input is clearly bracketed

```python
class DialogueInput(BaseModel):
    message: Annotated[str, Field(min_length=1, max_length=500)]

def normalize_player_message(message: str) -> str:
    """Normalize length/Unicode; security comes from isolation and validation."""
    return unicodedata.normalize("NFC", message.strip())
```

Keyword blocking is not a prompt-injection security boundary. The system must assume hostile text reaches the model, minimize tools/data exposed to the narrative layer, validate structured output, and prohibit narrative output from writing game state.

---

## 6. AI PROVIDER SECURITY

### 6.1 API Key Protection

- AI provider keys stored in environment only
- Backend never passes API keys to frontend
- Frontend never knows which AI provider is active
- API keys rotated if exposed (automatic detection via gitleaks)

### 6.2 Cost Controls

```python
# Per-user token budget (enforced in AI Orchestrator)
MAX_TOKENS_PER_DIALOGUE_REQUEST = 1000
MAX_TOKENS_PER_LORE_REQUEST = 500
MAX_AI_REQUESTS_PER_USER_PER_MINUTE = 20
MAX_AI_REQUESTS_PER_USER_PER_HOUR = 200
```

If a user exceeds their hourly AI request budget, they receive cached/template responses until the budget resets.

### 6.3 Output Validation (Security Aspect)

AI output is validated before storage or display. Rejected if it:
- Contains any numeric values that could be mistaken for stat changes
- References API keys, system information, or internal identifiers
- Contains instructions for the player (AI should describe, not direct)
- Appears to be a prompt injection reflection

Numeric text is not rejected merely for containing a number. Validation rejects structured or contextual attempts to mutate authoritative gameplay values while permitting harmless narrative numbers such as dates, prices quoted from canonical state, and counts.

---

## 7. DATABASE SECURITY

### 7.1 Connection Security

```python
# Use connection string from environment only
DATABASE_URL = settings.DATABASE_URL

# Connection pool limits prevent exhaustion attacks
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
)
```

### 7.2 Query Security

```python
# OK Safe -- parameterized via ORM
result = await session.execute(
    select(Character).where(Character.player_id == player_id)
)

# FORBIDDEN NEVER -- string interpolation into SQL
result = await session.execute(
    text(f"SELECT * FROM characters WHERE player_id = '{player_id}'")
)
```

### 7.3 Data Isolation

Players may only query their own data. Every repository method that returns player data must include a `player_id` filter:

```python
async def get_character(self, character_id: UUID, player_id: UUID) -> Character | None:
    """
    Always include player_id to prevent horizontal privilege escalation.
    A player must never access another player's character.
    """
    return await self._session.scalar(
        select(Character)
        .where(Character.id == character_id)
        .where(Character.player_id == player_id)  # REQUIRED
    )
```

---

## 8. HTTP SECURITY HEADERS

Configured at Nginx level for all responses:

```nginx
# nginx/conf.d/security.conf

add_header X-Frame-Options "DENY";
add_header X-Content-Type-Options "nosniff";
add_header Referrer-Policy "strict-origin-when-cross-origin";
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()";
add_header Content-Security-Policy "
    default-src 'self';
    script-src 'self' 'nonce-$request_id';
    style-src 'self' 'nonce-$request_id';
    img-src 'self' data:;
    connect-src 'self' https://api.yggdrasil.game;
    object-src 'none';
    base-uri 'self';
    frame-ancestors 'none';
";
```

Production CSP must use generated nonces or hashes. `'unsafe-inline'` and `'unsafe-eval'` are prohibited.

---

## 9. RATE LIMITING

### 9.1 Nginx-Level Rate Limiting

```nginx
# Limit zone definitions
limit_req_zone $binary_remote_addr zone=auth:10m rate=10r/m;
limit_req_zone $jwt_player_id zone=player:10m rate=60r/m;
limit_req_zone $jwt_player_id zone=ai:10m rate=20r/m;

# Apply to routes
location /api/v1/auth/ {
    limit_req zone=auth burst=5 nodelay;
}
location /api/v1/npcs/*/talk {
    limit_req zone=ai burst=5 nodelay;
}
```

### 9.2 Application-Level Rate Limiting (Backup)

Redis-backed rate limiting as a secondary layer in FastAPI middleware, in case Nginx configuration changes.

---

## 10. AUDIT LOGGING

Security-sensitive operations generate audit log entries. These logs are separate from application logs and are immutable.

### 10.1 Audited Operations

```python
class AuditEventType(Enum):
    # Auth
    LOGIN_SUCCESS = "auth.login_success"
    LOGIN_FAILURE = "auth.login_failure"
    LOGOUT = "auth.logout"
    PASSWORD_CHANGED = "auth.password_changed"
    TOKEN_REFRESHED = "auth.token_refreshed"
    # Admin
    ADMIN_WORLD_TICK_FORCED = "admin.world_tick_forced"
    ADMIN_MEMORY_REBUILT = "admin.memory_rebuilt"
    # Security
    RATE_LIMIT_EXCEEDED = "security.rate_limit_exceeded"
    INJECTION_ATTEMPT_DETECTED = "security.injection_attempt"
    UNAUTHORIZED_RESOURCE_ACCESS = "security.unauthorized_access"
```

### 10.2 Audit Log Format

```json
{
  "event_type": "auth.login_failure",
  "player_id": null,
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "timestamp": "2024-01-15T10:30:00Z",
  "details": {
    "email_attempted": "user@example.com",
    "failure_reason": "invalid_password"
  }
}
```

Audit logs are written to a separate database table and must not be deletable by application-level code.

Audit log retention is defined in `OBSERVABILITY.md`. Security incidents follow `OPERATIONS_RUNBOOK.md` and must create a post-mortem plus regression coverage.

---

## 11. DEPENDENCY SECURITY

### 11.1 Scanning

```bash
# Python dependencies
pip-audit --requirement requirements.txt

# Node dependencies
npm audit --audit-level=high
```

Both scans run in CI. High-severity vulnerabilities block merge.

Release candidates must also produce and archive:

- an SBOM for application and container contents
- container image vulnerability results
- dependency license review
- signed image digests
- build provenance/attestation

Critical vulnerabilities block release. High vulnerabilities require remediation or a time-bounded exception approved by Security with compensating controls.

### 11.2 Dependency Update Policy

- Security patches: applied within **48 hours** of disclosure
- Minor version updates: reviewed monthly
- Major version updates: planned per release cycle

---

## 12. INCIDENT RESPONSE

### 12.1 Severity Classification

| Severity | Example | Response Time |
|---|---|---|
| P0 -- Critical | Active account takeover, API key leak | Immediate |
| P1 -- High | Authentication bypass, game state manipulation | < 4 hours |
| P2 -- Medium | Rate limiting bypass, information disclosure | < 24 hours |
| P3 -- Low | Minor information leak, UX-impacting bug | < 1 week |

### 12.2 Response Steps (P0/P1)

1. **Contain** -- Disable affected endpoint or rotate compromised credential immediately
2. **Investigate** -- Review audit logs to determine scope of impact
3. **Remediate** -- Deploy fix, verify resolution
4. **Communicate** -- Notify affected players if data was accessed
5. **Post-mortem** -- Document root cause, add regression test, update threat model

---

## 13. FINAL RULE

```
If a security control appears to require bypassing architecture rules,
the control must be redesigned until both security and architecture are satisfied.

Security through obscurity is not security.
Security through correct design is.
```
