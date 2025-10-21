import os
import requests
from bs4 import BeautifulSoup
import telegram
import asyncio
import html # HTML 태그 이스케이프를 위해 추가

# 1. 회원님이 요청한 21개 언론사 목록
TARGET_PRESS = [
    "연합뉴스", "YTN", "조선일보", "중앙일보", "동아일보", "국민일보", 
    "한국일보", "서울신문", "한겨레", "경향신문", "문화일보", "뉴시스", 
    "뉴스1", "KBS", "MBC", "SBS", "JTBC", "TV조선", "매일경제", 
    "한국경제", "헬스조선"
]

# 2. 깃허브 'Secrets'에서 봇 정보 가져오기
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = "@newsnissue"

# 3. 네이버 뉴스 '가장 많이 본' 페이지 주소
URL = "https://news.naver.com/main/ranking/popularDay.naver"

def get_news():
    """네이버에서 '가장 많이 본 뉴스'를 가져와서 필터링합니다."""
    headers = {'User-Agent': 'Mozilla/5.0'} # 봇으로 접근하는 것을 숨기기 위함
    
    try:
        response = requests.get(URL, headers=headers)
        response.raise_for_status() # 오류가 나면 중단
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # '가장 많이 본 뉴스' 목록을 찾습니다.
        items = soup.select('ul.rankingnews_list > li')
        
        found_news = []
        
        for item in items:
            press_tag = item.select_one('span.rankingnews_box_press') # 언론사
            title_tag = item.select_one('div.list_content > a')      # 기사 제목과 링크
            
            if press_tag and title_tag:
                press_name = press_tag.text.strip()
                title = title_tag.text.strip()
                link = title_tag['href']
                
                # 4. 가져온 뉴스의 언론사가 우리가 찾는 언론사인지 확인
                if press_name in TARGET_PRESS:
                    found_news.append((press_name, title, link))
                    
        return found_news

    except Exception as e:
        print(f"Error scraping news: {e}")
        return None

async def send_message(text):
    """텔레그램으로 메시지를 비동기로 전송합니다."""
    if not BOT_TOKEN or not CHANNEL_ID:
        print("텔레그램 봇 토큰 또는 채널 ID가 설정되지 않았습니다.")
        return
        
    try:
        bot = telegram.Bot(token=BOT_TOKEN)
        # 텔레그램 메시지 길이는 4096자로 제한됩니다.
        max_length = 4096
        if len(text) <= max_length:
            await bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode='HTML', disable_web_page_preview=True)
        else:
            # 메시지가 너무 길면 나눠서 보냅니다.
            for i in range(0, len(text), max_length):
                await bot.send_message(chat_id=CHANNEL_ID, text=text[i:i+max_length], parse_mode='HTML', disable_web_page_preview=True)
                
    except Exception as e:
        print(f"Error sending message: {e}")

def format_message(news_list):
    """텔레그램 메시지 형식을 만듭니다."""
    if not news_list:
        return "오늘의 주요 뉴스 중 요청하신 언론사의 기사를 찾지 못했습니다."
    
    message = "📰 <b>오늘의 주요 뉴스 (조회수 순)</b> 📰\n\n"
    
    # 언론사별로 뉴스를 그룹화합니다.
    press_groups = {}
    for press, title, link in news_list:
        if press not in press_groups:
            press_groups[press] = []
        
        # 제목에 포함된 HTML 특수 문자(<, >)를 변환합니다.
        title_safe = html.escape(title)
        press_groups[press].append((title_safe, link))

    # 5. 보기 좋게 메시지 포맷 만들기 (언론사 순서는 회원님이 요청한 순서대로)
    for press in TARGET_PRESS:
        if press in press_groups:
            message += f"\n<b>[{press}]</b>\n"
            # 해당 언론사에서 순위에 든 기사를 최대 3개까지만 보여줍니다.
            for i, (title, link) in enumerate(press_groups[press][:3]): 
                message += f'- <a href="{link}">{title}</a>\n'
    
    return message

if __name__ == "__main__":
    news = get_news()
    if news:
        message = format_message(news)
        asyncio.run(send_message(message))
    else:
        asyncio.run(send_message("뉴스 수집 중 오류가 발생했습니다."))
