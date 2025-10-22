import os
import requests
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError
import asyncio
import html
from datetime import datetime, timedelta
import json

CONFIG_FILE = 'config.json'
SENT_NEWS_FILE = 'sent_news.json'

def load_config():
    """설정 파일(config.json)을 불러오거나 생성"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        default_config = {
            "TARGET_PRESS": [
                "연합뉴스","YTN","조선일보","중앙일보","동아일보","한겨레",
                "경향신문","한국경제","매일경제","JTBC","SBS","MBC","KBS"
            ]
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
        print(f"'{CONFIG_FILE}' created. (default TARGET_PRESS loaded)")
        return default_config

def load_sent_news():
    try:
        with open(SENT_NEWS_FILE, 'r') as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_sent_news(sent_links):
    with open(SENT_NEWS_FILE, 'w') as f:
        json.dump(list(sent_links), f)

# ✅ 봇 토큰은 Secrets에서 불러옴
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# ✅ 채널 ID를 코드에 직접 명시 (예: -1001234567890 또는 @channelusername)
CHANNEL_ID = "@newsnissue"  # ← 여기에 본인 채널 ID를 넣으세요!

CONFIG = load_config()
TARGET_PRESS = CONFIG.get("TARGET_PRESS", [])
URL = "https://news.naver.com/main/ranking/popularDay.naver"

def get_news(sent_links):
    """네이버 인기뉴스 수집"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    try:
        res = requests.get(URL, headers=headers, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')

        # ✅ 2025년 현재 네이버 구조 기준
        items = soup.select('li.ranking_item')

        found_news = []
        for item in items:
            press_tag = item.select_one('em.ranking_press_name')
            title_tag = item.select_one('a.list_title')

            if press_tag and title_tag:
                press_name = press_tag.text.strip()
                title = title_tag.text.strip()
                link = f"https://news.naver.com{title_tag['href']}"

                if press_name in TARGET_PRESS and link not in sent_links:
                    found_news.append({'press': press_name, 'title': title, 'link': link})

        return found_news

    except Exception as e:
        print(f"❌ 뉴스 수집 중 오류 발생: {e}")
        return None

async def send_message_async(text):
    """텔레그램 메시지 전송"""
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN 환경변수가 설정되지 않았습니다.")
        return
    if not CHANNEL_ID:
        print("❌ CHANNEL_ID가 설정되지 않았습니다.")
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
        print(f"텔레그램 전송 오류: {e}")
        print("봇이 채널의 관리자이며 메시지 전송 권한이 있는지 확인하세요.")
    except Exception as e:
        print(f"알 수 없는 오류: {e}")

def format_message(news_list):
    """메시지 구성"""
    if not news_list:
        return None
    now = datetime.utcnow() + timedelta(hours=9)
    date_str = now.strftime("%m월 %d일 %p %-I시").replace("AM","오전").replace("PM","오후")
    message = f"<b>{date_str} 주요 뉴스</b>\n(네이버 인기순)\n"

    press_groups = {p: [] for p in TARGET_PRESS}
    for n in news_list:
        if n['press'] in press_groups:
            press_groups[n['press']].append(n)

    for press, articles in press_groups.items():
        if articles:
            message += f"\n<b>[{press}]</b>\n"
            for a in articles[:2]:
                message += f'• <a href="{a["link"]}">{html.escape(a["title"])}</a>\n'
    return message

if __name__ == "__main__":
    sent_links_today = load_sent_news()
    new_articles = get_news(sent_links_today)

    if new_articles:
        msg = format_message(new_articles)
        if msg:
            asyncio.run(send_message_async(msg))
            print("✅ 인기 뉴스 전송 완료.")
            for a in new_articles:
                sent_links_today.add(a['link'])
            save_sent_news(sent_links_today)
        else:
            print("📰 전송할 뉴스 없음.")
    else:
        print("❌ 뉴스 수집 중 오류가 발생했습니다.")