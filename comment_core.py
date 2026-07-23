from __future__ import annotations

import re
from typing import List, Tuple

MAX_COMMENT_COUNT = 50
MAX_ARTICLE_CHARS = 8_000
DISCORD_CHUNK_LIMIT = 1_800

HEADER_SPLIT = re.compile(r"\n\s*\n", re.DOTALL)
STYLE_RE = re.compile(
    r"(海外反応|海外の反応)|(掲示板風?|bbs)|"
    r"(ヤフコメ|yahoo.?コメント?)|(ポスト風?|tweet|twitter|x)",
    re.I,
)
NUM_RE = re.compile(r"(\d+)\s*(個)?コメント|N\s*=\s*(\d+)", re.I)


def parse_header(
    body: str,
    default_n: int = 20,
) -> Tuple[str, int, str, str]:
    if HEADER_SPLIT.search(body):
        header, article = HEADER_SPLIT.split(body, 1)
    else:
        header, article = body, "（本文なし）"

    match = STYLE_RE.search(header)
    if match:
        style = (
            "海外反応"
            if match.group(1)
            else "掲示板"
            if match.group(2)
            else "ヤフコメ"
            if match.group(3)
            else "ポスト"
        )
    else:
        style = "掲示板"

    count_match = NUM_RE.search(header)
    requested = (
        int(count_match.group(1) or count_match.group(3))
        if count_match
        else default_n
    )
    count = min(max(requested, 1), MAX_COMMENT_COUNT)

    header_clean = STYLE_RE.sub("", header)
    header_clean = NUM_RE.sub("", header_clean)
    tone = header_clean.strip()[:500]

    normalized_article = article.strip()[:MAX_ARTICLE_CHARS]
    return style, count, normalized_article, tone


def clean_lines(text: str, count: int) -> List[str]:
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and line.strip() != "<END>"
    ]
    return lines[:count]


def chunk(
    text: str,
    limit: int = DISCORD_CHUNK_LIMIT,
) -> List[str]:
    parts: List[str] = []
    current = ""
    for original_line in text.splitlines():
        line = original_line
        while len(line) > limit:
            if current:
                parts.append(current.rstrip("\n"))
                current = ""
            parts.append(line[:limit])
            line = line[limit:]
        if len(current) + len(line) + 1 > limit:
            if current:
                parts.append(current.rstrip("\n"))
            current = ""
        current += line + "\n"
    if current.strip():
        parts.append(current.rstrip("\n"))
    return parts
