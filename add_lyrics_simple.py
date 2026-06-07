import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, USLT

def read_lrc_file(lrc_path):
    """Read LRC file and extract plain text (without timestamps)"""
    with open(lrc_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Extract text without timestamps
    lyrics_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Remove LRC timestamps: [mm:ss.xx]
        import re
        text = re.sub(r'\[\d{2}:\d{2}\.\d{2}\]', '', line)
        text = text.strip()
        
        if text:
            lyrics_lines.append(text)
    
    return '\n'.join(lyrics_lines)

def add_lyrics_to_mp3(mp3_path, lyrics_text):
    """Add lyrics to MP3 file metadata"""
    try:
        audio = MP3(mp3_path, ID3=ID3)
        
        if audio.tags is None:
            audio.add_tags()
        
        # Add unsynced lyrics (USLT)
        audio.tags.add(
            USLT(
                encoding=3,  # UTF-8
                lang='eng',
                desc='Lyrics',
                text=lyrics_text
            )
        )
        
        audio.save()
        return True
    except Exception as e:
        print(f"Error adding lyrics: {e}")
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
        
        print(f"[{i}/{len(mp3_files)}] Processing: {mp3_file}")
        
        try:
            # Read lyrics from LRC file
            lyrics_text = read_lrc_file(lrc_path)
            
            # Add lyrics to MP3
            if add_lyrics_to_mp3(mp3_path, lyrics_text):
                print(f"  OK - Lyrics added ({len(lyrics_text)} chars)")
                success_count += 1
            else:
                print(f"  FAIL - Could not add lyrics")
                
        except Exception as e:
            print(f"  ERROR - {e}")
    
    print("\n" + "=" * 60)
    print(f"Processing completed! Success: {success_count}/{len(mp3_files)}")
    
    if success_count > 0:
        print("\nTIP: Lyrics have been added to MP3 metadata!")
        print("      You can view them in most music players")
        print("      The LRC files with timestamps are also available")

def main():
    # MP3/LRC directory
    target_dir = os.path.join(os.getcwd(), "mp3_output")
    
    print("=" * 60)
    print("MP3 Lyrics Embedder")
    print("=" * 60)
    print()
    
    # Start processing
    process_mp3_files(target_dir)

if __name__ == "__main__":
    main()
