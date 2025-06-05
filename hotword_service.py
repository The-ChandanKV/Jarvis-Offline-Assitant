import win32serviceutil
import win32service
import win32event
import servicemanager
import subprocess
import sys
import os
import speech_recognition as sr

class JarvisHotwordService(win32serviceutil.ServiceFramework):
    _svc_name_ = "JarvisHotwordService"
    _svc_display_name_ = "Jarvis Hotword Listener Service"
    _svc_description_ = "Listens for 'Hey Jarvis' and launches the Jarvis assistant."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.is_running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.is_running = False
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ""))
        self.main()

    def main(self):
        recognizer = sr.Recognizer()
        while self.is_running:
            try:
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source)
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    try:
                        text = recognizer.recognize_google(audio)
                        if text.strip().lower() == "hey jarvis":
                            # Launch main.py if not already running
                            if not self.is_jarvis_running():
                                subprocess.Popen([sys.executable, os.path.join(os.path.dirname(__file__), "main.py")])
                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError:
                        pass
            except Exception:
                pass

    def is_jarvis_running(self):
        # Check if main.py is already running
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'main.py' in proc.info['cmdline']:
                    return True
            except Exception:
                continue
        return False

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(JarvisHotwordService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(JarvisHotwordService) 