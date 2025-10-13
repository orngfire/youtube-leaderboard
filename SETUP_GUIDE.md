# 🚀 YouTube 크리에이터 리더보드 - 설치 가이드

## 📌 로컬 테스트 완료 상태

✅ 모든 파일 생성 완료
✅ Python 가상환경 설정 완료
✅ 필요한 패키지 설치 완료
✅ 웹페이지 로컬 서버 실행 테스트 완료

## 🔑 YouTube API 키 발급 방법

### 1. Google Cloud Console 접속
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. Google 계정으로 로그인

### 2. 프로젝트 생성
1. 상단의 프로젝트 선택 드롭다운 클릭
2. "새 프로젝트" 클릭
3. 프로젝트 이름 입력 (예: "YouTube Leaderboard")
4. "만들기" 클릭

### 3. YouTube Data API v3 활성화
1. 왼쪽 메뉴에서 "API 및 서비스" > "라이브러리" 선택
2. 검색창에 "YouTube Data API v3" 입력
3. "YouTube Data API v3" 클릭
4. "사용 설정" 버튼 클릭

### 4. API 키 생성
1. 왼쪽 메뉴에서 "API 및 서비스" > "사용자 인증 정보" 선택
2. 상단의 "+ 사용자 인증 정보 만들기" 클릭
3. "API 키" 선택
4. API 키가 생성되면 복사 (나중에 다시 볼 수 있음)

### 5. API 키 제한 설정 (선택사항, 권장)
1. 생성된 API 키 옆의 "제한사항 수정" 클릭
2. "API 제한사항" 섹션에서 "키 제한" 선택
3. "YouTube Data API v3"만 선택
4. "저장" 클릭

## 💻 로컬 실행 방법

### 1. API 키 설정

`.env` 파일을 열고 발급받은 API 키를 입력:

```bash
YOUTUBE_API_KEY=여기에_발급받은_API_키_입력
```

### 2. 가상환경 활성화 및 스크립트 실행

```bash
# 가상환경 활성화
source venv/bin/activate

# 리더보드 생성
python leaderboard.py
```

실행 결과:
- `leaderboard.xlsx` - Excel 리더보드
- `leaderboard.json` - 웹페이지용 데이터
- `leaderboard.log` - 실행 로그

### 3. 웹페이지 확인

```bash
# 로컬 서버 실행 (이미 실행 중)
python3 -m http.server 8000

# 브라우저에서 접속
# http://localhost:8000
```

## 🌐 GitHub Pages 배포

### 1. GitHub 저장소 생성
1. GitHub에서 새 저장소 생성
2. 로컬에서 git 초기화 및 푸시:

```bash
git init
git add .
git commit -m "Initial commit: YouTube Creator Leaderboard"
git branch -M main
git remote add origin https://github.com/사용자명/저장소명.git
git push -u origin main
```

### 2. GitHub Secrets 설정
1. 저장소 > Settings > Secrets and variables > Actions
2. "New repository secret" 클릭
3. Name: `YOUTUBE_API_KEY`
4. Secret: 발급받은 YouTube API 키
5. "Add secret" 클릭

### 3. GitHub Pages 활성화
1. 저장소 > Settings > Pages
2. Source: "GitHub Actions" 선택
3. 저장

### 4. 워크플로우 실행
- 자동: 매일 한국시간 00:00, 12:00에 실행
- 수동: Actions 탭 > "Update Leaderboard" > "Run workflow"

### 5. 배포된 사이트 확인
`https://사용자명.github.io/저장소명/`

## 📊 현재 로컬 테스트 상태

**✅ 완료된 항목:**
- [x] 가상환경 생성 및 활성화
- [x] Python 패키지 설치 (pandas 2.3.3으로 업그레이드)
- [x] 테스트 데이터로 JSON 파일 생성
- [x] 로컬 웹서버 실행 (http://localhost:8000)

**⏳ 다음 단계:**
1. YouTube API 키 발급 및 설정
2. 실제 데이터로 스크립트 실행
3. GitHub에 푸시
4. GitHub Pages 배포

## 🔍 문제 해결

### API 키 관련 에러
```
YOUTUBE_API_KEY 환경 변수가 설정되지 않았습니다.
```
→ `.env` 파일에서 `YOUR_API_KEY_HERE`를 실제 API 키로 교체

### API 할당량 초과
```
quotaExceeded
```
→ YouTube API는 일일 할당량 10,000 units (약 100~200회 채널 조회)
→ 다음 날까지 대기하거나 추가 할당량 요청

### 데이터 부족 채널
```
평가 기간 내 영상이 2개로 데이터가 부족합니다.
```
→ 최소 3개 영상 필요, 정상 동작

## 📁 프로젝트 구조

```
TCC/
├── .env                              # API 키 (git 제외)
├── .env.example                      # API 키 예제
├── .github/workflows/
│   └── update-leaderboard.yml        # GitHub Actions
├── .gitignore                        # Git 제외 파일
├── README.md                         # 프로젝트 문서
├── SETUP_GUIDE.md                    # 이 파일
├── channels.json                     # 채널 목록
├── index.html                        # 웹페이지
├── leaderboard.json                  # 리더보드 데이터
├── leaderboard.py                    # 메인 스크립트
├── requirements.txt                  # Python 패키지
├── script.js                         # JavaScript
├── styles.css                        # CSS
└── venv/                             # 가상환경 (git 제외)
```

## 📞 도움이 필요하신가요?

1. [README.md](README.md) - 전체 프로젝트 문서
2. [GitHub Issues](../../issues) - 문제 보고
3. 로그 파일 확인: `leaderboard.log`

---

**현재 상태:** 로컬 테스트 환경 구축 완료 ✅
**다음 단계:** YouTube API 키 발급 및 실제 데이터 테스트
