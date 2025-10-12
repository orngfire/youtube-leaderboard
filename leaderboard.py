#!/usr/bin/env python3
"""
YouTube Creator Leaderboard System
평가 기간: 2025-10-02 ~ 2025-12-14
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional
import statistics

import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('leaderboard.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# 설정
API_KEY = os.getenv('YOUTUBE_API_KEY')
START_DATE = '2025-10-02T00:00:00Z'
END_DATE = '2025-12-14T23:59:59Z'
CHANNELS_FILE = 'channels.json'
MIN_VIDEOS = 3

# 가중치
WEIGHT_MEDIAN = 0.6
WEIGHT_ENGAGEMENT = 0.3
WEIGHT_VIRAL = 0.05
WEIGHT_GROWTH = 0.05

# 뱃지 기준
BADGE_STABLE_THRESHOLD = 5000
BADGE_ENGAGEMENT_THRESHOLD = 5.0
BADGE_VIRAL_MULTIPLIER = 10
BADGE_GROWTH_THRESHOLD = 1.5


class YouTubeAPI:
    """YouTube Data API v3 래퍼"""

    def __init__(self, api_key: str):
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.api_calls = 0

    def get_channel_id(self, channel_url: str) -> Optional[str]:
        """채널 URL에서 채널 ID 추출"""
        try:
            # @username 형식 처리
            if '@' in channel_url:
                username = channel_url.split('@')[-1].strip()

                # 방법 1: forHandle 파라미터 사용 (최신 API)
                try:
                    self.api_calls += 1
                    request = self.youtube.channels().list(
                        part='id',
                        forHandle=username
                    )
                    response = request.execute()

                    if response.get('items'):
                        logger.info(f"채널 ID 찾음 (forHandle): {response['items'][0]['id']}")
                        return response['items'][0]['id']
                except (HttpError, TypeError) as e:
                    logger.warning(f"forHandle 실패, search API 시도 중: {e}")

                # 방법 2: forUsername 파라미터 사용 (레거시 API)
                try:
                    self.api_calls += 1
                    request = self.youtube.channels().list(
                        part='id',
                        forUsername=username
                    )
                    response = request.execute()

                    if response.get('items'):
                        logger.info(f"채널 ID 찾음 (forUsername): {response['items'][0]['id']}")
                        return response['items'][0]['id']
                except (HttpError, TypeError) as e:
                    logger.warning(f"forUsername 실패, search API 시도 중: {e}")

                # 방법 3: search API 사용
                try:
                    self.api_calls += 1
                    search_request = self.youtube.search().list(
                        part='snippet',
                        q=username,
                        type='channel',
                        maxResults=5
                    )
                    search_response = search_request.execute()

                    # 정확한 채널명 매치 찾기
                    for item in search_response.get('items', []):
                        channel_title = item['snippet']['channelTitle'].lower()
                        # @username과 channelTitle 비교
                        if username.lower() in channel_title or channel_title in username.lower():
                            channel_id = item['snippet']['channelId']
                            logger.info(f"채널 ID 찾음 (search): {channel_id}")
                            return channel_id

                    # 정확한 매치가 없으면 첫 번째 결과 사용
                    if search_response.get('items'):
                        channel_id = search_response['items'][0]['snippet']['channelId']
                        logger.warning(f"정확한 매치 없음, 첫 결과 사용: {channel_id}")
                        return channel_id

                except HttpError as e:
                    logger.error(f"search API 실패: {e}")

            # /channel/UC... 형식 처리
            elif '/channel/' in channel_url:
                channel_id = channel_url.split('/channel/')[-1].strip()
                logger.info(f"채널 ID 추출 (URL): {channel_id}")
                return channel_id

            logger.warning(f"채널 ID를 찾을 수 없습니다: {channel_url}")
            return None

        except Exception as e:
            logger.error(f"예상치 못한 에러 (채널 ID): {e}")
            return None

    def get_channel_videos(self, channel_id: str, start_date: str, end_date: str) -> List[Dict]:
        """채널의 특정 기간 영상 목록 조회"""
        videos = []

        try:
            # 채널의 업로드 재생목록 ID 가져오기
            self.api_calls += 1
            request = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            )
            response = request.execute()

            if not response.get('items'):
                return videos

            uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

            # 재생목록에서 영상 목록 가져오기
            next_page_token = None

            while True:
                self.api_calls += 1
                request = self.youtube.playlistItems().list(
                    part='contentDetails',
                    playlistId=uploads_playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()

                video_ids = [item['contentDetails']['videoId'] for item in response.get('items', [])]

                if video_ids:
                    # 영상 세부 정보 가져오기
                    self.api_calls += 1
                    videos_request = self.youtube.videos().list(
                        part='snippet,statistics',
                        id=','.join(video_ids)
                    )
                    videos_response = videos_request.execute()

                    for video in videos_response.get('items', []):
                        published_at = video['snippet']['publishedAt']

                        # 날짜 필터링
                        if start_date <= published_at <= end_date:
                            stats = video['statistics']
                            videos.append({
                                'video_id': video['id'],
                                'title': video['snippet']['title'],
                                'published_at': published_at,
                                'views': int(stats.get('viewCount', 0)),
                                'likes': int(stats.get('likeCount', 0)),
                                'comments': int(stats.get('commentCount', 0))
                            })

                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break

            logger.info(f"채널 {channel_id}: {len(videos)}개 영상 수집")
            return videos

        except HttpError as e:
            logger.error(f"API 에러 (영상 목록): {e}")
            return videos


class ScoreCalculator:
    """점수 계산 클래스"""

    @staticmethod
    def calculate_basic_score(views: int, likes: int, comments: int) -> float:
        """영상별 기본 점수 계산"""
        return (views * 1) + (likes * 50) + (comments * 100)

    @staticmethod
    def calculate_engagement_rate(views: int, likes: int, comments: int) -> float:
        """인게이지먼트율 계산"""
        if views == 0:
            return 0.0
        return ((likes + comments * 2) / views) * 100

    @staticmethod
    def calculate_channel_scores(videos: List[Dict]) -> Dict:
        """채널 종합 점수 계산"""
        video_count = len(videos)

        # 영상이 없거나 부족한 경우 0점 처리
        if video_count == 0:
            return {
                'status': 'success',
                'video_count': 0,
                'median_score': 0,
                'avg_engagement': 0,
                'top3_avg': 0,
                'growth_ratio': 0,
                'score_median': 0,
                'score_engagement': 0,
                'score_viral': 0,
                'score_growth': 0,
                'total_score': 0,
                'videos': []
            }

        # 각 영상의 기본 점수와 인게이지먼트율 계산
        basic_scores = []
        engagement_rates = []

        for video in videos:
            basic_score = ScoreCalculator.calculate_basic_score(
                video['views'], video['likes'], video['comments']
            )
            engagement_rate = ScoreCalculator.calculate_engagement_rate(
                video['views'], video['likes'], video['comments']
            )

            basic_scores.append(basic_score)
            engagement_rates.append(engagement_rate)

        # 중앙값
        median_score = statistics.median(basic_scores) if basic_scores else 0

        # 평균 인게이지먼트율
        avg_engagement = statistics.mean(engagement_rates) if engagement_rates else 0

        # Top 3 평균 (영상이 3개 미만이면 있는 만큼만 사용)
        top3_scores = sorted(basic_scores, reverse=True)[:min(3, len(basic_scores))]
        top3_avg = statistics.mean(top3_scores) if top3_scores else 0

        # 성장 비율 (최근 3개 영상의 평균 / 전체 중앙값)
        # 영상이 3개 미만이면 있는 만큼만 사용
        recent_count = min(3, len(basic_scores))
        recent3_scores = basic_scores[-recent_count:] if basic_scores else []
        recent3_avg = statistics.mean(recent3_scores) if recent3_scores else 0
        growth_ratio = recent3_avg / median_score if median_score > 0 else 0

        # 최종 점수
        score_median = median_score * WEIGHT_MEDIAN
        score_engagement = avg_engagement * 100 * WEIGHT_ENGAGEMENT
        score_viral = top3_avg * WEIGHT_VIRAL
        score_growth = growth_ratio * 100 * WEIGHT_GROWTH

        total_score = score_median + score_engagement + score_viral + score_growth

        return {
            'status': 'success',
            'video_count': video_count,
            'median_score': median_score,
            'avg_engagement': avg_engagement,
            'top3_avg': top3_avg,
            'growth_ratio': growth_ratio,
            'score_median': score_median,
            'score_engagement': score_engagement,
            'score_viral': score_viral,
            'score_growth': score_growth,
            'total_score': total_score,
            'videos': videos
        }


class BadgeSystem:
    """뱃지 시스템"""

    @staticmethod
    def calculate_badges(channel_data: Dict, all_channels: List[Dict]) -> List[str]:
        """채널의 뱃지 계산"""
        if channel_data['status'] != 'success':
            return []

        badges = []

        # 안정 러너
        if channel_data['median_score'] >= BADGE_STABLE_THRESHOLD:
            badges.append('🎯')

        # 인게이지먼트 킹
        if channel_data['avg_engagement'] >= BADGE_ENGAGEMENT_THRESHOLD:
            badges.append('💬')

        # 바이럴 메이커
        if channel_data['top3_avg'] >= channel_data['median_score'] * BADGE_VIRAL_MULTIPLIER:
            badges.append('🔥')

        # 성장 로켓
        if channel_data['growth_ratio'] >= BADGE_GROWTH_THRESHOLD:
            badges.append('📈')

        # 올라운더: 모든 지표가 전체 평균 이상
        successful_channels = [c for c in all_channels if c['status'] == 'success']
        if successful_channels:
            avg_median = statistics.mean([c['median_score'] for c in successful_channels])
            avg_engagement_all = statistics.mean([c['avg_engagement'] for c in successful_channels])
            avg_top3 = statistics.mean([c['top3_avg'] for c in successful_channels])
            avg_growth = statistics.mean([c['growth_ratio'] for c in successful_channels])

            if (channel_data['median_score'] >= avg_median and
                channel_data['avg_engagement'] >= avg_engagement_all and
                channel_data['top3_avg'] >= avg_top3 and
                channel_data['growth_ratio'] >= avg_growth):
                badges.append('⭐')

        return badges


def load_channels(filename: str) -> List[Dict]:
    """채널 목록 로드"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"파일을 찾을 수 없습니다: {filename}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 에러: {e}")
        sys.exit(1)


