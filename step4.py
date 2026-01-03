# Step 4: 번역 요청
import requests


def translate_subtitles(subs_texts, source_lang='ja', dest_lang='ko'):
    # 자막 번역 요청
    print(f"\n[Step 4] 번역 요청")
    print(f"    자막 개수: {len(subs_texts)}")
    print(f"    {source_lang} -> {dest_lang}")

    # f 값 계산 (핵심 공식)
    f_value = (len(subs_texts) % 56) + 17
    print(f"    f 값: {f_value}")

    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'ko,en;q=0.9,en-US;q=0.8',
        'content-type': 'application/json',
        'origin': 'https://www.languagereactor.com',
        'priority': 'u=1, i',
        'referer': 'https://www.languagereactor.com/',
        'sec-ch-ua': '"Microsoft Edge";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    json_data = {
        'AZ1_sha256': 'AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBxMTEhUSEhMWFhUXF',
        'subs': subs_texts,
        'langCode_G': source_lang,
        'destLangCode_G': dest_lang,
        'f': f_value,
    }

    response = requests.post(
        'https://api-cdn.dioco.io/base_media_videoFileTranslations',
        headers=headers,
        json=json_data
    )

    print(f"    Status: {response.status_code}")
    result = response.json()

    if result.get('status') == 'success':
        translations = result.get('data', {}).get('subs', [])
        print(f"    [OK] 번역 완료")
        print(f"    번역 개수: {len(translations)}")
        return result
    else:
        print(f"    [ERROR] 번역 실패")
        return None
