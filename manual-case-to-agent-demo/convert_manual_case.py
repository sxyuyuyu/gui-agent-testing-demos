import argparse
import json
from pathlib import Path

from manual_case_agent.converter import ManualCaseConversionPipeline
from manual_case_agent.page_model import PageModel


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert manual natural-language cases to GUI Agent DSL.")
    parser.add_argument("--case", default="data/manual_cases/notification_switch_persist.txt", help="Manual case file path.")
    parser.add_argument("--page-model", default="data/page_model.json", help="Page model JSON path.")
    parser.add_argument("--out", default="output/notification_switch_persist.json", help="Output JSON path.")
    parser.add_argument("--case-id", default="TC_PROFILE_SETTING_001", help="Case id.")
    parser.add_argument("--title", default="关闭通知开关后状态保留", help="Case title.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    case_text = Path(args.case).read_text(encoding="utf-8")
    page_model = PageModel.from_json(args.page_model)
    pipeline = ManualCaseConversionPipeline(page_model)
    result = pipeline.convert(case_id=args.case_id, title=args.title, source_text=case_text)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"caseId": result["caseId"], **result["summary"], "output": args.out}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
