#!/usr/bin/env python3
"""
YouTube Creator Leaderboard System
평가 기간: 2025-10-02 ~ 2025-12-14
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import statistics

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

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
BADGE_STABLE_THRESHOLD = 3000  # 꾸준러: 중앙값 3,000점 이상
BADGE_ENGAGEMENT_THRESHOLD = 5.0  # 인게이지먼트 킹: 평균 인게이지먼트율 5% 이상
BADGE_VIRAL_MULTIPLIER = 10  # 바이럴 메이커: Top 3 평균이 중앙값의 10배 이상
BADGE_GROWTH_THRESHOLD = 1.5  # 성장 로켓: 성장 비율 1.5 이상

# 뱃지 정보
BADGE_INFO = {
    '🎯': {
        'name': '꾸준러',
        'message': '꾸준히 좋은 콘텐츠를 만들고 있어요!'
    },
    '💬': {
        'name': '인게이지먼트 킹',
        'message': '진짜 팬을 만드는 능력자!'
    },
    '🔥': {
        'name': '바이럴 메이커',
        'message': '히트 영상을 만들어내는 감각이 있으시네요 🚀'
    },
    '📈': {
        'name': '성장 로켓',
        'message': '최근 가장 빠르게 성장하고 있어요! 이 기세 어디까지?'
    },
    '⭐': {
        'name': '올라운더',
        'message': '모든 면에서 완벽! 골고루 잘하는 밸런스형 크리에이터예요!'
    }
}


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
                logger.info(f"===== 채널 검색 시작: @{username} =====")
                logger.info(f"원본 URL: {channel_url}")

                # 방법 1: search API로 직접 @handle 검색 (가장 정확)
                try:
                    logger.info(f"방법 1: @{username}으로 채널 검색")
                    self.api_calls += 1
                    search_request = self.youtube.search().list(
                        part='snippet',
                        q=f"@{username}",
                        type='channel',
                        maxResults=20  # 충분한 결과 검색
                    )
                    search_response = search_request.execute()

                    logger.info(f"검색 결과: {len(search_response.get('items', []))}개 채널")

                    # 정확한 handle 매치 찾기
                    for idx, item in enumerate(search_response.get('items', [])):
                        # customUrl이나 channelTitle에서 매치 찾기
                        channel_title = item['snippet'].get('title', '')
                        channel_desc = item['snippet'].get('description', '')
                        channel_id_temp = item['snippet']['channelId']

                        logger.debug(f"  [{idx}] 채널명: {channel_title}, ID: {channel_id_temp[:10]}...")

                        # @username과 정확히 매치되는 채널 찾기
                        title_lower = channel_title.lower().replace(' ', '').replace('-', '')
                        username_lower = username.lower().replace(' ', '').replace('-', '')

                        # 정확한 매치 확인
                        if username_lower == title_lower or f"@{username_lower}" in channel_desc.lower():
                            logger.info(f"✓ 정확한 채널 ID 찾음: {channel_id_temp} (채널명: {channel_title})")
                            return channel_id_temp

                        # 부분 매치 확인
                        if username_lower in title_lower or title_lower in username_lower:
                            logger.info(f"✓ 부분 매치 채널 ID 찾음: {channel_id_temp} (채널명: {channel_title})")
                            return channel_id_temp

                    # 정확한 매치가 없으면 첫 번째 결과 사용
                    if search_response.get('items'):
                        channel_id = search_response['items'][0]['snippet']['channelId']
                        channel_title = search_response['items'][0]['snippet']['title']
                        logger.warning(f"⚠ 정확한 매치 없음, 첫 번째 결과 사용: {channel_id} (채널명: {channel_title})")
                        return channel_id

                except HttpError as e:
                    logger.warning(f"방법 1 실패: {e}")

                # 방법 4: forUsername 파라미터 사용 (레거시)
                try:
                    logger.info(f"방법 4: forUsername 파라미터로 검색")
                    self.api_calls += 1
                    request = self.youtube.channels().list(
                        part='id,snippet',
                        forUsername=username
                    )
                    response = request.execute()

                    if response.get('items'):
                        channel_id = response['items'][0]['id']
                        channel_title = response['items'][0]['snippet']['title']
                        logger.info(f"✓ forUsername으로 채널 ID 찾음: {channel_id} (채널명: {channel_title})")
                        return channel_id
                except (HttpError, TypeError) as e:
                    logger.warning(f"방법 4 실패: {e}")

                # 모든 방법 실패
                logger.error(f"❌ 채널 ID를 찾을 수 없습니다: {channel_url}")

            # /channel/UC... 형식 처리
            elif '/channel/' in channel_url:
                channel_id = channel_url.split('/channel/')[-1].strip()
                logger.info(f"✓ 채널 ID 직접 추출 (URL): {channel_id}")
                return channel_id

            # /c/customname 형식 처리
            elif '/c/' in channel_url:
                custom_name = channel_url.split('/c/')[-1].strip()
                logger.info(f"Custom URL 감지: /c/{custom_name}")
                # Custom URL은 search API로 검색
                try:
                    self.api_calls += 1
                    search_request = self.youtube.search().list(
                        part='snippet',
                        q=custom_name,
                        type='channel',
                        maxResults=5
                    )
                    search_response = search_request.execute()

                    if search_response.get('items'):
                        channel_id = search_response['items'][0]['snippet']['channelId']
                        channel_title = search_response['items'][0]['snippet']['title']
                        logger.info(f"✓ Custom URL로 채널 ID 찾음: {channel_id} (채널명: {channel_title})")
                        return channel_id
                except HttpError as e:
                    logger.warning(f"Custom URL 검색 실패: {e}")

            logger.error(f"❌ 채널 ID를 찾을 수 없습니다: {channel_url}")
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
                                'url': f"https://www.youtube.com/watch?v={video['id']}",
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

    def get_channel_info(self, channel_id: str) -> Optional[Dict]:
        """채널의 구독자 수와 전체 영상 개수를 포함한 정보 조회"""
        try:
            self.api_calls += 1
            request = self.youtube.channels().list(
                part='statistics,snippet',
                id=channel_id
            )
            response = request.execute()

            if response.get('items'):
                item = response['items'][0]
                stats = item['statistics']
                snippet = item['snippet']

                # 구독자 수 숨김 여부 확인
                hidden_subscriber = stats.get('hiddenSubscriberCount', False)
                subscriber_count = int(stats.get('subscriberCount', 0))

                if hidden_subscriber:
                    logger.warning(f"채널 {snippet.get('title', channel_id)}: 구독자 수 비공개 설정됨")
                elif subscriber_count == 0:
                    logger.warning(f"채널 {snippet.get('title', channel_id)}: 구독자 수 0명 (실제로 0명이거나 API 오류)")

                return {
                    'subscriber_count': subscriber_count,
                    'total_videos': int(stats.get('videoCount', 0)),
                    'total_views': int(stats.get('viewCount', 0)),
                    'channel_title': snippet.get('title', ''),
                    'hidden_subscriber': hidden_subscriber
                }
            else:
                logger.warning(f"채널 ID {channel_id}: API 응답에 items가 없음")
            return None

        except HttpError as e:
            logger.error(f"API 에러 (채널 정보) - 채널 ID {channel_id}: {e}")
            return None

    def get_total_video_count(self, channel_id: str) -> int:
        """채널의 전체 영상 개수 조회 (기간 제한 없음)"""
        try:
            # 채널 통계 정보 가져오기
            self.api_calls += 1
            request = self.youtube.channels().list(
                part='statistics',
                id=channel_id
            )
            response = request.execute()

            if response.get('items'):
                video_count = int(response['items'][0]['statistics'].get('videoCount', 0))
                logger.info(f"채널 {channel_id}: 전체 영상 {video_count}개")
                return video_count

            return 0
        except HttpError as e:
            logger.error(f"API 에러 (전체 영상 개수): {e}")
            return 0


class SubscriberTracker:
    """구독자 추적 클래스"""

    def __init__(self, baseline_file: str = 'subscriber_baseline.json'):
        self.baseline_file = baseline_file
        self.baseline_data = self.load_baseline()

    def load_baseline(self) -> Dict:
        """기준선 데이터 로드"""
        if os.path.exists(self.baseline_file):
            try:
                with open(self.baseline_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"구독자 기준선 데이터 로드: {len(data.get('channels', {}))}개 채널")
                    return data
            except Exception as e:
                logger.error(f"기준선 데이터 로드 실패: {e}")

        # 파일이 없거나 오류가 있으면 새로운 구조 생성
        return {
            'description': '구독자 수 기준선 데이터 (최초 조회 시점)',
            'created_at': None,
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'channels': {}
        }

    def save_baseline(self):
        """기준선 데이터 저장"""
        try:
            self.baseline_data['updated_at'] = datetime.now(timezone.utc).isoformat()
            with open(self.baseline_file, 'w', encoding='utf-8') as f:
                json.dump(self.baseline_data, f, ensure_ascii=False, indent=2)
            logger.info("구독자 기준선 데이터 저장 완료")
        except Exception as e:
            logger.error(f"기준선 데이터 저장 실패: {e}")

    def update_channel(self, channel_id: str, name: str, current_subscribers: int) -> Dict:
        """채널 구독자 정보 업데이트 및 증감 계산"""
        if channel_id not in self.baseline_data['channels']:
            # 최초 조회
            self.baseline_data['channels'][channel_id] = {
                'name': name,
                'initial_subscribers': current_subscribers,
                'initial_date': datetime.now(timezone.utc).isoformat(),
                'last_subscribers': current_subscribers,
                'last_update': datetime.now(timezone.utc).isoformat()
            }

            if self.baseline_data['created_at'] is None:
                self.baseline_data['created_at'] = datetime.now(timezone.utc).isoformat()

            logger.info(f"신규 채널 추가: {name} - 초기 구독자: {current_subscribers:,}")
            return {
                'current': current_subscribers,
                'initial': current_subscribers,
                'change': 0,
                'change_percent': 0.0
            }
        else:
            # 기존 채널 업데이트
            channel_data = self.baseline_data['channels'][channel_id]
            initial = channel_data['initial_subscribers']
            change = current_subscribers - initial
            change_percent = (change / initial * 100) if initial > 0 else 0

            # 마지막 구독자 수 업데이트
            channel_data['last_subscribers'] = current_subscribers
            channel_data['last_update'] = datetime.now(timezone.utc).isoformat()

            logger.info(f"채널 업데이트: {name} - 현재: {current_subscribers:,}, 증감: {change:+,} ({change_percent:+.1f}%)")

            return {
                'current': current_subscribers,
                'initial': initial,
                'change': change,
                'change_percent': change_percent
            }


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
                'average_views': 0,  # 평균 조회수
                'average_likes': 0,  # 평균 좋아요 수
                'avg_engagement': 0,
                'top3_avg': 0,
                'max_single_views': 0,  # 단일 최고 조회수
                'viral_video': {  # 최고 조회수 영상 상세 정보
                    'views': 0,
                    'likes': 0,
                    'comments': 0,
                    'title': '',
                    'video_id': '',
                    'url': ''
                },
                'growth_ratio': 0,
                'score_median': 0,
                'score_engagement': 0,
                'score_viral': 0,
                'score_growth': 0,
                'total_score': 0,
                'videos': []
            }

        # 각 영상의 기본 점수 계산 및 전체 수치 합산
        basic_scores = []
        video_details = []  # 영상 상세 정보 저장
        total_views = 0
        total_likes = 0
        total_comments = 0

        for video in videos:
            basic_score = ScoreCalculator.calculate_basic_score(
                video['views'], video['likes'], video['comments']
            )
            basic_scores.append(basic_score)

            # 영상 상세 정보 저장
            video_details.append({
                'title': video.get('title', ''),
                'video_id': video.get('video_id', ''),
                'url': video.get('url', ''),
                'published_at': video.get('published_at', ''),
                'views': video['views'],
                'likes': video['likes'],
                'comments': video['comments'],
                'basic_score': basic_score
            })

            # 전체 합산 (인게이지먼트 계산용)
            total_views += video['views']
            total_likes += video['likes']
            total_comments += video['comments']

        # 중앙값
        median_score = statistics.median(basic_scores) if basic_scores else 0

        # 평균 조회수 (Most Active 탭용) - 모든 영상의 조회수 평균
        views_list = [v['views'] for v in videos]
        average_views = statistics.mean(views_list) if views_list else 0

        # 평균 좋아요 수 (Most Active 탭용) - 모든 영상의 좋아요 수 평균
        likes_list = [v['likes'] for v in videos]
        average_likes = statistics.mean(likes_list) if likes_list else 0

        # 전체 합산 방식의 인게이지먼트율 계산
        if total_views > 0:
            total_engagement_rate = ((total_likes + total_comments * 2) / total_views) * 100
        else:
            total_engagement_rate = 0

        # Top 3 평균 (영상이 3개 이상일 때만 계산)
        if len(basic_scores) >= 3:
            top3_scores = sorted(basic_scores, reverse=True)[:3]
            top3_avg = statistics.mean(top3_scores)
        else:
            top3_avg = 0  # 영상 3개 미만이면 0점

        # 최고 조회수 영상 정보 (Viral Hit 탭용)
        viral_video = None
        max_single_views = 0
        if videos:
            viral_video = max(videos, key=lambda v: v['views'])
            max_single_views = viral_video['views']

        # 성장 비율 (영상이 3개 이상일 때만 계산)
        if len(basic_scores) >= 3:
            recent3_scores = basic_scores[-3:]  # 최근 3개
            recent3_avg = statistics.mean(recent3_scores)
            growth_ratio = recent3_avg / median_score if median_score > 0 else 0
        else:
            growth_ratio = 0  # 영상 3개 미만이면 0

        # 최종 점수
        score_median = median_score * WEIGHT_MEDIAN
        score_engagement = total_engagement_rate * 100 * WEIGHT_ENGAGEMENT
        score_viral = top3_avg * WEIGHT_VIRAL
        score_growth = growth_ratio * 100 * WEIGHT_GROWTH

        total_score = score_median + score_engagement + score_viral + score_growth

        return {
            'status': 'success',
            'video_count': video_count,
            'median_score': median_score,
            'average_views': average_views,  # 평균 조회수 추가
            'average_likes': average_likes,  # 평균 좋아요 수 추가
            'avg_engagement': total_engagement_rate,
            'top3_avg': top3_avg,
            'max_single_views': max_single_views,  # 단일 최고 조회수 추가
            'viral_video': {  # 최고 조회수 영상 상세 정보
                'views': viral_video['views'] if viral_video else 0,
                'likes': viral_video['likes'] if viral_video else 0,
                'comments': viral_video['comments'] if viral_video else 0,
                'title': viral_video.get('title', '') if viral_video else '',
                'video_id': viral_video.get('video_id', '') if viral_video else '',
                'url': viral_video.get('url', '') if viral_video else ''
            },
            'growth_ratio': growth_ratio,
            'score_median': score_median,
            'score_engagement': score_engagement,
            'score_viral': score_viral,
            'score_growth': score_growth,
            'total_score': total_score,
            'videos': videos,
            'video_details': video_details  # 영상 상세 정보 추가
        }


class BadgeSystem:
    """뱃지 시스템"""

    @staticmethod
    def calculate_badges(channel_data: Dict) -> Tuple[List[str], Dict[str, Dict]]:
        """채널의 뱃지 계산

        Returns:
            badges: 획득한 뱃지 이모지 리스트
            badge_descriptions: 각 뱃지의 상세 정보
        """
        if channel_data['status'] != 'success':
            return [], {}

        badges = []
        badge_descriptions = {}

        # 🎯 꾸준러: 중앙값 3,000점 이상
        if channel_data['median_score'] >= BADGE_STABLE_THRESHOLD:
            badges.append('🎯')
            badge_descriptions['🎯'] = BADGE_INFO['🎯']

        # 💬 인게이지먼트 킹: 평균 인게이지먼트율 5% 이상
        if channel_data['avg_engagement'] >= BADGE_ENGAGEMENT_THRESHOLD:
            badges.append('💬')
            badge_descriptions['💬'] = BADGE_INFO['💬']

        # 🔥 바이럴 메이커: Top 3 평균이 중앙값의 10배 이상 (둘 다 0보다 큰 경우만)
        if channel_data['median_score'] > 0 and channel_data['top3_avg'] > 0 and channel_data['top3_avg'] >= channel_data['median_score'] * BADGE_VIRAL_MULTIPLIER:
            badges.append('🔥')
            badge_descriptions['🔥'] = BADGE_INFO['🔥']

        # 📈 성장 로켓: 성장 비율 1.5 이상 (실제 성장이 있는 경우만)
        if channel_data['growth_ratio'] >= BADGE_GROWTH_THRESHOLD and channel_data['video_count'] > 0:
            badges.append('📈')
            badge_descriptions['📈'] = BADGE_INFO['📈']

        # ⭐ 올라운더: 중앙값 2,000점 이상, 인게이지먼트율 3% 이상, Top3 평균 4,000점 이상
        if (channel_data['median_score'] >= 2000 and
            channel_data['avg_engagement'] >= 3.0 and
            channel_data['top3_avg'] >= 4000):
            badges.append('⭐')
            badge_descriptions['⭐'] = BADGE_INFO['⭐']

        return badges, badge_descriptions


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

    # Excel 생성 스킵 - Google Sheets 사용 중
    logger.info(f"Excel 생성 스킵 (Google Sheets 사용 중): {filename}")


def upload_to_google_sheets(leaderboard: List[Dict], all_channel_data: List[Dict]):
    """Google Sheets에 데이터 업로드"""
    try:
        logger.info("Google Sheets 업로드 시작...")

        # 환경 변수 확인
        credentials_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
        spreadsheet_id = os.getenv('GOOGLE_SHEET_ID')

        logger.info(f"Credentials file: {credentials_file}")
        logger.info(f"Spreadsheet ID: {spreadsheet_id}")

        if not spreadsheet_id:
            logger.error("GOOGLE_SHEET_ID 환경 변수가 설정되지 않았습니다.")
            return

        # 인증 설정
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        if not os.path.exists(credentials_file):
            logger.error(f"인증 파일을 찾을 수 없습니다: {credentials_file}")
            # 현재 디렉토리 파일 목록 출력
            logger.error(f"현재 디렉토리 파일: {os.listdir('.')}")
            return

        logger.info("인증 파일 존재 확인 완료")

        creds = Credentials.from_service_account_file(credentials_file, scopes=scope)
        client = gspread.authorize(creds)
        logger.info("Google API 인증 성공")

        # 스프레드시트 열기
        spreadsheet = client.open_by_key(spreadsheet_id)

        # 시트 1: 리더보드 (요약)
        try:
            leaderboard_sheet = spreadsheet.worksheet('리더보드')
        except gspread.exceptions.WorksheetNotFound:
            leaderboard_sheet = spreadsheet.add_worksheet(title='리더보드', rows=100, cols=20)

        # 리더보드 데이터 준비
        leaderboard_headers = [
            '순위', '이름', '채널명', '총점수', '채널점수', '인게이지먼트', '바이럴', '성장',
            '영상수', '중앙값', '인게이지먼트율(%)', 'Top3평균', '성장비율', '뱃지'
        ]

        leaderboard_data = [leaderboard_headers]

        logger.info(f"리더보드 데이터 준비 중... 총 {len(leaderboard)}개 채널")

        for rank, item in enumerate(leaderboard, 1):
            try:
                # 데이터 구조 확인 및 로깅
                if rank == 1:  # 첫 번째 아이템만 상세 로깅
                    logger.info(f"첫 번째 아이템 키: {item.keys()}")

                if item['status'] == 'success':
                    # item 자체가 이미 채널 데이터임 (leaderboard = all_channel_data)
                    # scores 정보가 있는지 확인
                    scores = item.get('scores', {})

                    row = [
                        rank,
                        item['name'],
                        f"@{item.get('channel_handle', '')}",
                        round(item.get('total_score', 0)),
                        round(scores.get('score_median', item.get('score_median', 0))),
                        round(scores.get('score_engagement', item.get('score_engagement', 0))),
                        round(scores.get('score_viral', item.get('score_viral', 0))),
                        round(scores.get('score_growth', item.get('score_growth', 0))),
                        scores.get('video_count', item.get('video_count', 0)),
                        round(scores.get('median_score', item.get('median_score', 0))),
                        round(scores.get('avg_engagement', item.get('avg_engagement', 0)), 2),
                        round(scores.get('top3_avg', item.get('top3_avg', 0))),
                        round(scores.get('growth_ratio', item.get('growth_ratio', 0)), 2),
                        ' '.join(item.get('badges', []))
                    ]
                else:
                    row = [
                        rank, item['name'], f"@{item.get('channel_handle', '')}",
                        0, 0, 0, 0, 0,
                        item.get('video_count', 0), 0, 0, 0, 0, ''
                    ]

                leaderboard_data.append(row)

            except Exception as e:
                logger.error(f"행 {rank} 처리 중 오류: {e}")
                # 오류 발생 시 기본값으로 행 추가
                row = [rank, item.get('name', 'Unknown'), '', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '']
                leaderboard_data.append(row)

        logger.info(f"리더보드 데이터 준비 완료: {len(leaderboard_data)}행")

        # 리더보드 시트 업데이트
        leaderboard_sheet.clear()
        leaderboard_sheet.update('A1', leaderboard_data)
        logger.info("리더보드 시트 업데이트 완료")

        # 서식 설정
        leaderboard_sheet.format('A1:N1', {
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
            'textFormat': {'bold': True},
            'horizontalAlignment': 'CENTER'
        })

        # 1-3위 색상
        if len(leaderboard) >= 1:
            leaderboard_sheet.format('A2:N2', {
                'backgroundColor': {'red': 1, 'green': 0.843, 'blue': 0}
            })  # 금색
        if len(leaderboard) >= 2:
            leaderboard_sheet.format('A3:N3', {
                'backgroundColor': {'red': 0.753, 'green': 0.753, 'blue': 0.753}
            })  # 은색
        if len(leaderboard) >= 3:
            leaderboard_sheet.format('A4:N4', {
                'backgroundColor': {'red': 0.804, 'green': 0.498, 'blue': 0.196}
            })  # 동색

        # 시트 2: 영상 상세
        try:
            videos_sheet = spreadsheet.worksheet('영상상세')
        except gspread.exceptions.WorksheetNotFound:
            videos_sheet = spreadsheet.add_worksheet(title='영상상세', rows=1000, cols=20)

        # 영상 상세 데이터 준비
        video_headers = [
            '업로드날짜', '이름', '채널명', '영상제목',
            '조회수', '좋아요', '댓글', '기본점수', 'URL'
        ]

        video_data = [video_headers]

        # 모든 채널의 영상 정보 수집
        video_count = 0
        for channel in all_channel_data:
            if channel['status'] == 'success' and 'video_details' in channel:
                for video in channel['video_details']:
                    # 날짜 형식 변환 (Google Sheets가 인식할 수 있는 형식으로)
                    published_at = video.get('published_at', '')
                    if published_at:
                        try:
                            # ISO 형식을 datetime으로 파싱
                            date_obj = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                            # Google Sheets가 인식할 수 있는 형식으로 변환 (YYYY-MM-DD HH:MM:SS)
                            formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            formatted_date = published_at
                    else:
                        formatted_date = ''

                    row = [
                        formatted_date,  # 업로드날짜를 첫 번째로
                        channel['name'],
                        f"@{channel.get('channel_handle', '')}",
                        video.get('title', ''),
                        video.get('views', 0),
                        video.get('likes', 0),
                        video.get('comments', 0),
                        round(video.get('basic_score', 0)),
                        video.get('url', '')
                    ]
                    video_data.append(row)
                    video_count += 1

        logger.info(f"영상 상세 데이터 준비 완료: {video_count}개 영상")

        # 영상 상세 시트 업데이트
        videos_sheet.clear()
        videos_sheet.update('A1', video_data)
        logger.info("영상 상세 시트 업데이트 완료")

        # 헤더 서식
        videos_sheet.format('A1:I1', {
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
            'textFormat': {'bold': True},
            'horizontalAlignment': 'CENTER'
        })

        # 마지막 업데이트 시간 추가
        kst = timezone(timedelta(hours=9))
        update_time = datetime.now(kst).strftime('%Y-%m-%d %H:%M:%S KST')

        # 리더보드 시트에 업데이트 시간 표시
        leaderboard_sheet.update('P1', [['마지막 업데이트'], [update_time]])

        logger.info(f"Google Sheets 업로드 완료: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")

    except gspread.exceptions.APIError as e:
        logger.error(f"Google Sheets API 오류: {e}")
        if 'PERMISSION_DENIED' in str(e):
            logger.error("권한 오류: 서비스 계정에 스프레드시트 편집 권한이 없습니다.")
            logger.error("해결 방법: Google Sheets에서 서비스 계정 이메일에 편집자 권한을 부여하세요.")
    except FileNotFoundError as e:
        logger.error(f"인증 파일 오류: {e}")
    except Exception as e:
        logger.error(f"Google Sheets 업로드 실패: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())


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
                'badge_descriptions': item.get('badge_descriptions', {}),
                'total_score': round(item['total_score']),
                'score_breakdown': {
                    'basic': round(item['score_median']),
                    'engagement': round(item['score_engagement']),
                    'viral': round(item['score_viral']),
                    'growth': round(item['score_growth'])
                },
                'metrics': {
                    'median_score': round(item['median_score']),
                    'average_views': round(item.get('average_views', 0)),  # 평균 조회수 추가
                    'average_likes': round(item.get('average_likes', 0)),  # 평균 좋아요 수 추가
                    'avg_engagement': round(item['avg_engagement'], 2),
                    'top3_avg': round(item['top3_avg']),
                    'max_single_views': round(item.get('max_single_views', 0)),  # 단일 최고 조회수 추가
                    'viral_video': item.get('viral_video', {  # 최고 조회수 영상 상세 정보
                        'views': 0,
                        'likes': 0,
                        'comments': 0,
                        'title': '',
                        'video_id': '',
                        'url': ''
                    }),
                    'growth_ratio': round(item['growth_ratio'], 2),
                    'video_count': item['video_count'],
                    'total_video_count': item.get('total_video_count', 0),
                    'subscriber_count': item.get('subscriber_count', 0),  # 현재 구독자 수
                    'subscriber_change': item.get('subscriber_change', 0),  # 평가 기간 중 증감
                    'subscriber_change_percent': round(item.get('subscriber_change_percent', 0), 1)  # 증감률
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
                'badge_descriptions': {},
                'total_score': 0,
                'score_breakdown': {
                    'basic': 0,
                    'engagement': 0,
                    'viral': 0,
                    'growth': 0
                },
                'metrics': {
                    'median_score': 0,
                    'average_views': 0,  # 평균 조회수
                    'average_likes': 0,  # 평균 좋아요 수
                    'avg_engagement': 0,
                    'top3_avg': 0,
                    'max_single_views': 0,  # 단일 최고 조회수
                    'viral_video': {  # 최고 조회수 영상 상세 정보
                        'views': 0,
                        'likes': 0,
                        'comments': 0,
                        'title': '',
                        'video_id': '',
                        'url': ''
                    },
                    'growth_ratio': 0,
                    'video_count': item.get('video_count', 0),
                    'total_video_count': item.get('total_video_count', 0),
                    'subscriber_count': item.get('subscriber_count', 0),  # 현재 구독자 수
                    'subscriber_change': item.get('subscriber_change', 0),  # 평가 기간 중 증감
                    'subscriber_change_percent': 0  # 증감률
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

    # 구독자 추적기 초기화
    subscriber_tracker = SubscriberTracker()

    # 채널 목록 로드
    channels = load_channels(CHANNELS_FILE)
    logger.info(f"총 {len(channels)}개 채널 로드")

    # 각 채널 데이터 수집
    all_channel_data = []

    for i, channel_info in enumerate(channels, 1):
        logger.info(f"\n[{i}/{len(channels)}] {channel_info['name']} 처리 중...")

        # channel_url에서 channel_handle 추출
        channel_handle = channel_info['channel_url'].split('@')[-1] if '@' in channel_info['channel_url'] else ''
        channel_info['channel_handle'] = channel_handle

        # 채널 ID 가져오기 (channel_id가 있으면 바로 사용, 없으면 검색)
        if channel_info.get('channel_id'):
            channel_id = channel_info['channel_id']
            logger.info(f"✓ 저장된 채널 ID 사용: {channel_id}")
        else:
            channel_id = api.get_channel_id(channel_info['channel_url'])
        if not channel_id:
            logger.warning(f"채널 ID를 찾을 수 없어 건너뜁니다: {channel_info['name']}")
            all_channel_data.append({
                **channel_info,
                'status': 'channel_not_found'
            })
            continue

        # 채널 정보 가져오기 (구독자 수 포함)
        channel_stats = api.get_channel_info(channel_id)
        if not channel_stats:
            logger.warning(f"채널 정보를 가져올 수 없습니다: {channel_info['name']}")
            channel_stats = {'subscriber_count': 0, 'total_videos': 0}

        # 구독자 증감 추적
        subscriber_info = subscriber_tracker.update_channel(
            channel_id,
            channel_info['name'],
            channel_stats['subscriber_count']
        )

        # 영상 목록 가져오기
        videos = api.get_channel_videos(channel_id, START_DATE, END_DATE)

        # 점수 계산
        scores = ScoreCalculator.calculate_channel_scores(videos)

        # 채널 정보 추가
        scores['total_video_count'] = channel_stats['total_videos']
        scores['subscriber_count'] = subscriber_info['current']
        scores['subscriber_change'] = subscriber_info['change']
        scores['subscriber_change_percent'] = subscriber_info['change_percent']

        all_channel_data.append({
            **channel_info,
            **scores
        })

    # 뱃지 계산
    for channel_data in all_channel_data:
        if channel_data['status'] == 'success':
            badges, badge_descriptions = BadgeSystem.calculate_badges(channel_data)
            channel_data['badges'] = badges
            channel_data['badge_descriptions'] = badge_descriptions
        else:
            channel_data['badges'] = []
            channel_data['badge_descriptions'] = {}

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

    # 구독자 기준선 데이터 저장
    subscriber_tracker.save_baseline()

    # 파일 생성
    logger.info("\n파일 생성 중...")
    create_json(leaderboard, 'leaderboard.json')  # JSON은 웹페이지용으로 필요

    # Google Sheets 업로드 (환경 변수 확인)
    if os.getenv('GOOGLE_SHEETS_ENABLED', 'false').lower() == 'true':
        logger.info("\nGoogle Sheets 업로드 중...")
        upload_to_google_sheets(leaderboard, all_channel_data)
    else:
        # Google Sheets가 비활성화된 경우에만 로컬 Excel 생성
        create_excel(leaderboard, 'leaderboard.xlsx')
        logger.info("Google Sheets가 비활성화되어 로컬 Excel 파일을 생성했습니다.")

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
