import re


def normalize_text(text: str) -> str:
    text = text.replace("\u3000", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_clauses(text: str) -> list[str]:
    text = normalize_text(text)
    replacements = [
        (r"(登录)后(进入|打开|跳转)", r"\1，\2"),
        (r"(提交)后(验证|检查|确认)", r"\1，\2"),
        (r"(支付成功)后(验证|检查|确认)", r"\1，\2"),
        (r"(返回)后(再次|重新)", r"\1，\2"),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)
    parts = re.split(r"[，,。；;\n]+|然后|并且|之后|再", text)
    return [part.strip() for part in parts if part.strip()]


def quoted_value(text: str) -> str | None:
    match = re.search(r"[“\"](.+?)[”\"]", text)
    return match.group(1) if match else None


def contains_any(text: str, words: list[str]) -> bool:
    return any(word in text for word in words)
