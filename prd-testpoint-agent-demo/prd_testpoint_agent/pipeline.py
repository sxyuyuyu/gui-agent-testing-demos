from datetime import datetime, timedelta, timezone

from .config import AgentConfig
from .generator import TestPointGenerator
from .knowledge_base import KnowledgeBase
from .prd_parser import PRDParser
from .retriever import HybridRetriever
from .schema import RequirementModel, RetrievalHit, Risk, TestPoint, to_camel_dict
from .validator import QualityValidator


class PRDTestPointPipeline:
    def __init__(self, config: AgentConfig | None = None):
        self.config = config or AgentConfig()
        self.parser = PRDParser()
        self.retriever = HybridRetriever(self.config)
        self.generator = TestPointGenerator()
        self.validator = QualityValidator()

    def run(self, prd_id: str, title: str, prd_text: str, knowledge_base: KnowledgeBase) -> dict:
        requirement = self.parser.parse(prd_id=prd_id, title=title, text=prd_text)
        hits = self.retriever.retrieve(requirement, knowledge_base)
        test_points = self.generator.generate(requirement, hits)
        risks = self.validator.validate(requirement, test_points)
        return self._build_output(requirement, hits, test_points, risks)

    def _build_output(
        self,
        requirement: RequirementModel,
        hits: list[RetrievalHit],
        test_points: list[TestPoint],
        risks: list[Risk],
    ) -> dict:
        generated_at = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
        output = {
            "prd_id": requirement.prd_id,
            "title": requirement.title,
            "generated_at": generated_at,
            "summary": {
                "feature_count": len(requirement.features),
                "test_point_count": len(test_points),
                "knowledge_hit_count": len(hits),
                "risk_count": len(risks),
            },
            "requirement_model": requirement,
            "retrieved_knowledge": hits,
            "test_points": test_points,
            "risks": risks,
        }
        return to_camel_dict(output)
