# 📊 Google Sheets 자동 연동 설정 가이드

리더보드가 자동으로 Google Sheets에 업데이트되도록 설정하는 방법입니다.

## 🎯 개요

Google Sheets 연동을 활성화하면:
- ✅ Python 스크립트 실행 시 자동으로 Google Sheets 업데이트
- ✅ 실시간으로 온라인에서 확인 가능
- ✅ 공유 링크로 다른 사람과 공유 가능
- ✅ 1-3위 자동 강조 (금/은/동 색상)
- ✅ 자동 서식 설정 및 열 너비 조정

---

## 📋 설정 단계

### 1단계: Google Cloud 프로젝트 생성

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. 프로젝트 이름: "YouTube Leaderboard" (원하는 이름)

### 2단계: Google Sheets API 활성화

1. 왼쪽 메뉴 > "API 및 서비스" > "라이브러리"
2. 검색창에 "Google Sheets API" 입력
3. "Google Sheets API" 클릭
4. "사용 설정" 버튼 클릭

### 3단계: 서비스 계정 생성

1. 왼쪽 메뉴 > "API 및 서비스" > "사용자 인증 정보"
2. 상단 "+ 사용자 인증 정보 만들기" 클릭
3. "서비스 계정" 선택
4. 서비스 계정 세부정보 입력:
   - **이름**: `youtube-leaderboard-service`
   - **ID**: 자동 생성됨
   - **설명**: YouTube Leaderboard Google Sheets 연동
5. "만들기 및 계속" 클릭
6. 역할 선택은 건너뛰기 (선택사항)
7. "완료" 클릭

### 4단계: 서비스 계정 키 다운로드

1. 생성된 서비스 계정 클릭
2. "키" 탭 선택
3. "키 추가" > "새 키 만들기"
4. 키 유형: **JSON** 선택
5. "만들기" 클릭
6. `credentials.json` 파일이 자동으로 다운로드됨
7. 이 파일을 프로젝트 루트 디렉토리(`TCC/`)로 이동:
   ```bash
   mv ~/Downloads/your-project-xxxxx.json TCC/credentials.json
   ```

### 5단계: Google Sheets 생성 및 공유

