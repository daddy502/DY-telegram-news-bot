import requests
import feedparser
import datetime
import os

# ===============================
# 텔레그램 채널 아이디
CHAT_ID = "@newsnissue"

# GitHub Secrets에 저장된 봇 토큰
BOT_TOKEN = os.getenv("BOT_TOKEN")
# ===============================

# 네이버 뉴스 '많이 본 뉴스' RSS 주소 모음
MEDIA_RSS = {
    "연합뉴스": "https://rss.naver.com/newspaper/001.xml",
    "YTN": "https://rss.naver.com/newspaper/052.xml",
    "조선일보": "https://rss.naver.com/newspaper/023.xml",
    "중앙일보": "https://rss.naver.com/newspaper/025.xml",
    "동아일보": "https://rss.naver.com/newspaper/020.xml",
    "국민일보": "https://rss.naver.com/newspaper/005.xml",
    "한국일보": "https://rss.naver.com/newspaper/469.xml",
    "서울신문": "https://rss.naver.com/newspaper/081.xml",
    "한겨레": "https://rss.naver.com/newspaper/028.xml",
    "경향신문": "https://rss.naver.com/newspaper/032.xml",
    "문화일보": "https://rss.naver.com/newspaper/021.xml",
    "뉴시스": "https://rss.naver.com/newspaper/003.xml",
    "뉴스1": "https://rss.naver.com/newspaper/421.xml",
    "KBS": "https://rss.naver.com/newspaper/056.xml",
    "MBC": "https://rss.naver.com/newspaper/214.xml",
    "SBS": "https://rss.naver.com/newspaper/055.xml",
    "JTBC": "https://rss.naver.com/newspaper/437.xml",
    "TV조선": "https://rss.naver.com/newspaper/366.xml",
    "매일경제": "https://rss.naver.com/newspaper/009.xml",
    "한국경제": "https://rss.naver.com/newspaper/015.xml",
    "헬스조선": "https://rss.naver.com/newspaper/346.xml"
}

# 한국 시간 기준
now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
date_str = now.strftime("%m월 %d일")
hour_str = now.strftime("%p %I시").replace("AM", "오전").replace("PM", "오후")

# 헤드라인 문구
text = f"{date_str} {hour_str}\n언론사 주요 뉴스 헤드라인\n\n"

# 각 언론사별 1위 기사 추출
for media, url in MEDIA_RSS.items():
    try:
        feed = feedparser.parse(url)
        if not feed.entries:
            continue
        entry = feed.entries[0]
        title = entry.title.strip()
        link = entry.link
        text += f"[{media}]\n{title}\n{link}\n\n"
    except Exception as e:
        text += f"[{media}]\n⚠️ 뉴스 불러오기 오류 ({e})\n\n"

# 텔레그램 전송
response = requests.get(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    params={"chat_id": CHAT_ID, "text": text}
)

print(response.text)