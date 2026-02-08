#!/bin/bash

# UTF-8 인코딩 설정
export LANG=ko_KR.UTF-8
export LC_ALL=ko_KR.UTF-8

# 스크립트 디렉토리
SCRIPT_DIR="/Users/hotaekim/Documents/code/Language-Transcribe"
cd "$SCRIPT_DIR"

if [ -z "$1" ]; then
    echo "사용법: 파일을 앱 아이콘으로 드래그앤드롭하세요."
    read -p "Enter를 눌러 종료..."
    exit 1
fi

INPUT_FILE="$1"
FILE_EXT="${INPUT_FILE##*.}"
FILE_DIR="$(dirname "$INPUT_FILE")/"
FILE_NAME="$(basename "$INPUT_FILE" ."$FILE_EXT")"
FILE_EXT_LOWER=$(echo "$FILE_EXT" | tr '[:upper:]' '[:lower:]')

echo "======================================"
echo "Language Reactor 자막 생성 및 번역"
echo "======================================"
echo ""
echo "파일: $(basename "$INPUT_FILE")"
echo ""

# 원본 언어 선택
echo "원본 언어를 선택하세요:"
echo "  1. 영어 (en)"
echo "  2. 일본어 (ja)"
echo "  3. 베트남어 (vi)"
echo "  4. 한국어 (ko)"
echo "  5. 중국어 (zh)"
echo "  6. 스페인어 (es)"
echo "  7. 프랑스어 (fr)"
echo ""
read -p "번호 선택 (기본: 1): " SOURCE_CHOICE

if [ -z "$SOURCE_CHOICE" ]; then SOURCE_CHOICE=1; fi

case "$SOURCE_CHOICE" in
    1) SOURCE_LANG="en" ;;
    2) SOURCE_LANG="ja" ;;
    3) SOURCE_LANG="vi" ;;
    4) SOURCE_LANG="ko" ;;
    5) SOURCE_LANG="zh" ;;
    6) SOURCE_LANG="es" ;;
    7) SOURCE_LANG="fr" ;;
    *)
        echo "[ERROR] 잘못된 선택입니다."
        read -p "Enter를 눌러 종료..."
        exit 1
        ;;
esac

echo ""
# 번역 언어 선택
echo "자막 형식을 선택하세요:"
echo "  1. 받아쓰기 (원본만)"
echo "  2. 한국어 번역 (원본 + 한국어)"
echo "  3. 영어 (en)"
echo "  4. 일본어 (ja)"
echo "  5. 베트남어 (vi)"
echo "  6. 중국어 (zh)"
echo "  7. 스페인어 (es)"
echo "  8. 프랑스어 (fr)"
echo ""
read -p "번호 선택 (기본: 1): " DEST_CHOICE

if [ -z "$DEST_CHOICE" ]; then DEST_CHOICE=1; fi

NO_TRANSLATE=""
MODE=""
DEST_LANG=""

case "$DEST_CHOICE" in
    1) DEST_LANG="ko"; NO_TRANSLATE="--no-translate"; MODE="orig" ;;
    2) DEST_LANG="ko"; MODE="dual" ;;
    3) DEST_LANG="en"; MODE="trans" ;;
    4) DEST_LANG="ja"; MODE="trans" ;;
    5) DEST_LANG="vi"; MODE="trans" ;;
    6) DEST_LANG="zh"; MODE="trans" ;;
    7) DEST_LANG="es"; MODE="trans" ;;
    8) DEST_LANG="fr"; MODE="trans" ;;
    *)
        echo "[ERROR] 잘못된 선택입니다."
        read -p "Enter를 눌러 종료..."
        exit 1
        ;;
esac

echo ""
echo "기존 자막이 있습니까?"
echo "  1. 없음 (음성 인식)"
echo "  2. 있음 (기존 SRT 번역)"
read -p "번호 선택 (기본: 1): " SUB_CHOICE

if [ -z "$SUB_CHOICE" ]; then SUB_CHOICE=1; fi

USE_EXTERNAL_SRT=""
if [ "$SUB_CHOICE" = "2" ]; then
    USE_EXTERNAL_SRT="--external-srt"
fi

echo ""
echo "======================================"
echo "원본 언어: $SOURCE_LANG"
if [ -n "$NO_TRANSLATE" ]; then
    echo "자막 형식: 받아쓰기 (원본만)"
else
    echo "자막 형식: 번역 (원본 + $DEST_LANG)"
fi
echo "======================================"
echo ""

# 비디오 파일 확장자 체크
if [[ "$FILE_EXT_LOWER" =~ ^(mp4|avi|mkv|mov|wmv|flv|webm)$ ]]; then
    echo "[INFO] 비디오 파일 감지 - 오디오 추출중..."
    AUDIO_FILE="${FILE_DIR}${FILE_NAME}.ogg"
    ffmpeg -i "$INPUT_FILE" -vn -ac 1 -ar 16000 -af "aresample=async=1:first_pts=0" -c:a libopus -b:a 32k -y "$AUDIO_FILE"

    if [ $? -ne 0 ]; then
        echo "[ERROR] 오디오 추출 실패"
        read -p "Enter를 눌러 종료..."
        exit 1
    fi

    python3 "${SCRIPT_DIR}/main.py" "$AUDIO_FILE" --source $SOURCE_LANG --dest $DEST_LANG $NO_TRANSLATE --subtitle-mode $MODE $USE_EXTERNAL_SRT --temp-audio
else
    python3 "${SCRIPT_DIR}/main.py" "$INPUT_FILE" --source $SOURCE_LANG --dest $DEST_LANG $NO_TRANSLATE --subtitle-mode $MODE $USE_EXTERNAL_SRT
fi

read -p "Enter를 눌러 종료..."
