# discord-comment-bot

DiscordでBotをメンションすると、入力した記事・要約を基に日本語の
コメント案を生成する最小実装です。掲示板風、ヤフコメ風、短いポスト風、
海外反応風を選べます。

## Status

公開レビュー用のDraftです。実運用のtoken、VM設定、ログは含みません。
公開ライセンスは未決定で、`LICENSE`が追加されるまでは再利用許諾を
付与していません。

## Setup

Python 3.10以上を推奨します。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.template .env
```

`.env`へ次を設定します。

```dotenv
DISCORD_TOKEN=your-discord-bot-token
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4.1-2025-04-14
```

`OPENAI_MODEL`は利用可能なモデル名へ変更できます。

Discord Developer PortalではBotの`MESSAGE CONTENT INTENT`を有効にし、
必要なチャンネルだけへBotを招待してください。

## Run

```powershell
python discord_comment_bot.py
```

DiscordでBotをメンションし、空行の前に形式と件数を書きます。

```text
@BotName 掲示板風 20個コメント

ここに記事本文または要約
```

1回の要求は最大50件、本文は最大8,000文字に制限されます。

## Validation

```powershell
python -m compileall -q comment_core.py discord_comment_bot.py tests
python -m unittest discover -s tests -v
```

## Safety and use boundary

- `.env`、token、API key、DiscordログをGitへ入れないでください。
- 出力はAI生成案です。実在する読者・利用者の投稿として偽装しないでください。
- 大量投稿、自動世論形成、嫌がらせ、個人情報を含む入力には使わないでください。
- 入力記事、引用、画像、ブランド名の利用権を確認してください。
- 公開・投稿前に人が事実、名誉、差別、プライバシー、各サービス規約を確認してください。

## GitHub flow

`codex/*`からDraft PRを作り、テストとsecret scanを通します。merge、
実Botへのtoken設定、VM deployは別の操作です。
