from .schema import RequirementModel, Risk, TestPoint


class QualityValidator:
    def validate(self, requirement: RequirementModel, test_points: list[TestPoint]) -> list[Risk]:
        risks = []
        risks.extend(self._requirement_risks(requirement))
        risks.extend(self._coverage_risks(requirement, test_points))
        risks.extend(self._test_point_risks(test_points))
        return risks

    def _requirement_risks(self, requirement: RequirementModel) -> list[Risk]:
        risks = []
        if not requirement.features:
            risks.append(
                Risk(
                    type="ambiguous_requirement",
                    description="PRD 中未识别到明确功能点",
                    suggestion="建议补充功能名称、用户操作、系统行为和预期结果",
                )
            )
        if "失败重试" in requirement.features and any("3 次" in item or "最多 3 次" in item for item in requirement.boundaries):
            risks.append(
                Risk(
                    type="missing_rule",
                    description="PRD 未明确重试 3 次全部失败后的用户通知和状态展示",
                    suggestion="建议补充最终失败后的通知、前端展示、后台状态和是否可人工重试",
                )
            )
        if "支付回调幂等" in requirement.features and "订单" not in requirement.entities:
            risks.append(
                Risk(
                    type="missing_data_model",
                    description="PRD 提到支付回调幂等，但未明确订单唯一键或支付流水号规则",
                    suggestion="建议补充支付流水号、订单号、回调幂等键和重复回调返回策略",
                )
            )
        return risks

    def _coverage_risks(self, requirement: RequirementModel, test_points: list[TestPoint]) -> list[Risk]:
        generated_features = {point.feature for point in test_points}
        risks = []
        for feature in requirement.features:
            if feature not in generated_features and feature != "开启自动续费":
                risks.append(
                    Risk(
                        type="missing_test_coverage",
                        description=f"功能点“{feature}”未生成对应测试点",
                        suggestion="建议检查功能识别规则或补充测试点模板",
                    )
                )
        return risks

    def _test_point_risks(self, test_points: list[TestPoint]) -> list[Risk]:
        risks = []
        for point in test_points:
            if not point.steps or not point.expected_results:
                risks.append(
                    Risk(
                        type="invalid_test_point",
                        description=f"测试点 {point.id} 缺少步骤或预期结果",
                        suggestion="请补充 steps 和 expectedResults 后再进入评审",
                    )
                )
            if not point.knowledge_refs:
                risks.append(
                    Risk(
                        type="weak_knowledge_support",
                        description=f"测试点 {point.id} 没有命中知识库依据",
                        suggestion="可补充历史用例、缺陷或业务规则，提升生成可信度",
                    )
                )
        return risks
