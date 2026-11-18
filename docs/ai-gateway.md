# AI provider gateway

All model access goes through `app/ai_gateway`. The orchestrator and agents depend only on the gateway's types; `groq` and `anthropic` SDKs are imported only inside their adapters.

## 1. Interface

```python
class ChatRequest(BaseModel):
    purpose: Purpose                 # chat, classify, plan, summarize, draft, code_analysis, ...
    messages: list[Message]
    tools: list[ToolSpec] = []       # JSON-schema tool definitions (from tool registry)
    response_schema: type[BaseModel] | None = None   # structured output
    max_output_tokens: int | None = None
    temperature: float | None = None
    requirements: Requirements       # derived: needs_tools, needs_json, min_context, complexity
    task_id: UUID | None = None      # for usage attribution

class ChatResponse(BaseModel):
    content: str
    tool_calls: list[ToolCall]       # requested only; never executed by the gateway
    parsed: BaseModel | None
    usage: Usage                     # input/output tokens, latency, cost estimate
    provider: str
    model: str
    finish_reason: str

class ModelProvider(Protocol):
    name: str
    async def chat(self, req: ChatRequest, model: ModelSpec) -> ChatResponse: ...
    async def health(self) -> HealthStatus: ...
```

Streaming (`chat_stream`) is added when the chat UI needs it (Phase 2).

Errors are mapped to a common hierarchy: `RateLimited`, `Timeout`, `Unavailable` (retryable), `AuthError`, `InvalidRequest`, `ContextTooLong`, `CapabilityMissing` (not retryable on the same model; may fall back).

## 2. Registry and capabilities

Models are configuration, not code (`config/models.yaml`, overridable by env):

```yaml
models:
  groq-fast:     { provider: groq, id: "<groq model id>", context: 131072, tools: true,  json_mode: true, tier: fast }
  groq-strong:   { provider: groq, id: "<groq model id>", context: 131072, tools: true,  json_mode: true, tier: standard }
  claude-strong: { provider: anthropic, id: "<anthropic model id>", context: 200000, tools: true, json_mode: true, tier: advanced }
purposes:
  classify:  [groq-fast]
  chat:      [groq-strong]
  plan:      [groq-strong, claude-strong]
  code_analysis: [claude-strong, groq-strong]
```

Exact model IDs are filled in and verified against each provider's model list during Phase 2; capability flags are checked per model, never assumed per provider. A provider is **registered only if credentials are present**, so Groq-only setups work without Anthropic.

## 3. Routing

Routing mode comes from `user_settings.routing_mode`:

| Mode | Behaviour |
|---|---|
| `groq_only` | Only Groq models; fails clearly if none satisfies the requirements |
| `anthropic_only` | Only Anthropic models; unavailable if no Anthropic key |
| `smart` (default) | Policy below |

Smart routing:

1. Candidates = models listed for the request's `purpose`, filtered to registered providers.
2. Drop models that fail hard requirements (tools, structured output, context ≥ estimated tokens).
3. Prefer Groq unless an escalation rule fires: purpose is `code_analysis` or complexity is `high`; plan length or tool count above configured thresholds; previous attempt failed validation; no Groq model meets requirements.
4. Escalation only targets Anthropic if registered; otherwise stay on the best Groq model and record that escalation was unavailable.

Every decision is recorded in `ai_calls.routing_reason`.

## 4. Retry, fallback, and validation

- Per model: up to 2 retries with exponential backoff + jitter for retryable errors; respect `retry-after`.
- Fallback: on exhausted retries or a non-retryable capability/context error, try the next candidate (max 1 fallback hop by default).
- Validation: structured outputs are parsed into `response_schema`; on failure, one repair attempt on the same model, then escalate (smart mode).
- Timeouts per call are configured; total budget per request is bounded.

**No duplicate external actions:** the gateway only returns `tool_calls`. Execution happens in the tool layer after a response is accepted, keyed by an idempotency key derived from `(task_step_id, tool_name, normalized input)`. A provider retry or fallback produces a new model response, but an action already recorded in `tool_executions` is not executed again.

## 5. Usage and health

- Each attempt writes an `ai_calls` row (provider, model, tokens, latency, cost estimate, status, routing reason, fallback source).
- `GET /ai/providers` returns registered providers, models, and last health result; `POST /ai/providers/{name}/health` runs a cheap check.
- Settings UI (Phase 2): routing mode, provider status, recent usage.

## 6. Adding a provider

See `.claude/skills/add-ai-provider/SKILL.md`. New adapter + config + registry entry + contract tests; no changes to orchestrator or agents.
