from qgis.PyQt.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QMessageBox
from qgis.core import QgsProject

class GeoReminderPanel(QDockWidget):
    def __init__(self, db_manager, iface_ref, plugin_ref, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.iface = iface_ref
        self.plugin = plugin_ref

        container = QWidget()
        layout = QVBoxLayout()

        # ➕ Table with 6 columns
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Feature ID", "Layer ID", "Reminder Text", "Reminder Time", "Zoom", "Delete"])
        layout.addWidget(self.table)

        # ✅ Pehle create karo button_layout
        button_layout = QHBoxLayout()

        # 1 ➕ Add to Selected Feature(s)
        add_selected_reminder_btn = QPushButton("➕ Add to Selected Feature(s)")
        add_selected_reminder_btn.clicked.connect(self.add_reminder_to_selected)
        button_layout.addWidget(add_selected_reminder_btn)

        # 2 ➕ Add GeoReminder
        add_reminder_btn = QPushButton("➕ Add GeoReminder")
        add_reminder_btn.clicked.connect(self.add_reminder)
        button_layout.addWidget(add_reminder_btn)

        # 3 📤 Export Button
        export_btn = QPushButton("📤 Export Reminders")
        export_btn.clicked.connect(self.export_reminders)
        button_layout.addWidget(export_btn)

        # 4 📥 Import Button
        import_btn = QPushButton("📥 Import Reminders")
        import_btn.clicked.connect(self.import_reminders)
        button_layout.addWidget(import_btn)

        # 5 🔄 Refresh Button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_reminders)
        button_layout.addWidget(refresh_btn)

        # ➕ Add the buttons layout to the main layout
        layout.addLayout(button_layout)

        container.setLayout(layout)
        self.setWidget(container)

        # Initial load
        self.load_reminders()

    def load_reminders(self):
        reminders = self.db.get_all_reminders()
        self.table.setRowCount(len(reminders))

        for row_idx, reminder in enumerate(reminders):
            reminder_id, feature_id, layer_id, reminder_text, reminder_time = reminder

            # Fill data columns
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(feature_id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(layer_id)))
            self.table.setItem(row_idx, 2, QTableWidgetItem(reminder_text))
            self.table.setItem(row_idx, 3, QTableWidgetItem(reminder_time))

            # 🔍 Zoom Button
            zoom_btn = QPushButton("🔍 Zoom")
            zoom_btn.clicked.connect(lambda _, fid=feature_id, lid=layer_id: self.zoom_to_feature(fid, lid))
            self.table.setCellWidget(row_idx, 4, zoom_btn)

            # ❌ Delete Button
            delete_btn = QPushButton("❌ Delete")
            delete_btn.clicked.connect(lambda _, rid=reminder_id: self.delete_reminder(rid))
            self.table.setCellWidget(row_idx, 5, delete_btn)

    def delete_reminder(self, reminder_id):
        self.db.delete_reminder(reminder_id)
        self.load_reminders()

    def add_reminder(self):
        # ✅ Just call the plugin's method
        self.plugin.open_reminder_dialog()


    def add_reminder_to_selected(self):
        # ✅ Sirf plugin call karo
        self.plugin.add_reminder_to_selected()

    def zoom_to_feature(self, feature_id, layer_name):
        layer = next((lyr for lyr in QgsProject.instance().mapLayers().values() if lyr.name() == layer_name), None)

        if not layer:
            QMessageBox.warning(self, "Error", f"Layer '{layer_name}' not found in project!")
            return

        # ✅ If multiple IDs (comma-separated)
        feature_ids = feature_id.split(",")
        try:
            feature_ids_list = [int(fid.strip()) for fid in feature_ids]
        except ValueError:
            QMessageBox.warning(self, "Error", f"Invalid feature ID(s): {feature_ids}")
            return

        # ✅ Select the features
        layer.selectByIds(feature_ids_list)

        # ✅ Get the extent of selected features
        extent = layer.boundingBoxOfSelected()
        if extent.isNull():
            QMessageBox.warning(self, "Error", f"No features found in layer '{layer_name}' for IDs: {feature_ids}")
            return

        # ✅ Zoom to combined extent
        self.iface.mapCanvas().setExtent(extent)
        self.iface.mapCanvas().refresh()

    def export_reminders(self):
        from qgis.PyQt.QtWidgets import QFileDialog
        import csv

        filepath, _ = QFileDialog.getSaveFileName(self, "Export Reminders", "", "CSV Files (*.csv)")
        if not filepath:
            return

        reminders = self.db.get_all_reminders()
        try:
            with open(filepath, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["ID", "Feature IDs", "Layer ID", "Reminder Text", "Reminder Time"])
                for reminder in reminders:
                    writer.writerow(reminder)

            QMessageBox.information(self, "Export Successful", f"Reminders exported to:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))

    def import_reminders(self):
        from qgis.PyQt.QtWidgets import QFileDialog
        import csv

        filepath, _ = QFileDialog.getOpenFileName(self, "Import Reminders", "", "CSV Files (*.csv)")
        if not filepath:
            return

        try:
            with open(filepath, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    feature_ids = row["Feature IDs"]
                    layer_id = row["Layer ID"]
                    reminder_text = row["Reminder Text"]
                    reminder_time = row["Reminder Time"]

                    self.db.add_reminder(feature_ids, layer_id, reminder_text, reminder_time)

            QMessageBox.information(self, "Import Successful", "Reminders imported successfully.")
            self.load_reminders()  # ✅ Table refresh
        except Exception as e:
            QMessageBox.critical(self, "Import Failed", str(e))
