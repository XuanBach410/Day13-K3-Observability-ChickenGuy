from __future__ import annotations

import time

from .incidents import STATE
from .pii import summarize_text
from .tracing import get_langfuse_client, observe

from .tracing import observe

CORPUS = {
    "refund": ["Refunds are available within 7 days with proof of purchase."],
    "monitoring": ["Metrics detect incidents, traces localize them, logs explain root cause."],
    "policy": ["Do not expose PII in logs. Use sanitized summaries only."],
}


@observe(name="retrieve-context", as_type="retriever", capture_input=False, capture_output=False)
def retrieve(message: str) -> list[str]:
    langfuse_client = get_langfuse_client()
    update_current_span = getattr(langfuse_client, "update_current_span", None)
    if callable(update_current_span):
        update_current_span(input={"query_preview": summarize_text(message)})

    if STATE["tool_fail"]:
        raise RuntimeError("Vector store timeout")
    if STATE["rag_slow"]:
        time.sleep(2.5)
    lowered = message.lower()
    for key, docs in CORPUS.items():
        if key in lowered:
            if callable(update_current_span):
                update_current_span(metadata={"retrieval_strategy": "keyword", "doc_count": len(docs)})
            return docs

    docs = ["No domain document matched. Use general fallback answer."]
    if callable(update_current_span):
        update_current_span(metadata={"retrieval_strategy": "fallback", "doc_count": len(docs)})
    return docs
