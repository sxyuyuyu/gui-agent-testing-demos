import json
from pathlib import Path

from .schema import KnowledgeDoc


class KnowledgeBase:
    def __init__(self, docs: list[KnowledgeDoc]):
        self.docs = docs

    @classmethod
    def from_json(cls, path: str | Path) -> "KnowledgeBase":
        with Path(path).open("r", encoding="utf-8") as f:
            raw_docs = json.load(f)

        docs = []
        for raw in raw_docs:
            docs.append(
                KnowledgeDoc(
                    doc_id=raw.get("docId", raw.get("doc_id", "")),
                    source=raw.get("source", ""),
                    title=raw.get("title", ""),
                    content=raw.get("content", ""),
                    keywords=raw.get("keywords", []),
                    test_angles=raw.get("testAngles", raw.get("test_angles", [])),
                    usable_knowledge=raw.get("usableKnowledge", raw.get("usable_knowledge", "")),
                    module=raw.get("module", ""),
                    priority=raw.get("priority", "P2"),
                )
            )
        return cls(docs)

    def searchable_text(self, doc: KnowledgeDoc) -> str:
        return " ".join(
            [
                doc.title,
                doc.content,
                doc.usable_knowledge,
                " ".join(doc.keywords),
                " ".join(doc.test_angles),
                doc.module,
                doc.priority,
            ]
        )
