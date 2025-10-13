# GitHub Secrets 설정 가이드

## 필요한 Secrets

GitHub Actions에서 리더보드를 자동으로 업데이트하려면 다음 Secrets를 설정해야 합니다:

1. **YOUTUBE_API_KEY** - YouTube Data API v3 키 (이미 설정됨)
2. **GOOGLE_SHEETS_CREDENTIALS** - Google Sheets 서비스 계정 인증 정보 (새로 추가 필요)

## Google Sheets Credentials 설정 방법

### 1. credentials.json 파일 내용 복사
```bash
# 로컬에서 credentials.json 파일 내용 확인
cat credentials.json
```

전체 JSON 내용을 복사합니다.

### 2. GitHub Repository에서 Secret 추가

1. GitHub 저장소 페이지로 이동: https://github.com/orngfire/youtube-leaderboard
2. Settings 탭 클릭
3. 왼쪽 메뉴에서 "Secrets and variables" → "Actions" 클릭
4. "New repository secret" 버튼 클릭
5. 다음 정보 입력:
   - **Name**: `GOOGLE_SHEETS_CREDENTIALS`
   - **Secret**: credentials.json 파일의 전체 JSON 내용 붙여넣기
6. "Add secret" 버튼 클릭

### 3. 설정 확인

Secrets 페이지에서 다음 두 개의 Secret이 표시되어야 합니다:
- YOUTUBE_API_KEY
- GOOGLE_SHEETS_CREDENTIALS

## 작동 방식

GitHub Actions 워크플로우가 실행될 때:

1. `GOOGLE_SHEETS_CREDENTIALS` Secret에서 JSON 내용을 읽어옴
2. 임시로 `credentials.json` 파일 생성
3. Python 스크립트에서 이 파일을 사용하여 Google Sheets API 인증
4. 리더보드 데이터를 Google Sheets에 업로드
5. 워크플로우 종료 시 임시 파일 자동 삭제

## 보안 참고사항

- credentials.json 파일은 절대 Git에 커밋하지 마세요
- .gitignore에 이미 추가되어 있음
- GitHub Secrets는 암호화되어 저장되며, 워크플로우 실행 중에만 접근 가능
- Secret 값은 로그에 자동으로 마스킹됨

## 테스트 방법

설정 완료 후:

1. Actions 탭으로 이동
2. "Update Leaderboard" 워크플로우 선택
3. "Run workflow" 버튼 클릭하여 수동 실행
4. 워크플로우가 성공적으로 완료되는지 확인
5. Google Sheets에 데이터가 업데이트되었는지 확인

## 문제 해결

워크플로우가 실패하는 경우:

1. **Authentication 오류**: GOOGLE_SHEETS_CREDENTIALS Secret이 올바른 JSON 형식인지 확인
2. **Permission 오류**: 서비스 계정이 Google Sheets에 대한 편집 권한이 있는지 확인
3. **API 오류**: Google Sheets API가 활성화되어 있는지 확인

## 예정된 실행 시간

워크플로우는 다음 시간에 자동 실행됩니다:
- 한국 시간 00:00 (매일 자정)
- 한국 시간 12:00 (매일 정오)

수동으로도 언제든지 실행 가능합니다.