import requests
import feedparser
import datetime
import os

# ===============================
CHAT_ID = "@newsnissue"
BOT_TOKEN = os.getenv("BOT_TOKEN")
# ===============================

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

UA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DYNewsBot/1.0; +https://github.com/)",
    "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
}

def get_top_entry(url: str):
    """네이버 RSS를 UA 넣어 받아서 첫 기사(entry 0)를 반환"""
    try:
        r = requests.get(url, headers=UA_HEADERS, timeout=15)
        r.raise_for_status()
        feed = feedparser.parse(r.content)
        if feed.entries:
            return feed.entries[0]
        return None
    except Exception:
        return None

# 한국 시간
now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
date_str = now.strftime("%m월 %d일")
hour_str = now.strftime("%p %I시").replace("AM", "오전").replace("PM", "오후")

text_lines = [f"{date_str} {hour_str}", "언론사 주요 뉴스 헤드라인", ""]

for media, url in MEDIA_RSS.items():
    entry = get_top_entry(url)
    if entry:
        title = entry.title.strip()
        link = entry.link
        text_lines.append(f"[{media}]")
        text_lines.append(title)
        text_lines.append(link)
        text_lines.append("")  # 빈 줄
    else:
        # 실패 시에도 어디서 빵꾸났는지 한 줄 남김(원하면 지워도 됨)
        text_lines.append(f"[{media}]")
        text_lines.append("⚠️ 헤드라인을 가져오지 못했습니다.")
        text_lines.append("")

text = "\n".join(text_lines)

# 텔레그램 전송
resp = requests.get(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    params={"chat_id": CHAT_ID, "text": text}
)
print(resp.text)