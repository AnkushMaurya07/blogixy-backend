# AI Module API

## Purpose
Modular blog draft generation from user prompts, with persistence of generation logs per user (provider, model, latency, output excerpt).

## Endpoints
- `POST /api/ai/generate-draft/` — **Authenticated.** Body: `{ "prompt": "<string>", "tone": "<optional>", "length": "short"|"medium"|"long" }`. Returns draft `title` and `content` plus `provider`, `model`, `generation_id`. Does not publish a blog.
- `GET /api/ai/history/` — List current user’s `AiGenerationLog` entries.

## Implementation notes
- Service layer lives in `ai/services.py`; swap implementations for external LLM providers without changing URLs.
- Logs store full prompt text and output excerpt for audit; extend with tokens/cost when wiring a billing provider.

## Error Handling
- Validation on serializer fields; downstream provider errors should populate log `status` / `error_message` when expanded.
