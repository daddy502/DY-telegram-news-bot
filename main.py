import requests
import feedparser
import datetime
import os

# ===============================
# 텔레그램 채널 아이디
CHAT_ID = "@newsnissue"

# GitHub Secrets에서 불러올 봇 토큰
BOT_TOKEN = os.getenv("BOT_TOKEN")
# ===============================

# 1. 조선일보 정치면 RSS 주소
RSS_URL = "https://www.chosun.com/arc/outboundfeeds/rss/category/politics/?outputType=xml"

# 2. RSS에서 뉴스 가져오기
feed = feedparser.parse(RSS_URL)
top5 = feed.entries[:5]  # 최신 5개 기사만 가져오기

# 3. 메시지 만들기 (한국 시간으로)
now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
today = now.strftime("%Y-%m-%d %H:%M")
text = f"🗞️ {today} 조선일보 정치면 주요뉴스\n\n"
for i, entry in enumerate(top5, 1):
    title = entry.title.replace("[", "").replace("]", "")
    link = entry.link
    text += f"{i}. [{title}]({link})\n"

# 4. 텔레그램으로 전송
response = requests.get(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    params={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
)

print(response.text)