def create_excel(leaderboard: List[Dict], filename: str):
    """Excel 파일 생성"""
    rows = []

    for rank, item in enumerate(leaderboard, 1):
        badges = ' '.join(item.get('badges', []))
        name_with_badges = f"{item['name']} {badges}".strip()
        channel_handle = item['channel_url'].split('@')[-1]

        if item['status'] == 'success':
            rows.append({
                '참여자': f"{name_with_badges}\n@{channel_handle}",
                '최종': round(item['total_score']),
                '기본': round(item['score_median']),
                '참여': round(item['score_engagement']),
                '바이럴': round(item['score_viral']),
                '성장': round(item['score_growth'])
            })
        else:
            # 채널을 찾을 수 없는 경우도 0점으로 처리
            rows.append({
                '참여자': f"{item['name']}\n@{channel_handle}",
                '최종': 0,
                '기본': 0,
                '참여': 0,
                '바이럴': 0,
                '성장': 0
            })

    df = pd.DataFrame(rows)

    # Excel 저장
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Leaderboard')

        # 서식 설정
        workbook = writer.book
        worksheet = writer.sheets['Leaderboard']

        # 열 너비 조정
        worksheet.column_dimensions['A'].width = 25
        for col in ['B', 'C', 'D', 'E', 'F']:
            worksheet.column_dimensions[col].width = 12

        # 텍스트 줄바꿈 설정
        from openpyxl.styles import Alignment
        for row in worksheet.iter_rows(min_row=2, max_row=worksheet.max_row, min_col=1, max_col=1):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical='center')

    logger.info(f"Excel 파일 생성 완료: {filename}")


