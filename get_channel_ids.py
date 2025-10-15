#!/usr/bin/env python3
"""
채널 ID 찾기 스크립트
channels.json의 각 채널에 대한 ID를 찾아서 업데이트
"""
import json
import os
import sys

# API 키 확인
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
    print("채널 ID를 수동으로 추가해야 합니다.")
    print("\n각 채널 URL에서 다음 방법으로 채널 ID를 찾을 수 있습니다:")
    print("1. 채널 페이지에서 소스 보기")
    print("2. 'channelId' 검색")
    print("3. UC로 시작하는 ID 복사")
    sys.exit(1)

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("❌ googleapiclient 모듈이 설치되지 않았습니다!")
    print("다음 명령어로 설치하세요:")
    print("pip install google-api-python-client")
    sys.exit(1)

# YouTube API 초기화
youtube = build('youtube', 'v3', developerKey=API_KEY)

# channels.json 읽기
with open('channels.json', 'r', encoding='utf-8') as f:
    channels = json.load(f)

print("채널 ID 검색 시작...")
print("=" * 60)

updated_channels = []

for channel in channels:
    name = channel['name']
    url = channel['channel_url']
    username = url.split('@')[-1] if '@' in url else ''

    print(f"\n{name} (@{username})")
    print(f"URL: {url}")

    channel_id = None

    # 방법 1: search API로 채널 검색
    try:
        search_request = youtube.search().list(
            part='snippet',
            q=f"@{username}",
            type='channel',
            maxResults=5
        )
        search_response = search_request.execute()

        if search_response.get('items'):
            # 정확한 매치 찾기
            for item in search_response['items']:
                channel_title = item['snippet'].get('title', '')
                found_id = item['snippet']['channelId']

                # username과 비교
                if username.lower().replace('-', '') in channel_title.lower().replace(' ', '').replace('-', ''):
                    channel_id = found_id
                    print(f"✅ 채널 ID 찾음: {channel_id}")
                    break

            # 매치가 없으면 첫 번째 결과
            if not channel_id and search_response['items']:
                channel_id = search_response['items'][0]['snippet']['channelId']
                print(f"⚠️  첫 번째 결과 사용: {channel_id}")

    except HttpError as e:
        if 'quotaExceeded' in str(e):
            print("❌ API 할당량 초과! 나중에 다시 시도하세요.")
            break
        print(f"❌ 오류: {e}")

    # 결과 저장
    updated_channel = {
        "name": name,
        "channel_url": url
    }

    if channel_id:
        updated_channel["channel_id"] = channel_id

    updated_channels.append(updated_channel)

print("\n" + "=" * 60)
print("결과:")
print(json.dumps(updated_channels, ensure_ascii=False, indent=2))

# 파일 저장 여부 확인
if len(updated_channels) == len(channels):
    save = input("\nchannels.json을 업데이트할까요? (y/n): ")
    if save.lower() == 'y':
        with open('channels.json', 'w', encoding='utf-8') as f:
            json.dump(updated_channels, f, ensure_ascii=False, indent=2)
        print("✅ channels.json 업데이트 완료!")
    else:
        print("취소되었습니다.")
else:
    print("\n⚠️ 일부 채널만 처리되었습니다. 수동으로 추가해주세요.")