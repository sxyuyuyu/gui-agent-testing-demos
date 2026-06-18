from .schema import Intent
from .text_utils import contains_any, quoted_value, split_clauses


class IntentParser:
    def __init__(self, page_model):
        self.page_model = page_model

    def parse(self, text: str) -> list[Intent]:
        intents = []
        for clause in split_clauses(text):
            intent = self._parse_clause(clause)
            if intent.action != "unknown":
                intents.append(intent)
        return intents

    def _parse_clause(self, clause: str) -> Intent:
        page = self.page_model.resolve_page(clause)

        if contains_any(clause, ["验证", "检查", "确认", "应", "不能", "不可", "保持"]):
            return Intent(
                action="assert",
                source_text=clause,
                target_text=clause,
                expectation=self._expectation(clause),
            )

        if contains_any(clause, ["进入", "打开", "跳转"]):
            return Intent(action="navigate", source_text=clause, target_page=page, target_text=clause)

        if clause in ["登录", "已登录"] or (clause.endswith("登录") and not contains_any(clause, ["点击登录", "登录按钮"])):
            return Intent(action="login", source_text=clause, target_text="normal_user")

        if contains_any(clause, ["返回", "退出"]):
            return Intent(action="back", source_text=clause)

        if contains_any(clause, ["输入", "填写"]):
            return Intent(action="input", source_text=clause, target_text=clause, value=quoted_value(clause) or "<TEST_DATA>")

        if "开关" in clause and contains_any(clause, ["关闭", "打开", "开启"]):
            value = False if "关闭" in clause else True
            return Intent(action="switch", source_text=clause, target_text=clause, value=value)

        if contains_any(clause, ["选择", "勾选"]):
            return Intent(action="select", source_text=clause, target_text=clause, value=quoted_value(clause))

        if contains_any(clause, ["点击", "点", "提交", "领取", "支付", "申请"]):
            return Intent(action="click", source_text=clause, target_text=clause)

        return Intent(action="unknown", source_text=clause)

    def _expectation(self, clause: str) -> str:
        if contains_any(clause, ["状态保留", "保持", "仍为", "仍然"]):
            return "state_persisted"
        if contains_any(clause, ["成功", "展示", "显示", "出现"]):
            return "visible_or_success"
        if contains_any(clause, ["不能", "不可", "不应", "不会"]):
            return "not_allowed"
        if contains_any(clause, ["一致", "正确"]):
            return "consistent"
        return "explicit_assertion_required"
