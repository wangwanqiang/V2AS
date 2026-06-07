import os
import whisper
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, SYLT, USLT
from pathlib import Path

def transcribe_with_timestamps(audio_path, model_size="base"):
    """Use Whisper model to transcribe audio with timestamps"""
    print(f"Loading Whisper model ({model_size})...")
    model = whisper.load_model(model_size)
    print(f"Transcribing: {audio_path}")
    result = model.transcribe(audio_path, language="en", word_timestamps=False)
    return result["segments"]

def format_timestamp(seconds):
    """Convert seconds to LRC format timestamp [mm:ss.xx]"""
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"[{minutes:02d}:{secs:05.2f}]"

def generate_lrc(segments):
    """Generate LRC format lyrics content"""
    lrc_lines = []
    
    for segment in segments:
        start_time = segment["start"]
        text = segment["text"].strip()
        
        if text:
            timestamp = format_timestamp(start_time)
            lrc_lines.append(f"{timestamp}{text}")
    
    return "\n".join(lrc_lines)

def add_synced_lyrics_to_mp3(mp3_path, segments):
    """Add synchronized lyrics to MP3 file SYLT tag"""
    try:
        audio = MP3(mp3_path, ID3=ID3)
        
        if audio.tags is None:
            audio.add_tags()
        
        # Prepare synchronized lyrics data
        # SYLT format: list of (timestamp_ms, text) tuples
        sync_lyrics = []
        for segment in segments:
            start_time = int(segment["start"] * 1000)  # Convert to milliseconds
            text = segment["text"].strip()
            
            if text:
                # Create SYLT entry with timestamp and text
                sync_lyrics.append((start_time, text))
        
        if sync_lyrics:
            # Separate timestamps and texts for SYLT
            times = [str(item[0]) for item in sync_lyrics]
            texts = [item[1] for item in sync_lyrics]
            
            # Add synchronized lyrics tag (SYLT)
            audio.tags.add(
                SYLT(
                    encoding=3,  # UTF-8
                    lang='eng',
                    desc='Lyrics',
                    format=2,  # Milliseconds
                    type=1,  # Lyrics
                    text=texts,
                    times=times
                )
            )
            
            # Also add unsynced lyrics as backup (USLT)
            unsynced_text = "\n".join([seg["text"].strip() for seg in segments if seg["text"].strip()])
            audio.tags.add(
                USLT(
                    encoding=3,
                    lang='eng',
                    desc='Lyrics',
                    text=unsynced_text
                )
            )
        
        audio.save()
        print(f"OK - Synchronized lyrics added to: {mp3_path}")
        return True
    except Exception as e:
        print(f"FAIL - Failed to add lyrics: {mp3_path}, Error: {e}")
        return False

def save_lrc_file(mp3_path, lrc_content, output_dir):
    """Save LRC format lyrics to text file"""
    filename = Path(mp3_path).stem
    lrc_path = os.path.join(output_dir, f"{filename}.lrc")
    
    try:
        with open(lrc_path, 'w', encoding='utf-8') as f:
            f.write(lrc_content)
        print(f"OK - LRC lyrics saved to: {lrc_path}")
    except Exception as e:
        print(f"FAIL - Failed to save LRC file: {lrc_path}, Error: {e}")

def process_mp3_files(input_dir, save_lrc=True, model_size="base"):
    """Process all MP3 files in directory"""
    if not os.path.exists(input_dir):
        print(f"ERROR - Directory not found: {input_dir}")
        return
    
    mp3_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.mp3')]
    
    if not mp3_files:
        print(f"INFO - No MP3 files found in {input_dir}")
        return
    
    print(f"Found {len(mp3_files)} MP3 files")
    print("=" * 60)
    
    success_count = 0
    for i, mp3_file in enumerate(mp3_files, 1):
        mp3_path = os.path.join(input_dir, mp3_file)
        print(f"\n[{i}/{len(mp3_files)}] Processing: {mp3_file}")
        
        try:
            # Transcribe audio and get timestamps
            segments = transcribe_with_timestamps(mp3_path, model_size)
            
            if segments:
                # Generate LRC format lyrics
                lrc_content = generate_lrc(segments)
                print(f"Detected {len(segments)} segments")
                
                # Add synchronized lyrics to MP3 metadata
                if add_synced_lyrics_to_mp3(mp3_path, segments):
                    success_count += 1
                
                # Save LRC file
                if save_lrc:
                    save_lrc_file(mp3_path, lrc_content, input_dir)
            else:
                print(f"WARNING - No speech content detected")
                
        except Exception as e:
            print(f"ERROR - Failed to process: {mp3_file}, Error: {e}")
    
    print("\n" + "=" * 60)
    print(f"Processing completed! Success: {success_count}/{len(mp3_files)}")
    print("\nTIP: Play the MP3 file in a player that supports lyrics display to see synchronized lyrics")

def main():
    # MP3 directory
    mp3_dir = os.path.join(os.getcwd(), "mp3_output")
    
    print("=" * 60)
    print("MP3 Synchronized Lyrics Generator")
    print("=" * 60)
    print("Features:")
    print("  1. Use Whisper AI to transcribe speech from MP3")
    print("  2. Generate LRC format lyrics with timestamps")
    print("  3. Embed synchronized lyrics into MP3 metadata")
    print("=" * 60)
    print()
    
    # Select Whisper model size
    # Options: "tiny", "base", "small", "medium", "large"
    # Larger = more accurate but slower
    model_size = "base"
    
    # Start processing
    process_mp3_files(mp3_dir, save_lrc=True, model_size=model_size)

if __name__ == "__main__":
    main()
