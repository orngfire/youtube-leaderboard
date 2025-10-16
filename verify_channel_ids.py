#!/usr/bin/env python3
"""
Verify channel IDs by extracting from YouTube page source
"""

import json
import re

# Channels to verify
CHANNELS_TO_CHECK = [
    {
        'name': '전우형',
        'url': 'https://www.youtube.com/@deundeun.papa_1',
        'stored_id': 'UCE_fO6R5HcM86Zyv-oecG_g'
    },
    {
        'name': '서혜리',
        'url': 'https://www.youtube.com/@quick_bite_english',
        'stored_id': 'UC_c2yUaR-70MTy7jy9vdCEA'
    }
]

print("=" * 70)
print("Channel ID Verification")
print("=" * 70)

print("\n📋 Instructions to verify channel IDs manually:")
print("-" * 70)

for i, channel in enumerate(CHANNELS_TO_CHECK, 1):
    print(f"\n{i}. {channel['name']} - {channel['url']}")
    print(f"   Stored ID: {channel['stored_id']}")
    print("\n   To verify:")
    print(f"   a) Open {channel['url']} in browser")
    print("   b) Right-click → View Page Source")
    print("   c) Search for: \"channelId\"")
    print("   d) You should find: \"channelId\":\"UC...\"")
    print("   e) Compare with stored ID above")

print("\n" + "=" * 70)
print("Alternative Method: Using YouTube Data API Explorer")
print("=" * 70)

print("\n1. Go to: https://developers.google.com/youtube/v3/docs/channels/list")
print("2. Click 'Try this API'")
print("3. Set parameters:")
print("   - part: statistics,snippet")

for channel in CHANNELS_TO_CHECK:
    print(f"\n   For {channel['name']}:")
    print(f"   - id: {channel['stored_id']}")
    print("   Execute and check if response contains subscriberCount")

print("\n" + "=" * 70)
print("Possible Issues")
print("=" * 70)

print("\n1. Wrong Channel ID:")
print("   - The stored channel ID might be incorrect")
print("   - Solution: Update channels.json with correct ID")

print("\n2. Hidden Subscriber Count:")
print("   - Channel owner may have hidden subscriber count")
print("   - In API response: \"hiddenSubscriberCount\": true")

print("\n3. API Permissions:")
print("   - API key might not have proper permissions")
print("   - Some channels require OAuth authentication")

print("\n4. Regional Restrictions:")
print("   - Some channels might be region-restricted")

# Check current channels.json
print("\n" + "=" * 70)
print("Current channels.json entries:")
print("=" * 70)

try:
    with open('channels.json', 'r', encoding='utf-8') as f:
        channels = json.load(f)

    for channel_data in CHANNELS_TO_CHECK:
        print(f"\n🔍 {channel_data['name']}:")
        found = False
        for ch in channels:
            if ch.get('channel_url') == channel_data['url']:
                found = True
                print(f"   URL: {ch.get('channel_url')}")
                print(f"   ID: {ch.get('channel_id')}")
                if ch.get('channel_id') != channel_data['stored_id']:
                    print(f"   ⚠️ MISMATCH! Expected: {channel_data['stored_id']}")
                break
        if not found:
            print("   ❌ Not found in channels.json")

except FileNotFoundError:
    print("❌ channels.json not found")

print("\n" + "=" * 70)
print("Next Steps:")
print("=" * 70)
print("\n1. Manually verify the channel IDs using the instructions above")
print("2. If IDs are wrong, update channels.json")
print("3. If IDs are correct, check API response for hiddenSubscriberCount")
print("4. Consider adding fallback: show 'Hidden' instead of 0 for private counts")