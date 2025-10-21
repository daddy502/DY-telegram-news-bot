import requests
from bs4 import BeautifulSoup
import datetime
import os

CHAT_ID = "@newsnissue"
BOT_TOKEN = os.getenv("BOT_TOKEN")

MEDIA_CODES = {
    "연합뉴스": "001", "YTN": "052", "조선일보": "023", "중앙일보": "025",
    "동아일보": "020", "국민일보": "005", "한국일보": "469", "서울신문": "081",
    "한겨레": "028", "경향신문": "032", "문화일보": "021", "뉴시스": "003",
    "뉴스1": "421", "KBS": "056", "MBC": "214", "SBS": "055", "JTBC": "437",
    "TV조선": "366", "매일경제": "009", "한국경제": "015", "헬스조선": "346"
}

# 기본 URL (GitHub Actions 차단 시 캐시 프록시 버전으로 바꿔보기)
URL = "https://news.naver.com/main/ranking/popularDay.naver"
# URL = "https://r.jina.ai/http://news.naver.com/main/ranking/popularDay.naver"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DYNewsBot/2.1",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
}

res = requests.get(URL, headers=HEADERS, timeout=15)
res.encoding = "utf-8"

if res.status_code != 200:
    text = f"⚠️ 네이버 페이지 접근 실패 (HTTP {res.status_code})"
else:
    soup = BeautifulSoup(res.text, "html.parser")
    articles = soup.select("li.rankingnews_item") or soup.select("li.ranking_item")

    results = {name: [] for name in MEDIA_CODES.keys()}

    for art in articles:
        link_tag = art.select_one("a.rankingnews_thumb, a.ranking_thumb, a.ranking_title")
        if not link_tag:
            continue
        href = link_tag.get("href", "")
        title = link_tag.get_text(strip=True)
        office_tag = art.select_one("div.rankingnews_name, div.ranking_office")
        office_name = office_tag.get_text(strip=True) if office_tag else ""

        if office_name in MEDIA_CODES.keys() and len(results[office_name]) < 2:
            results[office_name].append({"title": title, "link": href})

    now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    date_str = now.strftime("%m월 %d일")
    hour_str = now.strftime("%p %I시").replace("AM", "오전").replace("PM", "오후")

    text = f"{date_str} {hour_str}\n언론사 주요 뉴스 헤드라인 (네이버 인기순)\n\n"

    for media, items in results.items():
        if items:
            for i, art in enumerate(items, 1):
                text += f"[{media}] {art['title']}\n{art['link']}\n\n"
        else:
            text += f"[{media}] ⚠️ 인기 기사 없음\n\n"

requests.get(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    params={"chat_id": CHAT_ID, "text": text}
)
print("✅ 전송 완료")