from dataclasses import dataclass, field


@dataclass
class RetrievalWeights:
    keyword: float = 0.35
    vector: float = 0.35
    defect: float = 0.20
    rule: float = 0.10

    def normalized(self) -> "RetrievalWeights":
        total = self.keyword + self.vector + self.defect + self.rule
        if total <= 0:
            return RetrievalWeights()
        return RetrievalWeights(
            keyword=self.keyword / total,
            vector=self.vector / total,
            defect=self.defect / total,
            rule=self.rule / total,
        )


@dataclass
class AgentConfig:
    top_k: int = 8
    min_score: float = 0.01
    default_timezone: str = "+08:00"
    retrieval_weights: RetrievalWeights = field(default_factory=RetrievalWeights)
    evidence_required: list[str] = field(default_factory=lambda: ["requirement_ref", "knowledge_ref"])
