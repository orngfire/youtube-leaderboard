#!/usr/bin/env python3
"""
영상상세 데이터 테스트 스크립트
"""
import json

# JSON 파일 읽기
try:
    with open('leaderboard.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("=" * 60)
    print("영상상세 데이터 테스트")
    print("=" * 60)

    for idx, channel in enumerate(data['leaderboard'][:3], 1):  # 상위 3개만 테스트
        print(f"\n[{idx}] {channel['name']} (@{channel['channel_handle']})")
        print(f"  상태: {channel.get('status', 'unknown')}")

        # video_details 확인
        if 'video_details' in channel:
            video_count = len(channel['video_details'])
            print(f"  영상 수: {video_count}개")

            if video_count > 0:
                # 첫 번째 영상 정보 출력
                first_video = channel['video_details'][0]
                print(f"  첫 번째 영상:")
                print(f"    제목: {first_video.get('title', 'N/A')}")
                print(f"    조회수: {first_video.get('views', 0):,}")
                print(f"    좋아요: {first_video.get('likes', 0):,}")
                print(f"    댓글: {first_video.get('comments', 0):,}")
                print(f"    기본점수: {first_video.get('basic_score', 0):.2f}")
                print(f"    URL: {first_video.get('url', 'N/A')}")
        else:
            print(f"  ❌ video_details 필드 없음!")

    print("\n" + "=" * 60)

except FileNotFoundError:
    print("❌ leaderboard.json 파일을 찾을 수 없습니다.")
    print("   먼저 leaderboard.py를 실행하세요.")
except Exception as e:
    print(f"❌ 오류 발생: {e}")