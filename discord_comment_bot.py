from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

import discord
from dotenv import load_dotenv
from openai import OpenAI

from comment_core import MAX_ARTICLE_CHARS, chunk, clean_lines, parse_header

load_dotenv()

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "").strip()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.environ.get(
    "OPENAI_MODEL",
    "gpt-4.1-2025-04-14",
).strip()

client_ai: Optional[OpenAI] = None


def ensure_runtime_config() -> None:
    missing = []
    if not DISCORD_TOKEN or DISCORD_TOKEN.startswith("PUT_"):
        missing.append("DISCORD_TOKEN")
    if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("sk-XXXX"):
        missing.append("OPENAI_API_KEY")
    if not OPENAI_MODEL:
        missing.append("OPENAI_MODEL")
    if missing:
        raise SystemExit(f"{', '.join(missing)} を .env に設定してください")


def get_openai_client() -> OpenAI:
    global client_ai
    if client_ai is None:
        client_ai = OpenAI(api_key=OPENAI_API_KEY)
    return client_ai


logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

YT_SAFE = (
    "■ YouTubeガイドラインとプライバシーポリシーを守る。"
    "差別語・個人情報・暴力扇動・性的表現は出力しない。"
)

PROMPT_BBS = (
    "あなたは動画用に匿名掲示板風コメント案を生成するAIライター。\n"
    "入力された記事本文や要約に対して、自然な口語体のオリジナル案をN件生成してください。\n"
    "■ 出力は1行につき1案。番号・引用符・空行なし。\n"
    "■ 語尾や文型を続けて反復しない。\n"
    "■ 応援・ツッコミ・疑問・期待など温度差を付ける。\n"
    "■ 1行60〜130文字を目安にする。\n"
    f"{YT_SAFE}\n"
    "■ 実在する利用者の投稿だと主張しない。\n"
    "■ 出力は案だけを改行区切りでN行。"
)

PROMPT_YAHOO = (
    "あなたはニュースコメント欄風の意見案を生成するAIライター。\n"
    "■ 1行につき1案。番号・空行なし。\n"
    "■ 標準語中心で、事実と意見を混同しない。\n"
    "■ 1行80〜150文字を目安に長短を交える。\n"
    "■ 顔文字・絵文字・wは控えめにする。\n"
    f"{YT_SAFE}\n"
    "■ 実在する利用者の投稿だと主張しない。\n"
    "■ 出力は案だけを改行区切りでN行。"
)

PROMPT_POST = (
    "あなたは短いSNSポスト風の文案を生成するAIライター。\n"
    "■ 1行につき1案。番号・空行なし。\n"
    "■ 1行60〜140文字を目安にする。\n"
    "■ ハッシュタグは使わない。\n"
    f"{YT_SAFE}\n"
    "■ 実在する利用者の投稿だと主張しない。\n"
    "■ 出力は案だけを改行区切りでN行。"
)

PROMPT_KAIGAI = (
    "あなたは海外反応まとめ風の日本語コメント案を生成するAIライター。\n"
    "■ 1行につき1案。番号・空行なし。\n"
    "■ 入力に英語原文がある場合も意味を改変・誇張しない。\n"
    "■ 固有名詞と数字を正確に保つ。\n"
    "■ 1行60〜130文字を目安にする。\n"
    f"{YT_SAFE}\n"
    "■ 実在する利用者の投稿や翻訳結果だと主張しない。\n"
    "■ 出力は案だけを改行区切りでN行。"
)

PROMPTS = {
    "掲示板": PROMPT_BBS,
    "ヤフコメ": PROMPT_YAHOO,
    "ポスト": PROMPT_POST,
    "海外反応": PROMPT_KAIGAI,
}
TEMP_MAP = {
    "掲示板": 1.1,
    "ヤフコメ": 0.7,
    "ポスト": 1.0,
    "海外反応": 0.8,
}

def generate_comments(
    style: str,
    article: str,
    tone: str,
    count: int,
) -> str:
    messages = [
        {"role": "system", "content": PROMPTS[style]},
        {"role": "user", "content": article},
    ]
    if tone:
        messages.append(
            {"role": "user", "content": f"【トーン指定】{tone}"}
        )
    messages.append(
        {
            "role": "user",
            "content": (
                f"{count}行のコメント案を出力し、"
                "最後に<END>と記して終了"
            ),
        }
    )

    response = get_openai_client().chat.completions.create(
        model=OPENAI_MODEL,
        temperature=TEMP_MAP[style],
        presence_penalty=0.2,
        max_tokens=2_400,
        stop=["<END>"],
        messages=messages,
    )
    content = response.choices[0].message.content or ""
    return "\n".join(clean_lines(content, count))


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready() -> None:
    logger.info("Logged in as %s", client.user)


@client.event
async def on_message(message: discord.Message) -> None:
    if (
        message.author.bot
        or client.user is None
        or client.user not in message.mentions
    ):
        return

    body = (
        message.content.replace(f"<@{client.user.id}>", "")
        .replace(f"<@!{client.user.id}>", "")
        .lstrip()
    )
    if not body and not message.attachments:
        await message.channel.send("入力が見つかりません。")
        return

    try:
        style, count, article, tone = parse_header(body or "")
        for attachment in message.attachments:
            name = (attachment.filename or "").lower()
            content_type = attachment.content_type or ""
            if not (
                name.endswith((".txt", ".md"))
                or content_type.lower().startswith("text/")
            ):
                continue
            blob = await attachment.read()
            for encoding in ("utf-8-sig", "cp932"):
                try:
                    attachment_text = blob.decode(encoding)
                    break
                except UnicodeDecodeError:
                    attachment_text = ""
            if not attachment_text:
                attachment_text = blob.decode("utf-8", errors="replace")
            attachment_text = attachment_text[:MAX_ARTICLE_CHARS]
            article = (
                f"{article}\n\n{attachment_text}"
                if article and article != "（本文なし）"
                else attachment_text
            )
            article = article[:MAX_ARTICLE_CHARS]
            break
    except Exception:
        logger.exception("Input parsing failed")
        await message.channel.send("入力を解析できませんでした。")
        return

    try:
        logger.info(
            "style=%s count=%s tone_len=%s article_len=%s",
            style,
            count,
            len(tone),
            len(article),
        )
        async with message.channel.typing():
            output = await asyncio.to_thread(
                generate_comments,
                style,
                article,
                tone,
                count,
            )
    except Exception:
        logger.exception("Generation failed")
        await message.channel.send(
            "生成に失敗しました。設定とログを確認してください。"
        )
        return

    if not output:
        await message.channel.send("生成結果が空でした。")
        return
    for part in chunk(output):
        await message.channel.send(f"```text\n{part}\n```")


if __name__ == "__main__":
    ensure_runtime_config()
    client.run(DISCORD_TOKEN)
