#!/bin/bash

# UTF-8 인코딩 설정
export LANG=ko_KR.UTF-8
export LC_ALL=ko_KR.UTF-8

# 스크립트 디렉토리
SCRIPT_DIR="/Users/hotaekim/Documents/GEMINICLI/MCP/Language-Transcribe"
cd "$SCRIPT_DIR"

INPUT_FILE="$1"

# AppleScript로 언어 선택 다이얼로그
SOURCE_LANG=$(osascript -e 'choose from list {"영어 (en)", "일본어 (ja)", "베트남어 (vi)", "한국어 (ko)", "중국어 (zh)", "스페인어 (es)", "프랑스어 (fr)"} with prompt "원본 언어를 선택하세요:" default items {"영어 (en)"}')

if [ "$SOURCE_LANG" = "false" ]; then
    osascript -e 'display dialog "취소되었습니다." buttons {"확인"} default button 1'
    exit 1
fi

# 언어 코드 추출
case "$SOURCE_LANG" in
    *"영어"*) SOURCE_CODE="en" ;;
    *"일본어"*) SOURCE_CODE="ja" ;;
    *"베트남어"*) SOURCE_CODE="vi" ;;
    *"한국어"*) SOURCE_CODE="ko" ;;
    *"중국어"*) SOURCE_CODE="zh" ;;
    *"스페인어"*) SOURCE_CODE="es" ;;
    *"프랑스어"*) SOURCE_CODE="fr" ;;
    *) SOURCE_CODE="en" ;;
esac

# 번역 옵션 선택
TRANSLATE_OPTION=$(osascript -e 'choose from list {"받아쓰기 (원본만)", "한국어 번역 (원본 + 한국어)"} with prompt "자막 형식을 선택하세요:" default items {"받아쓰기 (원본만)"}')

if [ "$TRANSLATE_OPTION" = "false" ]; then
    osascript -e 'display dialog "취소되었습니다." buttons {"확인"} default button 1'
    exit 1
fi

NO_TRANSLATE=""
if [[ "$TRANSLATE_OPTION" == *"받아쓰기"* ]]; then
    NO_TRANSLATE="--no-translate"
fi

FILE_EXT="${INPUT_FILE##*.}"
FILE_DIR="$(dirname "$INPUT_FILE")"
FILE_NAME="$(basename "$INPUT_FILE" .$FILE_EXT)"
FILE_EXT_LOWER=$(echo "$FILE_EXT" | tr '[:upper:]' '[:lower:]')

echo "======================================"
echo "Language Reactor 자막 생성 및 번역"
echo "======================================"
echo ""
echo "파일: $(basename "$INPUT_FILE")"
echo "원본 언어: $SOURCE_CODE"
echo "번역: $TRANSLATE_OPTION"
echo "======================================"
echo ""

# 비디오 파일 체크
if [[ "$FILE_EXT_LOWER" =~ ^(mp4|avi|mkv|mov|wmv|flv|webm)$ ]]; then
    echo "[INFO] 비디오 파일 감지 - 오디오 추출중..."
    AUDIO_FILE="$FILE_DIR/$FILE_NAME.mp3"
    ffmpeg -i "$INPUT_FILE" -vn -ac 1 -ar 16000 -c:a libmp3lame -b:a 32k -y "$AUDIO_FILE"

    if [ $? -ne 0 ]; then
        echo "[ERROR] 오디오 추출 실패"
        read -p "Press Enter to exit..."
        exit 1
    fi

    python3 "$SCRIPT_DIR/main.py" "$AUDIO_FILE" --source "$SOURCE_CODE" --dest ko $NO_TRANSLATE --temp-audio
else
    python3 "$SCRIPT_DIR/main.py" "$INPUT_FILE" --source "$SOURCE_CODE" --dest ko $NO_TRANSLATE
fi

echo ""
echo "완료되었습니다. 터미널을 닫으려면 Cmd+W를 누르세요."
read -p "또는 Enter를 눌러 종료..."
