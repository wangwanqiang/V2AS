import os
import subprocess
from pathlib import Path

def add_lyrics_to_mp3_with_ffmpeg(mp3_path, lrc_path):
    """Use ffmpeg to add synchronized lyrics to MP3 file"""
    # Create a temporary file path
    temp_mp3 = mp3_path + ".tmp.mp3"
    
    # Use ffmpeg to add lyrics metadata
    command = [
        'ffmpeg',
        '-i', mp3_path,
        '-i', lrc_path,
        '-c', 'copy',
        '-metadata', 'lyrics',
        '-y',
        temp_mp3
    ]
    
    try:
        # Try to read LRC content and add as metadata
        with open(lrc_path, 'r', encoding='utf-8') as f:
            lyrics_content = f.read()
        
        # Remove LRC timestamps for simple lyrics metadata
        import re
        plain_lyrics = re.sub(r'\[\d{2}:\d{2}\.\d{2}\]', '', lyrics_content)
        plain_lyrics = '\n'.join([line.strip() for line in plain_lyrics.split('\n') if line.strip()])
        
        command = [
            'ffmpeg',
            '-i', mp3_path,
            '-metadata', f'lyrics={plain_lyrics}',
            '-c', 'copy',
            '-y',
            temp_mp3
        ]
        
        subprocess.run(command, check=True, capture_output=True, text=True)
        
        # Replace original file
        if os.path.exists(temp_mp3):
            os.remove(mp3_path)
            os.rename(temp_mp3, mp3_path)
            return True
        
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
    except Exception as e:
        print(f"Error: {e}")
    
    return False

def add_sylt_with_python(mp3_path, lrc_path):
    """Use mutagen to add SYLT tag"""
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, SYLT, USLT
    
    try:
        # Read LRC file
        with open(lrc_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        lyrics = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse LRC format: [mm:ss.xx]text
            if line.startswith('[') and ']' in line:
                try:
                    timestamp_str = line[1:line.index(']')]
                    text = line[line.index(']')+1:]
                    
                    if ':' in timestamp_str and '.' in timestamp_str:
                        parts = timestamp_str.split(':')
                        minutes = int(parts[0])
                        seconds = float(parts[1])
                        ms = int((minutes * 60 + seconds) * 1000)
                        
                        if text:
                            lyrics.append((ms, text))
                except:
                    pass
        
        if not lyrics:
            return False
        
        # Load MP3 and add tags
        audio = MP3(mp3_path, ID3=ID3)
        
        if audio.tags is None:
            audio.add_tags()
        
        # Try different SYLT formats
        for format_type in [2, 1]:  # Try millisecond and other formats
            try:
                # Prepare data - SYLT needs individual timestamp and text parameters
                times_list = []
                text_list = []
                for ms, text in lyrics:
                    times_list.append(ms)
                    text_list.append(text)
                
                # Create SYLT frame
                sylt_frame = SYLT(
                    encoding=3,  # UTF-8
                    lang='eng',
                    desc='Lyrics',
                    format=format_type,
                    type=1,
                    text=text_list,
                    times=times_list
                )
                
                audio.tags.add(sylt_frame)
                
                # Add unsynced lyrics as backup
                unsynced_text = "\n".join([item[1] for item in lyrics])
                audio.tags.add(
                    USLT(
                        encoding=3,
                        lang='eng',
                        desc='Lyrics',
                        text=unsynced_text
                    )
                )
                
                audio.save()
                return True
                
            except Exception as e:
                print(f"Format {format_type} failed: {e}")
                # Remove failed frame if it was added
                if audio.tags is not None:
                    for frame in audio.tags.getall('SYLT'):
                        audio.tags.delall('SYLT')
                        break
                continue
        
        return False
        
    except Exception as e:
        print(f"Mutagen error: {e}")
        return False

def process_mp3_files(input_dir):
    """Process all MP3 files and add lyrics from LRC files"""
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
        lrc_filename = mp3_file[:-4] + ".lrc"
        lrc_path = os.path.join(input_dir, lrc_filename)
        
        if not os.path.exists(lrc_path):
            print(f"[{i}/{len(mp3_files)}] SKIP - LRC not found: {lrc_filename}")
            continue
        
        print(f"\n[{i}/{len(mp3_files)}] Processing: {mp3_file}")
        
        # Try to add lyrics using mutagen
        if add_sylt_with_python(mp3_path, lrc_path):
            print(f"OK - Synchronized lyrics added to: {mp3_path}")
            success_count += 1
        else:
            print(f"FAIL - Failed to add lyrics to: {mp3_file}")
    
    print("\n" + "=" * 60)
    print(f"Processing completed! Success: {success_count}/{len(mp3_files)}")
    
    if success_count > 0:
        print("\nTIP: Play the MP3 file in a player that supports lyrics display")
        print("Note: Some players may require the LRC file to be in the same directory")

def main():
    # MP3/LRC directory
    target_dir = os.path.join(os.getcwd(), "mp3_output")
    
    print("=" * 60)
    print("MP3 Synchronized Lyrics Embedder")
    print("=" * 60)
    print()
    
    # Start processing
    process_mp3_files(target_dir)

if __name__ == "__main__":
    main()
