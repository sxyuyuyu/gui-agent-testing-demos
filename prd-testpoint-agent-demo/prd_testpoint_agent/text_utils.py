import re
from collections import Counter


DOMAIN_TERMS = [
    "自动续费",
    "开启自动续费",
    "取消自动续费",
    "自动扣费",
    "会员",
    "购买页",
    "设置页",
    "余额不足",
    "支付失败",
    "失败重试",
    "支付回调",
    "重复回调",
    "重复订单",
    "幂等",
    "续费订单",
    "会员有效期",
    "状态流转",
    "边界",
    "异常",
    "权限",
    "兼容性",
    "到期前",
    "24 小时",
    "3 次",
    "订单一致性",
    "重复扣费",
    "退款",
    "申请退款",
    "原路退款",
    "退款审核中",
    "退款金额",
    "重复退款",
    "优惠券",
    "领取",
    "卡包",
    "库存",
    "核销",
    "锁定",
    "释放",
    "门槛金额",
    "登录",
    "风控",
    "图形验证码",
    "短信验证码",
    "账号锁定",
    "密码错误",
    "新设备",
    "消息通知",
    "通知设置",
    "站内信",
    "短信",
    "Push",
    "开关状态",
    "跨端同步",
    "系统权限",
]


def normalize_text(text: str) -> str:
    text = text.replace("\u3000", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_sentences(text: str) -> list[str]:
    chunks = re.split(r"[。；;\n]+", normalize_text(text))
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def tokenize(text: str) -> list[str]:
    text = normalize_text(text).lower()
    tokens = []

    for term in DOMAIN_TERMS:
        if term.lower() in text:
            tokens.append(term.lower())

    chinese_chunks = re.findall(r"[\u4e00-\u9fff]+", text)
    for chunk in chinese_chunks:
        if len(chunk) <= 2:
            tokens.append(chunk)
        else:
            tokens.extend(chunk[i : i + 2] for i in range(len(chunk) - 1))
            tokens.extend(chunk[i : i + 3] for i in range(len(chunk) - 2))

    tokens.extend(re.findall(r"[a-zA-Z0-9_]+", text))
    return tokens


def term_overlap(left: str, right: str) -> list[str]:
    right_text = normalize_text(right)
    return [term for term in DOMAIN_TERMS if term in left and term in right_text]


def vectorize(tokens: list[str]) -> Counter:
    return Counter(tokens)
