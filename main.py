import sys
import speech_recognition as sr
import pyttsx3
import datetime
import os
import subprocess
import webbrowser
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QTextEdit, QPushButton, QLabel, QHBoxLayout, QGraphicsDropShadowEffect,
                            QSystemTrayIcon, QMenu, QAction)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QBrush, QPixmap, QFontDatabase, QIcon
from reminder import ReminderManager
from nlp_processor import NLPProcessor

FONT_PATH = os.path.join(os.path.dirname(__file__), 'resources', 'Orbitron-Regular.ttf')

class ListeningIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 120)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)
        self.pulse = 0
        self.pulse_dir = 1

    def animate(self):
        self.angle = (self.angle + 2) % 360
        self.pulse += self.pulse_dir * 0.5
        if self.pulse > 15 or self.pulse < 0:
            self.pulse_dir *= -1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        center = self.rect().center()
        radius = int(50 + self.pulse)
        # Outer glowing arc
        pen = QPen(QColor(0, 200, 255, 180), 8)
        painter.setPen(pen)
        painter.drawArc(center.x()-radius, center.y()-radius, 2*radius, 2*radius, self.angle*16, 270*16)
        # Inner circle
        brush = QBrush(QColor(0, 120, 255, 220))
        painter.setPen(Qt.NoPen)
        painter.setBrush(brush)
        painter.drawEllipse(center, 30, 30)

class VoiceThread(QThread):
    text_received = pyqtSignal(str)
    hotword_detected = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.is_listening = True
        
    def run(self):
        while self.is_listening:
            try:
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source)
                    audio = self.recognizer.listen(source)
                    text = self.recognizer.recognize_google(audio)
                    if text.lower() == "hey jarvis":
                        self.hotword_detected.emit()
                    else:
                        self.text_received.emit(text)
            except sr.UnknownValueError:
                pass
            except sr.RequestError:
                self.text_received.emit("Error: Could not request results")
            except Exception as e:
                self.text_received.emit(f"Error: {str(e)}")

class JarvisGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.reminder_manager = ReminderManager()
        self.nlp_processor = NLPProcessor()
        self.initUI()
        self.voice_thread = VoiceThread()
        self.voice_thread.text_received.connect(self.process_command)
        self.voice_thread.hotword_detected.connect(self.activate_assistant)
        self.voice_thread.start()
        
    def initUI(self):
        self.setWindowTitle('Jarvis - Voice Assistant')
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QMainWindow {
                background: transparent;
            }
            QTextEdit {
                background-color: #101522;
                color: #00bfff;
                border: 2px solid #00bfff;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
            }
            QPushButton {
                background-color: #0a223a;
                color: #00bfff;
                border: 2px solid #00bfff;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
                min-width: 120px;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #00bfff;
                color: #101522;
            }
            QLabel {
                color: #00bfff;
                font-size: 18px;
            }
        """)
        # Load Orbitron font
        id = QFontDatabase.addApplicationFont(FONT_PATH)
        family = QFontDatabase.applicationFontFamilies(id)[0] if id != -1 else 'Arial'
        font = QFont(family, 18)
        # Central widget and layout
        central_widget = QWidget()
        central_widget.setStyleSheet("background: transparent;")
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignCenter)
        # Listening indicator
        self.indicator = ListeningIndicator(self)
        layout.addWidget(self.indicator, alignment=Qt.AlignCenter)
        # Status label
        self.status_label = QLabel("Status: Listening...")
        self.status_label.setFont(QFont(family, 18))
        layout.addWidget(self.status_label, alignment=Qt.AlignCenter)
        # Voice log display
        self.voice_log = QTextEdit()
        self.voice_log.setReadOnly(True)
        self.voice_log.setFont(QFont(family, 13))
        self.voice_log.setMaximumHeight(200)
        layout.addWidget(self.voice_log)
        # Control buttons
        button_layout = QHBoxLayout()
        self.mic_button = QPushButton("🎤")
        self.mic_button.setFont(QFont(family, 13))
        self.mic_button.clicked.connect(self.toggle_listening)
        button_layout.addWidget(self.mic_button)
        self.clear_button = QPushButton("Clear Log")
        self.clear_button.setFont(QFont(family, 13))
        self.clear_button.clicked.connect(self.clear_log)
        button_layout.addWidget(self.clear_button)
        layout.addLayout(button_layout)
        # Drop shadow effect
        effect = QGraphicsDropShadowEffect(self)
        effect.setBlurRadius(40)
        effect.setColor(QColor(0, 200, 255, 180))
        effect.setOffset(0, 0)
        central_widget.setGraphicsEffect(effect)
        # Set window size and position
        self.setGeometry(500, 200, 500, 500)
        self.show()
        
    def process_command(self, text):
        self.voice_log.append(f"You: {text}")
        
        # Process commands
        text = text.lower()
        response = ""
        
        # Check if it's a general query (starts with "jarvis")
        if text.startswith("jarvis"):
            query = text.replace("jarvis", "").strip()
            nlp_response = self.nlp_processor.generate_response(query)
            if nlp_response:
                response = nlp_response
                self.voice_log.append(f"Jarvis: {response}")
                self.speak(response)
                return
        
        if "open" in text:
            app_name = text.replace("open", "").strip()
            try:
                if "browser" in app_name:
                    webbrowser.open("https://www.google.com")
                    response = "Opening web browser"
                else:
                    subprocess.Popen(app_name)
                    response = f"Opening {app_name}"
            except:
                response = f"Could not open {app_name}"
                
        elif "time" in text:
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            response = f"The current time is {current_time}"
            
        elif "date" in text:
            current_date = datetime.datetime.now().strftime("%B %d, %Y")
            response = f"Today's date is {current_date}"
            
        elif "set reminder" in text:
            # Extract reminder text and time
            reminder_text = text.replace("set reminder", "").strip()
            if "at" in reminder_text:
                text_part, time_part = reminder_text.split("at")
                reminder_text = text_part.strip()
                time_str = time_part.strip()
                response = self.reminder_manager.add_reminder(reminder_text, time_str)
            else:
                response = "Please specify a time for the reminder using 'at' (e.g., 'set reminder buy groceries at 3:00 PM')"
                
        elif "list reminders" in text:
            response = self.reminder_manager.list_reminders()
            
        elif "exit" in text or "quit" in text:
            self.close()
            return
            
        elif "hello" in text or "hi" in text:
            responses = [
                "Hello! How can I help you today?",
                "Hi there! What can I do for you?",
                "Greetings! How may I assist you?",
                "Hello! I'm here to help. What do you need?"
            ]
            response = responses[datetime.datetime.now().second % len(responses)]
            
        elif "thank you" in text or "thanks" in text:
            responses = [
                "You're welcome!",
                "Happy to help!",
                "Anytime!",
                "My pleasure!"
            ]
            response = responses[datetime.datetime.now().second % len(responses)]
            
        elif "google search" in text:
            query = text.replace("google search", "").strip()
            webbrowser.open(f"https://www.google.com/search?q={query}")
            response = f"Searching Google for {query}"
            
        else:
            # Try to get a response from the NLP processor
            nlp_response = self.nlp_processor.generate_response(text)
            if nlp_response:
                response = nlp_response
            else:
                response = "I'm not sure how to help with that."
            
        self.voice_log.append(f"Jarvis: {response}")
        self.speak(response)
        
    def speak(self, text):
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        
    def toggle_listening(self):
        if self.voice_thread.is_listening:
            self.voice_thread.is_listening = False
            self.status_label.setText("Status: Stopped")
            self.mic_button.setText("🎤/")
        else:
            self.voice_thread.is_listening = True
            self.voice_thread.start()
            self.status_label.setText("Status: Listening...")
            self.mic_button.setText("🎤")
        
    def clear_log(self):
        self.voice_log.clear()
        self.nlp_processor.clear_history()
            
    def closeEvent(self, event):
        self.voice_thread.is_listening = False
        self.voice_thread.wait()
        event.accept()

    def activate_assistant(self):
        self.show()
        self.raise_()
        self.activateWindow()
        self.status_label.setText("Status: Listening...")
        self.mic_button.setText("🎤")
        self.voice_thread.is_listening = True
        self.voice_thread.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = JarvisGUI()
    sys.exit(app.exec_()) 