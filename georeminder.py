import os
from qgis.PyQt.QtCore import QObject, QTimer, QDateTime
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QDialog, QVBoxLayout, QPushButton, QDateTimeEdit
from qgis.PyQt.QtGui import QIcon

from .georeminder_dialog import GeoReminderDialog
from .db_manager import DBManager
from .georeminder_panel import GeoReminderPanel

class GeoReminder(QObject):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.action = None

        # ✅ Setup database connection
        plugin_dir = os.path.dirname(__file__)
        db_path = os.path.join(plugin_dir, "reminders.db")
        self.db = DBManager(db_path)

        # 🔔 Setup Reminder Timer
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start(30000)  # every 30 sec

        self.panel = None  # ✅ Track panel instance

    def initGui(self):
        self.toolbar = self.iface.addToolBar("GeoReminder Toolbar")
        self.toolbar.setObjectName("GeoReminderToolbar")

        # ➕ Toolbar Button with icon
        icon_path = os.path.join(os.path.dirname(__file__), "icons", "georeminder_icon.png")
        self.action = QAction(QIcon(icon_path), "GeoReminder Panel", self.iface.mainWindow())
        self.action.triggered.connect(self.show_panel)
        self.toolbar.addAction(self.action)

        # ➕ Add to menu
        self.iface.addPluginToMenu("GeoReminder", self.action)

        # ➕ Add Reminder button
        self.add_reminder_action = QAction("Add GeoReminder", self.iface.mainWindow())
        self.add_reminder_action.triggered.connect(self.open_reminder_dialog)
        self.iface.addPluginToMenu("GeoReminder", self.add_reminder_action)

        # ➕ Add Reminder from Selected Features
        self.add_reminder_from_selection_action = QAction("Add Reminder to Selected Feature(s)", self.iface.mainWindow())
        self.add_reminder_from_selection_action.triggered.connect(self.add_reminder_to_selected)
        self.iface.addPluginToMenu("GeoReminder", self.add_reminder_from_selection_action)

    def unload(self):
        # ❌ Cleanup
        self.iface.removePluginMenu("GeoReminder", self.action)
        self.iface.removePluginMenu("GeoReminder", self.add_reminder_action)
        self.iface.removePluginMenu("GeoReminder", self.add_reminder_from_selection_action)

        if hasattr(self, 'toolbar'):
            for action in self.toolbar.actions():
                self.toolbar.removeAction(action)
            del self.toolbar

        # ✅ Panel ko bhi close karo jab plugin unload ho
        if self.panel:
            self.panel.close()
            self.panel = None

    def show_panel(self):
        if not self.panel:
            # ✅ Panel doesn't exist → create new
            self.panel = GeoReminderPanel(self.db, self.iface, self)
            self.iface.addDockWidget(0x1, self.panel)
        else:
            # ✅ Already exists → just show and raise it
            self.panel.show()
            self.panel.raise_()

    def open_reminder_dialog(self):
        dialog = GeoReminderDialog()
        if dialog.exec_():
            reminder_text, reminder_time = dialog.get_data()

            # Dummy feature & layer for manual add
            feature_id = "0"
            layer_id = "ManualEntry"

            try:
                self.db.add_reminder(feature_id, layer_id, reminder_text, reminder_time)
                QMessageBox.information(self.iface.mainWindow(), "Reminder Saved",
                                        f"Saved reminder: {reminder_text}\nTime: {reminder_time}")
            except Exception as e:
                QMessageBox.critical(self.iface.mainWindow(), "DB Error", str(e))

        self.show_or_refresh_panel()

    def add_reminder_to_selected(self):
        layer = self.iface.activeLayer()
        if not layer:
            QMessageBox.warning(self.iface.mainWindow(), "Error", "No active layer selected!")
            return

        if not layer.type() == layer.VectorLayer:
            QMessageBox.warning(self.iface.mainWindow(), "Error", "Active layer is not a vector layer!")
            return

        selected_features = layer.selectedFeatures()
        if not selected_features:
            QMessageBox.warning(self.iface.mainWindow(), "Error",
                                "No features selected!\nSelect using the 'Select Features' tool.")
            return

        dialog = GeoReminderDialog()
        if dialog.exec_():
            reminder_text, reminder_time = dialog.get_data()

            feature_ids = ",".join([str(f.id()) for f in selected_features])
            layer_id = layer.name()

            try:
                self.db.add_reminder(feature_ids, layer_id, reminder_text, reminder_time)
            except Exception as e:
                QMessageBox.critical(self.iface.mainWindow(), "DB Error", str(e))
                return

            QMessageBox.information(self.iface.mainWindow(), "Reminder Saved",
                                    f"Reminder added for {len(selected_features)} selected feature(s).")

            # ✅ Force refresh
            self.show_or_refresh_panel()

    def check_reminders(self):
        current_dt = QDateTime.currentDateTime()
        any_change = False

        try:
            reminders = self.db.get_all_reminders()
        except Exception as e:
            print(f"[DB ERROR] {e}")
            return

        for reminder in reminders:
            reminder_id, feature_id_str, layer_id, reminder_text, reminder_time_str = reminder
            reminder_dt = QDateTime.fromString(reminder_time_str, "yyyy-MM-dd HH:mm:ss")

            print("[DEBUG]", reminder)
            print(f"[CHECK] Reminder: {reminder_text}, Due: {reminder_time_str}, Now: {current_dt.toString('yyyy-MM-dd HH:mm:ss')}")

            if not reminder_dt.isValid():
                print(f"[ERROR] Invalid reminder time: {reminder_time_str}")
                continue

            if reminder_dt <= current_dt:
                feature_list = feature_id_str.split(",")
                feature_display = "\n".join([f"• Feature ID: {fid.strip()}" for fid in feature_list])

                response = QMessageBox.question(
                    self.iface.mainWindow(),
                    "Reminder Due!",
                    f"⏰ Reminder: {reminder_text}\n\nLayer: {layer_id}\nReminder Time: {reminder_time_str}\n\n"
                    f"Applied on {len(feature_list)} feature(s):\n{feature_display}\n\n"
                    "Do you want to extend this reminder?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if response == QMessageBox.Yes:
                    new_time = self.ask_new_reminder_time()
                    if new_time:
                        try:
                            self.db.update_reminder_time(reminder_id, new_time)
                            QMessageBox.information(self.iface.mainWindow(), "Reminder Extended",
                                                    f"Reminder extended to {new_time}")
                        except Exception as e:
                            QMessageBox.critical(self.iface.mainWindow(), "DB Error", str(e))
                        any_change = True
                    else:
                        self.db.delete_reminder(reminder_id)
                        QMessageBox.information(self.iface.mainWindow(), "Reminder Removed",
                                                "Reminder cancelled and removed.")
                        any_change = True

                else:
                    self.db.delete_reminder(reminder_id)
                    any_change = True

        if any_change:
            self.show_or_refresh_panel()

    def ask_new_reminder_time(self):
        dialog = QDialog()
        dialog.setWindowTitle("Pick New Reminder Time")
        layout = QVBoxLayout()

        datetime_edit = QDateTimeEdit()
        datetime_edit.setDateTime(QDateTime.currentDateTime())
        datetime_edit.setCalendarPopup(True)
        layout.addWidget(datetime_edit)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.accept)
        layout.addWidget(ok_button)

        dialog.setLayout(layout)

        if dialog.exec_():
            return datetime_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        else:
            return None

    def show_or_refresh_panel(self):
        if not self.panel:
            self.show_panel()
        else:
            print("[DEBUG] Refreshing Reminder Panel")
            self.panel.load_reminders()

# ✅ Plugin Factory
def classFactory(iface):
    return GeoReminder(iface)
