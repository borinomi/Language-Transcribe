@echo off
chcp 65001 >nul
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

if "%~1"=="" (
    echo 사용법: 파일을 이 bat 파일로 드래그앤드롭하세요.
    pause
    exit /b
)

set INPUT_FILE=%~1
set FILE_EXT=%~x1
set FILE_DIR=%~dp1
set FILE_NAME=%~n1

echo ======================================
echo Language Reactor 자막 생성 및 번역
echo ======================================
echo.
echo 파일: %~nx1
echo.

rem 원본 언어 선택
echo 원본 언어를 선택하세요:
echo   1. 영어 (en)
echo   2. 일본어 (ja)
echo   3. 베트남어 (vi)
echo   4. 한국어 (ko)
echo   5. 중국어 (zh)
echo   6. 스페인어 (es)
echo   7. 프랑스어 (fr)
echo.
set /p SOURCE_CHOICE="번호 선택 (기본: 1): "

if "%SOURCE_CHOICE%"=="" set SOURCE_CHOICE=1
if "%SOURCE_CHOICE%"=="1" set SOURCE_LANG=en
if "%SOURCE_CHOICE%"=="2" set SOURCE_LANG=ja
if "%SOURCE_CHOICE%"=="3" set SOURCE_LANG=vi
if "%SOURCE_CHOICE%"=="4" set SOURCE_LANG=ko
if "%SOURCE_CHOICE%"=="5" set SOURCE_LANG=zh
if "%SOURCE_CHOICE%"=="6" set SOURCE_LANG=es
if "%SOURCE_CHOICE%"=="7" set SOURCE_LANG=fr

if not defined SOURCE_LANG (
    echo [ERROR] 잘못된 선택입니다.
    pause
    exit /b 1
)

echo.
rem 번역 언어 선택
echo 자막 형식을 선택하세요:
echo   1. 받아쓰기 (원본만)
echo   2. 한국어 번역 (원본 + 한국어)
echo.
set /p DEST_CHOICE="번호 선택 (기본: 1): "

if "%DEST_CHOICE%"=="" set DEST_CHOICE=1
if "%DEST_CHOICE%"=="1" (
    set DEST_LANG=ko
    set NO_TRANSLATE=--no-translate
)
if "%DEST_CHOICE%"=="2" (
    set DEST_LANG=ko
    set NO_TRANSLATE=
)

if not defined DEST_LANG (
    echo [ERROR] 잘못된 선택입니다.
    pause
    exit /b 1
)

echo.
echo ======================================
echo 원본 언어: %SOURCE_LANG%
if defined NO_TRANSLATE (
    echo 자막 형식: 받아쓰기 ^(원본만^)
) else (
    echo 자막 형식: 한국어 번역 ^(원본 + 한국어^)
)
echo ======================================
echo.

rem 비디오 파일 확장자 체크
if /i "%FILE_EXT%"==".mp4" goto VIDEO
if /i "%FILE_EXT%"==".avi" goto VIDEO
if /i "%FILE_EXT%"==".mkv" goto VIDEO
if /i "%FILE_EXT%"==".mov" goto VIDEO
if /i "%FILE_EXT%"==".wmv" goto VIDEO
if /i "%FILE_EXT%"==".flv" goto VIDEO
if /i "%FILE_EXT%"==".webm" goto VIDEO
goto AUDIO

:VIDEO
echo [INFO] 비디오 파일 감지 - 오디오 추출중...
set AUDIO_FILE=%FILE_DIR%%FILE_NAME%.mp3
"C:\ffmpeg\bin\ffmpeg.exe" -i "%INPUT_FILE%" -vn -y "%AUDIO_FILE%"
if errorlevel 1 (
    echo [ERROR] 오디오 추출 실패
    pause
    exit /b 1
)
python "%SCRIPT_DIR%main.py" "%AUDIO_FILE%" --source %SOURCE_LANG% --dest %DEST_LANG% %NO_TRANSLATE% --temp-audio
goto END

:AUDIO
python "%SCRIPT_DIR%main.py" "%INPUT_FILE%" --source %SOURCE_LANG% --dest %DEST_LANG% %NO_TRANSLATE%
goto END

:END
pause
