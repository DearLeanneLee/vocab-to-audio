"""把词典格式的文字整理成语音引擎能自然朗读的形式。
Turn dictionary-style text into something a TTS engine reads naturally.
"""
import re

def zh_clean(s):
    s = s.replace("...", "…").replace("..", "…")
    s = re.sub(r"…+", "某事", s)                      # 与…隔绝 -> 与某事隔绝（"…" 读作「某事」/ read "…" as 「某事」）
    s = re.sub(r"(?:(?<=^)|(?<=\s))(\d)\.\s*",
               lambda m: "第" + "一二三四五"[int(m.group(1)) - 1] + "，", s)  # 1.xx 2.yy -> 第一，xx 第二，yy
    for a in "（）();；":
        s = s.replace(a, "，")
    s = re.sub(r"\s+", "，", s.strip())
    s = re.sub(r"，+", "，", s).strip("，")
    return s + "。"

def en_clean(s):
    return s.replace("-", " ")
