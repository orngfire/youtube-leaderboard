#!/usr/bin/env python3
"""Google Sheets 연결 테스트 스크립트"""

import os
import sys
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 필요한 라이브러리 임포트
try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError as e:
    print(f"Error: 필요한 라이브러리가 설치되지 않았습니다: {e}")
    print("다음 명령으로 설치하세요: pip install gspread google-auth")
    sys.exit(1)

def test_google_sheets_connection():
    """Google Sheets 연결 테스트"""

    print("=" * 60)
    print("Google Sheets 연결 테스트 시작")
    print("=" * 60)

    # 1. credentials.json 파일 확인
    credentials_file = 'credentials.json'
    if not os.path.exists(credentials_file):
        print(f"❌ 오류: {credentials_file} 파일을 찾을 수 없습니다.")
        return False
    print(f"✅ credentials.json 파일 존재 확인")

    # 2. 인증 시도
    try:
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_file(credentials_file, scopes=scope)
        client = gspread.authorize(creds)
        print("✅ Google API 인증 성공")
    except Exception as e:
        print(f"❌ 인증 실패: {e}")
        return False

    # 3. 스프레드시트 접근 시도
    spreadsheet_id = '1u_69cbkGHlrW4OYVLad3H5BEIAPO-hMSNjN1qgYVmC0'
    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
        print(f"✅ 스프레드시트 접근 성공: {spreadsheet.title}")
    except gspread.exceptions.APIError as e:
        if 'PERMISSION_DENIED' in str(e):
            print(f"❌ 권한 오류: 서비스 계정에 스프레드시트 편집 권한이 없습니다.")
            print(f"   해결 방법:")
            print(f"   1. credentials.json에서 'client_email' 값 확인")
            print(f"   2. Google Sheets에서 해당 이메일에 편집자 권한 부여")
        else:
            print(f"❌ API 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 스프레드시트 접근 실패: {e}")
        return False

    # 4. 시트 목록 확인
    try:
        worksheets = spreadsheet.worksheets()
        print(f"✅ 시트 목록 조회 성공:")
        for sheet in worksheets:
            print(f"   - {sheet.title}")
    except Exception as e:
        print(f"❌ 시트 목록 조회 실패: {e}")
        return False

    # 5. 테스트 데이터 쓰기 시도
    try:
        # '테스트' 시트가 있으면 사용, 없으면 생성
        try:
            test_sheet = spreadsheet.worksheet('테스트')
        except:
            test_sheet = spreadsheet.add_worksheet(title='테스트', rows=100, cols=10)
            print("✅ '테스트' 시트 생성")

        # 테스트 데이터 쓰기
        test_sheet.update('A1', 'Google Sheets 연결 테스트 성공!')
        test_sheet.update('A2', f'테스트 시간: {os.popen("date").read().strip()}')
        print("✅ 테스트 데이터 쓰기 성공")

    except Exception as e:
        print(f"❌ 데이터 쓰기 실패: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ 모든 테스트 통과! Google Sheets 연동 준비 완료")
    print("=" * 60)
    return True

if __name__ == '__main__':
    # 서비스 계정 이메일 출력
    if os.path.exists('credentials.json'):
        try:
            import json
            with open('credentials.json', 'r') as f:
                creds_data = json.load(f)
                client_email = creds_data.get('client_email', 'Not found')
                print(f"\n서비스 계정 이메일: {client_email}")
                print("(이 이메일에 Google Sheets 편집 권한을 부여해야 합니다)\n")
        except:
            pass

    # 테스트 실행
    success = test_google_sheets_connection()
    sys.exit(0 if success else 1)