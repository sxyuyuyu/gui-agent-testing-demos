import argparse
import json
from pathlib import Path

from .config import AgentConfig, RetrievalWeights
from .knowledge_base import KnowledgeBase
from .pipeline import PRDTestPointPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PRD knowledge-retrieval test-point generation agent.")
    parser.add_argument("--prd", default="data/sample_prd.txt", help="Path to PRD text file.")
    parser.add_argument("--kb", default="data/knowledge_base.json", help="Path to knowledge base JSON.")
    parser.add_argument("--out", default="output/full_test_points.json", help="Path to output JSON.")
    parser.add_argument("--prd-id", default="PRD_MEMBER_RENEW_001", help="PRD id.")
    parser.add_argument("--title", default="会员自动续费", help="PRD title.")
    parser.add_argument("--top-k", type=int, default=8, help="Top K retrieved knowledge docs.")
    parser.add_argument("--min-score", type=float, default=0.01, help="Minimum retrieval score.")
    parser.add_argument("--keyword-weight", type=float, default=0.35, help="Keyword retrieval weight.")
    parser.add_argument("--vector-weight", type=float, default=0.35, help="Vector retrieval weight.")
    parser.add_argument("--defect-weight", type=float, default=0.20, help="Historical defect similarity weight.")
    parser.add_argument("--rule-weight", type=float, default=0.10, help="Rule hit weight.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    prd_text = Path(args.prd).read_text(encoding="utf-8")
    knowledge_base = KnowledgeBase.from_json(args.kb)
    config = AgentConfig(
        top_k=args.top_k,
        min_score=args.min_score,
        retrieval_weights=RetrievalWeights(
            keyword=args.keyword_weight,
            vector=args.vector_weight,
            defect=args.defect_weight,
            rule=args.rule_weight,
        ),
    )
    pipeline = PRDTestPointPipeline(config=config)
    output = pipeline.run(
        prd_id=args.prd_id,
        title=args.title,
        prd_text=prd_text,
        knowledge_base=knowledge_base,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(output["summary"], ensure_ascii=False, indent=2))
    print(f"JSON output written to: {out_path}")


if __name__ == "__main__":
    main()
