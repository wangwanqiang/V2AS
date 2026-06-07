import sys
import os
import subprocess
import re
import webbrowser

# 先导入 torch/whisper，避免与 PyQt5 的 DLL 冲突
try:
    import whisper
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, USLT
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QProgressBar, QTextEdit,
    QFileDialog, QComboBox, QCheckBox, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class WorkerThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, mode, input_path, output_path, model_size="base"):
        super().__init__()
        self.mode = mode
        self.input_path = input_path
        self.output_path = output_path
        self.model_size = model_size
        self.stopped = False
    
    def stop(self):
        self.stopped = True
    
    def run(self):
        try:
            if self.mode == "convert":
                self.convert_mp4_to_mp3()
            elif self.mode == "transcribe":
                self.transcribe_and_add_lyrics()
            self.finished.emit(True, "处理完成")
        except Exception as e:
            self.finished.emit(False, str(e))
    
    def convert_mp4_to_mp3(self):
        mp4_files = [f for f in os.listdir(self.input_path) if f.lower().endswith('.mp4')]
        total = len(mp4_files)
        
        if not mp4_files:
            self.progress.emit(0, "未找到 MP4 文件")
            return
        
        os.makedirs(self.output_path, exist_ok=True)
        
        for i, mp4_file in enumerate(mp4_files, 1):
            if self.stopped:
                return
            
            mp4_path = os.path.join(self.input_path, mp4_file)
            mp3_filename = os.path.splitext(mp4_file)[0] + ".mp3"
            mp3_path = os.path.join(self.output_path, mp3_filename)
            
            self.progress.emit(int(i / total * 100), f"正在转换: {mp4_file}")
            
            # 使用 ffmpeg 转换
            cmd = [
                'ffmpeg', '-i', mp4_path,
                '-q:a', '0', '-map', 'a',
                '-y', mp3_path
            ]
            subprocess.run(cmd, capture_output=True)
    
    def transcribe_and_add_lyrics(self):
        if not WHISPER_AVAILABLE:
            self.progress.emit(0, "Whisper 库未安装")
            return
        
        mp3_files = [f for f in os.listdir(self.input_path) if f.lower().endswith('.mp3')]
        total = len(mp3_files)
        
        if not mp3_files:
            self.progress.emit(0, "未找到 MP3 文件")
            return
        
        # 加载 Whisper 模型
        self.progress.emit(5, f"正在加载 Whisper 模型 ({self.model_size})...")
        model = whisper.load_model(self.model_size)
        
        for i, mp3_file in enumerate(mp3_files, 1):
            if self.stopped:
                return
            
            mp3_path = os.path.join(self.input_path, mp3_file)
            progress = int((i / total) * 95) + 5
            self.progress.emit(progress, f"正在识别: {mp3_file}")
            
            # 转录音频
            result = model.transcribe(mp3_path, language="en")
            
            # 生成 LRC 歌词
            lrc_content = self.generate_lrc(result["segments"])
            lrc_path = os.path.join(self.input_path, os.path.splitext(mp3_file)[0] + ".lrc")
            
            with open(lrc_path, 'w', encoding='utf-8') as f:
                f.write(lrc_content)
            
            # 添加歌词到 MP3
            self.add_lyrics_to_mp3(mp3_path, lrc_content)
    
    def generate_lrc(self, segments):
        lrc_lines = []
        for segment in segments:
            start_time = segment["start"]
            text = segment["text"].strip()
            if text:
                minutes = int(start_time // 60)
                secs = start_time % 60
                timestamp = f"[{minutes:02d}:{secs:05.2f}]"
                lrc_lines.append(f"{timestamp}{text}")
        return "\n".join(lrc_lines)
    
    def add_lyrics_to_mp3(self, mp3_path, lyrics_text):
        audio = MP3(mp3_path, ID3=ID3)
        if audio.tags is None:
            audio.add_tags()
        
        # 移除时间戳
        plain_lyrics = re.sub(r'\[\d{2}:\d{2}\.\d{2}\]', '', lyrics_text)
        plain_lyrics = '\n'.join([line.strip() for line in plain_lyrics.split('\n') if line.strip()])
        
        audio.tags.add(
            USLT(encoding=3, lang='eng', desc='Lyrics', text=plain_lyrics)
        )
        audio.save()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MP4转MP3工具 - 带语音识别")
        self.setGeometry(100, 100, 600, 500)
        
        self.worker_thread = None
        
        self.init_ui()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 模式选择
        mode_group = QGroupBox("操作模式")
        mode_layout = QHBoxLayout(mode_group)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["MP4转MP3", "语音识别添加歌词"])
        mode_layout.addWidget(QLabel("选择操作:"))
        mode_layout.addWidget(self.mode_combo)
        layout.addWidget(mode_group)
        
        # 输入目录
        input_group = QGroupBox("输入设置")
        input_layout = QVBoxLayout(input_group)
        
        self.input_edit = QLineEdit()
        input_btn = QPushButton("浏览...")
        input_btn.clicked.connect(self.browse_input)
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("输入目录:"))
        h_layout.addWidget(self.input_edit)
        h_layout.addWidget(input_btn)
        input_layout.addLayout(h_layout)
        
        # Whisper 模型选择（仅在语音识别模式显示）
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny", "base", "small", "medium", "large"])
        self.model_combo.setCurrentText("base")
        
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Whisper 模型:"))
        model_layout.addWidget(self.model_combo)
        input_layout.addLayout(model_layout)
        
        layout.addWidget(input_group)
        
        # 输出目录
        output_group = QGroupBox("输出设置")
        output_layout = QVBoxLayout(output_group)
        
        self.output_edit = QLineEdit()
        output_btn = QPushButton("浏览...")
        output_btn.clicked.connect(self.browse_output)
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("输出目录:"))
        h_layout.addWidget(self.output_edit)
        h_layout.addWidget(output_btn)
        output_layout.addLayout(h_layout)
        layout.addWidget(output_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 日志区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("开始处理")
        self.start_btn.clicked.connect(self.start_processing)
        btn_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_processing)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)
        
        self.clear_btn = QPushButton("清除日志")
        self.clear_btn.clicked.connect(self.clear_log)
        btn_layout.addWidget(self.clear_btn)
        
        layout.addLayout(btn_layout)
        
        # GitHub 链接
        github_layout = QHBoxLayout()
        github_layout.addStretch()
        github_btn = QPushButton("GitHub 仓库")
        github_btn.clicked.connect(self.open_github)
        github_layout.addWidget(github_btn)
        github_layout.addStretch()
        layout.addLayout(github_layout)
        
        # 连接信号
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        self.on_mode_changed()
    
    def on_mode_changed(self):
        mode = self.mode_combo.currentText()
        if mode == "MP4转MP3":
            self.output_edit.setEnabled(True)
        else:
            self.output_edit.setEnabled(False)
            # 语音识别模式下输出目录等于输入目录
            self.output_edit.setText(self.input_edit.text())
    
    def browse_input(self):
        path = QFileDialog.getExistingDirectory(self, "选择输入目录")
        if path:
            self.input_edit.setText(path)
            if self.mode_combo.currentText() == "语音识别添加歌词":
                self.output_edit.setText(path)
    
    def browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self.output_edit.setText(path)
    
    def log(self, message):
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
    
    def start_processing(self):
        input_path = self.input_edit.text()
        output_path = self.output_edit.text()
        
        if not input_path or not os.path.exists(input_path):
            QMessageBox.warning(self, "错误", "请选择有效的输入目录")
            return
        
        if self.mode_combo.currentText() == "MP4转MP3" and (not output_path or not os.path.exists(output_path)):
            QMessageBox.warning(self, "错误", "请选择有效的输出目录")
            return
        
        # 设置状态
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("处理中...")
        self.log("=" * 50)
        
        mode = "convert" if self.mode_combo.currentText() == "MP4转MP3" else "transcribe"
        model_size = self.model_combo.currentText()
        
        # 创建工作线程
        self.worker_thread = WorkerThread(mode, input_path, output_path, model_size)
        self.worker_thread.progress.connect(self.on_progress)
        self.worker_thread.finished.connect(self.on_finished)
        self.worker_thread.start()
    
    def on_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        self.log(message)
    
    def on_finished(self, success, message):
        self.progress_bar.setValue(100 if success else 0)
        self.status_label.setText(message)
        self.log(message)
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        if success:
            QMessageBox.information(self, "完成", message)
        else:
            QMessageBox.critical(self, "错误", message)
    
    def stop_processing(self):
        if self.worker_thread:
            self.worker_thread.stop()
            self.status_label.setText("正在停止...")
    
    def clear_log(self):
        self.log_text.clear()
    
    def open_github(self):
        webbrowser.open("https://github.com/wangwanqiang/V2AS")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
