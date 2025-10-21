import os
import requests
from bs4 import BeautifulSoup
import telegram
import asyncio
import html
from datetime import datetime, timedelta

# ===============================
# GitHub Secrets에서 봇 토큰만 가져오고, 채널 아이디는 직접 입력
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = "@newsnissue"  # 채널 아이디를 직접 입력 ✅
# ===============================

# 1️⃣ 모니터링 대상 언론사 목록
TARGET_PRESS = [
    "연합뉴스", "YTN", "조선일보", "중앙일보", "동아일보", "국민일보",
    "한국일보", "서울신문", "한겨레", "경향신문", "문화일보", "뉴시스",
    "뉴스1", "KBS", "MBC", "SBS", "JTBC", "TV조선", "매일경제",
    "한국경제", "헬스조선"
]

# 2️⃣ 네이버 '가장 많이 본 뉴스' 페이지 URL
URL = "https://news.naver.com/main/ranking/popularDay.naver"


def get_news():
    """네이버에서 '가장 많이 본 뉴스'를 가져와 필터링합니다."""
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        response = requests.get(URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # ✅ 네이버 최신 구조 대응
        items = soup.select('ul.rankingnews_list > li')

        found_news = []
        for item in items:
            press_tag = item.select_one('span.rankingnews_box_press')
            title_tag = item.select_one('div.list_content > a')

            if press_tag and title_tag:
                press_name = press_tag.text.strip()
                title = title_tag.text.strip()
                link = title_tag['href']

                # 언론사 필터링
                if press_name in TARGET_PRESS:
                    found_news.append({'press': press_name, 'title': title, 'link': link})

        return found_news

    except Exception as e:
        print(f"Error scraping news: {e}")
        return None


async def send_message_async(text):
    """텔레그램으로 메시지를 비동기로 전송합니다."""
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
        return

    try:
        bot = telegram.Bot(token=BOT_TOKEN)
        max_length = 4096
        for i in range(0, len(text), max_length):
            chunk = text[i:i + max_length]
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=chunk,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
    except Exception as e:
        print(f"Error sending message: {e}")


def format_message(news_list):
    """메시지 형식을 보기 좋게 구성"""
    if not news_list:
        return "오늘의 인기 뉴스 중 요청하신 언론사의 기사를 찾지 못했습니다."

    # 한국 시간 기준 헤더
    now = datetime.utcnow() + timedelta(hours=9)
    date_str = now.strftime("%m월 %d일")
    hour_str = now.strftime("%p %-I시").replace("AM", "오전").replace("PM", "오후")

    message = f"<b>{date_str} {hour_str}</b>\n언론사 주요 뉴스 헤드라인 (네이버 인기순)\n"

    # 언론사별 그룹
    press_groups = {name: [] for name in TARGET_PRESS}
    for news_item in news_list:
        press = news_item['press']
        if press in press_groups:
            safe_title = html.escape(news_item['title'])
            press_groups[press].append({'title': safe_title, 'link': news_item['link']})

    # 정해진 순서대로 조합
    for press_name in TARGET_PRESS:
        articles = press_groups.get(press_name, [])
        if articles:
            message += f"\n<b>[{press_name}]</b>\n"
            for article in articles[:2]:  # 언론사당 최대 2개 기사
                message += f'• <a href="{article["link"]}">{article["title"]}</a>\n'

    return message


if __name__ == "__main__":
    news = get_news()
    if news:
        message = format_message(news)
        asyncio.run(send_message_async(message))
        print("✅ Successfully sent Naver ranking headlines.")
    else:
        asyncio.run(send_message_async("뉴스 수집 중 오류가 발생했습니다."))
        print("❌ Failed to get news.")