import sys
import os
import uuid
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLineEdit, QLabel, 
                            QSlider, QGroupBox, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
import yt_dlp
import music
import tempfile

class DownloadThread(QThread):
    finished = pyqtSignal(tuple)
    error = pyqtSignal(str)

    def __init__(self, youtube_link):
        super().__init__()
        self.youtube_link = youtube_link

    def run(self):
        try:
            uu = str(uuid.uuid4())
            with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 
                                 'outtmpl': 'uploaded_files/' + uu + '.%(ext)s',
                                 "quiet": True, 
                                 "noplaylist": True}) as ydl:
                info_dict = ydl.extract_info(self.youtube_link, download=True)
                audio_file = ydl.prepare_filename(info_dict)
                song_name = info_dict['title']
                mp3_file_base = music.msc_to_mp3_inf(audio_file)
                self.finished.emit((audio_file, mp3_file_base, song_name))
        except Exception as e:
            self.error.emit(str(e))

class LoFiConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LoFi Converter")
        self.setMinimumSize(800, 600)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # YouTube URL input
        url_group = QGroupBox("YouTube URL")
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter YouTube URL here...")
        url_layout.addWidget(self.url_input)
        url_group.setLayout(url_layout)
        layout.addWidget(url_group)
        
        # Advanced settings
        settings_group = QGroupBox("Advanced Settings")
        settings_layout = QVBoxLayout()
        
        # Room size
        self.room_size_slider = self.create_slider("Reverb Room Size", 0.1, 1.0, 0.75, 0.1)
        settings_layout.addWidget(self.room_size_slider)
        
        # Damping
        self.damping_slider = self.create_slider("Reverb Damping", 0.1, 1.0, 0.5, 0.1)
        settings_layout.addWidget(self.damping_slider)
        
        # Wet level
        self.wet_level_slider = self.create_slider("Reverb Wet Level", 0.0, 1.0, 0.08, 0.01)
        settings_layout.addWidget(self.wet_level_slider)
        
        # Dry level
        self.dry_level_slider = self.create_slider("Reverb Dry Level", 0.0, 1.0, 0.2, 0.01)
        settings_layout.addWidget(self.dry_level_slider)
        
        # Delay
        self.delay_slider = self.create_slider("Delay (ms)", 0, 20, 2, 1)
        settings_layout.addWidget(self.delay_slider)
        
        # Slow factor
        self.slow_factor_slider = self.create_slider("Slow Factor", 0.0, 0.2, 0.08, 0.01)
        settings_layout.addWidget(self.slow_factor_slider)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Convert button
        self.convert_btn = QPushButton("Convert to LoFi")
        self.convert_btn.clicked.connect(self.start_conversion)
        layout.addWidget(self.convert_btn)
        
        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        # Create uploaded_files directory if it doesn't exist
        os.makedirs("uploaded_files", exist_ok=True)
        
        self.download_thread = None
        self.current_files = None

    def create_slider(self, name, min_val, max_val, default, step):
        group = QWidget()
        layout = QHBoxLayout()
        label = QLabel(f"{name}: {default}")
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(int(min_val * 100))
        slider.setMaximum(int(max_val * 100))
        slider.setValue(int(default * 100))
        slider.setSingleStep(int(step * 100))
        
        slider.valueChanged.connect(
            lambda v: label.setText(f"{name}: {v/100:.2f}")
        )
        
        layout.addWidget(label)
        layout.addWidget(slider)
        group.setLayout(layout)
        return group

    def get_slider_value(self, slider):
        return slider.findChild(QSlider).value() / 100

    def start_conversion(self):
        youtube_link = self.url_input.text().strip()
        if not youtube_link:
            QMessageBox.warning(self, "Error", "Please enter a YouTube URL")
            return
        
        self.status_label.setText("Downloading and converting...")
        self.convert_btn.setEnabled(False)
        
        self.download_thread = DownloadThread(youtube_link)
        self.download_thread.finished.connect(self.on_download_complete)
        self.download_thread.error.connect(self.on_download_error)
        self.download_thread.start()

    def on_download_complete(self, result):
        audio_file, mp3_file_base, song_name = result
        self.current_files = (audio_file, mp3_file_base, song_name)
        
        # Get settings from sliders
        room_size = self.get_slider_value(self.room_size_slider)
        damping = self.get_slider_value(self.damping_slider)
        wet_level = self.get_slider_value(self.wet_level_slider)
        dry_level = self.get_slider_value(self.dry_level_slider)
        delay = self.get_slider_value(self.delay_slider)
        slow_factor = self.get_slider_value(self.slow_factor_slider)
        
        # Process the audio
        output_file = os.path.splitext(audio_file)[0] + "_lofi.wav"
        music.slowedreverb(audio_file, output_file, room_size, damping, 
                          wet_level, dry_level, delay, slow_factor)
        
        # Convert to MP3 for download
        mp3_output = music.msc_to_mp3_inf(output_file)
        
        # Save the file
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save LoFi MP3", 
            f"{song_name}_lofi.mp3",
            "MP3 Files (*.mp3)"
        )
        
        if save_path:
            with open(save_path, 'wb') as f:
                f.write(mp3_output)
            self.status_label.setText(f"Successfully saved to {save_path}")
        else:
            self.status_label.setText("Conversion complete but file not saved")
        
        self.convert_btn.setEnabled(True)
        
        # Clean up temporary files
        try:
            os.remove(audio_file)
            os.remove(output_file)
        except:
            pass

    def on_download_error(self, error_msg):
        self.status_label.setText(f"Error: {error_msg}")
        self.convert_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Failed to process video: {error_msg}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LoFiConverterApp()
    window.show()
    sys.exit(app.exec()) 