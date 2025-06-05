import sys
import json
import os
import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFileDialog, QTabWidget, QTableWidget,
    QTableWidgetItem, QDateEdit, QTimeEdit, QTextEdit, QComboBox, QHeaderView
)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QPainter, QPixmap, QPen, QFont, QColor

from reportlab.pdfgen import canvas

DATA_DIR = 'vehicle_data'
BACKUP_DIR = 'vehicle_backup'

def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)

def save_json(filename, data):
    with open(os.path.join(DATA_DIR, filename), 'w', encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(filename):
    try:
        with open(os.path.join(DATA_DIR, filename), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def backup_all_data(destination_folder):
    for fname in os.listdir(DATA_DIR):
        src = os.path.join(DATA_DIR, fname)
        dst = os.path.join(destination_folder, fname)
        with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
            fdst.write(fsrc.read())

def import_all_data(source_folder):
    imported = []
    for fname in os.listdir(source_folder):
        src = os.path.join(source_folder, fname)
        dst = os.path.join(DATA_DIR, fname)
        if os.path.isfile(src):
            with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
                fdst.write(fsrc.read())
            imported.append(fname)
    return imported

class SignaturePad(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(340, 110)
        self.pixmap = QPixmap(340, 110)
        self.pixmap.fill(Qt.white)
        self.last_point = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pixmap)

    def mousePressEvent(self, event):
        self.last_point = event.pos()

    def mouseMoveEvent(self, event):
        if self.last_point is not None:
            painter = QPainter(self.pixmap)
            pen = QPen(Qt.black, 2)
            painter.setPen(pen)
            painter.drawLine(self.last_point, event.pos())
            self.last_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        self.last_point = None

    def clear(self):
        self.pixmap.fill(Qt.white)
        self.update()

    def save(self, filename):
        self.pixmap.save(filename)

class ModernTable(QTableWidget):
    def __init__(self, rows, cols):
        super().__init__(rows, cols)
        self.setAlternatingRowColors(True)
        self.setStyleSheet("""
            QTableWidget {
                border-radius: 8px;
                border: 1px solid #dddddd;
                font-size: 13px;
                background: #fafbfc;
            }
            QHeaderView::section {
                background: #f6f8fa;
                font-weight: bold;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 3px;
            }
        """)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)

class SignatureDialog(QWidget):
    def __init__(self, parent=None, initial_signature=None):
        super().__init__(parent)
        self.setWindowTitle("Υπογραφή")
        self.layout = QVBoxLayout(self)
        self.sig_pad = SignaturePad()
        if initial_signature and os.path.exists(initial_signature):
            self.sig_pad.pixmap.load(initial_signature)
        self.layout.addWidget(self.sig_pad)
        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Αποθήκευση")
        self.cancel_btn = QPushButton("Ακύρωση")
        self.clear_btn = QPushButton("Καθαρισμός")
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.clear_btn)
        self.layout.addLayout(btn_row)
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.clear_btn.clicked.connect(self.sig_pad.clear)
        self.result = None

    def accept(self):
        self.result = True
        self.hide()

    def reject(self):
        self.result = False
        self.hide()

