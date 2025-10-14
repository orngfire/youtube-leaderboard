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

                # 방법 2: 전체 URL로 검색
                try:
                    logger.info(f"방법 2: 전체 URL로 검색")
                    self.api_calls += 1
                    search_request = self.youtube.search().list(
                        part='snippet',
                        q=channel_url,  # 전체 URL로 검색
                        type='channel',
                        maxResults=5
                    )
                    search_response = search_request.execute()

                    if search_response.get('items'):
                        channel_id = search_response['items'][0]['snippet']['channelId']
                        channel_title = search_response['items'][0]['snippet']['title']
                        logger.info(f"✓ URL 검색으로 채널 ID 찾음: {channel_id} (채널명: {channel_title})")
                        return channel_id
                except HttpError as e:
                    logger.warning(f"방법 2 실패: {e}")

                # 방법 3: username만으로 검색 (@ 제외)
                try:
                    logger.info(f"방법 3: username만으로 검색 ({username})")
                    self.api_calls += 1
                    search_request = self.youtube.search().list(
                        part='snippet',
                        q=username,  # @ 없이 검색
                        type='channel',
                        maxResults=10
                    )
                    search_response = search_request.execute()

                    # username과 매치되는 채널 찾기
                    for item in search_response.get('items', []):
                        channel_title = item['snippet'].get('title', '').lower()
                        # username과 채널명 비교
                        if username.lower() in channel_title.replace(' ', ''):
                            channel_id = item['snippet']['channelId']
                            logger.info(f"✓ username 매치로 채널 ID 찾음: {channel_id} (채널명: {item['snippet'].get('title', '')})")
                            return channel_id

                    # 매치가 없으면 첫 번째 결과
                    if search_response.get('items'):
                        channel_id = search_response['items'][0]['snippet']['channelId']
                        channel_title = search_response['items'][0]['snippet']['title']
                        logger.warning(f"⚠ 정확한 매치 없음, 첫 결과 사용: {channel_id} (채널명: {channel_title})")
                        return channel_id

                except HttpError as e:
                    logger.error(f"방법 3 실패: {e}")

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

                # 방법 5: 채널의 최근 영상을 통한 역추적
                # 채널 URL로 영상을 먼저 검색하고, 그 영상의 채널 ID를 가져오기
                try:
                    logger.info(f"방법 5: 영상을 통한 채널 ID 역추적")
                    self.api_calls += 1
                    # 채널 URL 또는 @handle로 최근 영상 검색
                    search_request = self.youtube.search().list(
                        part='snippet',
                        q=f"@{username}",  # @handle로 영상 검색
                        type='video',
                        order='date',
                        maxResults=10
                    )
                    search_response = search_request.execute()

                    logger.info(f"영상 검색 결과: {len(search_response.get('items', []))}개")

                    # 영상을 찾았다면 그 채널 ID를 사용
                    if search_response.get('items'):
                        for idx, video_item in enumerate(search_response['items']):
                            video_channel_id = video_item['snippet']['channelId']
                            video_channel_title = video_item['snippet']['channelTitle']
                            video_title = video_item['snippet']['title']

                            logger.debug(f"  [{idx}] 영상: {video_title[:30]}... / 채널: {video_channel_title}")

                            # 채널 이름이 username과 유사한지 확인
                            if username.lower().replace('-', '') in video_channel_title.lower().replace(' ', '').replace('-', ''):
                                logger.info(f"✓ 영상을 통해 채널 ID 찾음: {video_channel_id} (채널: {video_channel_title})")
                                return video_channel_id

                        # 유사한 이름이 없으면 첫 번째 영상의 채널 사용
                        video_channel_id = search_response['items'][0]['snippet']['channelId']
                        video_channel_title = search_response['items'][0]['snippet']['channelTitle']
                        logger.warning(f"⚠ 영상의 채널 ID 사용 (첫 번째 결과): {video_channel_id} (채널: {video_channel_title})")
                        return video_channel_id

                except HttpError as e:
                    logger.warning(f"방법 5 실패: {e}")

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

        # 전체 합산 방식의 인게이지먼트율 계산
        if total_views > 0:
            total_engagement_rate = ((total_likes + total_comments * 2) / total_views) * 100
        else:
            total_engagement_rate = 0

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
        score_engagement = total_engagement_rate * 100 * WEIGHT_ENGAGEMENT
        score_viral = top3_avg * WEIGHT_VIRAL
        score_growth = growth_ratio * 100 * WEIGHT_GROWTH

        total_score = score_median + score_engagement + score_viral + score_growth

        return {
            'status': 'success',
            'video_count': video_count,
            'median_score': median_score,
            'avg_engagement': total_engagement_rate,
            'top3_avg': top3_avg,
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
    def calculate_badges(channel_data: Dict, all_channels: List[Dict]) -> Tuple[List[str], Dict[str, Dict]]:
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

        # channel_url에서 channel_handle 추출
        channel_handle = channel_info['channel_url'].split('@')[-1] if '@' in channel_info['channel_url'] else ''
        channel_info['channel_handle'] = channel_handle

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
            badges, badge_descriptions = BadgeSystem.calculate_badges(channel_data, all_channel_data)
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
