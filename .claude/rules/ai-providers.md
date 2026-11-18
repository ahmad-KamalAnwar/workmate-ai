# AI provider rules
- All model access goes through a provider-independent interface; business logic and specialist agents never call provider SDKs.
- Groq is the initial default; Anthropic is an optional advanced provider.
- Model identifiers are configuration, never hard-coded in logic.
- Routing is capability-aware (tool use, context size, structured output, etc.).
- Retries are bounded with backoff; fallback to another provider is explicit and bounded.
- Record usage (provider, model, tokens, latency, cost estimate) per call.
- Retries/fallbacks must not repeat external side effects: tool actions carry idempotency keys and are not re-executed.
- Provider adapters are covered by shared contract tests.
