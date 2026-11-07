from __future__ import annotations

import os
import threading
import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Iterator


DEFAULT_MAX_LLM_CALLS = 3200
DEFAULT_MAX_PYTHON_TOOL_CALLS = 1600
DEFAULT_MAX_WALL_SECONDS = 21600

_CURRENT_SAMPLE_ID = ContextVar("spq_sample_budget_id", default="")
_CURRENT_SAMPLE_STARTED_AT = ContextVar(
    "spq_sample_budget_started_at",
    default=None,
)
_REGISTRY_LOCK = threading.RLock()


@dataclass
class _SampleBudget:
    sample_id: str
    max_llm_calls: int
    max_python_tool_calls: int
    max_wall_seconds: int
    llm_calls: int = 0
    python_tool_calls: int = 0
    stop_reason: str = ""


_REGISTRY: dict[str, _SampleBudget] = {}


class SampleBudgetExceeded(BaseException):
    """Non-retriable signal that stops only the active sample."""

    def __init__(self, *, kind: str, budget: dict[str, object]):
        self.kind = kind
        self.sample_id = str(budget.get("sample_id") or "")
        self.stop_reason = str(budget.get("stop_reason") or "sample_budget_exceeded")
        self.budget = dict(budget)
        limit_key = {
            "llm": "max_llm_calls",
            "python_tool": "max_python_tool_calls",
            "wall_time": "max_wall_seconds",
        }[kind]
        unit = "seconds" if kind == "wall_time" else "calls"
        super().__init__(
            f"Sample {self.sample_id!r} reached the {kind} call limit "
            f"({budget.get(limit_key)} {unit})."
        )


def _positive_env_int(name: str, default: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


def _new_budget(sample_id: str) -> _SampleBudget:
    return _SampleBudget(
        sample_id=sample_id,
        max_llm_calls=_positive_env_int(
            "SPQ_SAMPLE_MAX_LLM_CALLS",
            DEFAULT_MAX_LLM_CALLS,
        ),
        max_python_tool_calls=_positive_env_int(
            "SPQ_SAMPLE_MAX_PYTHON_TOOL_CALLS",
            DEFAULT_MAX_PYTHON_TOOL_CALLS,
        ),
        max_wall_seconds=_positive_env_int(
            "SPQ_SAMPLE_MAX_WALL_SECONDS",
            DEFAULT_MAX_WALL_SECONDS,
        ),
    )


def _budget_for(sample_id: str) -> _SampleBudget:
    budget = _REGISTRY.get(sample_id)
    if budget is None:
        budget = _new_budget(sample_id)
        _REGISTRY[sample_id] = budget
    return budget


def _elapsed_wall_seconds() -> float:
    started_at = _CURRENT_SAMPLE_STARTED_AT.get()
    if started_at is None:
        return 0.0
    return max(0.0, time.monotonic() - started_at)


def _snapshot(budget: _SampleBudget) -> dict[str, object]:
    return {
        "sample_id": budget.sample_id,
        "llm_calls": budget.llm_calls,
        "max_llm_calls": budget.max_llm_calls,
        "python_tool_calls": budget.python_tool_calls,
        "max_python_tool_calls": budget.max_python_tool_calls,
        "elapsed_wall_seconds": round(_elapsed_wall_seconds(), 3),
        "max_wall_seconds": budget.max_wall_seconds,
        "stopped": bool(budget.stop_reason),
        "stop_reason": budget.stop_reason,
    }


def check_sample_budget() -> None:
    sample_id = _CURRENT_SAMPLE_ID.get()
    if not sample_id:
        return

    with _REGISTRY_LOCK:
        budget = _budget_for(sample_id)
        if _elapsed_wall_seconds() < budget.max_wall_seconds:
            return
        if not budget.stop_reason:
            budget.stop_reason = "sample_wall_time_limit_reached"
        raise SampleBudgetExceeded(
            kind="wall_time",
            budget=_snapshot(budget),
        )


@contextmanager
def sample_budget_scope(sample_id: str) -> Iterator[None]:
    """Bind calls to one sample attempt and enforce its operation budgets."""

    normalized_id = str(sample_id or "").strip()
    if not normalized_id:
        raise ValueError("sample_budget_scope requires a non-empty sample_id.")

    with _REGISTRY_LOCK:
        _budget_for(normalized_id)

    sample_token = _CURRENT_SAMPLE_ID.set(normalized_id)
    started_token = _CURRENT_SAMPLE_STARTED_AT.set(time.monotonic())
    try:
        check_sample_budget()
        yield
        check_sample_budget()
    finally:
        _CURRENT_SAMPLE_STARTED_AT.reset(started_token)
        _CURRENT_SAMPLE_ID.reset(sample_token)


def _consume(kind: str) -> int:
    sample_id = _CURRENT_SAMPLE_ID.get()
    if not sample_id:
        return 0

    check_sample_budget()

    with _REGISTRY_LOCK:
        budget = _budget_for(sample_id)
        if kind == "llm":
            current = budget.llm_calls
            limit = budget.max_llm_calls
            stop_reason = "sample_llm_call_limit_reached"
        elif kind == "python_tool":
            current = budget.python_tool_calls
            limit = budget.max_python_tool_calls
            stop_reason = "sample_python_tool_call_limit_reached"
        else:
            raise ValueError(f"Unknown sample budget kind: {kind}")

        if current >= limit:
            if not budget.stop_reason:
                budget.stop_reason = stop_reason
            raise SampleBudgetExceeded(
                kind=kind,
                budget=_snapshot(budget),
            )

        current += 1
        if kind == "llm":
            budget.llm_calls = current
        else:
            budget.python_tool_calls = current
        return current


def consume_llm_call() -> int:
    return _consume("llm")


def consume_python_tool_call() -> int:
    return _consume("python_tool")


def get_sample_budget_snapshot(sample_id: str | None = None) -> dict[str, object]:
    normalized_id = str(sample_id or _CURRENT_SAMPLE_ID.get() or "").strip()
    if not normalized_id:
        return {}
    with _REGISTRY_LOCK:
        return _snapshot(_budget_for(normalized_id))
