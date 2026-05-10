import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from github import Github

load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
ALLOWED_USER_IDS = {
    int(x.strip()) for x in os.getenv("ALLOWED_USER_IDS", "").split(",") if x.strip()
}

gh = Github(GITHUB_TOKEN)
repo = gh.get_repo(GITHUB_REPO)


def is_allowed(user_id: int) -> bool:
    return user_id in ALLOWED_USER_IDS if ALLOWED_USER_IDS else True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    await update.message.reply_text(
        "봇 준비 완료!\n"
        "명령어:\n"
        "/help\n"
        "/new_task <ticket> <priority> <title>\n"
        "/daily"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    await update.message.reply_text(
        "/new_task AUTH-142 P1 로그인401수정\n"
        "/daily"
    )


async def new_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return

    if len(context.args) < 3:
        await update.message.reply_text("사용법: /new_task <ticket> <priority> <title>")
        return

    ticket = context.args[0]
    priority = context.args[1]
    title = " ".join(context.args[2:])

    body = f"""## Request Info
- Requester: @{update.effective_user.username or update.effective_user.id}
- Requested date: {datetime.utcnow().date()}
- Priority: {priority}
- Ticket: {ticket}

## Problem
- (여기에 문제 설명)

## Goal
- (여기에 목표)

## Scope
- In scope:
- Out of scope:
"""

    issue = repo.create_issue(
        title=f"[{ticket}] {title}",
        body=body,
        labels=["task", priority.lower()]
    )
    await update.message.reply_text(f"Issue created: {issue.html_url}")


async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return

    open_issues = repo.get_issues(state="open")
    lines = ["오늘 오픈 이슈:"]
    count = 0
    for i in open_issues:
        if i.pull_request is None:
            lines.append(f"- #{i.number} {i.title}")
            count += 1
        if count >= 10:
            break
    await update.message.reply_text("\n".join(lines) if count else "오픈 이슈 없음")


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("new_task", new_task))
    app.add_handler(CommandHandler("daily", daily))
    app.run_polling()


if __name__ == "__main__":
    main()