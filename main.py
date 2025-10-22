import os
import asyncio
import html
import json
from datetime import datetime, timedelta
import feedparser
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

# --- 파일 설정 ---
SENT_NEWS_FILE = 'sent_news.json'

def load_sent_news():
    try:
        with open(SENT_NEWS_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_sent_news(sent_links):
    with open(SENT_NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(sent_links), f, ensure_ascii=False, indent=2)

# --- 환경 변수 및 설정 ---
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = "-1001234567890"   # 👈 여기에 본인 채널 ID 입력하세요
RSS_URL = "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"

# --- RSS 뉴스 수집 ---
def get_news(sent_links):
    """구글 뉴스 RSS에서 상위 뉴스 15개 가져오기"""
    try:
        feed = feedparser.parse(RSS_URL)
        if not feed.entries:
            raise ValueError("Empty RSS feed")

        news_items = []
        for entry in feed.entries[:15]:
            title = entry.title.strip()
            link = entry.link.strip()
            if link not in sent_links:
                news_items.append({"title": title, "link": link})
        return news_items
    except Exception as e:
        print(f"❌ 뉴스 수집 중 오류: {e}")
        return None

# --- 텔레그램 메시지 전송 ---
async def send_message_async(text):
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN 환경변수가 설정되지 않았습니다.")
        return
    if not CHANNEL_ID:
        print("❌ CHANNEL_ID가 비어 있습니다.")
        return

    try:
        bot = Bot(token=BOT_TOKEN)
        max_length = 4096
        for i in range(0, len(text), max_length):
            chunk = text[i:i + max_length]
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=chunk,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
    except TelegramError as e:
        print(f"⚠️ 텔레그램 전송 오류: {e}")
    except Exception as e:
        print(f"⚠️ 알 수 없는 오류: {e}")

# --- 메시지 포맷 ---
def format_message(news_list):
    if not news_list:
        return None
    now = datetime.utcnow() + timedelta(hours=9)
    header = now.strftime("%m월 %d일 %p %-I시").replace("AM","오전").replace("PM","오후")
    msg = f"<b>{header} 주요 뉴스</b>\n(구글 뉴스 RSS 기반)\n\n"
    for i, n in enumerate(news_list, start=1):
        title = html.escape(n['title'])
        msg += f"{i}. <a href='{n['link']}'>{title}</a>\n"
    return msg

# --- 메인 ---
if __name__ == "__main__":
    sent_links = load_sent_news()
    new_articles = get_news(sent_links)

    if new_articles:
        msg = format_message(new_articles)
        if msg:
            asyncio.run(send_message_async(msg))
            print("✅ 뉴스 전송 완료.")
            for n in new_articles:
                sent_links.add(n['link'])
            save_sent_news(sent_links)
        else:
            print("📰 전송할 뉴스 없음.")
    else:
        print("❌ 뉴스 수집 중 오류가 발생했습니다.")