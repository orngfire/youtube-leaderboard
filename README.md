# 🏆 YouTube 크리에이터 리더보드

2025년 10월 2일부터 12월 14일까지 게재된 영상을 기준으로 YouTube 채널들을 평가하고 순위를 매기는 자동화 시스템입니다.

## 📋 목차

- [개요](#개요)
- [평가 시스템](#평가-시스템)
- [설치 방법](#설치-방법)
- [사용 방법](#사용-방법)
- [GitHub Actions 설정](#github-actions-설정)
- [파일 구조](#파일-구조)
- [출력 결과](#출력-결과)

## 개요

이 시스템은 YouTube Data API v3를 사용하여 채널의 영상 데이터를 수집하고, 다양한 지표를 기반으로 점수를 계산하여 리더보드를 생성합니다.

### 주요 기능

- 📊 자동 데이터 수집 (YouTube Data API v3)
- 📈 다차원 평가 시스템 (기본, 인게이지먼트, 바이럴, 성장)
- 🏅 뱃지 시스템 (5가지 유형)
- 📑 Excel 파일 자동 생성
- 🌐 반응형 웹 리더보드
- 🤖 GitHub Actions 자동화
- 🚀 GitHub Pages 자동 배포

## 평가 시스템

### 1. 영상별 기본 점수

```
기본 점수 = (조회수 × 1) + (좋아요 × 50) + (댓글 × 100)
```

### 2. 채널 종합 점수

```
총점 = (중앙값 × 0.6) + (평균 인게이지먼트율 × 100 × 0.3) + (Top 3 평균 × 0.05) + (성장 비율 × 100 × 0.05)
```

#### 각 지표 설명

**기본 점수 (60%)**
- 기간 내 모든 영상의 기본 점수를 계산
- 이들의 중앙값(median)을 사용하여 안정적인 성과 측정

**인게이지먼트 점수 (30%)**
- 각 영상의 인게이지먼트율 = ((좋아요 + 댓글×2) / 조회수) × 100
- 평균 인게이지먼트율을 기반으로 점수 계산

**바이럴 보너스 (5%)**
- Top 3 평균 = (가장 높은 기본 점수 3개 영상의 합) / 3
- 바이럴 영상의 영향력 반영

**성장 점수 (5%)**
- 성장 비율 = (최근 3개 영상의 평균 기본 점수) / (전체 영상 기본 점수 중앙값)
- 최근 성장세 반영

### 3. 뱃지 시스템

| 뱃지 | 이름 | 조건 |
|------|------|------|
| 🎯 | 안정 러너 | 중앙값 5,000점 이상 |
| 💬 | 인게이지먼트 킹 | 평균 인게이지먼트율 5% 이상 |
| 🔥 | 바이럴 메이커 | Top 3 평균이 중앙값의 10배 이상 |
| 📈 | 성장 로켓 | 성장 비율 1.5 이상 |
| ⭐ | 올라운더 | 모든 지표가 전체 참여자 평균 이상 |

## 설치 방법

### 1. 저장소 클론

```bash
git clone <repository-url>
cd TCC
```

### 2. Python 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. YouTube API 키 발급

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. "API 및 서비스" > "라이브러리"로 이동
4. "YouTube Data API v3" 검색 및 활성화
5. "사용자 인증 정보" > "사용자 인증 정보 만들기" > "API 키" 선택
6. API 키 복사

### 4. 환경 변수 설정

`.env` 파일 생성:

```bash
cp .env.example .env
```

`.env` 파일에 API 키 입력:

```
YOUTUBE_API_KEY=your_api_key_here
```

## 사용 방법

### 로컬에서 실행

```bash
python leaderboard.py
```

실행 결과:
- `leaderboard.xlsx` - Excel 파일
- `leaderboard.json` - 웹페이지용 JSON 데이터
- `leaderboard.log` - 실행 로그

### 웹페이지 로컬 테스트

```bash
# 간단한 HTTP 서버 실행
python -m http.server 8000

# 브라우저에서 접속
# http://localhost:8000
```

## GitHub Actions 설정

### 1. GitHub Secrets 설정

1. GitHub 저장소 > Settings > Secrets and variables > Actions
2. "New repository secret" 클릭
3. Name: `YOUTUBE_API_KEY`
4. Secret: YouTube API 키 입력
5. "Add secret" 클릭

### 2. GitHub Pages 활성화

1. GitHub 저장소 > Settings > Pages
2. Source: "GitHub Actions" 선택
3. 저장

### 3. 워크플로우 실행

자동 실행:
- 매일 한국시간 00:00 (UTC 15:00)
- 매일 한국시간 12:00 (UTC 3:00)

수동 실행:
1. Actions 탭 이동
2. "Update Leaderboard" 워크플로우 선택
3. "Run workflow" 클릭

### 4. 배포된 웹사이트 확인

`https://<username>.github.io/<repository-name>/`

## 파일 구조

```
TCC/
├── .github/
│   └── workflows/
│       └── update-leaderboard.yml  # GitHub Actions 워크플로우
├── docs/                           # GitHub Pages 배포 폴더
│   ├── index.html
│   ├── styles.css
│   ├── script.js
│   ├── leaderboard.json
│   └── leaderboard.xlsx
├── channels.json                   # 채널 목록
├── leaderboard.py                  # 메인 스크립트
├── requirements.txt                # Python 패키지
├── index.html                      # 웹페이지 템플릿
├── styles.css                      # 스타일시트
├── script.js                       # JavaScript
├── .env.example                    # 환경 변수 예제
├── .gitignore                      # Git 제외 파일
└── README.md                       # 문서
```

## 출력 결과

### Excel 파일 (leaderboard.xlsx)

| 참여자 | 최종 | 기본 | 참여 | 바이럴 | 성장 |
|--------|------|------|------|--------|------|
| 김소윤 🎯💬<br>@catmocotto | 12,345 | 7,407 | 3,702 | 617 | 617 |

- **참여자**: 이름 + 뱃지, 채널명
- **최종**: 최종 점수
- **기본**: 중앙값 × 0.6
- **참여**: 인게이지먼트 점수 × 0.3
- **바이럴**: Top 3 평균 × 0.05
- **성장**: 성장 점수 × 0.05

### 웹페이지

- 모바일 최적화 반응형 디자인
- 다크/라이트 테마 지원
- 1-3위 메달 강조 (금, 은, 동)
- 클릭하여 상세 정보 확장
- 실시간 새로고침 기능
- 채널 바로가기 링크

## 채널 추가/제거

`channels.json` 파일 수정:

```json
[
  {
    "name": "채널 이름",
    "channel_url": "https://www.youtube.com/@channel_handle"
  }
]
```

## 문제 해결

### API 할당량 초과

YouTube Data API는 일일 할당량이 있습니다 (기본 10,000 units).

해결 방법:
1. API 호출 빈도 줄이기 (cron 스케줄 조정)
2. Google Cloud Console에서 할당량 증가 요청
3. 여러 API 키 로테이션 사용

### 데이터가 표시되지 않음

1. API 키가 올바르게 설정되었는지 확인
2. YouTube Data API v3가 활성화되었는지 확인
3. `leaderboard.log` 파일에서 에러 확인
4. 채널 URL 형식 확인 (`@username` 형식)

### GitHub Pages 배포 실패

1. Settings > Pages에서 Source가 "GitHub Actions"인지 확인
2. Actions 탭에서 워크플로우 로그 확인
3. `docs/` 폴더에 필요한 파일이 있는지 확인

## 라이선스

MIT License

## 기여

이슈나 PR은 언제나 환영합니다!

## 문의

문제가 발생하면 [Issues](../../issues)에 등록해주세요.
