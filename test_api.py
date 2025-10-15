#!/usr/bin/env python3
"""
API 키 테스트 스크립트 - urllib만 사용
"""
import json
import urllib.request
import urllib.parse
import os

# .env 파일에서 API 키 읽기
API_KEY = None
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('YOUTUBE_API_KEY='):
                API_KEY = line.split('=', 1)[1].strip()
                break

if not API_KEY or API_KEY == 'YOUR_API_KEY_HERE':
    print("❌ YouTube API 키가 설정되지 않았습니다!")
    exit(1)

print(f"✅ API 키 확인: {API_KEY[:10]}...")

# 테스트할 채널
test_channels = [
    "@catmocotto",
    "@vitaminute4u"
]

print("\n채널 검색 테스트")
print("=" * 60)

for handle in test_channels:
    print(f"\n검색: {handle}")

    # YouTube API 호출 (search.list)
    params = {
        'part': 'snippet',
        'q': handle,
        'type': 'channel',
        'maxResults': '3',
        'key': API_KEY
    }

    url = f"https://www.googleapis.com/youtube/v3/search?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())

        if data.get('items'):
            print(f"✅ 검색 성공! {len(data['items'])}개 결과")
            for idx, item in enumerate(data['items'], 1):
                channel_id = item['snippet']['channelId']
                channel_title = item['snippet']['title']
                print(f"  [{idx}] {channel_title}")
                print(f"      ID: {channel_id}")
        else:
            print("❌ 검색 결과 없음")

    except urllib.error.HTTPError as e:
        error_data = json.loads(e.read())
        error_msg = error_data.get('error', {}).get('message', 'Unknown error')
        print(f"❌ API 오류: {error_msg}")
    except Exception as e:
        print(f"❌ 오류: {e}")

print("\n" + "=" * 60)
print("테스트 완료!")