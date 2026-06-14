from prometheus_client import Counter, Histogram

HTTP_ERRORS_TOTAL = Counter(
    "http_errors_total",
    "Total HTTP responses with status codes at or above 400.",
    ["method", "path", "status_code"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "path"],
)
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests.",
    ["method", "path", "status_code"],
)
SAVE_OPERATIONS_TOTAL = Counter(
    "save_operations_total",
    "Total save workflow outcomes.",
    ["operation", "result"],
)
SAVE_MIGRATIONS_TOTAL = Counter(
    "save_migrations_total",
    "Total save compatibility migrations.",
    ["source_version", "target_version", "result"],
)
SAVE_ATTEMPTS_TOTAL = Counter(
    "save_attempts_total",
    "Total save workflow attempts.",
    ["operation"],
)
SAVE_FAILURES_TOTAL = Counter(
    "save_failures_total",
    "Total save workflow failures.",
    ["operation", "reason"],
)
SAVE_DURATION_SECONDS = Histogram(
    "save_duration_seconds",
    "Transactional save creation duration in seconds.",
)
LOAD_DURATION_SECONDS = Histogram(
    "load_duration_seconds",
    "Transactional save load duration in seconds.",
)
AI_REQUESTS_TOTAL = Counter(
    "ai_requests_total",
    "Total provider-neutral narrative requests.",
    ["result"],
)
AI_PROVIDER_FAILURES_TOTAL = Counter(
    "ai_provider_failures_total",
    "Total AI provider failures.",
    ["provider", "reason"],
)
AI_PROVIDER_LATENCY_SECONDS = Histogram(
    "ai_provider_latency_seconds",
    "AI provider call latency in seconds.",
    ["provider"],
)
AI_OUTPUT_REJECTIONS_TOTAL = Counter(
    "ai_output_rejections_total",
    "Total AI outputs rejected by the narrative validation boundary.",
    ["provider", "reason"],
)
AI_FALLBACK_USES_TOTAL = Counter(
    "ai_fallback_uses_total",
    "Total successful non-primary provider responses.",
    ["provider"],
)
AI_CACHED_TEMPLATE_USES_TOTAL = Counter(
    "ai_cached_template_uses_total",
    "Total approved cached narrative responses.",
    ["reason"],
)
MEMORY_RECORDS_CREATED_TOTAL = Counter(
    "memory_records_created_total",
    "Total canonical memory creation outcomes.",
    ["result"],
)
MEMORY_INDEX_JOBS_TOTAL = Counter(
    "memory_index_jobs_total",
    "Total durable memory index job outcomes.",
    ["operation", "result"],
)
QDRANT_QUERY_DURATION_SECONDS = Histogram(
    "qdrant_query_duration_seconds",
    "Qdrant retrieval duration in seconds.",
)
CELERY_TASK_DURATION_SECONDS = Histogram(
    "celery_task_duration_seconds",
    "Background task duration in seconds.",
    ["task"],
)
CELERY_TASK_FAILURES_TOTAL = Counter(
    "celery_task_failures_total",
    "Background task failures.",
    ["task", "reason"],
)
RAG_CACHE_OPERATIONS_TOTAL = Counter(
    "rag_cache_operations_total",
    "RAG context cache operations.",
    ["operation", "result"],
)
CHARACTER_OPERATIONS_TOTAL = Counter(
    "character_operations_total",
    "Deterministic character system outcomes.",
    ["operation", "result"],
)
INVENTORY_OPERATIONS_TOTAL = Counter(
    "inventory_operations_total",
    "Transactional inventory and equipment outcomes.",
    ["operation", "result"],
)
TRAVEL_OPERATIONS_TOTAL = Counter(
    "travel_operations_total",
    "Deterministic navigation outcomes.",
    ["result"],
)
COMBAT_ACTIONS_TOTAL = Counter(
    "combat_actions_total",
    "Deterministic combat actions resolved.",
    ["actor_side", "action_type", "result"],
)
COMBAT_ENCOUNTERS_TOTAL = Counter(
    "combat_encounters_total",
    "Canonical combat encounter outcomes.",
    ["result"],
)
COMBAT_DETERMINISM_FAILURES_TOTAL = Counter(
    "combat_determinism_failures_total",
    "Detected combat replay or deterministic contract failures.",
)
QUEST_TRANSITIONS_TOTAL = Counter(
    "quest_transitions_total",
    "Deterministic quest state transition outcomes.",
    ["source", "target", "result"],
)
NPC_INTERACTIONS_TOTAL = Counter(
    "npc_interactions_total",
    "Deterministic NPC menu interaction outcomes.",
    ["action", "result"],
)
DUNGEON_OPERATIONS_TOTAL = Counter(
    "dungeon_operations_total",
    "Persistent dungeon operation outcomes.",
    ["operation", "result"],
)
WORLD_EVENTS_TOTAL = Counter(
    "world_events_total",
    "Permanent world event outcomes.",
    ["event_type", "result"],
)
NARRATIVE_GENERATIONS_TOTAL = Counter(
    "narrative_generations_total",
    "Validated narrative generation outcomes.",
    ["kind", "result"],
)
