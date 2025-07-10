from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QDateTimeEdit, QMessageBox
from qgis.PyQt.QtCore import QDateTime

class GeoReminderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add GeoReminder")

        layout = QVBoxLayout()

        # Reminder Text
        layout.addWidget(QLabel("Reminder Text:"))
        self.reminder_text = QLineEdit()
        layout.addWidget(self.reminder_text)

        # Reminder Time
        layout.addWidget(QLabel("Reminder Time:"))
        self.reminder_time = QDateTimeEdit()
        self.reminder_time.setDateTime(QDateTime.currentDateTime())
        self.reminder_time.setCalendarPopup(True)
        layout.addWidget(self.reminder_time)

        # OK Button
        self.ok_button = QPushButton("Save Reminder")
        self.ok_button.clicked.connect(self.validate_and_accept)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

    def validate_and_accept(self):
        if not self.reminder_text.text().strip():
            QMessageBox.warning(self, "⚠️ Validation Error", "Reminder text cannot be empty!")
            return

        if self.reminder_time.dateTime() < QDateTime.currentDateTime():
            QMessageBox.warning(self, "⚠️ Validation Error", "Reminder time cannot be in the past!")
            return

        self.accept()

    def get_data(self):
        return self.reminder_text.text(), self.reminder_time.dateTime().toString("yyyy-MM-dd HH:mm:ss")
