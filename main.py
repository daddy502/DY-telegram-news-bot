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

# --- 설정 파일 경로 ---
CONFIG_FILE = 'config.json'
SENT_NEWS_FILE = 'sent_news.json'

def load_config():
    """설정 파일(config.json)을 불러오거나, 없으면 새로 생성합니다."""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # 설정 파일이 없으면 CHANNEL_ID와 언론사 목록을 포함한 기본 구조 생성
        default_config = {
            "CHANNEL_ID": "@newsnissue",  # <-- 이 부분을 수정해야 합니다.
            "TARGET_PRESS": [
                "연합뉴스", "YTN", "조선일보", "중앙일보", "동아일보", "국민일보",
                "한국일보", "서울신문", "한겨레", "경향신문", "문화일보", "뉴시스",
                "뉴스1", "KBS", "MBC", "SBS", "JTBC", "TV조선", "매일경제",
                "한국경제", "헬스조선"
            ]
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
        print(f"'{CONFIG_FILE}'이 생성되었습니다. 파일 안의 CHANNEL_ID를 본인 채널 ID로 수정해주세요.")
        return default_config

def load_sent_news():
    """이전에 보냈던 뉴스 링크를 불러옵니다."""
    try:
        with open(SENT_NEWS_FILE, 'r') as f:
            # 파일이 비어있는 경우 예외 처리
            content = f.read()
            if not content:
                return set()
            return set(json.loads(content))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_sent_news(sent_links):
    """전송 완료한 뉴스 링크를 저장합니다."""
    with open(SENT_NEWS_FILE, 'w') as f:
        json.dump(list(sent_links), f)

# --- 전역 설정 ---
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CONFIG = load_config()
CHANNEL_ID = "@newsnissue"
TARGET_PRESS = CONFIG.get("TARGET_PRESS", [])
URL = "https://news.naver.com/main/ranking/popularDay.naver"

def get_news(sent_links):
    """
    네이버 인기뉴스 페이지에서 타겟 언론사 기사만 필터링합니다.
    이미 보낸 뉴스는 제외합니다.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        res = requests.get(URL, headers=headers, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')

        # ✅ 현재 네이버 구조에 맞는 정확한 선택자로 수정
        items = soup.select('ul.rankingnews_list > li.rankingnews_item')

        found_news = []
        for item in items:
            # ✅ 언론사와 제목 태그 선택자 수정
            press_tag = item.select_one('a.rankingnews_box_press')
            title_tag = item.select_one('div.list_content > a.list_title')

            if press_tag and title_tag:
                press_name = press_tag.text.strip()
                title = title_tag.text.strip()
                link = title_tag['href'] # ✅ 링크를 그대로 사용하도록 수정

                # 이미 보낸 뉴스는 건너뛰기
                if press_name in TARGET_PRESS and link not in sent_links:
                    found_news.append({'press': press_name, 'title': title, 'link': link})
        
        return found_news

    except requests.exceptions.RequestException as e:
        print(f"네이버 뉴스에 접속 중 오류 발생: {e}")
        return None
    except Exception as e:
        print(f"뉴스 스크래핑 중 알 수 없는 오류 발생: {e}")
        return None


async def send_message_async(text):
    """텔레그램으로 메시지를 비동기로 전송"""
    if not BOT_TOKEN:
        print("❌ 텔레그램 봇 토큰(TELEGRAM_BOT_TOKEN) 환경변수가 설정되지 않았습니다.")
        return
    if not CHANNEL_ID or CHANNEL_ID == "@YourChannelID":
        print(f"❌ '{CONFIG_FILE}' 파일에 채널 ID를 정확히 입력해주세요.")
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
        print(f"텔레그램 메시지 전송 오류: {e}")
        print("봇이 채널의 관리자로 지정되어 있고, 메시지 보내기 권한이 있는지 확인하세요.")
    except Exception as e:
        print(f"메시지 전송 중 알 수 없는 오류 발생: {e}")


def format_message(news_list):
    """텔레그램 메시지 형식 구성"""
    if not news_list:
        return None

    now = datetime.utcnow() + timedelta(hours=9)
    date_str = now.strftime("%m월 %d일")
    hour_str = now.strftime("%p %-I시").replace("AM", "오전").replace("PM", "오후")

    message = f"<b>{date_str} {hour_str}</b>\n언론사별 주요 뉴스 (네이버 인기순)\n"

    press_groups = {name: [] for name in TARGET_PRESS}
    for n in news_list:
        press = n['press']
        if press in press_groups:
            safe_title = html.escape(n['title'])
            press_groups[press].append({'title': safe_title, 'link': n['link']})

    has_content = False
    for press_name in TARGET_PRESS:
        articles = press_groups.get(press_name, [])
        if articles:
            has_content = True
            message += f"\n<b>[{press_name}]</b>\n"
            for article in articles[:2]:
                message += f'• <a href="{article["link"]}">{article["title"]}</a>\n'
    
    return message if has_content else None


if __name__ == "__main__":
    sent_links = load_sent_news()
    
    new_articles = get_news(sent_links)

    if new_articles:
        msg = format_message(new_articles)
        if msg:
            asyncio.run(send_message_async(msg))
            print("✅ 새로운 인기 뉴스를 성공적으로 전송했습니다.")
            
            for article in new_articles:
                sent_links.add(article['link'])
            save_sent_news(sent_links)
        else:
            print("📰 전송할 새로운 뉴스가 없습니다 (모두 이미 전송된 뉴스).")
    else:
        print("❌ 뉴스 수집에 실패했거나, 수집된 뉴스가 없습니다.")


