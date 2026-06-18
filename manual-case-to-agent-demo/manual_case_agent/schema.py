from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Intent:
    action: str
    source_text: str
    target_text: str = ""
    target_page: str | None = None
    value: Any = None
    expectation: str | None = None


@dataclass
class Risk:
    type: str
    source_text: str
    suggestion: str
    level: str = "warning"


@dataclass
class IRStep:
    step_id: str
    intent: str
    page: str
    target: str | None = None
    target_name: str | None = None
    locator: dict | None = None
    value: Any = None
    wait_condition: dict | None = None
    post_assert: dict | None = None
    timeout: int = 10000
    source_text: str = ""


@dataclass
class IRAssertion:
    assertion_id: str
    page: str
    target: str
    locator: dict
    type: str
    expected: Any
    evidence: list[str] = field(default_factory=lambda: ["screenshot", "ui_tree"])
    source_text: str = ""


@dataclass
class IntermediateCase:
    case_id: str
    title: str
    source_text: str
    preconditions: list[dict]
    steps: list[IRStep]
    assertions: list[IRAssertion]
    risk_flags: list[Risk]


def camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def to_dict(value: Any) -> Any:
    if isinstance(value, list):
        return [to_dict(item) for item in value]
    if isinstance(value, dict):
        return {camel(k): to_dict(v) for k, v in value.items()}
    if hasattr(value, "__dataclass_fields__"):
        return to_dict(asdict(value))
    return value
