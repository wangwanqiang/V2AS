import os
import subprocess
from pathlib import Path

def extract_audio_from_video(input_file, output_dir):
    """
    从视频文件中提取音频并保存为MP3格式
    :param input_file: 输入的视频文件路径
    :param output_dir: 输出目录
    """
    # 获取文件名（不含扩展名）
    file_name = Path(input_file).stem
    output_file = os.path.join(output_dir, f"{file_name}.mp3")
    
    # 使用ffmpeg提取音频
    command = [
        'ffmpeg',
        '-i', input_file,
        '-q:a', '0',
        '-map', 'a',
        '-y',
        output_file
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ 成功提取: {input_file} -> {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 提取失败: {input_file}")
        print(f"错误信息: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ 错误：未找到ffmpeg，请确保ffmpeg已安装并添加到系统PATH中")
        return False

def main():
    # 当前目录
    current_dir = os.getcwd()
    
    # 输出目录
    output_dir = os.path.join(current_dir, "mp3_output")
    
    # 如果输出目录不存在，创建它
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 创建输出目录: {output_dir}")
    
    # 支持的视频格式
    video_extensions = ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.m4v', '.webm')
    
    # 查找所有视频文件
    video_files = [f for f in os.listdir(current_dir) if f.lower().endswith(video_extensions)]
    
    if not video_files:
        print("ℹ️ 当前目录没有找到视频文件")
        return
    
    print(f"🔍 找到 {len(video_files)} 个视频文件")
    
    # 处理每个视频文件
    success_count = 0
    for video_file in video_files:
        input_path = os.path.join(current_dir, video_file)
        if extract_audio_from_video(input_path, output_dir):
            success_count += 1
    
    print(f"\n📊 处理完成！成功: {success_count}/{len(video_files)}")

if __name__ == "__main__":
    main()