def create_json(leaderboard: List[Dict], filename: str):
    """JSON 파일 생성 (웹페이지용)"""
    output = {
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'period': {
            'start': START_DATE,
            'end': END_DATE
        },
        'leaderboard': []
    }

    for rank, item in enumerate(leaderboard, 1):
        channel_handle = item['channel_url'].split('@')[-1]

        if item['status'] == 'success':
            output['leaderboard'].append({
                'rank': rank,
                'name': item['name'],
                'channel_handle': channel_handle,
                'channel_url': item['channel_url'],
                'badges': item.get('badges', []),
                'total_score': round(item['total_score']),
                'score_breakdown': {
                    'basic': round(item['score_median']),
                    'engagement': round(item['score_engagement']),
                    'viral': round(item['score_viral']),
                    'growth': round(item['score_growth'])
                },
                'metrics': {
                    'median_score': round(item['median_score']),
                    'avg_engagement': round(item['avg_engagement'], 2),
                    'top3_avg': round(item['top3_avg']),
                    'growth_ratio': round(item['growth_ratio'], 2),
                    'video_count': item['video_count']
                },
                'status': 'success'
            })
        else:
            # 채널을 찾을 수 없는 경우도 0점으로 표시
            output['leaderboard'].append({
                'rank': rank,
                'name': item['name'],
                'channel_handle': channel_handle,
                'channel_url': item['channel_url'],
                'badges': [],
                'total_score': 0,
                'score_breakdown': {
                    'basic': 0,
                    'engagement': 0,
                    'viral': 0,
                    'growth': 0
                },
                'metrics': {
                    'median_score': 0,
                    'avg_engagement': 0,
                    'top3_avg': 0,
                    'growth_ratio': 0,
                    'video_count': item.get('video_count', 0)
                },
                'status': 'channel_not_found'
            })

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    logger.info(f"JSON 파일 생성 완료: {filename}")


