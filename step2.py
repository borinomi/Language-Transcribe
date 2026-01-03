# Step 2: 파일 업로드 (exists가 false인 경우만)
import requests


def upload_file(file_content, data_hash):
    # 오디오/비디오 파일을 서버에 업로드
    print(f"\n[Step 2] 파일 업로드")

    headers = {
        'accept': '*/*',
        'accept-language': 'ko,en;q=0.9,en-US;q=0.8',
        'content-type': 'application/octet-stream',
        'origin': 'https://www.languagereactor.com',
        'referer': 'https://www.languagereactor.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    response = requests.post(
        f'https://api.dioco.io/fasr_uploadAudio?dataHash={data_hash}',
        headers=headers,
        data=file_content
    )

    print(f"    Status: {response.status_code}")

    if response.status_code == 200:
        print(f"    [OK] 업로드 완료")
        return response.json()
    else:
        print(f"    [ERROR] 업로드 실패")
        return None
