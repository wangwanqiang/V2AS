import os
import re
import eyeD3

def parse_lrc_file(lrc_path):
    """Parse LRC file and return list of (timestamp_ms, text) tuples"""
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
    
    return lyrics

def add_synced_lyrics_to_mp3(mp3_path, lrc_path):
    """Add synchronized lyrics to MP3 file using eyeD3"""
    try:
        # Check if eyeD3 can handle the file
        if not eyeD3.isMp3File(mp3_path):
            return False
        
        # Try to tag the file
        tag = eyeD3.Tag()
        tag.link(mp3_path)
        
        # Read LRC file
        lyrics = parse_lrc_file(lrc_path)
        
        if not lyrics:
            return False
        
        # Add unsynced lyrics (USLT)
        unsynced_text = "\n".join([item[1] for item in lyrics])
        tag.addLyrics(unsynced_text, lang='eng', desc='Lyrics')
        
        # Try to add synchronized lyrics (SYLT)
        try:
            for ms, text in lyrics:
                # Add each line as a synchronized lyrics entry
                # eyeD3 uses seconds for timestamps
                timestamp_sec = ms / 1000.0
                tag.addSyncLyrics(text, timestamp_sec, eyeD3.utils.SyncLyricsType.SYNC_LYRICS, 'eng')
        except Exception as sylt_err:
            print(f"SYLT warning: {sylt_err}")
            # Continue even if SYLT fails - USLT is still useful
        
        # Save the tag
        tag.update()
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
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
        
        if add_synced_lyrics_to_mp3(mp3_path, lrc_path):
            print(f"OK - Lyrics added to: {mp3_path}")
            success_count += 1
        else:
            print(f"FAIL - Failed: {mp3_file}")
    
    print("\n" + "=" * 60)
    print(f"Processing completed! Success: {success_count}/{len(mp3_files)}")
    
    if success_count > 0:
        print("\nTIP: Play the MP3 file in a player that supports lyrics display")
        print("      (e.g., Musicbee, AIMP, foobar2000, or most mobile players)")

def main():
    # MP3/LRC directory
    target_dir = os.path.join(os.getcwd(), "mp3_output")
    
    print("=" * 60)
    print("MP3 Synchronized Lyrics Embedder (using eyeD3)")
    print("=" * 60)
    print()
    
    # Start processing
    process_mp3_files(target_dir)

if __name__ == "__main__":
    main()
