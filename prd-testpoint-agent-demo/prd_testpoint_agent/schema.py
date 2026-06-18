from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PRDSection:
    section_id: str
    title: str
    text: str


@dataclass
class RequirementModel:
    prd_id: str
    title: str
    raw_text: str
    sections: list[PRDSection]
    features: list[str]
    entities: list[str]
    rules: list[str]
    boundaries: list[str]
    exceptions: list[str]
    keywords: list[str]
    expanded_keywords: list[str]


@dataclass
class KnowledgeDoc:
    doc_id: str
    source: str
    title: str
    content: str
    keywords: list[str] = field(default_factory=list)
    test_angles: list[str] = field(default_factory=list)
    usable_knowledge: str = ""
    module: str = ""
    priority: str = "P2"


@dataclass
class RetrievalHit:
    doc_id: str
    source: str
    title: str
    score: float
    score_detail: dict[str, float]
    matched_keywords: list[str]
    usable_knowledge: str
    test_angles: list[str]


@dataclass
class RequirementRef:
    section_id: str
    text: str


@dataclass
class KnowledgeRef:
    doc_id: str
    source: str
    reason: str


@dataclass
class TestPoint:
    id: str
    title: str
    type: str
    priority: str
    feature: str
    requirement_ref: RequirementRef
    knowledge_refs: list[KnowledgeRef]
    preconditions: list[str]
    steps: list[str]
    expected_results: list[str]
    test_data: list[str]
    tags: list[str]
    confidence: float


@dataclass
class Risk:
    type: str
    description: str
    suggestion: str


def to_camel_dict(obj: Any) -> Any:
    if isinstance(obj, list):
        return [to_camel_dict(item) for item in obj]
    if isinstance(obj, dict):
        return {to_camel_case(key): to_camel_dict(value) for key, value in obj.items()}
    if hasattr(obj, "__dataclass_fields__"):
        return to_camel_dict(asdict(obj))
    return obj


def to_camel_case(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])