1. [Google Sheets](https://sheets.google.com/) 접속
2. "새 스프레드시트" 생성
3. 스프레드시트 이름: "YouTube Creator Leaderboard" (원하는 이름)
4. URL에서 **스프레드시트 ID** 복사:
   ```
   https://docs.google.com/spreadsheets/d/{이_부분이_ID}/edit
   ```
5. **중요!** 서비스 계정에게 편집 권한 부여:
   - 우측 상단 "공유" 버튼 클릭
   - `credentials.json` 파일 내 `client_email` 주소 복사
   - 이메일 주소 입력 (예: `youtube-leaderboard-service@your-project.iam.gserviceaccount.com`)
   - 권한: **편집자** 선택
   - "전송" 클릭

### 6단계: 환경 변수 설정

`.env` 파일을 열고 다음 설정 추가:

```bash
# Google Sheets 연동 활성화
GOOGLE_SHEETS_ENABLED=true

# 인증 파일 경로 (기본값: credentials.json)
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json

# 스프레드시트 ID (5단계에서 복사한 ID)
GOOGLE_SHEET_ID=your_spreadsheet_id_here
```

---

## 🚀 실행

모든 설정이 완료되면 스크립트를 실행:

```bash
cd TCC
source venv/bin/activate
python leaderboard.py
```

성공 시 로그에 다음 메시지 표시:
```
Google Sheets 업로드 완료: https://docs.google.com/spreadsheets/d/{SHEET_ID}
```

---

## 📊 결과 확인

Google Sheets를 열면 다음과 같이 표시됩니다:

| 순위 | 참여자 | 채널 | 뱃지 | 최종 | 기본 | 참여 | 바이럴 | 성장 | 영상 수 |
|------|--------|------|------|------|------|------|--------|------|---------|
| 1 | 김소윤 | @catmocotto | 🎯💬⭐ | 45820 | 27000 | 13650 | 2730 | 2440 | 12 |
| 2 | 리로 | @lee-lo-4u | 🎯🔥 | 38450 | 22000 | 11400 | 3150 | 1900 | 9 |

**특징:**
- 헤더 행: 회색 배경, 굵은 글씨
- 1위: 금색 배경
- 2위: 은색 배경
- 3위: 동색 배경
- 자동 열 너비 조정
- 마지막 업데이트 시간 표시

---

## 🤖 GitHub Actions 설정

GitHub Actions에서도 자동으로 업데이트하려면:

### 1. GitHub Secrets에 인증 정보 추가

1. GitHub 저장소 > Settings > Secrets and variables > Actions
2. "New repository secret" 클릭
3. **Secret 1**: 서비스 계정 키
   - Name: `GOOGLE_SHEETS_CREDENTIALS`
   - Secret: `credentials.json` 파일의 **전체 내용** 복사 붙여넣기
4. **Secret 2**: 스프레드시트 ID
   - Name: `GOOGLE_SHEET_ID`
   - Secret: 스프레드시트 ID 입력

### 2. GitHub Actions 워크플로우 수정

`.github/workflows/update-leaderboard.yml` 파일의 `Run leaderboard script` 단계에 환경 변수 추가:

```yaml
- name: Run leaderboard script
  env:
    YOUTUBE_API_KEY: ${{ secrets.YOUTUBE_API_KEY }}
    GOOGLE_SHEETS_ENABLED: true
    GOOGLE_SHEETS_CREDENTIALS_FILE: credentials.json
    GOOGLE_SHEET_ID: ${{ secrets.GOOGLE_SHEET_ID }}
  run: |
    # credentials.json 파일 생성
    echo '${{ secrets.GOOGLE_SHEETS_CREDENTIALS }}' > credentials.json

    # 스크립트 실행
    python leaderboard.py
```

---

## 🔧 문제 해결

### 에러: "인증 파일을 찾을 수 없습니다"
- `credentials.json` 파일이 프로젝트 루트 디렉토리에 있는지 확인
- 파일명이 정확한지 확인

### 에러: "Permission denied"
- 서비스 계정 이메일이 스프레드시트에 편집자로 공유되었는지 확인
- 5단계를 다시 확인

### 에러: "Spreadsheet not found"
- `GOOGLE_SHEET_ID`가 올바른지 확인
- 스프레드시트 URL에서 ID 부분만 복사했는지 확인

### Google Sheets 업로드 건너뛰기
`.env` 파일에서:
```bash
GOOGLE_SHEETS_ENABLED=false
```

---

## 📁 파일 구조

```
TCC/
├── credentials.json          # Google 서비스 계정 키 (Git 제외)
├── token.json               # OAuth 토큰 (자동 생성, Git 제외)
├── .env                      # 환경 변수 설정 (Git 제외)
├── .gitignore               # Git 제외 파일 목록
├── leaderboard.py            # 메인 스크립트
└── ...
```

---

## 🔐 보안 주의사항

⚠️ **중요**: 다음 파일들은 민감한 인증 정보를 포함하고 있습니다.

**절대 Git에 커밋하면 안 되는 파일:**
- `credentials.json` - Google 서비스 계정 키 (Private Key 포함)
- `token.json` - OAuth 인증 토큰 (자동 생성)
- `.env` - API 키 및 환경 변수

**보안 체크리스트:**
- ✅ `.gitignore`에 이미 추가되어 있음 (확인 필수!)
- ✅ GitHub에 업로드하기 전 `git status`로 확인
- ❌ 절대로 public repository에 노출하지 마세요
- ✅ GitHub Actions에서는 Secrets 사용
- ⚠️ 실수로 커밋했다면 즉시 Service Account 삭제 후 재생성

---

## 📞 도움이 필요하신가요?

- [Google Sheets API 문서](https://developers.google.com/sheets/api)
- [Google Cloud Console](https://console.cloud.google.com/)
- [gspread 문서](https://docs.gspread.org/)

설정이 완료되면 리더보드가 자동으로 Google Sheets에 업데이트됩니다! 🎉
