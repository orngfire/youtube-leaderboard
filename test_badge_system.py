#!/usr/bin/env python3
"""
뱃지 시스템 테스트 스크립트
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from leaderboard import BadgeSystem, BADGE_INFO

# 테스트 데이터 세트
test_cases = [
    {
        'name': '꾸준러 테스트 (중앙값 3000 이상)',
        'data': {
            'status': 'success',
            'median_score': 3500,
            'avg_engagement': 2.0,
            'top3_avg': 5000,
            'growth_ratio': 1.2,
            'video_count': 5
        },
        'expected_badges': ['🎯']
    },
    {
        'name': '인게이지먼트 킹 테스트 (평균 5% 이상)',
        'data': {
            'status': 'success',
            'median_score': 2000,
            'avg_engagement': 6.5,
            'top3_avg': 3000,
            'growth_ratio': 1.2,
            'video_count': 5
        },
        'expected_badges': ['💬']
    },
    {
        'name': '바이럴 메이커 테스트 (Top3가 중앙값의 10배)',
        'data': {
            'status': 'success',
            'median_score': 1000,
            'avg_engagement': 3.0,
            'top3_avg': 12000,  # 1000 * 10 = 10000 이상
            'growth_ratio': 1.2,
            'video_count': 5
        },
        'expected_badges': ['🔥']
    },
    {
        'name': '성장 로켓 테스트 (성장 비율 1.5 이상)',
        'data': {
            'status': 'success',
            'median_score': 2000,
            'avg_engagement': 3.0,
            'top3_avg': 3000,
            'growth_ratio': 1.8,
            'video_count': 5
        },
        'expected_badges': ['📈']
    },
    {
        'name': '올라운더 테스트 (모든 조건 충족)',
        'data': {
            'status': 'success',
            'median_score': 2500,  # 2000 이상
            'avg_engagement': 4.0,  # 3.0 이상
            'top3_avg': 4500,       # 4000 이상
            'growth_ratio': 1.2,
            'video_count': 5
        },
        'expected_badges': ['⭐']
    },
    {
        'name': '복합 뱃지 테스트 (여러 뱃지 동시 획득)',
        'data': {
            'status': 'success',
            'median_score': 3500,   # 꾸준러 (3000 이상)
            'avg_engagement': 5.5,   # 인게이지먼트 킹 (5% 이상)
            'top3_avg': 35000,       # 바이럴 메이커 (3500 * 10)
            'growth_ratio': 1.6,     # 성장 로켓 (1.5 이상)
            'video_count': 5
        },
        'expected_badges': ['🎯', '💬', '🔥', '📈', '⭐']  # 올라운더는 조건 미충족 (top3_avg < 4000)
    },
    {
        'name': '데이터 부족 테스트',
        'data': {
            'status': 'channel_not_found',
            'median_score': 5000,
            'avg_engagement': 10.0,
            'top3_avg': 50000,
            'growth_ratio': 2.0,
            'video_count': 0
        },
        'expected_badges': []
    },
    {
        'name': '경계값 테스트 (모든 값이 정확히 기준)',
        'data': {
            'status': 'success',
            'median_score': 3000,    # 정확히 3000 (꾸준러 조건 충족, 올라운더도 2000 이상이므로 충족)
            'avg_engagement': 5.0,    # 정확히 5.0 (인게이지먼트 킹 충족, 올라운더도 3.0 이상이므로 충족)
            'top3_avg': 30000,        # 정확히 10배 (바이럴 메이커 충족, 올라운더도 4000 이상이므로 충족)
            'growth_ratio': 1.5,      # 정확히 1.5 (성장 로켓 충족)
            'video_count': 5
        },
        'expected_badges': ['🎯', '💬', '🔥', '📈', '⭐']  # 모든 올라운더 조건을 충족하므로 ⭐도 포함
    }
]

def test_badge_system():
    """뱃지 시스템 테스트"""
    print("=" * 60)
    print("뱃지 시스템 테스트 시작")
    print("=" * 60)

    # 뱃지 정보 출력
    print("\n뱃지 획득 조건:")
    print("-" * 60)
    print("🎯 꾸준러: 중앙값 3,000점 이상")
    print("💬 인게이지먼트 킹: 평균 인게이지먼트율 5% 이상")
    print("🔥 바이럴 메이커: Top 3 평균이 중앙값의 10배 이상")
    print("📈 성장 로켓: 성장 비율 1.5 이상")
    print("⭐ 올라운더: 중앙값 2,000점 + 인게이지먼트율 3% + Top3 평균 4,000점 이상")
    print("=" * 60)

    passed = 0
    failed = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n테스트 {i}: {test_case['name']}")
        print("-" * 40)

        # 테스트 데이터 출력
        data = test_case['data']
        if data['status'] == 'success':
            print(f"  상태: {data['status']}")
            print(f"  중앙값: {data['median_score']:,}")
            print(f"  인게이지먼트율: {data['avg_engagement']:.2f}%")
            print(f"  Top3 평균: {data['top3_avg']:,}")
            print(f"  성장 비율: {data['growth_ratio']:.2f}")
            print(f"  영상 개수: {data['video_count']}")
        else:
            print(f"  상태: {data['status']} (채널 없음)")

        # 뱃지 계산
        badges, badge_descriptions = BadgeSystem.calculate_badges(data)

        # 결과 출력
        print(f"\n  획득한 뱃지: {' '.join(badges) if badges else '없음'}")
        print(f"  예상된 뱃지: {' '.join(test_case['expected_badges']) if test_case['expected_badges'] else '없음'}")

        # 검증
        if set(badges) == set(test_case['expected_badges']):
            print("  ✅ 성공")
            passed += 1

            # 뱃지 설명 출력
            if badges:
                print("\n  뱃지 설명:")
                for badge in badges:
                    if badge in badge_descriptions:
                        desc = badge_descriptions[badge]
                        print(f"    {badge} {desc['name']}: {desc['message']}")
        else:
            print("  ❌ 실패")
            failed += 1

            # 차이점 분석
            missing = set(test_case['expected_badges']) - set(badges)
            unexpected = set(badges) - set(test_case['expected_badges'])

            if missing:
                print(f"  누락된 뱃지: {' '.join(missing)}")
            if unexpected:
                print(f"  예상하지 못한 뱃지: {' '.join(unexpected)}")

    # 최종 결과
    print("\n" + "=" * 60)
    print("테스트 결과")
    print("=" * 60)
    print(f"✅ 성공: {passed}개")
    print(f"❌ 실패: {failed}개")
    print(f"총 테스트: {passed + failed}개")

    if failed == 0:
        print("\n🎉 모든 테스트 통과!")
    else:
        print(f"\n⚠️  {failed}개 테스트 실패")

    return failed == 0

if __name__ == '__main__':
    success = test_badge_system()
    sys.exit(0 if success else 1)