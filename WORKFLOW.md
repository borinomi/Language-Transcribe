# Language Reactor API 워크플로우 분석

## 전체 프로세스

```
1. dataHash 생성 & 파일 존재 확인
   ↓
   exists = false? → 2. 파일 업로드
   exists = true?  → 3. 자막 요청으로 바로 이동
   ↓
3. 자막 생성/조회 요청
   ↓
4. 번역 요청
```

---

## 1단계: dataHash 생성 & 파일 존재 확인

**파일:** `upload_complete.py`, `test1.py`

### 1-1. dataHash 생성

```python
# 파일 읽기
with open(file_path, 'rb') as f:
    file_content = f.read()

# MD5 해시 계산
md5_hash = hashlib.md5(file_content).hexdigest()
file_size = len(file_content)

# dataHash 생성 (핵심!)
dataHash = f"{md5_hash}_{file_size}"
# 예: "5930fdf933c10f51cdac3c557857c611_288328"
```

### 1-2. 파일 존재 여부 확인 (필수!)

**API:** `POST https://api-cdn.dioco.io/fasr_ada_UPLOAD`

**Request:**
```json
{
  "dataHash": "5930fdf933c10f51cdac3c557857c611_288328"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "exists": false  // false: 업로드 필요, true: 이미 존재
  }
}
```

**분기 처리:**
- `exists = false` → **2단계(파일 업로드)로 이동**
- `exists = true` → **3단계(자막 요청)로 바로 이동**

---

## 2단계: 파일 업로드 (exists가 false인 경우만)

**파일:** `upload_complete.py`

**API:** `POST https://api.dioco.io/fasr_uploadAudio?dataHash={dataHash}`

**Request:**
- Content-Type: `application/octet-stream`
- Body: 파일의 raw binary 데이터

**Response:**
```json
{
  "status": "success",
  "data": {
    "dataHash": "5930fdf933c10f51cdac3c557857c611_288328"
  }
}
```

**⚠️ 주의:** exists가 true면 이 단계는 건너뜁니다!

---

## 3단계: 자막 생성/조회 요청

**파일:** `upload_complete.py`, `test2.py`

**API:** `POST https://api-cdn.dioco.io/fasr_asc`

**Request:**
```json
{
  "source": "UPLOAD",
  "dataHash": "5930fdf933c10f51cdac3c557857c611_288328",
  "lang_G": "ja"  // 오디오 언어
}
```

**Response (처음 - 자막 생성 중):**
```json
{
  "status": "success",
  "data": {
    "subs": [
      {
        "begin": 0,
        "end": 17998.367,
        "text": "[ASR loading...]"
      }
    ],
    "segments": [],
    "status": {
      "lastChunkDoneIndex": null,
      "lastChunkIndex": 0
    }
  }
}
```

**Response (완료 후):**
```json
{
  "status": "success",
  "data": {
    "subs": [
      {
        "begin": 2720,
        "end": 4240,
        "text": "お名前を教えてください",
        "lang_G": "ja"
      },
      {
        "begin": 4240,
        "end": 5140,
        "text": "ミサキです",
        "lang_G": "ja"
      }
    ],
    "segments": [
      {
        "begin": 2720,
        "end": 4240,
        "text": "お名前を教えてください",
        "words": [
          {
            "begin": 2720.000000000001,
            "end": 3080.0000000000005,
            "text": "お",
            "probability": 0.1524658203125
          }
        ],
        "lang_G": "ja"
      }
    ],
    "status": "COMPLETE"
  }
}
```

**핵심 데이터:**
- `subs`: 자막 배열 (타임스탬프 + 텍스트)
- `segments`: 단어별 상세 정보
- `status`: "COMPLETE" (완료 상태)

---

## 4단계: 번역 요청

**파일:** `test3.py` 또는 `request_translation.py`

**API:** `POST https://api-cdn.dioco.io/base_media_videoFileTranslations`

### 4-1. 번역 요청 데이터 생성

```python
# 자막에서 text만 추출
subs_texts = [sub['text'] for sub in subtitle_data['data']['subs']]

# f 값 계산 (핵심 공식!)
f = (len(subs_texts) % 56) + 17
```

### 4-2. API 호출

**Request:**
```json
{
  "AZ1_sha256": "AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBxMTEhUSEhMWFhUXF",
  "subs": [
    "お名前を教えてください",
    "ミサキです",
    "年齢は?",
    "21歳です"
  ],
  "langCode_G": "ja",
  "destLangCode_G": "ko",
  "f": 31
}
```

**파라미터 설명:**

| 파라미터 | 설명 | 예시 |
|---------|------|------|
| `AZ1_sha256` | **하드코딩된 고정값** | `"AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBxMTEhUSEhMWFhUXF"` |
| `subs` | 번역할 자막 텍스트 배열 | `["자막1", "자막2", ...]` |
| `langCode_G` | 원본 언어 코드 | `"ja"` (일본어) |
| `destLangCode_G` | 번역 대상 언어 코드 | `"ko"` (한국어) |
| `f` | `(자막개수 % 56) + 17` | 14개 자막 → `(14 % 56) + 17 = 31` |

### 4-3. 응답

**Response:**
```json
{
  "status": "success",
  "data": {
    "subs": [
      "이름을 알려주세요",
      "미사키입니다",
      "나이는?",
      "21살입니다"
    ]
  }
}
```

---

## 핵심 발견 사항

### 1. dataHash 생성 공식
```python
dataHash = f"{MD5(파일내용)}_{파일크기}"
```

### 2. f 값 계산 공식
```python
f = (자막개수 % 56) + 17
```

**검증:**
- 3개 자막: `(3 % 56) + 17 = 20` ✅
- 14개 자막: `(14 % 56) + 17 = 31` ✅
- 1174개 자막: `(1174 % 56) + 17 = 49` ✅

### 3. AZ1_sha256
- **하드코딩된 고정값**
- 값: `"AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBxMTEhUSEhMWFhUXF"`
- 파일마다 다르지 않음

---

## API 엔드포인트 정리

| API | 용도 | Method |
|-----|------|--------|
| `/fasr_ada_UPLOAD` | 파일 존재 여부 확인 | POST |
| `/fasr_uploadAudio` | 오디오 파일 업로드 | POST |
| `/fasr_asc` | 자막 생성 요청 & 조회 | POST |
| `/base_media_videoFileTranslations` | 자막 번역 요청 | POST |

---

## Headers 공통 사항

```python
headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'ko,en;q=0.9,en-US;q=0.8',
    'content-type': 'application/json',
    'origin': 'https://www.languagereactor.com',
    'referer': 'https://www.languagereactor.com/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}
```

---

## 전체 자동화 예시

```python
import time

# 1. dataHash 생성
dataHash = generate_data_hash('audio.mp3')

# 2. 파일 존재 여부 확인
exists = check_file_exists(dataHash)

# 3. 존재하지 않으면 업로드
if not exists:
    upload_file('audio.mp3', dataHash)

# 4. 자막 생성 요청
request_subtitles(dataHash, 'ja')

# 5. 자막 완료될 때까지 대기
while True:
    result = get_subtitles(dataHash, 'ja')
    if result['data']['status'] == 'COMPLETE':
        break
    time.sleep(5)

# 6. 자막 추출
subs_texts = [sub['text'] for sub in result['data']['subs']]

# 7. 번역 요청
translations = translate_subtitles(subs_texts, 'ja', 'ko')
```
