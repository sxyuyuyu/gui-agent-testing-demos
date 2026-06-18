from .schema import KnowledgeRef, RequirementModel, RequirementRef, RetrievalHit, TestPoint


class TestPointGenerator:
    def generate(self, requirement: RequirementModel, hits: list[RetrievalHit]) -> list[TestPoint]:
        points: list[TestPoint] = []
        index = 1

        for builder in [
            self._build_enable_auto_renew,
            self._build_auto_charge,
            self._build_insufficient_balance,
            self._build_retry,
            self._build_cancel_auto_renew,
            self._build_callback_idempotency,
            self._build_state_transition,
        ]:
            generated = builder(requirement, hits, index)
            points.extend(generated)
            index += len(generated)

        generated_features = {point.feature for point in points}
        for feature in requirement.features:
            if feature in generated_features:
                continue
            generated = self._build_generic_feature_points(requirement, hits, index, feature)
            points.extend(generated)
            index += len(generated)

        return self._deduplicate(points)

    def _build_enable_auto_renew(self, requirement: RequirementModel, hits: list[RetrievalHit], start: int) -> list[TestPoint]:
        if "开启自动续费" not in requirement.features:
            return []
        return [
            self._point(
                start,
                "用户可成功开启自动续费",
                "functional",
                "P0",
                "开启自动续费",
                requirement,
                "开启自动续费",
                hits,
                ["用户已登录", "用户未开启自动续费"],
                ["进入会员购买页", "开启自动续费", "查看开启结果"],
                ["自动续费开启成功", "页面展示自动续费已开启", "后台订阅状态为已开启"],
                ["普通会员账号"],
                ["正向", "会员", "状态展示"],
                0.95,
            )
        ]

    def _build_auto_charge(self, requirement: RequirementModel, hits: list[RetrievalHit], start: int) -> list[TestPoint]:
        if "自动扣费" not in requirement.features:
            return []
        return [
            self._point(
                start,
                "会员到期前 1 天自动扣费成功",
                "boundary",
                "P0",
                "自动扣费",
                requirement,
                "到期前",
                hits,
                ["用户已开启自动续费", "支付方式可用", "会员将在 1 天后到期"],
                ["构造会员到期前 1 天状态", "触发自动扣费任务", "查询扣费结果和会员有效期"],
                ["扣费成功", "生成一笔续费订单", "会员有效期正确延长"],
                ["余额充足账号", "到期前 1 天会员"],
                ["边界值", "自动扣费", "订单"],
                0.93,
            ),
            self._point(
                start + 1,
                "未到扣费时间不应提前扣费",
                "boundary",
                "P1",
                "自动扣费",
                requirement,
                "到期前",
                hits,
                ["用户已开启自动续费", "会员将在 2 天后到期"],
                ["构造会员到期前 2 天状态", "触发自动扣费任务", "查询订单和扣费记录"],
                ["系统不发起自动扣费", "不生成续费订单", "会员有效期不变化"],
                ["到期前 2 天会员"],
                ["边界值", "防提前扣费"],
                0.90,
            ),
        ]

    def _build_insufficient_balance(self, requirement: RequirementModel, hits: list[RetrievalHit], start: int) -> list[TestPoint]:
        if "余额不足" not in requirement.exceptions:
            return []
        return [
            self._point(
                start,
                "余额不足时续费失败并记录失败状态",
                "exception",
                "P0",
                "失败重试",
                requirement,
                "余额不足",
                hits,
                ["用户已开启自动续费", "会员到期前 1 天", "账户余额不足"],
                ["触发自动扣费任务", "查询扣费结果", "查询会员状态"],
                ["扣费失败", "不延长会员有效期", "记录失败原因余额不足", "生成待重试记录"],
                ["余额不足账号"],
                ["异常", "余额不足", "失败状态"],
                0.94,
            )
        ]

    def _build_retry(self, requirement: RequirementModel, hits: list[RetrievalHit], start: int) -> list[TestPoint]:
        if "失败重试" not in requirement.features:
            return []
        return [
            self._point(
                start,
                "扣费失败后 24 小时触发重试",
                "boundary",
                "P0",
                "失败重试",
                requirement,
                "重试",
                hits,
                ["用户自动续费扣费失败", "存在待重试记录"],
                ["构造失败后未满 24 小时状态", "验证不会重试", "构造失败后满 24 小时状态", "触发重试任务"],
                ["未满 24 小时时不重试", "满 24 小时后发起重试", "重试结果被正确记录"],
                ["扣费失败记录", "时间模拟能力"],
                ["边界值", "24小时", "重试"],
                0.91,
            ),
            self._point(
                start + 1,
                "最多只重试 3 次",
                "boundary",
                "P0",
                "失败重试",
                requirement,
                "最多",
                hits,
                ["用户自动续费连续失败", "存在重试记录"],
                ["构造连续 3 次扣费失败", "继续推进时间", "再次触发重试任务"],
                ["系统最多发起 3 次重试", "第 4 次不再发起扣费", "最终状态标记为续费失败"],
                ["连续扣费失败账号"],
                ["边界值", "次数限制", "重试上限"],
                0.92,
            ),
        ]

    def _build_cancel_auto_renew(self, requirement: RequirementModel, hits: list[RetrievalHit], start: int) -> list[TestPoint]:
        if "取消自动续费" not in requirement.features:
            return []
        return [
            self._point(
                start,
                "用户取消自动续费后不再自动扣费",
                "functional",
                "P0",
                "取消自动续费",
                requirement,
                "取消自动续费",
                hits,
                ["用户已开启自动续费"],
                ["进入设置页", "取消自动续费", "构造会员到期前 1 天状态", "触发自动扣费任务"],
                ["自动续费状态为已关闭", "系统不发起扣费", "不生成续费订单"],
                ["已开启自动续费账号"],
                ["取消", "防扣费", "状态流转"],
                0.96,
            )
        ]

    def _build_callback_idempotency(self, requirement: RequirementModel, hits: list[RetrievalHit], start: int) -> list[TestPoint]:
        if "支付回调幂等" not in requirement.features:
            return []
        return [
            self._point(
                start,
                "重复支付回调不会生成重复续费订单",
                "idempotency",
                "P0",
                "支付回调幂等",
                requirement,
                "支付回调",
                hits,
                ["用户自动续费扣费成功", "存在同一支付流水号"],
                ["模拟支付成功回调", "再次发送相同支付流水号的回调", "查询续费订单和扣费记录"],
                ["只生成一笔续费订单", "只延长一次会员有效期", "重复回调返回幂等成功或已处理"],
                ["相同支付流水号", "支付回调模拟器"],
                ["幂等", "重复回调", "历史缺陷"],
                0.97,
            )
        ]

    def _build_state_transition(self, requirement: RequirementModel, hits: list[RetrievalHit], start: int) -> list[TestPoint]:
        if not ({"开启自动续费", "取消自动续费"} & set(requirement.features)):
            return []
        return [
            self._point(
                start,
                "自动续费状态流转正确",
                "state_transition",
                "P1",
                "自动续费状态",
                requirement,
                "自动续费",
                hits,
                ["用户已登录"],
                ["从未开启状态开启自动续费", "验证状态变为已开启", "取消自动续费", "验证状态变为已关闭", "重新进入页面验证状态保留"],
                ["状态按未开启 -> 已开启 -> 已关闭流转", "页面展示与后台状态一致", "重新进入页面后状态保持正确"],
                ["普通会员账号"],
                ["状态流转", "前后端一致性"],
                0.89,
            )
        ]

    def _point(
        self,
        index: int,
        title: str,
        tp_type: str,
        priority: str,
        feature: str,
        requirement: RequirementModel,
        requirement_keyword: str,
        hits: list[RetrievalHit],
        preconditions: list[str],
        steps: list[str],
        expected_results: list[str],
        test_data: list[str],
        tags: list[str],
        confidence: float,
    ) -> TestPoint:
        return TestPoint(
            id=f"TP_{index:03d}",
            title=title,
            type=tp_type,
            priority=priority,
            feature=feature,
            requirement_ref=self._requirement_ref(requirement, requirement_keyword),
            knowledge_refs=self._knowledge_refs(feature, hits),
            preconditions=preconditions,
            steps=steps,
            expected_results=expected_results,
            test_data=test_data,
            tags=tags,
            confidence=confidence,
        )

    def _requirement_ref(self, requirement: RequirementModel, keyword: str) -> RequirementRef:
        for section in requirement.sections:
            if keyword in section.text:
                return RequirementRef(section_id=section.section_id, text=section.text)
        section = requirement.sections[0] if requirement.sections else None
        if section is None:
            return RequirementRef(section_id="S0", text="")
        return RequirementRef(section_id=section.section_id, text=section.text)

    def _knowledge_refs(self, feature: str, hits: list[RetrievalHit]) -> list[KnowledgeRef]:
        refs = []
        for hit in hits:
            haystack = " ".join([hit.title, hit.usable_knowledge, " ".join(hit.matched_keywords), " ".join(hit.test_angles)])
            if feature in haystack or any(term in haystack for term in ["自动续费", "重试", "幂等", "边界", "支付"]):
                refs.append(KnowledgeRef(doc_id=hit.doc_id, source=hit.source, reason=hit.usable_knowledge))
        return refs[:2]

    def _deduplicate(self, points: list[TestPoint]) -> list[TestPoint]:
        seen = set()
        result = []
        for point in points:
            key = (point.title, point.feature, tuple(point.expected_results))
            if key in seen:
                continue
            seen.add(key)
            result.append(point)
        for index, point in enumerate(result, start=1):
            point.id = f"TP_{index:03d}"
        return result

    def _build_generic_feature_points(
        self,
        requirement: RequirementModel,
        hits: list[RetrievalHit],
        start: int,
        feature: str,
    ) -> list[TestPoint]:
        templates = self._generic_templates()
        template = templates.get(feature)
        if template is None:
            return [
                self._point(
                    start,
                    f"{feature}功能规则正确",
                    "functional",
                    "P1",
                    feature,
                    requirement,
                    feature,
                    hits,
                    ["用户满足功能使用条件", "测试环境和测试数据已准备"],
                    [f"进入{feature}相关页面", f"执行{feature}操作", "查看系统处理结果"],
                    ["操作结果符合 PRD 描述", "页面状态、后台状态和数据记录一致"],
                    ["普通测试账号"],
                    ["功能", "PRD覆盖"],
                    0.78,
                )
            ]

        points = [
            self._point(
                start,
                template["title"],
                template["type"],
                template["priority"],
                feature,
                requirement,
                template["keyword"],
                hits,
                template["preconditions"],
                template["steps"],
                template["expected"],
                template["data"],
                template["tags"],
                template["confidence"],
            )
        ]

        if template.get("risk_title"):
            points.append(
                self._point(
                    start + 1,
                    template["risk_title"],
                    template["risk_type"],
                    template["risk_priority"],
                    feature,
                    requirement,
                    template["keyword"],
                    hits,
                    template["risk_preconditions"],
                    template["risk_steps"],
                    template["risk_expected"],
                    template["risk_data"],
                    template["risk_tags"],
                    template["risk_confidence"],
                )
            )
        return points

    def _generic_templates(self) -> dict[str, dict]:
        return {
            "申请退款": {
                "title": "用户可从订单详情页成功提交退款申请",
                "type": "functional",
                "priority": "P0",
                "keyword": "申请退款",
                "preconditions": ["用户已登录", "存在满足退款规则的已支付订单"],
                "steps": ["进入订单详情页", "点击申请退款", "选择退款原因并提交", "查看订单状态"],
                "expected": ["退款申请提交成功", "订单状态变为退款审核中", "只生成一笔进行中的退款申请"],
                "data": ["已支付订单", "可退款用户"],
                "tags": ["退款", "正向流程", "状态流转"],
                "confidence": 0.92,
                "risk_title": "重复点击提交不会创建多笔退款申请",
                "risk_type": "idempotency",
                "risk_priority": "P0",
                "risk_preconditions": ["用户已进入退款提交页", "网络延迟或弱网环境"],
                "risk_steps": ["连续多次点击提交退款", "查询退款申请记录", "查看订单状态"],
                "risk_expected": ["仅创建一笔退款申请", "订单状态保持退款审核中", "不会出现多笔进行中退款"],
                "risk_data": ["弱网环境", "已支付订单"],
                "risk_tags": ["幂等", "重复提交", "历史缺陷"],
                "risk_confidence": 0.94,
            },
            "退款审核": {
                "title": "退款审核通过和拒绝状态流转正确",
                "type": "state_transition",
                "priority": "P0",
                "keyword": "审核",
                "preconditions": ["存在退款审核中的订单"],
                "steps": ["审核通过退款申请", "查看订单状态", "重新构造退款申请", "审核拒绝并填写原因"],
                "expected": ["审核通过后进入退款中或已退款", "审核拒绝后订单恢复已支付", "页面展示拒绝原因"],
                "data": ["退款审核中订单"],
                "tags": ["审核", "状态流转"],
                "confidence": 0.88,
            },
            "原路退款": {
                "title": "审核通过后系统发起原路退款并更新订单状态",
                "type": "functional",
                "priority": "P0",
                "keyword": "原路退款",
                "preconditions": ["退款申请审核通过", "支付渠道可用"],
                "steps": ["触发原路退款", "模拟退款成功回调", "查询订单和资金流水"],
                "expected": ["退款成功", "订单状态变为已退款", "资金流水只记录一次", "用户收到通知"],
                "data": ["已支付订单", "支付流水号"],
                "tags": ["退款", "资金安全", "回调"],
                "confidence": 0.91,
                "risk_title": "重复退款回调不会导致重复退款",
                "risk_type": "idempotency",
                "risk_priority": "P0",
                "risk_preconditions": ["存在同一退款流水号", "退款已成功"],
                "risk_steps": ["发送退款成功回调", "再次发送相同退款回调", "查询资金流水和订单状态"],
                "risk_expected": ["只入账一次退款流水", "订单状态保持已退款", "不会重复退款"],
                "risk_data": ["相同退款流水号"],
                "risk_tags": ["回调幂等", "资金安全"],
                "risk_confidence": 0.95,
            },
            "退款金额计算": {
                "title": "退款金额按全额、部分和最小金额边界正确计算",
                "type": "boundary",
                "priority": "P0",
                "keyword": "退款金额",
                "preconditions": ["存在未使用订单和部分使用订单"],
                "steps": ["申请未使用订单退款", "申请部分使用订单退款", "构造最小退款金额 0.01 元", "构造退款金额为 0 的场景"],
                "expected": ["未使用订单全额退款", "部分使用订单按剩余权益折算", "0.01 元允许退款", "金额为 0 或超过可退金额被拦截"],
                "data": ["未使用订单", "部分使用订单", "金额边界数据"],
                "tags": ["金额边界", "退款计算"],
                "confidence": 0.9,
            },
            "优惠券领取": {
                "title": "用户可成功领取优惠券并进入卡包",
                "type": "functional",
                "priority": "P0",
                "keyword": "领取",
                "preconditions": ["用户已登录", "优惠券在领取时间内", "优惠券库存充足"],
                "steps": ["进入优惠券中心", "点击立即领取", "进入用户卡包查看优惠券"],
                "expected": ["领取成功", "用户卡包展示该优惠券", "同一用户不能重复领取同一张券"],
                "data": ["可领取优惠券", "普通用户"],
                "tags": ["优惠券", "领取", "卡包"],
                "confidence": 0.93,
                "risk_title": "多端同时领取不会导致库存超发",
                "risk_type": "concurrency",
                "risk_priority": "P0",
                "risk_preconditions": ["优惠券库存较少", "同一或多个用户多端并发领取"],
                "risk_steps": ["两个设备同时点击领取", "查询库存和发券记录"],
                "risk_expected": ["发券数量不超过库存", "库存不会变为负数", "失败端展示明确提示"],
                "risk_data": ["库存为 1 的优惠券", "多端用户"],
                "risk_tags": ["并发", "库存", "防超发"],
                "risk_confidence": 0.96,
            },
            "优惠券使用": {
                "title": "订单结算页只展示并核销当前可用优惠券",
                "type": "functional",
                "priority": "P0",
                "keyword": "结算页",
                "preconditions": ["用户已领取多张不同规则优惠券", "存在待支付订单"],
                "steps": ["进入订单结算页", "查看可用优惠券列表", "选择优惠券并支付成功", "查看优惠券状态"],
                "expected": ["只展示满足当前订单条件的优惠券", "支付成功后优惠券变为已使用", "订单金额正确抵扣"],
                "data": ["满减券", "未达门槛订单", "达门槛订单"],
                "tags": ["优惠券", "结算", "核销"],
                "confidence": 0.91,
            },
            "优惠券库存": {
                "title": "库存为 0 或领取结束后不可领取优惠券",
                "type": "boundary",
                "priority": "P0",
                "keyword": "库存",
                "preconditions": ["存在库存为 0 的优惠券", "存在已过领取结束时间的优惠券"],
                "steps": ["尝试领取库存为 0 的优惠券", "尝试领取已过领取时间的优惠券"],
                "expected": ["库存为 0 时不可领取", "领取结束后不可领取", "不扣减库存且不发券"],
                "data": ["库存为 0 的券", "已过期领取券"],
                "tags": ["边界", "库存", "过期"],
                "confidence": 0.89,
            },
            "优惠券释放": {
                "title": "订单取消或支付失败后优惠券释放回可用状态",
                "type": "exception",
                "priority": "P0",
                "keyword": "释放",
                "preconditions": ["订单已锁定优惠券", "订单未支付成功"],
                "steps": ["选择优惠券提交订单", "模拟支付失败或取消订单", "查看优惠券状态"],
                "expected": ["优惠券从锁定恢复为可用", "用户可再次使用该优惠券", "不会被错误核销"],
                "data": ["已锁定优惠券", "支付失败订单"],
                "tags": ["异常恢复", "释放", "状态回滚"],
                "confidence": 0.94,
            },
            "账号登录": {
                "title": "用户输入正确手机号和密码可登录成功",
                "type": "functional",
                "priority": "P0",
                "keyword": "登录",
                "preconditions": ["账号未锁定", "密码正确"],
                "steps": ["输入手机号和密码", "点击登录", "查看登录结果"],
                "expected": ["登录成功", "进入首页", "密码错误次数清零"],
                "data": ["正常账号"],
                "tags": ["登录", "正向", "状态清零"],
                "confidence": 0.9,
            },
            "验证码校验": {
                "title": "连续第 3 次密码错误时展示图形验证码",
                "type": "boundary",
                "priority": "P0",
                "keyword": "图形验证码",
                "preconditions": ["账号未锁定", "密码错误次数可控"],
                "steps": ["连续输入错误密码 2 次", "验证不展示图形验证码", "第 3 次输入错误密码", "查看验证码展示"],
                "expected": ["第 2 次不展示验证码", "第 3 次展示图形验证码", "验证码错误时不允许登录"],
                "data": ["正常账号", "错误密码"],
                "tags": ["安全", "次数边界", "验证码"],
                "confidence": 0.95,
            },
            "账号锁定": {
                "title": "连续第 5 次密码错误后账号锁定 30 分钟",
                "type": "boundary",
                "priority": "P0",
                "keyword": "锁定",
                "preconditions": ["账号未锁定", "密码错误次数可控"],
                "steps": ["连续输入错误密码 5 次", "尝试使用正确密码登录", "推进时间到未满 30 分钟", "推进时间满 30 分钟后再次登录"],
                "expected": ["第 5 次后账号锁定", "锁定未满 30 分钟不能登录", "锁定结束后可重新登录"],
                "data": ["正常账号", "时间模拟能力"],
                "tags": ["安全", "账号锁定", "时间边界"],
                "confidence": 0.95,
            },
            "新设备二次校验": {
                "title": "新设备登录需要短信验证码二次校验",
                "type": "permission",
                "priority": "P0",
                "keyword": "新设备",
                "preconditions": ["用户在新设备首次登录", "短信服务可用"],
                "steps": ["输入正确账号密码", "触发新设备登录", "输入短信验证码", "查看登录结果"],
                "expected": ["系统要求短信验证码", "验证码正确后登录成功", "验证码错误或过期时不允许登录"],
                "data": ["新设备标识", "短信验证码"],
                "tags": ["风控", "短信验证码", "新设备"],
                "confidence": 0.9,
            },
            "通知设置": {
                "title": "用户修改通知开关后状态可保存并重新进入保持一致",
                "type": "functional",
                "priority": "P0",
                "keyword": "通知设置",
                "preconditions": ["用户已登录", "进入设置页"],
                "steps": ["关闭某类通知开关", "退出设置页后重新进入", "重新打开通知开关", "再次查看状态"],
                "expected": ["关闭后状态保存", "重新进入后状态一致", "重新打开后恢复发送策略"],
                "data": ["普通用户"],
                "tags": ["通知设置", "状态保留"],
                "confidence": 0.93,
                "risk_title": "保存通知设置接口失败时页面提示失败并回滚",
                "risk_type": "exception",
                "risk_priority": "P0",
                "risk_preconditions": ["用户已进入设置页", "模拟保存接口失败"],
                "risk_steps": ["切换通知开关", "触发保存接口失败", "查看页面状态和后台状态"],
                "risk_expected": ["页面提示保存失败", "开关状态回滚到真实状态", "前后端状态一致"],
                "risk_data": ["接口失败 mock"],
                "risk_tags": ["异常恢复", "状态回滚"],
                "risk_confidence": 0.95,
            },
            "通知渠道开关": {
                "title": "站内信、短信、Push 三类通知可独立控制",
                "type": "functional",
                "priority": "P0",
                "keyword": "Push",
                "preconditions": ["用户已登录", "三类通知默认开启"],
                "steps": ["分别关闭站内信、短信、Push", "触发对应业务通知", "查看各渠道触达情况"],
                "expected": ["各渠道独立生效", "关闭渠道不再发送", "未关闭渠道正常发送"],
                "data": ["通知触发事件"],
                "tags": ["渠道隔离", "通知发送"],
                "confidence": 0.92,
            },
            "通知跨端同步": {
                "title": "A 设备修改通知设置后 B 设备展示最新状态",
                "type": "state_transition",
                "priority": "P1",
                "keyword": "跨端同步",
                "preconditions": ["同一账号登录 A、B 两台设备"],
                "steps": ["A 设备修改通知设置", "B 设备重新进入设置页", "多端同时修改通知设置"],
                "expected": ["B 设备展示 A 设备最新设置", "多端同时修改时按最后更新时间生效", "后台状态一致"],
                "data": ["同一账号双设备"],
                "tags": ["跨端同步", "状态一致"],
                "confidence": 0.9,
            },
            "系统权限引导": {
                "title": "系统 Push 权限关闭时页面展示权限引导",
                "type": "permission",
                "priority": "P1",
                "keyword": "系统权限",
                "preconditions": ["系统 Push 权限关闭", "用户已登录"],
                "steps": ["进入通知设置页", "查看 Push 开关区域", "点击权限引导"],
                "expected": ["页面提示系统权限关闭", "展示开启权限引导", "不误判为业务开关保存失败"],
                "data": ["关闭系统权限设备"],
                "tags": ["权限", "Push", "引导"],
                "confidence": 0.88,
            },
        }
