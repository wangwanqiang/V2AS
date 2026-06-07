import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, SYLT, USLT
from pathlib import Path

def read_lrc_file(lrc_path):
    """Read LRC file and parse timestamps and lyrics"""
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
                # Extract timestamp and text
                timestamp_str = line[1:line.index(']')]
                text = line[line.index(']')+1:]
                
                # Parse timestamp to milliseconds
                if ':' in timestamp_str and '.' in timestamp_str:
                    parts = timestamp_str.split(':')
                    minutes = int(parts[0])
                    seconds = float(parts[1])
                    ms = int((minutes * 60 + seconds) * 1000)
                    
                    if text:
                        lyrics.append((ms, text))
            except:
                pass
    
    return lyrics

def add_synced_lyrics_to_mp3(mp3_path, lyrics):
    """Add synchronized lyrics to MP3 file SYLT tag"""
    try:
        audio = MP3(mp3_path, ID3=ID3)
        
        if audio.tags is None:
            audio.add_tags()
        
        if lyrics:
            # Separate timestamps and texts for SYLT
            times = [str(item[0]) for item in lyrics]
            texts = [item[1] for item in lyrics]
            
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
        print(f"OK - Synchronized lyrics added to: {mp3_path}")
        return True
    except Exception as e:
        print(f"FAIL - Failed to add lyrics: {mp3_path}, Error: {e}")
        return False

def process_lrc_files(input_dir):
    """Process all LRC files and add lyrics to corresponding MP3 files"""
    if not os.path.exists(input_dir):
        print(f"ERROR - Directory not found: {input_dir}")
        return
    
    lrc_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.lrc')]
    
    if not lrc_files:
        print(f"INFO - No LRC files found in {input_dir}")
        return
    
    print(f"Found {len(lrc_files)} LRC files")
    print("=" * 60)
    
    success_count = 0
    for i, lrc_file in enumerate(lrc_files, 1):
        lrc_path = os.path.join(input_dir, lrc_file)
        mp3_filename = lrc_file[:-4] + ".mp3"  # Replace .lrc with .mp3
        mp3_path = os.path.join(input_dir, mp3_filename)
        
        if not os.path.exists(mp3_path):
            print(f"SKIP - MP3 file not found: {mp3_filename}")
            continue
        
        print(f"\n[{i}/{len(lrc_files)}] Processing: {lrc_file}")
        
        try:
            # Read LRC file
            lyrics = read_lrc_file(lrc_path)
            print(f"Found {len(lyrics)} lyric lines")
            
            # Add synchronized lyrics to MP3
            if add_synced_lyrics_to_mp3(mp3_path, lyrics):
                success_count += 1
                
        except Exception as e:
            print(f"ERROR - Failed to process: {lrc_file}, Error: {e}")
    
    print("\n" + "=" * 60)
    print(f"Processing completed! Success: {success_count}/{len(lrc_files)}")
    print("\nTIP: Play the MP3 file in a player that supports lyrics display to see synchronized lyrics")

def main():
    # MP3/LRC directory
    target_dir = os.path.join(os.getcwd(), "mp3_output")
    
    print("=" * 60)
    print("MP3 Synchronized Lyrics Embedder")
    print("=" * 60)
    print("This script reads existing LRC files and embeds the")
    print("synchronized lyrics into the corresponding MP3 files.")
    print("=" * 60)
    print()
    
    # Start processing
    process_lrc_files(target_dir)

if __name__ == "__main__":
    main()
