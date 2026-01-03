# Step 3: 자막 생성 및 조회 요청
import requests
import time


def request_subtitles(data_hash, language='ja'):
    # 자막 생성 요청
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'ko,en;q=0.9,en-US;q=0.8',
        'content-type': 'application/json',
        'origin': 'https://www.languagereactor.com',
        'referer': 'https://www.languagereactor.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    response = requests.post(
        'https://api-cdn.dioco.io/fasr_asc',
        headers=headers,
        json={
            'source': 'UPLOAD',
            'dataHash': data_hash,
            'lang_G': language
        }
    )

    if response.status_code != 200:
        print(f"    [ERROR] API 응답 오류: {response.status_code}")
        print(f"    응답 내용: {response.text}")
        return None

    try:
        return response.json()
    except Exception as e:
        print(f"    [ERROR] JSON 파싱 실패: {e}")
        print(f"    응답 내용: {response.text}")
        return None


def wait_for_subtitles(data_hash, language='ja', max_wait=300, interval=5):
    # 자막 생성 완료까지 대기
    print(f"\n[Step 3] 자막 생성 대기중...")

    elapsed = 0

    while elapsed < max_wait:
        result = request_subtitles(data_hash, language)

        if result is None:
            print(f"\n    [ERROR] API 요청 실패")
            return None

        status = result.get('data', {}).get('status')

        if status == 'COMPLETE':
            subs = result.get('data', {}).get('subs', [])
            print(f"\n    [OK] 자막 생성 완료")
            print(f"    자막 개수: {len(subs)}")
            return result

        print(f"    [INFO] 처리중... ({elapsed}초 경과)", end='\r')
        time.sleep(interval)
        elapsed += interval

    print(f"\n    [ERROR] 타임아웃 ({max_wait}초 초과)")
    return None
