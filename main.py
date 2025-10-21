name: Send Naver News

on:
  workflow_dispatch: # 수동 실행 버튼
  schedule:
    # 한국 시간 기준 오전 9시, 오후 1시, 오후 5시에 실행
    # UTC 기준: 00:00(9시), 04:00(13시), 08:00(17시)
    - cron: '0 0,4,8 * * *'

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
        
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          
      - name: Run script
        env:
          # 코드에서 os.environ.get()으로 읽을 수 있도록 설정
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHANNEL_ID: ${{ secrets.TELEGRAM_CHANNEL_ID }}
        run: python main.py

