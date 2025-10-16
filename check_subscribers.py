#!/usr/bin/env python3
"""
모든 채널의 현재 구독자 수 확인
"""

import os
import json
import urllib.request
import urllib.parse

# API 키
API_KEY = os.getenv('YOUTUBE_API_KEY')

def get_subscriber_count(channel_id, channel_name):
    """채널의 현재 구독자 수 가져오기"""
    base_url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        'part': 'statistics',
        'id': channel_id,
        'key': API_KEY
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())

        if data.get('items'):
            stats = data['items'][0]['statistics']

            # hiddenSubscriberCount 확인
            if stats.get('hiddenSubscriberCount', False):
                return f"{channel_name}: 구독자 수 비공개"
            else:
                subscriber_count = int(stats.get('subscriberCount', 0))
                return f"{channel_name}: {subscriber_count:,}명"
        else:
            return f"{channel_name}: 채널을 찾을 수 없음"
    except Exception as e:
        return f"{channel_name}: 오류 - {str(e)}"

def main():
    if not API_KEY:
        print("❌ YOUTUBE_API_KEY 환경변수를 설정해주세요!")
        return

    # channels.json 읽기
    with open('channels.json', 'r', encoding='utf-8') as f:
        channels = json.load(f)

    print("="*60)
    print("YouTube 채널 구독자 수 확인")
    print("="*60)
    print()

    # 주요 채널 먼저 확인
    important_channels = ['조준철', '조한준', '임동한', '클로이', '전우형', '서혜리']

    print("주요 채널:")
    print("-"*40)
    for channel in channels:
        if channel['name'] in important_channels:
            result = get_subscriber_count(channel['channel_id'], channel['name'])
            print(result)

    print("\n기타 채널:")
    print("-"*40)
    for channel in channels:
        if channel['name'] not in important_channels:
            result = get_subscriber_count(channel['channel_id'], channel['name'])
            print(result)

if __name__ == "__main__":
    main()