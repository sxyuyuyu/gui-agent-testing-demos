import re

from .schema import PRDSection, RequirementModel
from .text_utils import DOMAIN_TERMS, normalize_text, split_sentences, unique


FEATURE_PATTERNS = [
    (r"开启自动续费", "开启自动续费"),
    (r"取消自动续费", "取消自动续费"),
    (r"自动扣费|自动续费.*扣费|到期前.*扣费", "自动扣费"),
    (r"重试|失败后.*重试", "失败重试"),
    (r"支付回调|重复回调|幂等|重复生成|重复订单", "支付回调幂等"),
    (r"申请退款|发起退款", "申请退款"),
    (r"退款审核|审核通过|审核拒绝", "退款审核"),
    (r"原路退款|退款成功|已退款", "原路退款"),
    (r"退款金额|全额退款|部分退款|剩余权益", "退款金额计算"),
    (r"优惠券.*领取|立即领取|发券", "优惠券领取"),
    (r"优惠券.*使用|订单结算页|抵扣|核销", "优惠券使用"),
    (r"库存|超发", "优惠券库存"),
    (r"优惠券.*释放|锁定.*释放|支付失败.*优惠券", "优惠券释放"),
    (r"登录|手机号.*密码", "账号登录"),
    (r"图形验证码|验证码", "验证码校验"),
    (r"账号锁定|锁定", "账号锁定"),
    (r"新设备|二次校验", "新设备二次校验"),
    (r"通知设置|消息通知", "通知设置"),
    (r"站内信|短信|Push|通知开关", "通知渠道开关"),
    (r"跨端同步|多端.*修改|A 设备|B 设备", "通知跨端同步"),
    (r"系统权限|权限引导", "系统权限引导"),
]

ENTITY_PATTERNS = [
    (r"用户", "用户"),
    (r"会员", "会员"),
    (r"订单|续费订单", "订单"),
    (r"退款申请|退款", "退款单"),
    (r"优惠券|卡包", "优惠券"),
    (r"支付方式|支付|扣费", "支付方式"),
    (r"设置页", "设置页"),
    (r"购买页", "会员购买页"),
    (r"手机号|账号", "账号"),
    (r"验证码", "验证码"),
    (r"站内信|短信|Push", "通知渠道"),
]

EXCEPTION_PATTERNS = [
    (r"余额不足", "余额不足"),
    (r"支付失败|扣费失败", "支付失败"),
    (r"网络异常", "网络异常"),
    (r"重复回调|重复到达", "重复回调"),
    (r"重复点击|重复提交", "重复提交"),
    (r"库存为 0|库存不足", "库存不足"),
    (r"支付失败|订单取消", "支付失败"),
    (r"验证码输入错误|验证码.*错误", "验证码错误"),
    (r"接口失败", "接口失败"),
    (r"系统权限关闭", "系统权限关闭"),
]

KEYWORD_EXPANSION = {
    "自动续费": ["订阅续期", "周期扣款", "自动扣款"],
    "开启自动续费": ["开启订阅", "开启周期扣款"],
    "取消自动续费": ["取消订阅", "关闭自动扣款"],
    "支付回调": ["重复回调", "回调幂等", "重复扣费"],
    "余额不足": ["扣费失败", "支付失败"],
    "失败重试": ["重试间隔", "重试上限"],
    "申请退款": ["退款申请", "售后申请"],
    "原路退款": ["退款成功", "退款回调", "资金流"],
    "退款金额计算": ["全额退款", "部分退款", "金额边界"],
    "优惠券领取": ["发券", "库存扣减", "防超发"],
    "优惠券使用": ["优惠券核销", "订单抵扣", "锁券"],
    "账号登录": ["密码登录", "异常登录", "撞库防护"],
    "验证码校验": ["图形验证码", "短信验证码", "验证码有效期"],
    "通知设置": ["通知开关", "消息设置", "状态保存"],
    "通知跨端同步": ["多端一致性", "最后写入生效"],
}


class PRDParser:
    def parse(self, prd_id: str, title: str, text: str) -> RequirementModel:
        text = normalize_text(text)
        sentences = split_sentences(text)
        sections = [
            PRDSection(section_id=f"S{index}", title=f"需求片段 {index}", text=sentence)
            for index, sentence in enumerate(sentences, start=1)
        ]

        features = self._extract_by_patterns(FEATURE_PATTERNS, text)
        entities = self._extract_by_patterns(ENTITY_PATTERNS, text)
        exceptions = self._extract_by_patterns(EXCEPTION_PATTERNS, text)
        boundaries = self._extract_boundaries(text)
        rules = self._extract_rules(sentences)
        keywords, expanded_keywords = self._extract_keywords(text, features, boundaries, exceptions)

        return RequirementModel(
            prd_id=prd_id,
            title=title,
            raw_text=text,
            sections=sections,
            features=features,
            entities=entities,
            rules=rules,
            boundaries=boundaries,
            exceptions=exceptions,
            keywords=keywords,
            expanded_keywords=expanded_keywords,
        )

    def _extract_by_patterns(self, patterns: list[tuple[str, str]], text: str) -> list[str]:
        values = []
        for pattern, value in patterns:
            if re.search(pattern, text):
                values.append(value)
        return unique(values)

    def _extract_boundaries(self, text: str) -> list[str]:
        values = []
        patterns = [
            r"到期前\s*\d+\s*天",
            r"\d+\s*小时",
            r"\d+\s*次",
            r"\d+\s*天",
            r"\d+\s*分钟",
            r"\d+\s*秒",
            r"\d+\.\d+\s*元",
            r"最多\s*\d+\s*次",
        ]
        for pattern in patterns:
            values.extend(re.findall(pattern, text))
        return unique([re.sub(r"\s+", " ", value).strip() for value in values])

    def _extract_rules(self, sentences: list[str]) -> list[str]:
        rule_words = ["需要", "如果", "则", "最多", "不再", "保证", "开启后", "取消后"]
        return [sentence for sentence in sentences if any(word in sentence for word in rule_words)]

    def _extract_keywords(
        self,
        text: str,
        features: list[str],
        boundaries: list[str],
        exceptions: list[str],
    ) -> tuple[list[str], list[str]]:
        keywords = []
        for term in DOMAIN_TERMS:
            if term in text:
                keywords.append(term)

        keywords.extend(features)
        keywords.extend(boundaries)
        keywords.extend(exceptions)
        keywords = unique(keywords)

        expanded = []
        for keyword in keywords:
            expanded.extend(KEYWORD_EXPANSION.get(keyword, []))
        return keywords, unique(expanded)
