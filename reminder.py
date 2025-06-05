import datetime
import json
import os
from threading import Timer

class ReminderManager:
    def __init__(self):
        self.reminders = []
        self.reminders_file = "reminders.json"
        self.load_reminders()
        
    def load_reminders(self):
        if os.path.exists(self.reminders_file):
            try:
                with open(self.reminders_file, 'r') as f:
                    self.reminders = json.load(f)
            except:
                self.reminders = []
                
    def save_reminders(self):
        with open(self.reminders_file, 'w') as f:
            json.dump(self.reminders, f)
            
    def add_reminder(self, text, time_str):
        try:
            reminder_time = datetime.datetime.strptime(time_str, "%I:%M %p")
            now = datetime.datetime.now()
            reminder_time = now.replace(
                hour=reminder_time.hour,
                minute=reminder_time.minute,
                second=0,
                microsecond=0
            )
            
            if reminder_time < now:
                reminder_time = reminder_time + datetime.timedelta(days=1)
                
            reminder = {
                "text": text,
                "time": reminder_time.strftime("%I:%M %p"),
                "date": reminder_time.strftime("%Y-%m-%d")
            }
            
            self.reminders.append(reminder)
            self.save_reminders()
            
            # Calculate seconds until reminder
            seconds_until = (reminder_time - now).total_seconds()
            
            # Set timer for reminder
            Timer(seconds_until, self.trigger_reminder, args=[reminder]).start()
            
            return f"Reminder set for {reminder['time']}"
        except Exception as e:
            return f"Error setting reminder: {str(e)}"
            
    def trigger_reminder(self, reminder):
        # Remove the triggered reminder
        self.reminders = [r for r in self.reminders if r != reminder]
        self.save_reminders()
        
        # Return the reminder text
        return f"Reminder: {reminder['text']}"
        
    def list_reminders(self):
        if not self.reminders:
            return "No active reminders"
            
        reminder_list = "Active reminders:\n"
        for reminder in self.reminders:
            reminder_list += f"- {reminder['text']} at {reminder['time']}\n"
        return reminder_list 