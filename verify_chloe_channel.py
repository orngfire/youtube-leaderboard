#!/usr/bin/env python3
"""
Verify 클로이 channel ID and find the correct one
"""

print("=" * 70)
print("클로이 채널 ID 확인")
print("=" * 70)

print("\n현재 설정:")
print("- 이름: 클로이")
print("- URL: https://www.youtube.com/@neo_chloe")
print("- 저장된 ID: UC59F8hHuNyS9aP4fvSTD6Og")

print("\n" + "-" * 70)
print("문제: 이 channel_id로 가져오는 영상이 클로이 채널의 영상이 아님")
print("-" * 70)

print("\n올바른 channel ID를 찾는 방법:")
print("1. https://www.youtube.com/@neo_chloe 방문")
print("2. 브라우저에서 F12 (개발자 도구)")
print("3. Console 탭에서 다음 입력:")
print('   ytInitialData.metadata.channelMetadataRenderer.externalId')
print("4. 또는 페이지 소스에서 'channelId' 검색")

print("\n" + "-" * 70)
print("channel_id가 틀렸을 가능성이 높습니다.")
print("올바른 channel_id를 찾아서 channels.json을 업데이트해야 합니다.")
print("-" * 70)

print("\n대체 방법:")
print("1. YouTube Data API Explorer 사용")
print("   https://developers.google.com/youtube/v3/docs/search/list")
print("2. Parameters:")
print("   - part: snippet")
print("   - q: neo_chloe")
print("   - type: channel")
print("3. Execute 후 결과에서 올바른 channel ID 확인")

print("\n주의사항:")
print("- @neo_chloe가 실제로 맞는 handle인지 확인")
print("- 채널이 비공개거나 삭제되지 않았는지 확인")
print("- 영상이 다른 채널의 것이라면 channel_id가 100% 잘못된 것")