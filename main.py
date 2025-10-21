import requests
from bs4 import BeautifulSoup
import datetime
import os

# ===============================
CHAT_ID = "@newsnissue"
BOT_TOKEN = os.getenv("BOT_TOKEN")
# ===============================

# 21개 언론사 코드 (네이버 고유 ID)
MEDIA_CODES = {
    "연합뉴스": "001",
    "YTN": "052",
    "조선일보": "023",
    "중앙일보": "025",
    "동아일보": "020",
    "국민일보": "005",
    "한국일보": "469",
    "서울신문": "081",
    "한겨레": "028",
    "경향신문": "032",
    "문화일보": "021",
    "뉴시스": "003",
    "뉴스1": "421",
    "KBS": "056",
    "MBC": "214",
    "SBS": "055",
    "JTBC": "437",
    "TV조선": "366",
    "매일경제": "009",
    "한국경제": "015",
    "헬스조선": "346"
}

# 1️⃣ 네이버 많이 본 뉴스 페이지
URL = "https://news.naver.com/main/ranking/popularDay.naver"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DYNewsBot/2.0",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
}

# 2️⃣ 페이지 가져오기
res = requests.get(URL, headers=HEADERS)
res.raise_for_status()
soup = BeautifulSoup(res.text, "html.parser")

# 3️⃣ 기사 추출
articles = soup.select("li.ranking_item")

# 4️⃣ 결과 담기
results = {name: [] for name in MEDIA_CODES.keys()}

for art in articles:
    link_tag = art.select_one("a.ranking_thumb, a.ranking_thumb_mobile, a.ranking_title")
    if not link_tag:
        continue
    href = link_tag.get("href", "")
    title = link_tag.get_text(strip=True)
    office_tag = art.select_one("div.ranking_office")
    office_name = office_tag.get_text(strip=True) if office_tag else ""

    # 언론사 코드 확인
    if office_name in MEDIA_CODES.keys():
        # 중복 방지 및 상위 1~2개만
        if len(results[office_name]) < 2:
            results[office_name].append({"title": title, "link": href})

# 5️⃣ 한국 시간
now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
date_str = now.strftime("%m월 %d일")
hour_str = now.strftime("%p %I시").replace("AM", "오전").replace("PM", "오후")

# 6️⃣ 포맷 구성
text = f"{date_str} {hour_str}\n언론사 주요 뉴스 헤드라인 (네이버 인기순)\n\n"

for media, items in results.items():
    if items:
        for i, art in enumerate(items, 1):
            text += f"[{media}] {art['title']}\n{art['link']}\n\n"
    else:
        text += f"[{media}] ⚠️ 인기 기사 없음\n\n"

# 7️⃣ 텔레그램 전송
requests.get(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    params={"chat_id": CHAT_ID, "text": text}
)

print("✅ Successfully sent Naver ranking headlines.")