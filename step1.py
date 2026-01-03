# Step 1: dataHash 생성 및 파일 존재 확인
import hashlib
import requests


def generate_data_hash(file_path):
    # 파일의 MD5 해시와 크기로 dataHash 생성
    print(f"[Step 1-1] 파일 읽기: {file_path}")

    with open(file_path, 'rb') as f:
        file_content = f.read()

    md5_hash = hashlib.md5(file_content).hexdigest()
    file_size = len(file_content)
    data_hash = f"{md5_hash}_{file_size}"

    print(f"    MD5: {md5_hash}")
    print(f"    Size: {file_size}")
    print(f"    DataHash: {data_hash}")

    return {
        'dataHash': data_hash,
        'file_content': file_content,
        'md5': md5_hash,
        'size': file_size
    }


def check_file_exists(data_hash):
    # 서버에 파일이 이미 존재하는지 확인
    print(f"\n[Step 1-2] 파일 존재 여부 확인")

    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'ko,en;q=0.9,en-US;q=0.8',
        'content-type': 'application/json',
        'origin': 'https://www.languagereactor.com',
        'referer': 'https://www.languagereactor.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    response = requests.post(
        'https://api-cdn.dioco.io/fasr_ada_UPLOAD',
        headers=headers,
        json={'dataHash': data_hash}
    )

    print(f"    Status: {response.status_code}")
    result = response.json()
    exists = result.get('data', {}).get('exists', False)

    if exists:
        print(f"    [OK] 파일이 이미 서버에 존재함")
    else:
        print(f"    [INFO] 파일 없음 - 업로드 필요")

    return exists
