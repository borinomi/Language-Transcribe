"""
FastAPI wrapper for LanguageReactor subtitle generation and translation.
Designed for n8n integration with shared /workspace volume.
"""
import os
import subprocess
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from step1 import generate_data_hash, check_file_exists
from step2 import upload_file
from step3 import wait_for_subtitles
from step4 import translate_subtitles
from srt_build import parse_srt

# Constants
WORKSPACE_DIR = Path("/workspace")
SUPPORTED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}

app = FastAPI(title="LanguageReactor API", version="1.0.0")


class TranscribeRequest(BaseModel):
    filename: str
    source_lang: str = "ja"
    target_lang: str = "ko"
    mode: str = "orig"  # "orig", "dual", or "trans"


class TranscribeResponse(BaseModel):
    success: bool
    output_filename: str
    output_path: str
    used_external_srt: bool
    subtitle_count: int
    message: Optional[str] = None


def ms_to_srt_time(ms):
    """Convert milliseconds to SRT time format."""
    seconds = ms / 1000
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((ms % 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def create_srt_content(subs, originals, translations, mode='orig'):
    """Generate SRT file content."""
    lines = []
    for i, (sub, orig, trans) in enumerate(zip(subs, originals, translations), 1):
        start_time = ms_to_srt_time(sub['begin'])
        end_time = ms_to_srt_time(sub['end'])

        lines.append(f"{i}")
        lines.append(f"{start_time} --> {end_time}")
        
        if mode == 'orig':
            lines.append(orig)
        elif mode == 'dual':
            lines.append(orig)
            if trans:
                lines.append(f"({trans})")
        elif mode == 'trans':
            if trans:
                lines.append(trans)
            else:
                lines.append(orig)
        
        lines.append("")  # Empty line between subtitles
    
    return "\n".join(lines)


def extract_audio_from_video(video_path: Path, output_audio_path: Path) -> bool:
    """Extract audio from video file using ffmpeg."""
    try:
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-vn',  # No video
            '-ac', '1',  # Mono
            '-ar', '16000',  # Sample rate
            '-af', 'aresample=async=1:first_pts=0',
            '-c:a', 'libopus',
            '-b:a', '32k',
            '-y',  # Overwrite
            str(output_audio_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"[INFO] Audio extracted: {output_audio_path}")
            return True
        else:
            print(f"[ERROR] FFmpeg failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] Failed to extract audio: {e}")
        return False


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "LanguageReactor API"}


@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(request: TranscribeRequest):
    """
    Generate or translate subtitles for audio/video files.
    
    Automatically detects if a matching .srt file exists in /workspace.
    If found, skips ASR and uses the existing subtitle file.
    """
    filename = request.filename
    source_lang = request.source_lang
    target_lang = request.target_lang
    mode = request.mode
    
    # Validate mode
    if mode not in ['orig', 'dual', 'trans']:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {mode}. Must be 'orig', 'dual', or 'trans'")
    
    # Build paths
    input_path = WORKSPACE_DIR / filename
    file_stem = input_path.stem
    file_ext = input_path.suffix.lower()
    
    if not input_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    
    # Check for external SRT file
    srt_path = WORKSPACE_DIR / f"{file_stem}.srt"
    has_external_srt = srt_path.exists()
    
    print(f"[INFO] Processing: {filename}")
    print(f"[INFO] Mode: {mode}")
    print(f"[INFO] Languages: {source_lang} -> {target_lang}")
    print(f"[INFO] External SRT: {has_external_srt}")
    
    try:
        # Handle video files (extract audio)
        audio_path = input_path
        is_video = file_ext in SUPPORTED_VIDEO_EXTENSIONS
        temp_audio_path = None
        
        if is_video:
            print("[INFO] Video file detected, extracting audio...")
            temp_audio_path = WORKSPACE_DIR / f"{file_stem}_temp.ogg"
            if not extract_audio_from_video(input_path, temp_audio_path):
                raise HTTPException(status_code=500, detail="Failed to extract audio from video")
            audio_path = temp_audio_path
        
        # Step 1: Generate hash and check existence
        print("[Step 1] Generating hash and checking existence...")
        hash_info = generate_data_hash(str(audio_path))
        exists = check_file_exists(hash_info['dataHash'])
        
        # Step 2: Upload if not exists
        if not exists:
            print("[Step 2] Uploading audio file...")
            upload_file(hash_info['file_content'], hash_info['dataHash'])
        else:
            print("[Step 2] File already exists on server, skipping upload")
        
        # Step 3: Get subtitles (either from external SRT or ASR)
        if has_external_srt:
            print(f"[Step 3] Using external SRT: {srt_path}")
            subs, subs_texts = parse_srt(str(srt_path))
        else:
            print("[Step 3] Requesting ASR subtitles from API...")
            subtitle_result = wait_for_subtitles(hash_info['dataHash'], source_lang)
            if not subtitle_result:
                raise HTTPException(status_code=500, detail="ASR subtitle generation failed")
            
            subs = subtitle_result['data']['subs']
            subs_texts = [sub['text'] for sub in subs]
        
        print(f"[INFO] Subtitle count: {len(subs)}")
        
        # Step 4: Translate if needed
        translations = []
        if mode in ['dual', 'trans']:
            print(f"[Step 4] Translating subtitles to {target_lang}...")
            translation_result = translate_subtitles(subs_texts, source_lang, target_lang)
            if translation_result:
                translations = translation_result['data']['subs']
            else:
                print("[WARNING] Translation failed, using original text")
                translations = [None] * len(subs_texts)
        else:
            print("[Step 4] Skipping translation (mode=orig)")
            translations = [None] * len(subs_texts)
        
        # Generate output SRT
        srt_content = create_srt_content(subs, subs_texts, translations, mode)
        
        # Save output file
        if mode == "trans":
            output_filename = f"{file_stem}_{target_lang}.srt"
        else:
            output_filename = f"{file_stem}.srt"
        
        output_path = WORKSPACE_DIR / output_filename
        output_path.write_text(srt_content, encoding='utf-8')
        
        print(f"[OK] Output saved: {output_path}")
        
        # Clean up temporary audio file
        if temp_audio_path and temp_audio_path.exists():
            temp_audio_path.unlink()
            print(f"[INFO] Cleaned up temp audio: {temp_audio_path}")
        
        return TranscribeResponse(
            success=True,
            output_filename=output_filename,
            output_path=str(output_path),
            used_external_srt=has_external_srt,
            subtitle_count=len(subs),
            message="Subtitles generated successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
