---
name: add-ai-provider
description: Add a new LLM provider (e.g. OpenAI, Gemini) as an adapter without touching business logic or existing agents.
---
# Add an AI provider
**When to use:** supporting another model vendor.

1. Read `rules/ai-providers.md` and the existing adapters.
2. Create one new adapter module implementing the `ModelProvider` interface; the vendor SDK is imported only there.
3. Declare its capabilities (tool use, structured output, context window, streaming) so the router can select it.
4. Add configuration: API key env var (documented in `.env.example`, no real values), model identifiers as config.
5. Register the adapter in the provider registry/factory — the only shared file that changes.
6. Map vendor errors to the common error types so bounded retry/fallback works; ensure usage tracking is populated.
7. Add the adapter to the shared provider contract tests with a mocked client; add adapter-specific tests.
8. Verify `git diff` shows no changes to services, specialist agents, or other adapters.

**Verification:** contract tests pass (show output); grep confirms no SDK import outside the adapter.
**Deliverables:** adapter, config, registry entry, tests, docs note.
