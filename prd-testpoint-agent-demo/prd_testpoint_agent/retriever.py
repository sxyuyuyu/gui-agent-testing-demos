import math
from collections import Counter

from .config import AgentConfig
from .knowledge_base import KnowledgeBase
from .schema import KnowledgeDoc, RequirementModel, RetrievalHit
from .text_utils import tokenize, unique


class HybridRetriever:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.weights = config.retrieval_weights.normalized()

    def retrieve(self, requirement: RequirementModel, knowledge_base: KnowledgeBase) -> list[RetrievalHit]:
        queries = self._build_queries(requirement)
        token_cache = {doc.doc_id: tokenize(knowledge_base.searchable_text(doc)) for doc in knowledge_base.docs}
        best: dict[str, RetrievalHit] = {}

        for query in queries:
            query_tokens = tokenize(query)
            for doc in knowledge_base.docs:
                doc_tokens = token_cache[doc.doc_id]
                keyword = self._keyword_score(query_tokens, doc_tokens, knowledge_base.docs, token_cache)
                vector = self._cosine_score(query_tokens, doc_tokens)
                defect = self._defect_score(requirement, doc, knowledge_base.searchable_text(doc))
                rule = self._rule_score(requirement, knowledge_base.searchable_text(doc))
                final_score = (
                    self.weights.keyword * keyword
                    + self.weights.vector * vector
                    + self.weights.defect * defect
                    + self.weights.rule * rule
                )

                if final_score < self.config.min_score:
                    continue

                matched_keywords = self._matched_keywords(requirement, knowledge_base.searchable_text(doc))
                hit = RetrievalHit(
                    doc_id=doc.doc_id,
                    source=doc.source,
                    title=doc.title,
                    score=round(final_score, 4),
                    score_detail={
                        "keyword": round(keyword, 4),
                        "vector": round(vector, 4),
                        "defect": round(defect, 4),
                        "rule": round(rule, 4),
                    },
                    matched_keywords=matched_keywords,
                    usable_knowledge=doc.usable_knowledge,
                    test_angles=doc.test_angles,
                )

                current = best.get(doc.doc_id)
                if current is None or hit.score > current.score:
                    best[doc.doc_id] = hit

        return sorted(best.values(), key=lambda item: item.score, reverse=True)[: self.config.top_k]

    def _build_queries(self, requirement: RequirementModel) -> list[str]:
        queries = []
        for feature in requirement.features:
            queries.extend([feature, f"{feature} 测试点", f"{feature} 历史缺陷"])
        for rule in requirement.rules:
            queries.extend([f"{rule} 边界", f"{rule} 异常场景"])
        for boundary in requirement.boundaries:
            queries.extend([f"{boundary} 边界值", f"{boundary} 时间规则"])
        for exception in requirement.exceptions:
            queries.extend([f"{exception} 处理逻辑", f"{exception} 回归用例"])
        queries.extend(requirement.keywords)
        queries.extend(requirement.expanded_keywords)
        return unique(queries)

    def _keyword_score(
        self,
        query_tokens: list[str],
        doc_tokens: list[str],
        docs: list[KnowledgeDoc],
        token_cache: dict[str, list[str]],
    ) -> float:
        if not query_tokens:
            return 0.0

        counts = Counter(doc_tokens)
        score = 0.0
        for token in query_tokens:
            score += counts[token] * self._idf(token, docs, token_cache)
        return min(score / max(len(query_tokens), 1), 1.0)

    def _idf(self, token: str, docs: list[KnowledgeDoc], token_cache: dict[str, list[str]]) -> float:
        total = len(docs)
        hit = sum(1 for doc in docs if token in token_cache[doc.doc_id])
        return math.log((total + 1) / (hit + 1)) + 1

    def _cosine_score(self, query_tokens: list[str], doc_tokens: list[str]) -> float:
        query_counter = Counter(query_tokens)
        doc_counter = Counter(doc_tokens)
        common = set(query_counter) & set(doc_counter)
        numerator = sum(query_counter[token] * doc_counter[token] for token in common)
        query_norm = math.sqrt(sum(value * value for value in query_counter.values()))
        doc_norm = math.sqrt(sum(value * value for value in doc_counter.values()))
        if query_norm == 0 or doc_norm == 0:
            return 0.0
        return numerator / (query_norm * doc_norm)

    def _defect_score(self, requirement: RequirementModel, doc: KnowledgeDoc, doc_text: str) -> float:
        if doc.source != "历史缺陷库":
            return 0.0
        hits = sum(1 for keyword in requirement.keywords + requirement.expanded_keywords if keyword in doc_text)
        return min(hits / 5, 1.0)

    def _rule_score(self, requirement: RequirementModel, doc_text: str) -> float:
        values = requirement.features + requirement.boundaries + requirement.exceptions
        hits = sum(1 for value in values if value and value in doc_text)
        return min(hits / 4, 1.0)

    def _matched_keywords(self, requirement: RequirementModel, doc_text: str) -> list[str]:
        values = requirement.keywords + requirement.expanded_keywords
        return unique([value for value in values if value in doc_text])[:10]
