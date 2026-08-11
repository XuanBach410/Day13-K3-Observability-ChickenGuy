from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Any

from .incidents import STATE
from .pii import summarize_text
from .tracing import get_langfuse_client, observe


@dataclass
class FakeUsage:
    input_tokens: int
    output_tokens: int


@dataclass
class FakeResponse:
    text: str
    usage: FakeUsage
    model: str


from .tracing import observe


class FakeLLM:
    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        self.model = model

    @observe(name="generate-response", as_type="generation", capture_input=False, capture_output=False)
    def generate(
        self,
        prompt: str,
        *,
        prompt_obj: Any | None = None,
        prompt_context: dict[str, str | None] | None = None,
        langfuse_client: Any | None = None,
    ) -> FakeResponse:
        time.sleep(0.15)
        input_tokens = max(20, len(prompt) // 4)
        output_tokens = random.randint(80, 180)
        if STATE["cost_spike"]:
            output_tokens *= 4
        answer = (
            "Starter answer. Teams should improve this output logic and add better quality checks. "
            "Use retrieved context and keep responses concise."
        )
        response = FakeResponse(text=answer, usage=FakeUsage(input_tokens, output_tokens), model=self.model)

        metadata = {
            "prompt_preview": summarize_text(prompt),
        }
        if prompt_context:
            metadata.update(prompt_context)

        (langfuse_client or get_langfuse_client()).update_current_generation(
            model=self.model,
            input={"prompt_preview": summarize_text(prompt)},
            output={"answer_preview": summarize_text(answer)},
            metadata=metadata,
            usage_details={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
            prompt=prompt_obj,
        )

        return response
