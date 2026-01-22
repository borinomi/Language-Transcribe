# Language Reactor 자막 생성 및 번역 메인 프로그램
import os
import sys
import argparse

from step1 import generate_data_hash, check_file_exists
from step2 import upload_file
from step3 import wait_for_subtitles
from step4 import translate_subtitles
from srt_build import parse_srt


def ms_to_srt_time(ms):
    # 밀리초를 SRT 시간 형식으로 변환
    seconds = ms / 1000
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((ms % 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def create_srt(subs, originals, translations, output_path, mode='orig'):
    # SRT 파일 생성 (원본 + 번역)
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, (sub, orig, trans) in enumerate(zip(subs, originals, translations), 1):
            start_time = ms_to_srt_time(sub['begin'])
            end_time = ms_to_srt_time(sub['end'])

            f.write(f"{i}\n")
            f.write(f"{start_time} --> {end_time}\n")
            
            if mode == 'orig':
                f.write(f"{orig}\n")
            
            elif mode == 'dual':
                f.write(f"{orig}\n")
                if trans:
                    f.write(f"({trans})\n")

            elif mode == 'trans':
                if trans:
                    f.write(f"{trans}\n")
                else:
                    f.write(f"{orig}\n")
            
            f.write(f"\n")

    print(f"[OK] SRT 파일 생성: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Language Reactor 자막 생성 & 번역')
    parser.add_argument('file_path', help='오디오/비디오 파일 경로')
    parser.add_argument('--source', default='ja', help='원본 언어 (기본: ja)')
    parser.add_argument('--dest', default='ko', help='번역 대상 언어 (기본: ko)')
    parser.add_argument('--no-translate', action='store_true', help='번역 건너뛰기')
    parser.add_argument('--temp-audio', action='store_true', help='임시 오디오 파일 (완료 후 삭제)')
    parser.add_argument('--subtitle-mode', choices=['orig', 'dual', 'trans'], default='orig', help='자막 출력 방식: orig(원어), dual(원어+번역), trans(번역만)')
    parser.add_argument('--external-srt', action='store_true', help='기존 SRT 사용 (파일명 동일한 .srt)')

    args = parser.parse_args()
    mode = args.subtitle_mode

    if not os.path.exists(args.file_path):
        print(f"[ERROR] 파일이 존재하지 않습니다: {args.file_path}")
        sys.exit(1)

    file_path = os.path.abspath(args.file_path)
    file_dir = os.path.dirname(file_path)
    file_name = os.path.splitext(os.path.basename(file_path))[0]

    print("="*60)
    print("Language Reactor 자막 생성 및 번역")
    print("="*60)
    print(f"파일: {file_path}")
    print(f"언어: {args.source} -> {args.dest}")
    print("="*60)

    try:
        # Step 1
        hash_info = generate_data_hash(file_path)
        exists = check_file_exists(hash_info['dataHash'])

        # Step 2
        if not exists:
            upload_file(hash_info['file_content'], hash_info['dataHash'])
        else:
            print("\n[INFO] Step 2 건너뜀 (파일이 이미 존재)")

        # Step 3
        if args.external_srt:
            srt_path = os.path.splitext(file_path)[0] + '.srt'

            if not os.path.exists(srt_path):
                print(f"[ERROR] SRT 파일 없음: {srt_path}")
                sys.exit(1)

            subs, subs_texts = parse_srt(srt_path)

        else:
            subtitle_result = wait_for_subtitles(hash_info['dataHash'], args.source)
            if not subtitle_result:
                print("[ERROR] 자막 생성 실패")
                sys.exit(1)

            subs = subtitle_result['data']['subs']
            subs_texts = [sub['text'] for sub in subs]

        # Step 4
        if not args.no_translate:
            translation_result = translate_subtitles(subs_texts, args.source, args.dest)
            if translation_result:
                translations = translation_result['data']['subs']
            else:
                translations = None
        else:
            translations = None

        # SRT 파일 저장 (원본 파일명과 동일하게)
        if mode == "trans":
            output_path = os.path.join(file_dir, f"{file_name}_{args.dest}.srt")
        else:
            output_path = os.path.join(file_dir, f"{file_name}.srt")

        if translations:
            create_srt(subs, subs_texts, translations, output_path, mode)
        else:
            create_srt(subs, subs_texts, [None]*len(subs_texts), output_path, mode)

        print("\n" + "="*60)
        print("[OK] 모든 작업 완료")
        print("="*60)

        # 임시 오디오 파일 삭제
        if args.temp_audio:
            try:
                os.remove(file_path)
                print(f"[INFO] 임시 오디오 파일 삭제: {file_path}")
            except Exception as e:
                print(f"[WARNING] 임시 파일 삭제 실패: {e}")

    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")
        # 오류 발생 시에도 임시 파일 삭제 시도
        if args.temp_audio and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"[INFO] 임시 오디오 파일 삭제: {file_path}")
            except:
                pass
        sys.exit(1)


if __name__ == '__main__':
    main()
