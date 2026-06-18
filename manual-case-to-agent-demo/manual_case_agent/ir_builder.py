from .schema import IRAssertion, IRStep, IntermediateCase, Risk


class IRBuilder:
    def __init__(self, page_model):
        self.page_model = page_model

    def build(self, case_id: str, title: str, source_text: str, intents: list) -> IntermediateCase:
        current_page = self.page_model.default_start_page()
        preconditions = []
        steps = []
        assertions = []
        risks = []
        last_state_change = None

        if any(intent.action == "login" for intent in intents):
            preconditions.append(
                {
                    "type": "login",
                    "accountPool": "normal_user_pool",
                    "assert": self.page_model.page_assertion(current_page),
                }
            )

        for intent in intents:
            if intent.action == "login":
                continue

            if intent.action == "navigate":
                if not intent.target_page:
                    risks.append(self._risk("ambiguous_page", intent.source_text, "未识别目标页面，请补充页面名称或页面别名"))
                    continue
                path = self.page_model.shortest_path(current_page, intent.target_page)
                if path is None:
                    steps.append(
                        IRStep(
                            step_id=f"S{len(steps) + 1}",
                            intent="open_page",
                            page=current_page,
                            target=intent.target_page,
                            wait_condition=self.page_model.page_assertion(intent.target_page),
                            source_text=intent.source_text,
                        )
                    )
                    current_page = intent.target_page
                    continue
                for edge in path:
                    step = self._nav_step(len(steps) + 1, edge, intent.source_text)
                    steps.append(step)
                    current_page = edge["to"]
                continue

            if intent.action in ["click", "input", "switch", "select"]:
                control = self.page_model.resolve_control(current_page, intent.target_text)
                if control is None:
                    risks.append(self._risk("control_not_found", intent.source_text, f"当前页面 {current_page} 未找到匹配控件"))
                    continue
                if control.get("ambiguous"):
                    risks.append(self._risk("ambiguous_control", intent.source_text, f"匹配到多个控件：{control.get('candidates')}"))
                    continue

                step = self._op_step(len(steps) + 1, current_page, control, intent)
                steps.append(step)

                next_page = self.page_model.click_next_page(current_page, control["id"])
                if intent.action == "click" and next_page:
                    current_page = next_page
                    step.wait_condition = self.page_model.page_assertion(next_page)

                if intent.action in ["switch", "select", "input"]:
                    last_state_change = {
                        "page": current_page,
                        "control": control,
                        "value": intent.value,
                    }
                    if intent.action == "switch":
                        step.post_assert = {"type": "state_equals", "expected": intent.value}
                continue

            if intent.action == "back":
                previous = current_page
                current_page = self.page_model.back_page(current_page)
                steps.append(
                    IRStep(
                        step_id=f"S{len(steps) + 1}",
                        intent="back",
                        page=previous,
                        wait_condition=self.page_model.page_assertion(current_page),
                        timeout=5000,
                        source_text=intent.source_text,
                    )
                )
                continue

            if intent.action == "assert":
                assertion = self._assertion(len(assertions) + 1, current_page, intent, last_state_change)
                if assertion is None:
                    risks.append(self._risk("ambiguous_assertion", intent.source_text, "断言目标或期望值不明确，需要人工补充"))
                else:
                    assertions.append(assertion)

        return IntermediateCase(
            case_id=case_id,
            title=title,
            source_text=source_text,
            preconditions=preconditions,
            steps=steps,
            assertions=assertions,
            risk_flags=risks,
        )

    def _nav_step(self, index: int, edge: dict, source_text: str) -> IRStep:
        control = self.page_model.resolve_control(edge["from"], edge["via"])
        return IRStep(
            step_id=f"S{index}",
            intent="navigate",
            page=edge["from"],
            target=control["id"] if control else edge["via"],
            target_name=control["name"] if control else edge["via"],
            locator=control["locator"] if control else None,
            wait_condition=self.page_model.page_assertion(edge["to"]),
            source_text=source_text,
        )

    def _op_step(self, index: int, page: str, control: dict, intent) -> IRStep:
        return IRStep(
            step_id=f"S{index}",
            intent=intent.action,
            page=page,
            target=control["id"],
            target_name=control["name"],
            locator=control["locator"],
            value=intent.value,
            source_text=intent.source_text,
        )

    def _assertion(self, index: int, current_page: str, intent, last_state_change: dict | None) -> IRAssertion | None:
        if intent.expectation == "state_persisted" and last_state_change:
            control = last_state_change["control"]
            return IRAssertion(
                assertion_id=f"A{index}",
                page=last_state_change["page"],
                target=control["id"],
                locator=control["locator"],
                type="state_equals",
                expected=last_state_change["value"],
                source_text=intent.source_text,
            )

        control = self.page_model.resolve_control(current_page, intent.target_text)
        if control and control.get("ambiguous"):
            control = self._prefer_assertion_control(current_page, control.get("candidates", []))
        if control and not control.get("ambiguous"):
            return IRAssertion(
                assertion_id=f"A{index}",
                page=current_page,
                target=control["id"],
                locator=control["locator"],
                type="visible",
                expected=True,
                source_text=intent.source_text,
            )
        return None

    def _prefer_assertion_control(self, page: str, candidates: list[str]) -> dict | None:
        preferred_roles = ["label", "image", "card", "switch"]
        controls = [self.page_model.get_control(page, control_id) for control_id in candidates]
        controls = [control for control in controls if control]
        for role in preferred_roles:
            for control in controls:
                if control.get("role") == role:
                    return control
        return None

    def _risk(self, risk_type: str, source_text: str, suggestion: str) -> Risk:
        return Risk(type=risk_type, source_text=source_text, suggestion=suggestion)