class VehicleManager(QMainWindow):
    def __init__(self):
        super().__init__()
        ensure_dirs()
        self.setWindowTitle("Διαχείριση Κίνησης Οχημάτων")
        self.resize(1300, 770)
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background: #f4f7fb;
            }
            QLabel {
                font-size: 15px;
            }
            QPushButton {
                background: #2563eb;
                color: #fff;
                border-radius: 6px;
                padding: 7px 14px;
                font-size: 15px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #1741a7;
            }
            QLineEdit, QTextEdit, QDateEdit, QTimeEdit, QComboBox {
                background: #fff;
                border: 1px solid #cfd8dc;
                border-radius: 5px;
                padding: 5px;
                font-size: 15px;
            }
            QComboBox QAbstractItemView {
                background: #2563eb;
                color: white;
                selection-background-color: #1741a7;
                selection-color: white;
                font-size: 15px;
            }
            QTabBar::tab {
                background: #e5e9f2;
                padding: 10px 25px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 16px;
                min-width: 140px;
            }
            QTabBar::tab:selected {
                background: #2563eb;
                color: #fff;
            }
        """)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.drivers = load_json('drivers.json')
        self.vehicles = load_json('vehicles.json')
        self.trips = load_json('trips.json')
        self.services = load_json('services.json')

        self.edit_driver_row = None
        self.edit_vehicle_row = None
        self.edit_trip_row = None
        self.edit_service_row = None
        self.temp_signature_file = None

        self.tabs.addTab(self.driver_tab(), "Οδηγοί")
        self.tabs.addTab(self.vehicle_tab(), "Οχήματα")
        self.tabs.addTab(self.trip_tab(), "Διαδρομές")
        self.tabs.addTab(self.service_tab(), "Service")
        self.tabs.addTab(self.search_tab(), "Αναζήτηση")
        self.tabs.addTab(self.backup_tab(), "Backup / Import")

        self.warning_timer = QTimer(self)
        self.warning_timer.timeout.connect(self.check_kteo_dates)
        self.warning_timer.start(60 * 60 * 1000)
        self.check_kteo_dates()

    # --- Driver Tab (with live update in comboboxes) ---
    def driver_tab(self):
        w = QWidget()
        layout = QVBoxLayout()
        title = QLabel("Διαχείριση Οδηγών")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)
        layout.addSpacing(8)
        form = QHBoxLayout()
        self.driver_name = QLineEdit()
        self.driver_name.setPlaceholderText("Όνομα Οδηγού")
        self.driver_add_btn = QPushButton("➕ Καταχώρηση Οδηγού")
        self.driver_add_btn.clicked.connect(self.add_driver)
        form.addWidget(self.driver_name)
        form.addWidget(self.driver_add_btn)
        layout.addLayout(form)
        layout.addSpacing(8)
        self.driver_table = ModernTable(0, 3)
        self.driver_table.setHorizontalHeaderLabels(['Όνομα', 'Επεξεργασία', 'Διαγραφή'])
        layout.addWidget(self.driver_table)
        w.setLayout(layout)
        self.refresh_driver_table()
        return w

    def add_driver(self):
        name = self.driver_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Σφάλμα", "Συμπληρώστε όνομα οδηγού.")
            return
        self.drivers.append({'name': name})
        save_json('drivers.json', self.drivers)
        self.driver_name.clear()
        self.refresh_driver_table()
        self.update_driver_comboboxes()

    def delete_driver(self, row):
        driver = self.drivers[row]['name']
        if QMessageBox.question(self, "Διαγραφή Οδηγού", f"Θέλετε να διαγράψετε τον οδηγό {driver};") == QMessageBox.Yes:
            self.drivers.pop(row)
            save_json('drivers.json', self.drivers)
            self.refresh_driver_table()
            self.update_driver_comboboxes()

    def refresh_driver_table(self):
        self.driver_table.setRowCount(len(self.drivers))
        for i, d in enumerate(self.drivers):
            self.driver_table.setItem(i, 0, QTableWidgetItem(d['name']))
            edit_btn = QPushButton("✏️")
            edit_btn.setMaximumWidth(40)
            edit_btn.clicked.connect(lambda _, row=i: self.start_edit_driver(row))
            del_btn = QPushButton("🗑️")
            del_btn.setMaximumWidth(40)
            del_btn.clicked.connect(lambda _, row=i: self.delete_driver(row))
            self.driver_table.setCellWidget(i, 1, edit_btn)
            self.driver_table.setCellWidget(i, 2, del_btn)

    def start_edit_driver(self, row):
        self.edit_driver_row = row
        self.driver_name.setText(self.drivers[row]['name'])
        self.tabs.setCurrentIndex(0)
        self.driver_add_btn.setText("💾 Ενημέρωση Οδηγού")
        self.driver_add_btn.clicked.disconnect()
        self.driver_add_btn.clicked.connect(self.finish_edit_driver)

    def finish_edit_driver(self):
        row = self.edit_driver_row
        name = self.driver_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Σφάλμα", "Συμπληρώστε όνομα οδηγού.")
            return
        self.drivers[row]['name'] = name
        save_json('drivers.json', self.drivers)
        self.driver_name.clear()
        self.refresh_driver_table()
        self.edit_driver_row = None
        self.driver_add_btn.setText("➕ Καταχώρηση Οδηγού")
        self.driver_add_btn.clicked.disconnect()
        self.driver_add_btn.clicked.connect(self.add_driver)
        self.update_driver_comboboxes()

    # --- Vehicle Tab (with live update in comboboxes) ---
    def vehicle_tab(self):
        w = QWidget()
        layout = QVBoxLayout()
        title = QLabel("Διαχείριση Οχημάτων & ΚΤΕΟ")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)
        layout.addSpacing(8)
        form = QHBoxLayout()
        self.plate_input = QLineEdit()
        self.plate_input.setPlaceholderText("Πινακίδα")
        self.kteo_passed = QDateEdit()
        self.kteo_passed.setCalendarPopup(True)
        self.kteo_passed.setDate(QDate.currentDate())
        self.kteo_next = QDateEdit()
        self.kteo_next.setCalendarPopup(True)
        self.kteo_next.setDate(QDate.currentDate().addDays(365))
        self.vehicle_add_btn = QPushButton("➕ Καταχώρηση Οχήματος")
        self.vehicle_add_btn.clicked.connect(self.add_vehicle)
        form.addWidget(self.plate_input)
        form.addWidget(QLabel("ΚΤΕΟ πέρασε"))
        form.addWidget(self.kteo_passed)
        form.addWidget(QLabel("Επόμενο ΚΤΕΟ"))
        form.addWidget(self.kteo_next)
        form.addWidget(self.vehicle_add_btn)
        layout.addLayout(form)
        layout.addSpacing(8)
        self.vehicle_table = ModernTable(0, 6)
        self.vehicle_table.setHorizontalHeaderLabels(['Πινακίδα', 'ΚΤΕΟ πέρασε', 'ΚΤΕΟ επόμενο', 'Κατάσταση', 'Επεξεργασία', 'Διαγραφή'])
        layout.addWidget(self.vehicle_table)
        w.setLayout(layout)
        self.refresh_vehicle_table()
        return w

    def add_vehicle(self):
        plate = self.plate_input.text().strip()
        passed = self.kteo_passed.date().toString("yyyy-MM-dd")
        next_ = self.kteo_next.date().toString("yyyy-MM-dd")
        if not plate:
            QMessageBox.warning(self, "Σφάλμα", "Συμπληρώστε πινακίδα.")
            return
        self.vehicles.append({'plate': plate, 'kteo_passed': passed, 'kteo_next': next_})
        save_json('vehicles.json', self.vehicles)
        self.plate_input.clear()
        self.refresh_vehicle_table()
        self.update_vehicle_comboboxes()

    def delete_vehicle(self, row):
        plate = self.vehicles[row]['plate']
        if QMessageBox.question(self, "Διαγραφή Οχήματος", f"Θέλετε να διαγράψετε το όχημα {plate};") == QMessageBox.Yes:
            self.vehicles.pop(row)
            save_json('vehicles.json', self.vehicles)
            self.refresh_vehicle_table()
            self.update_vehicle_comboboxes()

    def refresh_vehicle_table(self):
        self.vehicle_table.setRowCount(len(self.vehicles))
        for i, v in enumerate(self.vehicles):
            self.vehicle_table.setItem(i, 0, QTableWidgetItem(v['plate']))
            self.vehicle_table.setItem(i, 1, QTableWidgetItem(v['kteo_passed']))
            self.vehicle_table.setItem(i, 2, QTableWidgetItem(v['kteo_next']))
            status = self.get_kteo_status(v['kteo_next'])
            item = QTableWidgetItem(status)
            if status == "DANGER":
                item.setBackground(QColor("#fa5252"))
            elif status == "WARNING":
                item.setBackground(QColor("#ffd43b"))
            self.vehicle_table.setItem(i, 3, item)
            edit_btn = QPushButton("✏️")
            edit_btn.setMaximumWidth(40)
            edit_btn.clicked.connect(lambda _, row=i: self.start_edit_vehicle(row))
            del_btn = QPushButton("🗑️")
            del_btn.setMaximumWidth(40)
            del_btn.clicked.connect(lambda _, row=i: self.delete_vehicle(row))
            self.vehicle_table.setCellWidget(i, 4, edit_btn)
            self.vehicle_table.setCellWidget(i, 5, del_btn)

    def start_edit_vehicle(self, row):
        self.edit_vehicle_row = row
        v = self.vehicles[row]
        self.plate_input.setText(v['plate'])
        self.kteo_passed.setDate(QDate.fromString(v['kteo_passed'], "yyyy-MM-dd"))
        self.kteo_next.setDate(QDate.fromString(v['kteo_next'], "yyyy-MM-dd"))
        self.tabs.setCurrentIndex(1)
        self.vehicle_add_btn.setText("💾 Ενημέρωση Οχήματος")
        self.vehicle_add_btn.clicked.disconnect()
        self.vehicle_add_btn.clicked.connect(self.finish_edit_vehicle)

    def finish_edit_vehicle(self):
        row = self.edit_vehicle_row
        plate = self.plate_input.text().strip()
        passed = self.kteo_passed.date().toString("yyyy-MM-dd")
        next_ = self.kteo_next.date().toString("yyyy-MM-dd")
        if not plate:
            QMessageBox.warning(self, "Σφάλμα", "Συμπληρώστε πινακίδα.")
            return
        self.vehicles[row] = {'plate': plate, 'kteo_passed': passed, 'kteo_next': next_}
        save_json('vehicles.json', self.vehicles)
        self.plate_input.clear()
        self.refresh_vehicle_table()
        self.edit_vehicle_row = None
        self.vehicle_add_btn.setText("➕ Καταχώρηση Οχήματος")
        self.vehicle_add_btn.clicked.disconnect()
        self.vehicle_add_btn.clicked.connect(self.add_vehicle)
        self.update_vehicle_comboboxes()

    def get_kteo_status(self, date_next):
        today = datetime.date.today()
        kteo_next = datetime.datetime.strptime(date_next, "%Y-%m-%d").date()
        delta = (kteo_next - today).days
        if delta < 0:
            return "DANGER"
        elif delta < 15:
            return "WARNING"
        else:
            return "OK"

    def check_kteo_dates(self):
        alerts = []
        for v in self.vehicles:
            status = self.get_kteo_status(v['kteo_next'])
            if status == "DANGER":
                alerts.append(f"🚨 Όχημα {v['plate']} έχει ληγμένο ΚΤΕΟ!")
            elif status == "WARNING":
                alerts.append(f"⚠️ Όχημα {v['plate']} χρειάζεται ΚΤΕΟ σύντομα.")
        if alerts:
            QMessageBox.warning(self, "ΚΤΕΟ Alerts", "\n".join(alerts))
        self.refresh_vehicle_table()

    # --- Trip Tab (live comboboxes, signature edit) ---
    def trip_tab(self):
        w = QWidget()
        layout = QVBoxLayout()
        title = QLabel("Καταγραφή Διαδρομών")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)
        layout.addSpacing(8)
        form = QHBoxLayout()
        self.trip_driver = QComboBox()
        self.trip_driver.addItems([d['name'] for d in self.drivers])
        self.trip_vehicle = QComboBox()
        self.trip_vehicle.addItems([v['plate'] for v in self.vehicles])
        self.trip_depart_date = QDateEdit()
        self.trip_depart_date.setCalendarPopup(True)
        self.trip_depart_date.setDate(QDate.currentDate())
        self.trip_depart_time = QTimeEdit()
        self.trip_depart_time.setTime(datetime.datetime.now().time())
        self.trip_arrive_date = QDateEdit()
        self.trip_arrive_date.setCalendarPopup(True)
        self.trip_arrive_date.setDate(QDate.currentDate())
        self.trip_arrive_time = QTimeEdit()
        self.trip_arrive_time.setTime(datetime.datetime.now().time())
        form.addWidget(QLabel("Οδηγός:"))
        form.addWidget(self.trip_driver)
        form.addWidget(QLabel("Όχημα:"))
        form.addWidget(self.trip_vehicle)
        layout.addLayout(form)
        time_form = QHBoxLayout()
        time_form.addWidget(QLabel("Αναχώρηση:"))
        time_form.addWidget(self.trip_depart_date)
        time_form.addWidget(self.trip_depart_time)
        time_form.addSpacing(15)
        time_form.addWidget(QLabel("Άφιξη:"))
        time_form.addWidget(self.trip_arrive_date)
        time_form.addWidget(self.trip_arrive_time)
        layout.addLayout(time_form)
        layout.addSpacing(8)
        self.trip_details = QTextEdit()
        self.trip_details.setPlaceholderText("Λεπτομέρειες διαδρομής...")
        layout.addWidget(self.trip_details)
        sig_layout = QHBoxLayout()
        self.signature_pad = SignaturePad()
        sig_layout.addWidget(QLabel("Υπογραφή:"))
        sig_layout.addWidget(self.signature_pad)
        self.sign_btn = QPushButton("🧹 Καθαρισμός Υπογραφής")
        self.sign_btn.clicked.connect(self.signature_pad.clear)
        sig_layout.addWidget(self.sign_btn)
        layout.addLayout(sig_layout)
        self.trip_add_btn = QPushButton("➕ Καταχώρηση Διαδρομής")
        self.trip_add_btn.clicked.connect(self.add_trip)
        layout.addWidget(self.trip_add_btn)
        self.trip_table = ModernTable(0, 8)
        self.trip_table.setHorizontalHeaderLabels(['Οδηγός', 'Όχημα', 'Αναχώρηση', 'Άφιξη', 'Λεπτομέρειες', 'Υπογραφή', 'Επεξεργασία', 'Διαγραφή'])
        layout.addWidget(self.trip_table)
        export_btn = QPushButton("⤴️ Εξαγωγή Διαδρομής σε PDF")
        export_btn.clicked.connect(self.export_trip_pdf)
        layout.addWidget(export_btn)
        w.setLayout(layout)
        self.refresh_trip_table()
        return w

    def add_trip(self):
        trip = {
            'driver': self.trip_driver.currentText(),
            'vehicle': self.trip_vehicle.currentText(),
            'depart': self.trip_depart_date.date().toString("yyyy-MM-dd") + " " + self.trip_depart_time.time().toString("HH:mm"),
            'arrive': self.trip_arrive_date.date().toString("yyyy-MM-dd") + " " + self.trip_arrive_time.time().toString("HH:mm"),
            'details': self.trip_details.toPlainText(),
            'signature': f"signature_{len(self.trips)}.png"
        }
        self.signature_pad.save(os.path.join(DATA_DIR, trip['signature']))
        self.trips.append(trip)
        save_json('trips.json', self.trips)
        self.trip_details.clear()
        self.signature_pad.clear()
        self.refresh_trip_table()

    def delete_trip(self, row):
        if QMessageBox.question(self, "Διαγραφή Διαδρομής", f"Θέλετε να διαγράψετε τη διαδρομή;") == QMessageBox.Yes:
            self.trips.pop(row)
            save_json('trips.json', self.trips)
            self.refresh_trip_table()

    def refresh_trip_table(self):
        self.trip_table.setRowCount(len(self.trips))
        for i, t in enumerate(self.trips):
            self.trip_table.setItem(i, 0, QTableWidgetItem(t['driver']))
            self.trip_table.setItem(i, 1, QTableWidgetItem(t['vehicle']))
            self.trip_table.setItem(i, 2, QTableWidgetItem(t['depart']))
            self.trip_table.setItem(i, 3, QTableWidgetItem(t['arrive']))
            self.trip_table.setItem(i, 4, QTableWidgetItem(t['details']))
            self.trip_table.setItem(i, 5, QTableWidgetItem(t['signature']))
            edit_btn = QPushButton("✏️")
            edit_btn.setMaximumWidth(40)
            edit_btn.clicked.connect(lambda _, row=i: self.start_edit_trip(row))
            del_btn = QPushButton("🗑️")
            del_btn.setMaximumWidth(40)
            del_btn.clicked.connect(lambda _, row=i: self.delete_trip(row))
            self.trip_table.setCellWidget(i, 6, edit_btn)
            self.trip_table.setCellWidget(i, 7, del_btn)

    def start_edit_trip(self, row):
        self.edit_trip_row = row
        t = self.trips[row]
        self.trip_driver.setCurrentText(t['driver'])
        self.trip_vehicle.setCurrentText(t['vehicle'])
        d_date, d_time = t['depart'].split()
        a_date, a_time = t['arrive'].split()
        self.trip_depart_date.setDate(QDate.fromString(d_date, "yyyy-MM-dd"))
        self.trip_depart_time.setTime(datetime.datetime.strptime(d_time, "%H:%M").time())
        self.trip_arrive_date.setDate(QDate.fromString(a_date, "yyyy-MM-dd"))
        self.trip_arrive_time.setTime(datetime.datetime.strptime(a_time, "%H:%M").time())
        self.trip_details.setText(t['details'])
        sig_path = os.path.join(DATA_DIR, t['signature'])
        if os.path.exists(sig_path):
            self.signature_pad.pixmap.load(sig_path)
            self.signature_pad.update()
        self.temp_signature_file = t['signature']
        self.trip_add_btn.setText("💾 Ενημέρωση Διαδρομής")
        self.trip_add_btn.clicked.disconnect()
        self.trip_add_btn.clicked.connect(self.finish_edit_trip)
        self.sign_btn.setText("✍️ Υπογραφή (Ενημέρωση)")
        self.sign_btn.clicked.disconnect()
        self.sign_btn.clicked.connect(self.open_sign_dialog)

    def open_sign_dialog(self):
        t = self.trips[self.edit_trip_row] if self.edit_trip_row is not None else None
        initial = os.path.join(DATA_DIR, t['signature']) if t else None
        sig_dialog = SignatureDialog(self, initial_signature=initial)
        sig_dialog.setWindowModality(Qt.ApplicationModal)
        sig_dialog.show()
        sig_dialog.save_btn.clicked.connect(lambda: self.save_signature(sig_dialog))
        sig_dialog.cancel_btn.clicked.connect(sig_dialog.reject)

    def save_signature(self, sig_dialog):
        if self.edit_trip_row is not None:
            fname = self.trips[self.edit_trip_row]['signature']
        else:
            fname = f"signature_{len(self.trips)}.png"
        sig_dialog.sig_pad.save(os.path.join(DATA_DIR, fname))
        self.signature_pad.pixmap.load(os.path.join(DATA_DIR, fname))
        self.signature_pad.update()
        sig_dialog.accept()

    def finish_edit_trip(self):
        row = self.edit_trip_row
        trip = {
            'driver': self.trip_driver.currentText(),
            'vehicle': self.trip_vehicle.currentText(),
            'depart': self.trip_depart_date.date().toString("yyyy-MM-dd") + " " + self.trip_depart_time.time().toString("HH:mm"),
            'arrive': self.trip_arrive_date.date().toString("yyyy-MM-dd") + " " + self.trip_arrive_time.time().toString("HH:mm"),
            'details': self.trip_details.toPlainText(),
            'signature': self.trips[row]['signature']
        }
        self.signature_pad.save(os.path.join(DATA_DIR, trip['signature']))
        self.trips[row] = trip
        save_json('trips.json', self.trips)
        self.trip_details.clear()
        self.signature_pad.clear()
        self.refresh_trip_table()
        self.edit_trip_row = None
        self.trip_add_btn.setText("➕ Καταχώρηση Διαδρομής")
        self.trip_add_btn.clicked.disconnect()
        self.trip_add_btn.clicked.connect(self.add_trip)
        self.sign_btn.setText("🧹 Καθαρισμός Υπογραφής")
        self.sign_btn.clicked.disconnect()
        self.sign_btn.clicked.connect(self.signature_pad.clear)

    def export_trip_pdf(self):
        idx = self.trip_table.currentRow()
        if idx < 0:
            QMessageBox.warning(self, "Σφάλμα", "Επιλέξτε διαδρομή για εξαγωγή.")
            return
        trip = self.trips[idx]
        fname, _ = QFileDialog.getSaveFileName(self, "Αποθήκευση PDF", f"{trip['driver']}_{trip['vehicle']}.pdf", "PDF Files (*.pdf)")
        if fname:
            c = canvas.Canvas(fname)
            c.setFont("Helvetica", 15)
            c.drawString(100, 800, f"Οδηγός: {trip['driver']}")
            c.drawString(100, 780, f"Όχημα: {trip['vehicle']}")
            c.drawString(100, 760, f"Αναχώρηση: {trip['depart']}")
            c.drawString(100, 740, f"Άφιξη: {trip['arrive']}")
            c.setFont("Helvetica", 12)
            c.drawString(100, 720, f"Λεπτομέρειες: {trip['details']}")
            signature_path = os.path.join(DATA_DIR, trip['signature'])
            if os.path.exists(signature_path):
                c.drawImage(signature_path, 100, 650, width=200, height=60)
            c.save()
            QMessageBox.information(self, "Εξαγωγή", "Επιτυχής εξαγωγή PDF.")

    # --- Service Tab (live comboboxes) ---
    def service_tab(self):
        w = QWidget()
        layout = QVBoxLayout()
        title = QLabel("Καταγραφή Service Οχημάτων")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)
        layout.addSpacing(8)
        form = QHBoxLayout()
        self.service_vehicle = QComboBox()
        self.service_vehicle.addItems([v['plate'] for v in self.vehicles])
        self.service_date = QDateEdit()
        self.service_date.setCalendarPopup(True)
        self.service_date.setDate(QDate.currentDate())
        self.service_detail = QLineEdit()
        self.service_detail.setPlaceholderText("Λεπτομέρειες")
        self.service_add_btn = QPushButton("➕ Καταχώρηση Service")
        self.service_add_btn.clicked.connect(self.add_service)
        form.addWidget(self.service_vehicle)
        form.addWidget(self.service_date)
        form.addWidget(self.service_detail)
        form.addWidget(self.service_add_btn)
        layout.addLayout(form)
        layout.addSpacing(8)
        self.service_table = ModernTable(0, 5)
        self.service_table.setHorizontalHeaderLabels(['Όχημα', 'Ημερομηνία', 'Λεπτομέρειες', 'Επεξεργασία', 'Διαγραφή'])
        layout.addWidget(self.service_table)
        w.setLayout(layout)
        self.refresh_service_table()
        return w

    def add_service(self):
        s = {'vehicle': self.service_vehicle.currentText(),
             'date': self.service_date.date().toString("yyyy-MM-dd"),
             'details': self.service_detail.text()}
        self.services.append(s)
        save_json('services.json', self.services)
        self.refresh_service_table()

    def delete_service(self, row):
        if QMessageBox.question(self, "Διαγραφή Service", "Θέλετε να διαγράψετε το service;") == QMessageBox.Yes:
            self.services.pop(row)
            save_json('services.json', self.services)
            self.refresh_service_table()

    def refresh_service_table(self):
        self.service_table.setRowCount(len(self.services))
        for i, s in enumerate(self.services):
            self.service_table.setItem(i, 0, QTableWidgetItem(s['vehicle']))
            self.service_table.setItem(i, 1, QTableWidgetItem(s['date']))
            self.service_table.setItem(i, 2, QTableWidgetItem(s['details']))
            edit_btn = QPushButton("✏️")
            edit_btn.setMaximumWidth(40)
            edit_btn.clicked.connect(lambda _, row=i: self.start_edit_service(row))
            del_btn = QPushButton("🗑️")
            del_btn.setMaximumWidth(40)
            del_btn.clicked.connect(lambda _, row=i: self.delete_service(row))
            self.service_table.setCellWidget(i, 3, edit_btn)
            self.service_table.setCellWidget(i, 4, del_btn)

    def start_edit_service(self, row):
        self.edit_service_row = row
        s = self.services[row]
        self.service_vehicle.setCurrentText(s['vehicle'])
        self.service_date.setDate(QDate.fromString(s['date'], "yyyy-MM-dd"))
        self.service_detail.setText(s['details'])
        self.tabs.setCurrentIndex(3)
        self.service_add_btn.setText("💾 Ενημέρωση Service")
        self.service_add_btn.clicked.disconnect()
        self.service_add_btn.clicked.connect(self.finish_edit_service)

    def finish_edit_service(self):
        row = self.edit_service_row
        s = {'vehicle': self.service_vehicle.currentText(),
             'date': self.service_date.date().toString("yyyy-MM-dd"),
             'details': self.service_detail.text()}
        self.services[row] = s
        save_json('services.json', self.services)
        self.service_detail.clear()
        self.refresh_service_table()
        self.edit_service_row = None
        self.service_add_btn.setText("➕ Καταχώρηση Service")
        self.service_add_btn.clicked.disconnect()
        self.service_add_btn.clicked.connect(self.add_service)

    # --- Live Combobox Updates ---
    def update_driver_comboboxes(self):
        # Update trip driver combo live
        names = [d['name'] for d in self.drivers]
        current = self.trip_driver.currentText() if hasattr(self, "trip_driver") else ""
        self.trip_driver.clear()
        self.trip_driver.addItems(names)
        if current in names:
            self.trip_driver.setCurrentText(current)

    def update_vehicle_comboboxes(self):
        # Update trip and service vehicle combos live
        plates = [v['plate'] for v in self.vehicles]
        tcur = self.trip_vehicle.currentText() if hasattr(self, "trip_vehicle") else ""
        scur = self.service_vehicle.currentText() if hasattr(self, "service_vehicle") else ""
        self.trip_vehicle.clear()
        self.trip_vehicle.addItems(plates)
        self.service_vehicle.clear()
        self.service_vehicle.addItems(plates)
        if tcur in plates:
            self.trip_vehicle.setCurrentText(tcur)
        if scur in plates:
            self.service_vehicle.setCurrentText(scur)

    # --- Search Tab ---
    def search_tab(self):
        w = QWidget()
        layout = QVBoxLayout()
        title = QLabel("🔎 Αναζήτηση Σε Όλα Τα Δεδομένα")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)
        layout.addSpacing(8)
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Πληκτρολογήστε όνομα, όχημα, κτλ...")
        self.search_btn = QPushButton("Αναζήτηση")
        self.search_btn.clicked.connect(self.do_search)
        search_row.addWidget(self.search_input)
        search_row.addWidget(self.search_btn)
        layout.addLayout(search_row)
        self.search_results = QTextEdit()
        self.search_results.setReadOnly(True)
        self.search_results.setMaximumHeight(220)
        layout.addWidget(self.search_results)
        w.setLayout(layout)
        return w

    def do_search(self):
        q = self.search_input.text().lower()
        results = []
        for d in self.drivers:
            if q in d['name'].lower():
                results.append(f"[Οδηγός] {d['name']}")
        for v in self.vehicles:
            if q in v['plate'].lower() or q in v['kteo_passed'] or q in v['kteo_next']:
                results.append(f"[Όχημα] {v['plate']} - ΚΤΕΟ Πέρασε: {v['kteo_passed']} Επόμενο: {v['kteo_next']}")
        for t in self.trips:
            if q in t['driver'].lower() or q in t['vehicle'].lower() or q in t['details'].lower():
                results.append(f"[Διαδρομή] Οδηγός: {t['driver']} Όχημα: {t['vehicle']} [{t['depart']} -> {t['arrive']}] {t['details']}")
        for s in self.services:
            if q in s['vehicle'].lower() or q in s['details'].lower():
                results.append(f"[Service] Όχημα: {s['vehicle']} Ημ/νία: {s['date']} {s['details']}")
        self.search_results.setText('\n'.join(results) if results else "Δεν βρέθηκαν αποτελέσματα.")

    # --- Backup and Import Tab ---
    def backup_tab(self):
        w = QWidget()
        layout = QVBoxLayout()
        title = QLabel("🗄️ Backup & Εισαγωγή Δεδομένων")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)
        layout.addSpacing(8)
        backup_btn = QPushButton("Backup δεδομένων σε φάκελο...")
        backup_btn.clicked.connect(self.do_backup)
        layout.addWidget(backup_btn)
        import_btn = QPushButton("Εισαγωγή δεδομένων από φάκελο backup...")
        import_btn.clicked.connect(self.do_import)
        layout.addWidget(import_btn)
        w.setLayout(layout)
        return w

    def do_backup(self):
        folder = QFileDialog.getExistingDirectory(self, "Επιλογή φακέλου backup")
        if folder:
            backup_all_data(folder)
            QMessageBox.information(self, "Backup", "Το backup ολοκληρώθηκε.")

    def do_import(self):
        folder = QFileDialog.getExistingDirectory(self, "Επιλογή φακέλου backup για εισαγωγή")
        if folder:
            imported = import_all_data(folder)
            self.reload_all_data()
            QMessageBox.information(self, "Εισαγωγή", f"Εισαγωγή δεδομένων ολοκληρώθηκε ({len(imported)} αρχεία).")

    def reload_all_data(self):
        self.drivers = load_json('drivers.json')
        self.vehicles = load_json('vehicles.json')
        self.trips = load_json('trips.json')
        self.services = load_json('services.json')
        self.refresh_driver_table()
        self.refresh_vehicle_table()
        self.refresh_trip_table()
        self.refresh_service_table()
        self.update_driver_comboboxes()
        self.update_vehicle_comboboxes()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VehicleManager()
    window.show()
    sys.exit(app.exec_())
