from .schema import IntermediateCase, to_dict


class AgentDSLGenerator:
    def generate(self, ir: IntermediateCase) -> dict:
        steps = []

        for precondition in ir.preconditions:
            if precondition["type"] == "login":
                steps.append(
                    {
                        "id": "S0",
                        "action": "login",
                        "using": precondition["accountPool"],
                        "expect": precondition["assert"],
                    }
                )

        for step in ir.steps:
            payload = {
                "id": step.step_id,
                "action": self._action(step.intent),
                "sourceText": step.source_text,
            }
            if step.locator:
                payload["target"] = step.locator
            if step.value is not None:
                payload["value"] = step.value
            if step.wait_condition:
                payload["expect"] = step.wait_condition
            if step.post_assert:
                payload["postAssert"] = step.post_assert
            steps.append(payload)

        for assertion in ir.assertions:
            steps.append(
                {
                    "id": assertion.assertion_id,
                    "action": "assert",
                    "target": assertion.locator,
                    "assertion": {
                        "type": assertion.type,
                        "expected": assertion.expected,
                    },
                    "evidence": assertion.evidence,
                    "sourceText": assertion.source_text,
                }
            )

        return {
            "agentTaskId": f"AGENT_{ir.case_id}",
            "name": ir.title,
            "environment": {
                "platform": "android",
                "app": "target_app",
                "resetBeforeRun": False,
            },
            "executionPolicy": {
                "stepTimeoutMs": 10000,
                "caseTimeoutMs": 60000,
                "retry": {
                    "maxRetry": 1,
                    "retryOn": ["ELEMENT_NOT_FOUND", "PAGE_LOAD_TIMEOUT", "AGENT_RUNTIME_ERROR"],
                },
                "evidence": ["screenshot_on_each_step", "ui_tree_on_failure", "screen_record"],
            },
            "steps": steps,
        }

    def _action(self, intent: str) -> str:
        return {
            "navigate": "tap",
            "click": "tap",
            "input": "input",
            "switch": "set_switch",
            "select": "select",
            "open_page": "open_page",
            "back": "back",
        }.get(intent, intent)
