"""
Blog draft "AI" for Blogixy demos.

This module does **not** call OpenAI, Anthropic, or any remote LLM. It builds a short
structured post from your prompt using fixed paragraphs so the product works offline
and costs nothing. For production, replace `generate_blog_draft` with your provider
client and keep the same return shape (title, content, provider, model, latency_ms).
"""

import time


def generate_blog_draft(prompt: str, tone: str = '', length: str = 'medium') -> dict:
    started = time.perf_counter()
    tone_text = tone.strip() or 'professional'
    max_paragraphs = {'short': 2, 'medium': 4, 'long': 6}.get(length, 4)
    title = f"{prompt[:60].strip().title()}"[:80]
    paragraphs = [
        f"{prompt.strip()} is an important topic for modern content teams. This draft uses a {tone_text} voice.",
        "Start with a clear problem statement, then support claims with concrete examples and actionable takeaways.",
        "Use concise sections, credible references, and a practical conclusion that guides the reader to next steps.",
        "Close with a call-to-action that aligns with your audience intent and product goals.",
        "Add supporting data points and implementation notes to improve trust.",
        "Summarize key lessons and list follow-up ideas for future posts.",
    ]
    content = '\n\n'.join(paragraphs[:max_paragraphs])
    latency = int((time.perf_counter() - started) * 1000)
    return {
        'title': title or 'AI Draft',
        'content': content,
        'provider': 'internal-template',
        'model': 'blogixy-draft-v1',
        'latency_ms': latency,
    }
