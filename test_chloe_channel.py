#!/usr/bin/env python3
"""
클로이 채널 ID 직접 테스트
"""

import os
import json
from googleapiclient.discovery import build
from datetime import datetime

# API 키 설정
API_KEY = os.getenv('YOUTUBE_API_KEY')

def test_channel_id(channel_id):
    """채널 ID를 직접 테스트"""
    print(f"\n{'='*70}")
    print(f"Testing Channel ID: {channel_id}")
    print('='*70)

    youtube = build('youtube', 'v3', developerKey=API_KEY)

    # 1. 채널 정보 가져오기
    print("\n1. 채널 정보 조회:")
    try:
        request = youtube.channels().list(
            part='snippet,statistics,contentDetails',
            id=channel_id
        )
        response = request.execute()

        if response.get('items'):
            channel = response['items'][0]
            snippet = channel['snippet']
            stats = channel['statistics']

            print(f"   채널 이름: {snippet['title']}")
            print(f"   채널 설명: {snippet.get('description', '')[:100]}...")
            print(f"   구독자 수: {stats.get('subscriberCount', 'Hidden')}")
            print(f"   전체 영상 수: {stats.get('videoCount', 0)}")

            # Uploads playlist ID
            uploads_id = channel['contentDetails']['relatedPlaylists']['uploads']
            print(f"   Uploads Playlist ID: {uploads_id}")

            # 2. 최근 영상 확인
            print("\n2. 최근 영상 목록 (최대 5개):")
            playlist_request = youtube.playlistItems().list(
                part='contentDetails',
                playlistId=uploads_id,
                maxResults=5
            )
            playlist_response = playlist_request.execute()

            video_ids = []
            for item in playlist_response.get('items', []):
                video_ids.append(item['contentDetails']['videoId'])

            if video_ids:
                videos_request = youtube.videos().list(
                    part='snippet,statistics',
                    id=','.join(video_ids)
                )
                videos_response = videos_request.execute()

                for i, video in enumerate(videos_response.get('items', []), 1):
                    print(f"\n   영상 {i}:")
                    print(f"      제목: {video['snippet']['title']}")
                    print(f"      채널명: {video['snippet']['channelTitle']}")
                    print(f"      채널 ID: {video['snippet']['channelId']}")
                    print(f"      게시일: {video['snippet']['publishedAt']}")
                    print(f"      조회수: {video['statistics'].get('viewCount', 0)}")
                    print(f"      URL: https://www.youtube.com/watch?v={video['id']}")
        else:
            print("   ❌ 채널을 찾을 수 없습니다!")

    except Exception as e:
        print(f"   ❌ 오류 발생: {e}")

def compare_with_stored_channel():
    """저장된 채널 정보와 비교"""
    print(f"\n{'='*70}")
    print("저장된 채널 정보 확인")
    print('='*70)

    # channels.json 읽기
    with open('channels.json', 'r', encoding='utf-8') as f:
        channels = json.load(f)

    chloe_channel = None
    for ch in channels:
        if ch['name'] == '클로이':
            chloe_channel = ch
            break

    if chloe_channel:
        print(f"\nchannels.json의 클로이 정보:")
        print(f"   이름: {chloe_channel['name']}")
        print(f"   URL: {chloe_channel['channel_url']}")
        print(f"   ID: {chloe_channel.get('channel_id', 'None')}")

        return chloe_channel.get('channel_id')
    else:
        print("   ❌ 클로이 채널이 channels.json에 없습니다!")
        return None

def main():
    if not API_KEY:
        print("❌ YOUTUBE_API_KEY 환경변수를 설정해주세요!")
        return

    print("클로이 채널 ID 검증 테스트")
    print("="*70)

    # 1. 저장된 채널 정보 확인
    stored_id = compare_with_stored_channel()

    # 2. 저장된 ID로 테스트
    if stored_id:
        test_channel_id(stored_id)

    # 3. 사용자가 제공한 올바른 ID로도 테스트
    correct_id = "UCYY4jQLw225dbINMhDipRzg"
    if stored_id != correct_id:
        print(f"\n{'='*70}")
        print("사용자가 제공한 올바른 ID로 테스트:")
        test_channel_id(correct_id)

if __name__ == "__main__":
    main()