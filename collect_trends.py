import os
import json
import time
from playwright.sync_api import sync_playwright
from googleapiclient.discovery import build

YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')

def get_tiktok_trends():
    """TikTok Creative Centerから急上昇ワードを5個抽出"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        # 日本のトレンドページ
        page.goto("https://ads.tiktok.com/business/creativecenter/trends/keyword/pc/ja?region=JP")
        page.wait_for_timeout(5000) # 読み込み待ち
        
        # タイトル要素を全取得
        keywords = page.locator("span.Keyword_name__XXXXX").all_inner_texts()[:5] # セレクタは適時修正
        if not keywords: # フォールバック（暫定）
            keywords = ["猫ミーム", "ダンス", "ライフハック"] # 取得失敗時のテスト用
        
        browser.close()
        return list(set(keywords))

def query_youtube(keyword):
    """YouTubeでの投稿状況を確認"""
    if not YOUTUBE_API_KEY: return 0
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    res = youtube.search().list(q=f"{keyword} #shorts", part="id", maxResults=50, type="video", videoDuration="short").execute()
    return len(res.get("items", []))

def main():
    trends = get_tiktok_trends()
    data = []
    for t in trends:
        count = query_youtube(t)
        # スコア計算: YouTubeでの動画が少ないほど高得点 (MAX 100)
        score = max(0, 100 - (count * 2))
        data.append({"keyword": t, "yt_count": count, "warp_score": score})
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
