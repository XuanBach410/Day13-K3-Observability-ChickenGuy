from __future__ import annotations

from contextlib import contextmanager
import functools
import os
from typing import Any

try:
    import langfuse

    get_client = getattr(langfuse, "get_client")

    _observe = getattr(langfuse, "observe", None)
    _propagate_attributes = getattr(langfuse, "propagate_attributes", None)

    if _observe is None or _propagate_attributes is None:
        try:
            from langfuse import decorators as _langfuse_decorators  # type: ignore[attr-defined]

            _observe = _observe or getattr(_langfuse_decorators, "observe", None)
            _propagate_attributes = _propagate_attributes or getattr(
                _langfuse_decorators, "propagate_attributes", None
            )
        except Exception:
            pass

    if _observe is None or _propagate_attributes is None:
        raise ImportError("Langfuse observe/propagate_attributes APIs are unavailable")

    observe = _observe
    propagate_attributes = _propagate_attributes

    if not hasattr(langfuse, "observe"):
        setattr(langfuse, "observe", observe)

    LANGFUSE_SDK_AVAILABLE = True
except Exception:  # pragma: no cover - chỉ dùng khi chưa cài requirements
    LANGFUSE_SDK_AVAILABLE = False

    def observe(*args: Any, **kwargs: Any):
        def decorator(func):
            @functools.wraps(func)
            def wrapped(*f_args: Any, **f_kwargs: Any):
                return func(*f_args, **f_kwargs)

            return wrapped

        return decorator

    class _DummyClient:
        def update_current_trace(self, **kwargs: Any) -> None:
            return None

        def update_current_generation(self, **kwargs: Any) -> None:
            return None

        def update_current_span(self, **kwargs: Any) -> None:
            return None

        def flush(self) -> None:
            return None

        def get_current_trace_id(self):
            return None

    def get_client():
        return _DummyClient()

    try:
        import langfuse as _langfuse  # type: ignore[import-not-found]

        if not hasattr(_langfuse, "observe"):
            setattr(_langfuse, "observe", observe)
    except Exception:
        pass

    @contextmanager
    def propagate_attributes(**kwargs: Any):
        yield


def get_langfuse_client():
    return get_client()


def tracing_enabled() -> bool:
    return bool(
        os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")
    )


@contextmanager
def trace_attributes(**kwargs: Any):
    if not tracing_enabled():
        yield
        return
    with propagate_attributes(**kwargs):
        yield
