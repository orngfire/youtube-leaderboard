#!/usr/bin/env python3
"""
클로이 채널 ID를 API로 직접 확인
"""

import os
import json
import urllib.request
import urllib.parse

# API 키
API_KEY = os.getenv('YOUTUBE_API_KEY')

def check_channel_by_id(channel_id):
    """채널 ID로 채널 정보 확인"""
    print(f"\n{'='*70}")
    print(f"채널 ID로 조회: {channel_id}")
    print('='*70)

    # API URL
    base_url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        'part': 'snippet,statistics,contentDetails',
        'id': channel_id,
        'key': API_KEY
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())

        if data.get('items'):
            channel = data['items'][0]
            snippet = channel['snippet']
            stats = channel['statistics']
            content = channel['contentDetails']

            print(f"\n✅ 채널 발견!")
            print(f"채널 이름: {snippet['title']}")
            print(f"채널 설명: {snippet.get('description', '')[:100]}...")
            print(f"Custom URL: {snippet.get('customUrl', 'None')}")
            print(f"구독자 수: {stats.get('subscriberCount', 'Hidden')}")
            print(f"전체 영상 수: {stats.get('videoCount', 0)}")
            print(f"Uploads Playlist: {content['relatedPlaylists']['uploads']}")

            return content['relatedPlaylists']['uploads']
        else:
            print("❌ 채널을 찾을 수 없습니다!")
            return None

    except Exception as e:
        print(f"❌ API 오류: {e}")
        return None

def check_recent_videos(uploads_playlist_id):
    """업로드 플레이리스트에서 최근 영상 확인"""
    print(f"\n{'='*70}")
    print(f"최근 영상 확인: {uploads_playlist_id}")
    print('='*70)

    # API URL
    base_url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        'part': 'contentDetails',
        'playlistId': uploads_playlist_id,
        'maxResults': 5,
        'key': API_KEY
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())

        video_ids = []
        for item in data.get('items', []):
            video_ids.append(item['contentDetails']['videoId'])

        if video_ids:
            # 영상 상세 정보 가져오기
            videos_url = "https://www.googleapis.com/youtube/v3/videos"
            videos_params = {
                'part': 'snippet,statistics',
                'id': ','.join(video_ids),
                'key': API_KEY
            }

            url = f"{videos_url}?{urllib.parse.urlencode(videos_params)}"

            with urllib.request.urlopen(url) as response:
                videos_data = json.loads(response.read())

            print("\n최근 영상 목록:")
            for i, video in enumerate(videos_data.get('items', []), 1):
                print(f"\n영상 {i}:")
                print(f"  제목: {video['snippet']['title']}")
                print(f"  채널명: {video['snippet']['channelTitle']}")
                print(f"  채널 ID: {video['snippet']['channelId']}")
                print(f"  게시일: {video['snippet']['publishedAt']}")
                print(f"  조회수: {video['statistics'].get('viewCount', 0)}")
                print(f"  URL: https://www.youtube.com/watch?v={video['id']}")

    except Exception as e:
        print(f"❌ API 오류: {e}")

def search_channel_by_handle(handle):
    """채널 핸들로 검색"""
    print(f"\n{'='*70}")
    print(f"채널 핸들로 검색: @{handle}")
    print('='*70)

    # API URL
    base_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'part': 'snippet',
        'q': f"@{handle}",
        'type': 'channel',
        'maxResults': 3,
        'key': API_KEY
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())

        if data.get('items'):
            print("\n검색 결과:")
            for i, item in enumerate(data['items'], 1):
                snippet = item['snippet']
                print(f"\n결과 {i}:")
                print(f"  채널명: {snippet['title']}")
                print(f"  채널 ID: {snippet['channelId']}")
                print(f"  설명: {snippet.get('description', '')[:100]}...")
        else:
            print("❌ 검색 결과가 없습니다!")

    except Exception as e:
        print(f"❌ API 오류: {e}")

def main():
    if not API_KEY:
        print("❌ YOUTUBE_API_KEY 환경변수를 설정해주세요!")
        return

    print("="*70)
    print("클로이 채널 API 검증")
    print("="*70)

    # 1. 저장된 채널 ID로 확인
    stored_id = "UCYY4jQLw225dbINMhDipRzg"
    print(f"\n1. 저장된 채널 ID 확인: {stored_id}")
    uploads_id = check_channel_by_id(stored_id)

    # 2. 최근 영상 확인
    if uploads_id:
        check_recent_videos(uploads_id)

    # 3. 핸들로 검색해보기
    search_channel_by_handle("neo_chloe")

    # 4. 다른 검색어로도 시도
    print("\n" + "="*70)
    print("추가 검색: 'neo chloe channel'")
    base_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'part': 'snippet',
        'q': 'neo chloe channel',
        'type': 'channel',
        'maxResults': 3,
        'key': API_KEY
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())

        if data.get('items'):
            print("\n검색 결과:")
            for i, item in enumerate(data['items'], 1):
                snippet = item['snippet']
                print(f"\n결과 {i}:")
                print(f"  채널명: {snippet['title']}")
                print(f"  채널 ID: {snippet['channelId']}")
    except Exception as e:
        print(f"❌ API 오류: {e}")

if __name__ == "__main__":
    main()