def main():
    """메인 함수"""
    logger.info("=" * 60)
    logger.info("YouTube Creator Leaderboard 생성 시작")
    logger.info(f"평가 기간: {START_DATE} ~ {END_DATE}")
    logger.info("=" * 60)

    # API 키 확인
    if not API_KEY:
        logger.error("YOUTUBE_API_KEY 환경 변수가 설정되지 않았습니다.")
        sys.exit(1)

    # YouTube API 초기화
    api = YouTubeAPI(API_KEY)

    # 채널 목록 로드
    channels = load_channels(CHANNELS_FILE)
    logger.info(f"총 {len(channels)}개 채널 로드")

    # 각 채널 데이터 수집
    all_channel_data = []

    for i, channel_info in enumerate(channels, 1):
        logger.info(f"\n[{i}/{len(channels)}] {channel_info['name']} 처리 중...")

        # 채널 ID 가져오기
        channel_id = api.get_channel_id(channel_info['channel_url'])
        if not channel_id:
            logger.warning(f"채널 ID를 찾을 수 없어 건너뜁니다: {channel_info['name']}")
            all_channel_data.append({
                **channel_info,
                'status': 'channel_not_found'
            })
            continue

        # 영상 목록 가져오기
        videos = api.get_channel_videos(channel_id, START_DATE, END_DATE)

        # 점수 계산
        scores = ScoreCalculator.calculate_channel_scores(videos)

        all_channel_data.append({
            **channel_info,
            **scores
        })

    # 뱃지 계산
    for channel_data in all_channel_data:
        if channel_data['status'] == 'success':
            channel_data['badges'] = BadgeSystem.calculate_badges(channel_data, all_channel_data)
        else:
            channel_data['badges'] = []

    # 순위 정렬
    leaderboard = sorted(
        all_channel_data,
        key=lambda x: x.get('total_score', -1),
        reverse=True
    )

    # 결과 출력
    logger.info("\n" + "=" * 60)
    logger.info("최종 순위")
    logger.info("=" * 60)
    for rank, item in enumerate(leaderboard, 1):
        if item['status'] == 'success':
            badges = ' '.join(item['badges'])
            logger.info(f"{rank}위: {item['name']} {badges} - {round(item['total_score'])}점")
        else:
            logger.info(f"{rank}위: {item['name']} - 데이터 부족")

    # 파일 생성
    logger.info("\n파일 생성 중...")
    create_excel(leaderboard, 'leaderboard.xlsx')
    create_json(leaderboard, 'leaderboard.json')

    # 통계
    logger.info("\n" + "=" * 60)
    logger.info("실행 통계")
    logger.info("=" * 60)
    logger.info(f"총 API 호출 횟수: {api.api_calls}")
    logger.info(f"성공적으로 처리된 채널: {sum(1 for x in leaderboard if x['status'] == 'success')}개")
    logger.info(f"데이터 부족 채널: {sum(1 for x in leaderboard if x['status'] != 'success')}개")
    logger.info("=" * 60)
    logger.info("완료!")


if __name__ == '__main__':
    main()
