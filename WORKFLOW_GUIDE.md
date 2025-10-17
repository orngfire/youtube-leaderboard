# GitHub Workflow 관리 가이드

## 브랜치 전략

### 1. 기본 원칙
- **main 브랜치**: 프로덕션 환경 (GitHub Pages 배포)
- **개발 브랜치**: 새 기능 개발 및 테스트
- **중요**: channels.json 등 핵심 설정 파일 수정 시 반드시 main에 즉시 반영

### 2. 작업 흐름

#### 채널 정보 수정 시 (channels.json)
```bash
# 1. main 브랜치에서 직접 작업
git checkout main
git pull origin main

# 2. channels.json 수정
# 예: 채널 ID 변경, 새 채널 추가

# 3. 즉시 커밋 및 푸시
git add channels.json
git commit -m "Update channel ID for [채널명]"
git push origin main

# 4. 개발 브랜치에도 반영
git checkout dev-branch
git merge main
```

#### 새 기능 개발 시
```bash
# 1. 기능 브랜치 생성
git checkout -b feature/new-feature

# 2. 개발 및 테스트

# 3. main에 머지
git checkout main
git merge feature/new-feature
git push origin main
```

## GitHub Actions 워크플로우 개선

### 현재 상태
- 하루 3번 자동 실행 (00:00, 08:00, 16:00 KST)
- main 브랜치의 코드와 설정 사용
- docs/leaderboard.json 자동 업데이트

### 개선 방안

#### 1. 수동 실행 시 브랜치 선택 가능하게 수정
`.github/workflows/update-leaderboard.yml` 수정:

```yaml
on:
  workflow_dispatch:
    inputs:
      branch:
        description: 'Branch to run workflow from'
        required: false
        default: 'main'
        type: choice
        options:
          - main
          - development
          - test
```

#### 2. 채널 정보 검증 스크립트 추가
```yaml
- name: Validate channels
  run: |
    python validate_channels.py
  continue-on-error: false
```

## 체크리스트

### 채널 정보 변경 시
- [ ] channels.json 수정
- [ ] main 브랜치에 커밋
- [ ] GitHub Actions 수동 실행하여 확인
- [ ] GitHub Pages 업데이트 확인 (10분 후)

### 새 기능 배포 시
- [ ] 기능 브랜치에서 개발 완료
- [ ] 로컬 테스트 완료
- [ ] main 브랜치에 머지
- [ ] GitHub Actions 실행 확인
- [ ] GitHub Pages 정상 동작 확인

## 트러블슈팅

### GitHub Pages가 업데이트되지 않을 때
1. 캐시 문제: 10분 대기 또는 브라우저 캐시 삭제
2. 빌드 실패: Actions 탭에서 에러 확인
3. 강제 업데이트:
   ```bash
   git commit --allow-empty -m "Force GitHub Pages update"
   git push origin main
   ```

### 잘못된 데이터가 표시될 때
1. channels.json 확인
2. main 브랜치가 최신인지 확인
3. GitHub Actions 로그 확인
4. 필요시 수동 실행

## 모니터링

### 확인 사항
- GitHub Actions 실행 상태: https://github.com/orngfire/youtube-leaderboard/actions
- GitHub Pages 상태: https://orngfire.github.io/youtube-leaderboard/
- 최신 데이터: https://raw.githubusercontent.com/orngfire/youtube-leaderboard/main/docs/leaderboard.json

### 알림 설정
GitHub 저장소 Settings → Notifications에서 Actions 실패 시 이메일 알림 설정 권장