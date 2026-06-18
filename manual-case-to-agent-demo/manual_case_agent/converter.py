from datetime import datetime, timedelta, timezone

from .agent_dsl import AgentDSLGenerator
from .intent_parser import IntentParser
from .ir_builder import IRBuilder
from .schema import to_dict
from .text_utils import split_clauses


class ManualCaseConversionPipeline:
    def __init__(self, page_model):
        self.page_model = page_model
        self.intent_parser = IntentParser(page_model)
        self.ir_builder = IRBuilder(page_model)
        self.dsl_generator = AgentDSLGenerator()

    def convert(self, case_id: str, title: str, source_text: str) -> dict:
        clauses = split_clauses(source_text)
        intents = self.intent_parser.parse(source_text)
        ir = self.ir_builder.build(case_id=case_id, title=title, source_text=source_text, intents=intents)
        agent_input = self.dsl_generator.generate(ir)

        return {
            "caseId": case_id,
            "title": title,
            "generatedAt": datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds"),
            "sourceText": source_text,
            "clauses": clauses,
            "intents": to_dict(intents),
            "intermediateRepresentation": to_dict(ir),
            "agentInput": agent_input,
            "summary": {
                "intentCount": len(intents),
                "irStepCount": len(ir.steps),
                "assertionCount": len(ir.assertions),
                "riskCount": len(ir.risk_flags),
            },
            "risks": to_dict(ir.risk_flags),
        }
