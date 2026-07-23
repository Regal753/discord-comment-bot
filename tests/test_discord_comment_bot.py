from __future__ import annotations

import unittest

from comment_core import (
    MAX_ARTICLE_CHARS,
    MAX_COMMENT_COUNT,
    chunk,
    clean_lines,
    parse_header,
)


class ParseHeaderTests(unittest.TestCase):
    def test_parses_style_count_article_and_tone(self) -> None:
        style, count, article, tone = parse_header(
            "掲示板風 12個コメント 強め\n\n記事本文"
        )
        self.assertEqual(style, "掲示板")
        self.assertEqual(count, 12)
        self.assertEqual(article, "記事本文")
        self.assertEqual(tone, "強め")

    def test_caps_comment_count(self) -> None:
        _, count, _, _ = parse_header("ヤフコメ 999個コメント\n\n本文")
        self.assertEqual(count, MAX_COMMENT_COUNT)

    def test_caps_article_length(self) -> None:
        article = "あ" * (MAX_ARTICLE_CHARS + 50)
        _, _, bounded, _ = parse_header(f"ポスト 5個コメント\n\n{article}")
        self.assertEqual(len(bounded), MAX_ARTICLE_CHARS)


class OutputTests(unittest.TestCase):
    def test_clean_lines_does_not_fabricate_missing_rows(self) -> None:
        self.assertEqual(clean_lines("a\n\nb\n<END>\n", 4), ["a", "b"])

    def test_chunk_keeps_every_part_within_limit(self) -> None:
        parts = chunk("a" * 35 + "\nshort", limit=10)
        self.assertTrue(parts)
        self.assertTrue(all(len(part) <= 10 for part in parts))
        self.assertEqual("".join(parts).replace("\n", ""), "a" * 35 + "short")


if __name__ == "__main__":
    unittest.main()
