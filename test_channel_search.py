#!/usr/bin/env python3
"""
채널 검색 테스트 스크립트
"""
import os
try:
    from googleapiclient.discovery import build
except ImportError:
    print("❌ googleapiclient 모듈이 설치되지 않았습니다!")
    print("   pip install google-api-python-client를 실행하세요.")
    exit(1)

# .env 파일 직접 읽기
API_KEY = None
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('YOUTUBE_API_KEY='):
                API_KEY = line.split('=', 1)[1].strip()
                break

if not API_KEY:
    API_KEY = os.getenv('YOUTUBE_API_KEY')

if not API_KEY or API_KEY == 'YOUR_API_KEY_HERE':
    print("❌ YouTube API 키가 설정되지 않았습니다!")
    print("   .env 파일에 YOUTUBE_API_KEY를 설정하세요.")
    exit(1)

print(f"✅ API 키 확인: {API_KEY[:10]}...")

# YouTube API 초기화
youtube = build('youtube', 'v3', developerKey=API_KEY)

# 테스트할 채널들
test_channels = [
    "https://www.youtube.com/@catmocotto",
    "https://www.youtube.com/@lee-lo-4u",
    "https://www.youtube.com/@vitaminute4u"
]

print("\n채널 검색 테스트 시작")
print("=" * 60)

for channel_url in test_channels:
    username = channel_url.split('@')[-1] if '@' in channel_url else ''
    print(f"\n테스트: @{username}")
    print(f"URL: {channel_url}")

    try:
        # Search API로 채널 검색
        search_request = youtube.search().list(
            part='snippet',
            q=f"@{username}",
            type='channel',
            maxResults=5
        )
        search_response = search_request.execute()

        if search_response.get('items'):
            print(f"검색 결과: {len(search_response['items'])}개")
            for idx, item in enumerate(search_response['items']):
                channel_title = item['snippet']['title']
                channel_id = item['snippet']['channelId']
                print(f"  [{idx+1}] {channel_title} (ID: {channel_id[:15]}...)")
        else:
            print("  ❌ 검색 결과 없음")

    except Exception as e:
        print(f"  ❌ 에러: {e}")

print("\n" + "=" * 60)
print("테스트 완료")