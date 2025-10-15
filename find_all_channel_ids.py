#!/usr/bin/env python3
"""
모든 채널 ID 찾기 - urllib만 사용
"""
import json
import urllib.request
import urllib.parse
import os
import time

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

# channels.json 읽기
with open('channels.json', 'r', encoding='utf-8') as f:
    channels = json.load(f)

print("\n모든 채널 ID 검색")
print("=" * 60)

updated_channels = []

for channel in channels:
    name = channel['name']
    url = channel['channel_url']
    username = url.split('@')[-1] if '@' in url else ''

    print(f"\n{name}")
    print(f"  @{username}")

    # YouTube API 호출 (search.list)
    params = {
        'part': 'snippet',
        'q': f'@{username}',
        'type': 'channel',
        'maxResults': '5',
        'key': API_KEY
    }

    api_url = f"https://www.googleapis.com/youtube/v3/search?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(api_url) as response:
            data = json.loads(response.read())

        channel_id = None

        if data.get('items'):
            # 첫 번째 결과 사용 (대부분 정확함)
            channel_id = data['items'][0]['snippet']['channelId']
            channel_title = data['items'][0]['snippet']['title']
            print(f"  ✅ ID: {channel_id}")
            print(f"     이름: {channel_title}")
        else:
            print("  ❌ 검색 결과 없음")

        updated_channel = {
            "name": name,
            "channel_url": url,
            "channel_id": channel_id
        }
        updated_channels.append(updated_channel)

        # API 할당량 보호를 위해 잠시 대기
        time.sleep(0.5)

    except urllib.error.HTTPError as e:
        error_data = json.loads(e.read())
        error_msg = error_data.get('error', {}).get('message', 'Unknown error')
        print(f"  ❌ API 오류: {error_msg}")

        # 오류가 나도 기존 정보는 유지
        updated_channel = {
            "name": name,
            "channel_url": url,
            "channel_id": None
        }
        updated_channels.append(updated_channel)

    except Exception as e:
        print(f"  ❌ 오류: {e}")
        updated_channel = {
            "name": name,
            "channel_url": url,
            "channel_id": None
        }
        updated_channels.append(updated_channel)

print("\n" + "=" * 60)
print("결과 요약:")
print(json.dumps(updated_channels, ensure_ascii=False, indent=2))

# channels.json 업데이트
with open('channels.json', 'w', encoding='utf-8') as f:
    json.dump(updated_channels, f, ensure_ascii=False, indent=2)

print("\n✅ channels.json 업데이트 완료!")