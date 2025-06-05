import sys
import json
import os
import datetime
import shutil
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageDraw, ImageTk
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Constants
DATA_DIR = 'vehicle_data'
BACKUP_DIR = 'vehicle_backups'
LOG_FILE = 'app_log.txt'

def ensure_dirs():
    """Create necessary directories if they don't exist"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)

def save_json(filename, data):
    """Save data to JSON file with error handling"""
    try:
        with open(os.path.join(DATA_DIR, filename), 'w', encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        log_error(f"Error saving {filename}: {str(e)}")
        messagebox.showerror("Σφάλμα αποθήκευσης δεδομένων", f"Σφάλμα αρχείου: {str(e)}")
        return False

def load_json(filename):
    """Load data from JSON file with error handling"""
    try:
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)
                
                # Migrate old data format if needed
                if filename == 'drivers.json' and data and 'id' not in data[0]:
                    for i, item in enumerate(data):
                        item['id'] = i + 1
                    save_json(filename, data)
                    
                elif filename == 'vehicles.json' and data and 'id' not in data[0]:
                    for i, item in enumerate(data):
                        item['id'] = i + 1
                    save_json(filename, data)
                    
                elif filename == 'trips.json' and data and 'id' not in data[0]:
                    for i, item in enumerate(data):
                        item['id'] = i + 1
                    save_json(filename, data)
                    
                elif filename == 'services.json' and data and 'id' not in data[0]:
                    for i, item in enumerate(data):
                        item['id'] = i + 1
                    save_json(filename, data)
                
                return data
        return []
    except Exception as e:
        log_error(f"Error loading {filename}: {str(e)}")
        messagebox.showerror("Σφάλμα φόρτωσης δεδομένων", f"Σφάλμα αρχείου: {str(e)}")
        return []

def log_error(message):
    """Log errors to file with timestamp"""
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, 'a', encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass  # Avoid crashing if logging fails

def backup_all_data(destination_folder):
    """Backup data to specified folder with error handling"""
    try:
        os.makedirs(destination_folder, exist_ok=True)
        for fname in os.listdir(DATA_DIR):
            src = os.path.join(DATA_DIR, fname)
            if os.path.isfile(src):
                dst = os.path.join(destination_folder, fname)
                shutil.copy2(src, dst)
        return True
    except Exception as e:
        log_error(f"Backup error: {str(e)}")
        messagebox.showerror("Σφάλμα Backup", f"Σφάλμα κατά τη δημιουργίας backup: {str(e)}")
        return False

def import_all_data(source_folder):
    """Import data from backup folder with error handling"""
    try:
        imported = []
        for fname in os.listdir(source_folder):
            src = os.path.join(source_folder, fname)
            if os.path.isfile(src) and fname.endswith('.json'):
                dst = os.path.join(DATA_DIR, fname)
                shutil.copy2(src, dst)
                imported.append(fname)
        return imported
    except Exception as e:
        log_error(f"Import error: {str(e)}")
        messagebox.showerror("Σφάλμα Εισαγωγής", f"Σφάλμα κατά την εισαγωγή δεδομένων: {str(e)}")
        return []

def validate_date(date_str):
    """Validate date format (YYYY-MM-DD)"""
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_time(time_str):
    """Validate time format (HH:MM)"""
    try:
        datetime.datetime.strptime(time_str, '%H:%M')
        return True
    except ValueError:
        return False

class SignaturePad(tk.Canvas):
    def __init__(self, master, width=400, height=180, **kwargs):
        super().__init__(master, width=width, height=height, bg='white', 
                         bd=0, highlightthickness=1, relief='ridge', **kwargs)
        self.width = width
        self.height = height
        self.image = Image.new('RGB', (width, height), 'white')
        self.draw = ImageDraw.Draw(self.image)
        self.last_point = None
        self.bind("<Button-1>", self.start_draw)
        self.bind("<B1-Motion>", self.draw_motion)
        self.bind("<ButtonRelease-1>", self.end_draw)
        self.tk_image = None  # Keep reference to prevent garbage collection

    def start_draw(self, event):
        self.last_point = (event.x, event.y)

    def draw_motion(self, event):
        if self.last_point:
            self.create_line(self.last_point[0], self.last_point[1], event.x, event.y, 
                            fill='#222', width=2)
            self.draw.line([self.last_point, (event.x, event.y)], fill='#222', width=2)
            self.last_point = (event.x, event.y)

    def end_draw(self, event):
        self.last_point = None

    def clear(self):
        self.delete('all')
        self.image = Image.new('RGB', (self.width, self.height), 'white')
        self.draw = ImageDraw.Draw(self.image)

    def save(self, filename):
        try:
            self.image.save(filename)
            return True
        except Exception as e:
            log_error(f"Signature save error: {str(e)}")
            return False

    def load(self, filename):
        if os.path.exists(filename):
            try:
                img = Image.open(filename)
                self.image.paste(img)
                self.draw = ImageDraw.Draw(self.image)
                self.delete('all')
                self.tk_image = ImageTk.PhotoImage(img)
                self.create_image(0, 0, image=self.tk_image, anchor='nw')
                return True
            except Exception as e:
                log_error(f"Signature load error: {str(e)}")
        return False

class VehicleManager(tk.Tk):
    def __init__(self):
        super().__init__()
        ensure_dirs()
        
        # Application setup
        self.title("Διαχείριση Κίνησης Οχημάτων")
        self.geometry("1400x900")
        self.minsize(1200, 750)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Set application font
        self.font = ("Segoe UI", 12)
        self.title_font = ("Segoe UI", 16, "bold")
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=12, pady=8)
        
        # Initialize data
        self.drivers = load_json('drivers.json')
        self.vehicles = load_json('vehicles.json')
        self.trips = load_json('trips.json')
        self.services = load_json('services.json')
        
        # State variables
        self.edit_driver_row = None
        self.edit_vehicle_row = None
        self.edit_trip_row = None
        self.edit_service_row = None
        
        # Create tabs
        self.create_tabs()
        
        # Start periodic KΤΕΟ check
        self.after(1000, self.check_kteo_dates)

    def create_tabs(self):
        """Create all application tabs"""
        self.driver_tab()
        self.vehicle_tab()
        self.trip_tab()
        self.service_tab()
        self.search_tab()
        self.backup_tab()
        self.about_tab()

    def create_scrollable_table(self, parent, columns, height=10):
        """Create a frame with treeview and scrollbars"""
        frame = ttk.Frame(parent)
        frame.pack(fill='both', expand=True, padx=8, pady=6)
        
        # Create Treeview
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=height, selectmode="browse")
        
        # Create Scrollbars
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        
        return tree

    def driver_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Οδηγοί")
        
        # Title
        title_frame = ttk.Frame(frame)
        title_frame.pack(fill='x', pady=(0, 10))
        tk.Label(title_frame, text="Διαχείριση Οδηγών", font=self.title_font).pack(side='left', padx=12, pady=8)
        
        # Form
        form = ttk.Frame(frame)
        form.pack(fill='x', padx=12, pady=8)
        
        tk.Label(form, text="Όνομα Οδηγού:", width=15).pack(side='left')
        self.driver_name = ttk.Entry(form, width=30)
        self.driver_name.pack(side='left', padx=8)
        
        btn_frame = ttk.Frame(form)
        btn_frame.pack(side='right', padx=20)
        self.driver_add_btn = ttk.Button(btn_frame, text="➕ Καταχώρηση", command=self.add_driver)
        self.driver_add_btn.pack(side='left', padx=5)
        
        # Table
        self.driver_table = self.create_scrollable_table(frame, ("id", "Όνομα", "Επεξεργασία", "Διαγραφή"))
        self.driver_table.heading("id", text="ID", anchor='center')
        self.driver_table.heading("Όνομα", text="Όνομα Οδηγού", anchor='w')
        self.driver_table.heading("Επεξεργασία", text="Επεξεργασία", anchor='center')
        self.driver_table.heading("Διαγραφή", text="Διαγραφή", anchor='center')
        
        # Set column widths
        self.driver_table.column("id", width=50, anchor='center', stretch=False)
        self.driver_table.column("Όνομα", width=400, anchor='w')
        self.driver_table.column("Επεξεργασία", width=140, anchor='center')
        self.driver_table.column("Διαγραφή", width=140, anchor='center')
        self.driver_table["displaycolumns"] = ("Όνομα", "Επεξεργασία", "Διαγραφή")
        
        self.driver_table.bind('<Button-1>', self.driver_table_action)
        self.refresh_driver_table()

    def add_driver(self):
        name = self.driver_name.get().strip()
        if not name:
            messagebox.showwarning("Απαιτούμενο πεδίο", "Συμπληρώστε όνομα οδηγού")
            return
        
        # Check for duplicate names
        if any(d['name'].lower() == name.lower() for d in self.drivers):
            messagebox.showwarning("Duplicate", "Ο οδηγός υπάρχει ήδη στο σύστημα")
            return
            
        # Generate new ID
        new_id = max([d['id'] for d in self.drivers]) + 1 if self.drivers else 1
            
        self.drivers.append({'id': new_id, 'name': name})
        if save_json('drivers.json', self.drivers):
            self.driver_name.delete(0, 'end')
            self.refresh_driver_table()
            self.update_driver_comboboxes()
            messagebox.showinfo("Επιτυχία", "Ο οδηγός καταχωρήθηκε επιτυχώς")

    def driver_table_action(self, event):
        item = self.driver_table.identify_row(event.y)
        if not item: return
        
        col = self.driver_table.identify_column(event.x)
        values = self.driver_table.item(item, 'values')
        row_id = int(values[0]) - 1  # ID is stored as first value
        
        # FIXED: Corrected column indices
        if col == '#2':  # Edit column (Όνομα is #1, Επεξεργασία is #2)
            self.start_edit_driver(row_id)
        elif col == '#3':  # Delete column (Διαγραφή is #3)
            self.delete_driver(row_id)

    def delete_driver(self, row):
        driver = self.drivers[row]['name']
        if messagebox.askyesno("Επιβεβαίωση Διαγραφής", f"Θέλετε να διαγράψετε τον οδηγό {driver};"):
            self.drivers.pop(row)
            if save_json('drivers.json', self.drivers):
                # Reindex IDs
                for idx, driver in enumerate(self.drivers):
                    driver['id'] = idx + 1
                save_json('drivers.json', self.drivers)
                self.refresh_driver_table()
                self.update_driver_comboboxes()

    def refresh_driver_table(self):
        self.driver_table.delete(*self.driver_table.get_children())
        for driver in self.drivers:
            self.driver_table.insert('', 'end', values=(
                driver['id'], 
                driver['name'], 
                "✏️ Επεξεργασία", 
                "🗑️ Διαγραφή"
            ))

    def start_edit_driver(self, row):
        self.edit_driver_row = row
        self.driver_name.delete(0, 'end')
        self.driver_name.insert(0, self.drivers[row]['name'])
        self.driver_add_btn.config(text="💾 Ενημέρωση", command=self.finish_edit_driver)

    def finish_edit_driver(self):
        row = self.edit_driver_row
        name = self.driver_name.get().strip()
        if not name:
            messagebox.showwarning("Απαιτούμενο πεδίο", "Συμπληρώστε όνομα οδηγού")
            return
            
        # Check for duplicate names
        if any(i != row and d['name'].lower() == name.lower() for i, d in enumerate(self.drivers)):
            messagebox.showwarning("Duplicate", "Ο οδηγός υπάρχει ήδη στο σύστημα")
            return
            
        self.drivers[row]['name'] = name
        if save_json('drivers.json', self.drivers):
            self.driver_name.delete(0, 'end')
            self.refresh_driver_table()
            self.edit_driver_row = None
            self.driver_add_btn.config(text="➕ Καταχώρηση", command=self.add_driver)
            self.update_driver_comboboxes()
            messagebox.showinfo("Επιτυχία", "Τα στοιχεία ενημερώθηκαν επιτυχώς")

    def vehicle_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Οχήματα")
        
        # Title
        title_frame = ttk.Frame(frame)
        title_frame.pack(fill='x', pady=(0, 10))
        tk.Label(title_frame, text="Διαχείριση Οχημάτων & ΚΤΕΟ", font=self.title_font).pack(side='left', padx=12, pady=8)
        
        # Form
        form = ttk.Frame(frame)
        form.pack(fill='x', padx=12, pady=8)
        
        # Plate
        plate_frame = ttk.Frame(form)
        plate_frame.pack(side='left', padx=10)
        tk.Label(plate_frame, text="Πινακίδα:").pack(anchor='w')
        self.plate_input = ttk.Entry(plate_frame, width=15)
        self.plate_input.pack()
        
        # KΤΕΟ Passed
        passed_frame = ttk.Frame(form)
        passed_frame.pack(side='left', padx=10)
        tk.Label(passed_frame, text="ΚΤΕΟ πέρασε:").pack(anchor='w')
        self.kteo_passed = ttk.Entry(passed_frame, width=12)
        self.kteo_passed.pack()
        self.kteo_passed.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        
        # KΤΕΟ Next
        next_frame = ttk.Frame(form)
        next_frame.pack(side='left', padx=10)
        tk.Label(next_frame, text="Επόμενο ΚΤΕΟ:").pack(anchor='w')
        self.kteo_next = ttk.Entry(next_frame, width=12)
        self.kteo_next.pack()
        next_date = datetime.date.today() + datetime.timedelta(days=365)
        self.kteo_next.insert(0, next_date.strftime("%Y-%m-%d"))
        
        # Buttons
        btn_frame = ttk.Frame(form)
        btn_frame.pack(side='right', padx=20)
        self.vehicle_add_btn = ttk.Button(btn_frame, text="➕ Καταχώρηση", command=self.add_vehicle)
        self.vehicle_add_btn.pack(pady=5)
        
        # Table
        self.vehicle_table = self.create_scrollable_table(frame, 
            ("id", "Πινακίδα", "ΚΤΕΟ πέρασε", "ΚΤΕΟ επόμενο", "Κατάσταση", "Επεξεργασία", "Διαγραφή"))
        
        self.vehicle_table.heading("id", text="ID", anchor='center')
        self.vehicle_table.heading("Πινακίδα", text="Πινακίδα", anchor='w')
        self.vehicle_table.heading("ΚΤΕΟ πέρασε", text="ΚΤΕΟ πέρασε", anchor='center')
        self.vehicle_table.heading("ΚΤΕΟ επόμενο", text="ΚΤΕΟ επόμενο", anchor='center')
        self.vehicle_table.heading("Κατάσταση", text="Κατάσταση", anchor='center')
        self.vehicle_table.heading("Επεξεργασία", text="Επεξεργασία", anchor='center')
        self.vehicle_table.heading("Διαγραφή", text="Διαγραφή", anchor='center')
        
        # Set column widths
        self.vehicle_table.column("id", width=50, anchor='center', stretch=False)
        self.vehicle_table.column("Πινακίδα", width=180, anchor='w')
        self.vehicle_table.column("ΚΤΕΟ πέρασε", width=140, anchor='center')
        self.vehicle_table.column("ΚΤΕΟ επόμενο", width=140, anchor='center')
        self.vehicle_table.column("Κατάσταση", width=140, anchor='center')
        self.vehicle_table.column("Επεξεργασία", width=140, anchor='center')
        self.vehicle_table.column("Διαγραφή", width=140, anchor='center')
        self.vehicle_table["displaycolumns"] = ("Πινακίδα", "ΚΤΕΟ πέρασε", "ΚΤΕΟ επόμενο", "Κατάσταση", "Επεξεργασία", "Διαγραφή")
        
        # Configure status colors
        self.vehicle_table.tag_configure("danger", background="#ffcccc")
        self.vehicle_table.tag_configure("warning", background="#fff0cc")
        self.vehicle_table.tag_configure("info", background="#e6f3ff")
        self.vehicle_table.tag_configure("success", background="#ccffcc")
        self.vehicle_table.tag_configure("secondary", background="#f0f0f0")
        
        self.vehicle_table.bind('<Button-1>', self.vehicle_table_action)
        self.refresh_vehicle_table()

    def add_vehicle(self):
        plate = self.plate_input.get().strip().upper()
        passed = self.kteo_passed.get().strip()
        next_ = self.kteo_next.get().strip()
        
        # Validation
        if not plate:
            messagebox.showwarning("Απαιτούμενο πεδίο", "Συμπληρώστε πινακίδα οχήματος")
            return
            
        if not validate_date(passed):
            messagebox.showwarning("Μη έγκυρη ημερομηνία", "Μη έγκυρη ημερομηνία ΚΤΕΟ (YYYY-MM-DD)")
            return
            
        if not validate_date(next_):
            messagebox.showwarning("Μη έγκυρη ημερομηνία", "Μη έγκυρη ημερομηνία επόμενου ΚΤΕΟ (YYYY-MM-DD)")
            return
            
        # Check for duplicate plates
        if any(v['plate'].upper() == plate for v in self.vehicles):
            messagebox.showwarning("Duplicate", "Η πινακίδα υπάρχει ήδη στο σύστημα")
            return
            
        # Generate new ID
        new_id = max([v['id'] for v in self.vehicles]) + 1 if self.vehicles else 1
            
        self.vehicles.append({
            'id': new_id,
            'plate': plate,
            'kteo_passed': passed,
            'kteo_next': next_
        })
        
        if save_json('vehicles.json', self.vehicles):
            self.plate_input.delete(0, 'end')
            self.refresh_vehicle_table()
            self.update_vehicle_comboboxes()
            messagebox.showinfo("Επιτυχία", "Το όχημα καταχωρήθηκε επιτυχώς")

    def vehicle_table_action(self, event):
        item = self.vehicle_table.identify_row(event.y)
        if not item: return
        
        col = self.vehicle_table.identify_column(event.x)
        values = self.vehicle_table.item(item, 'values')
        row_id = int(values[0]) - 1  # ID is stored as first value
        
        # FIXED: Corrected column indices
        if col == '#5':  # Edit column (Επεξεργασία is #5)
            self.start_edit_vehicle(row_id)
        elif col == '#6':  # Delete column (Διαγραφή is #6)
            self.delete_vehicle(row_id)

    def delete_vehicle(self, row):
        plate = self.vehicles[row]['plate']
        if messagebox.askyesno("Επιβεβαίωση Διαγραφής", f"Θέλετε να διαγράψετε το όχημα {plate};"):
            self.vehicles.pop(row)
            if save_json('vehicles.json', self.vehicles):
                # Reindex IDs
                for idx, vehicle in enumerate(self.vehicles):
                    vehicle['id'] = idx + 1
                save_json('vehicles.json', self.vehicles)
                self.refresh_vehicle_table()
                self.update_vehicle_comboboxes()

    def refresh_vehicle_table(self):
        self.vehicle_table.delete(*self.vehicle_table.get_children())
        for vehicle in self.vehicles:
            status = self.get_kteo_status(vehicle['kteo_next'])
            status_text, style = self.get_status_display(status)
            
            self.vehicle_table.insert('', 'end', values=(
                vehicle['id'],
                vehicle['plate'],
                vehicle['kteo_passed'],
                vehicle['kteo_next'],
                status_text,
                "✏️ Επεξεργασία",
                "🗑️ Διαγραφή"
            ), tags=(style,))

    def get_kteo_status(self, date_next):
        today = datetime.date.today()
        try:
            kteo_next = datetime.datetime.strptime(date_next, "%Y-%m-%d").date()
            delta = (kteo_next - today).days
            
            if delta < 0:
                return "expired"
            elif delta < 15:
                return "warning"
            elif delta < 30:
                return "notice"
            else:
                return "ok"
        except Exception:
            return "error"

    def get_status_display(self, status):
        status_map = {
            "expired": ("ΛΗΓΜΕΝΟ", "danger"),
            "warning": ("ΠΡΟΣΕΧΩΣ", "warning"),
            "notice": ("ΚΟΝΤΑ", "info"),
            "ok": ("ΕΝΤΑΞΕΙ", "success"),
            "error": ("ΛΑΘΟΣ", "danger")
        }
        return status_map.get(status, ("ΑΓΝΩΣΤΟ", "secondary"))

    def start_edit_vehicle(self, row):
        self.edit_vehicle_row = row
        v = self.vehicles[row]
        self.plate_input.delete(0, 'end')
        self.plate_input.insert(0, v['plate'])
        self.kteo_passed.delete(0, 'end')
        self.kteo_passed.insert(0, v['kteo_passed'])
        self.kteo_next.delete(0, 'end')
        self.kteo_next.insert(0, v['kteo_next'])
        self.vehicle_add_btn.config(text="💾 Ενημέρωση", command=self.finish_edit_vehicle)

    def finish_edit_vehicle(self):
        row = self.edit_vehicle_row
        plate = self.plate_input.get().strip().upper()
        passed = self.kteo_passed.get().strip()
        next_ = self.kteo_next.get().strip()
        
        # Validation
        if not plate:
            messagebox.showwarning("Απαιτούμενο πεδίο", "Συμπληρώστε πινακίδα οχήματος")
            return
            
        if not validate_date(passed):
            messagebox.showwarning("Μη έγκυρη ημερομηνία", "Μη έγκυρη ημερομηνία ΚΤΕΟ (YYYY-MM-DD)")
            return
            
        if not validate_date(next_):
            messagebox.showwarning("Μη έγκυρη ημερομηνία", "Μη έγκυρη ημερομηνία επόμενου ΚΤΕΟ (YYYY-MM-DD)")
            return
            
        # Check for duplicate plates
        if any(i != row and v['plate'].upper() == plate for i, v in enumerate(self.vehicles)):
            messagebox.showwarning("Duplicate", "Η πινακίδα υπάρχει ήδη στο σύστημα")
            return
            
        self.vehicles[row]['plate'] = plate
        self.vehicles[row]['kteo_passed'] = passed
        self.vehicles[row]['kteo_next'] = next_
        
        if save_json('vehicles.json', self.vehicles):
            self.plate_input.delete(0, 'end')
            self.refresh_vehicle_table()
            self.edit_vehicle_row = None
            self.vehicle_add_btn.config(text="➕ Καταχώρηση", command=self.add_vehicle)
            self.update_vehicle_comboboxes()
            messagebox.showinfo("Επιτυχία", "Τα στοιχεία ενημερώθηκαν επιτυχώς")

    def check_kteo_dates(self):
        alerts = []
        for v in self.vehicles:
            status = self.get_kteo_status(v['kteo_next'])
            if status == "expired":
                alerts.append(f"🚨 Όχημα {v['plate']} έχει ληγμένο ΚΤΕΟ!")
            elif status == "warning":
                alerts.append(f"⚠️ Όχημα {v['plate']} χρειάζεται ΚΤΕΟ εντός 15 ημερών!")
        
        if alerts:
            messagebox.showwarning("Ειδοποίηση ΚΤΕΟ", "\n".join(alerts))
        
        self.refresh_vehicle_table()
        self.after(60 * 60 * 1000, self.check_kteo_dates)  # Check every hour

    def trip_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Διαδρομές")
        
        # Title
        title_frame = ttk.Frame(frame)
        title_frame.pack(fill='x', pady=(0, 10))
        tk.Label(title_frame, text="Καταγραφή Διαδρομών", font=self.title_font).pack(side='left', padx=12, pady=8)
        
        # Form
        form = ttk.LabelFrame(frame, text="Στοιχεία Διαδρομής")
        form.pack(fill='x', padx=12, pady=8)
        
        # Driver and Vehicle
        row1 = ttk.Frame(form)
        row1.pack(fill='x', padx=10, pady=5)
        
        tk.Label(row1, text="Οδηγός:", width=12).pack(side='left')
        self.trip_driver = ttk.Combobox(row1, values=[d['name'] for d in self.drivers], width=25)
        self.trip_driver.pack(side='left', padx=8)
        
        tk.Label(row1, text="Όχημα:", width=12).pack(side='left')
        self.trip_vehicle = ttk.Combobox(row1, values=[v['plate'] for v in self.vehicles], width=12)
        self.trip_vehicle.pack(side='left', padx=8)
        
        # Departure
        row2 = ttk.Frame(form)
        row2.pack(fill='x', padx=10, pady=5)
        
        tk.Label(row2, text="Αναχώρηση:", width=12).pack(side='left')
        
        tk.Label(row2, text="Ημ/νία:").pack(side='left')
        self.trip_depart_date = ttk.Entry(row2, width=12)
        self.trip_depart_date.pack(side='left', padx=2)
        self.trip_depart_date.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        
        tk.Label(row2, text="Ώρα:").pack(side='left', padx=(10, 2))
        self.trip_depart_time = ttk.Entry(row2, width=7)
        self.trip_depart_time.pack(side='left')
        self.trip_depart_time.insert(0, datetime.datetime.now().strftime("%H:%M"))
        
        # Arrival
        row3 = ttk.Frame(form)
        row3.pack(fill='x', padx=10, pady=5)
        
        tk.Label(row3, text="Άφιξη:", width=12).pack(side='left')
        
        tk.Label(row3, text="Ημ/νία:").pack(side='left')
        self.trip_arrive_date = ttk.Entry(row3, width=12)
        self.trip_arrive_date.pack(side='left', padx=2)
        self.trip_arrive_date.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        
        tk.Label(row3, text="Ώρα:").pack(side='left', padx=(10, 2))
        self.trip_arrive_time = ttk.Entry(row3, width=7)
        self.trip_arrive_time.pack(side='left')
        self.trip_arrive_time.insert(0, datetime.datetime.now().strftime("%H:%M"))
        
        # Details
        details_frame = ttk.LabelFrame(frame, text="Λεπτομέρειες Διαδρομής")
        details_frame.pack(fill='x', padx=12, pady=8)
        
        self.trip_details = ScrolledText(details_frame, height=4, font=self.font)
        self.trip_details.pack(fill='x', padx=10, pady=5)
        
        # Signature
        sig_frame = ttk.LabelFrame(frame, text="Υπογραφή Οδηγού")
        sig_frame.pack(fill='x', padx=12, pady=8)
        
        sig_row = ttk.Frame(sig_frame)
        sig_row.pack(fill='x', padx=10, pady=5)
        
        self.signature_pad = SignaturePad(sig_row, width=400, height=180)
        self.signature_pad.pack(side='left', padx=8)
        
        btn_frame = ttk.Frame(sig_row)
        btn_frame.pack(side='left', fill='y', padx=8)
        
        self.sign_btn = ttk.Button(btn_frame, text="🧹 Καθαρισμός", command=self.signature_pad.clear)
        self.sign_btn.pack(pady=5, fill='x')
        
        self.trip_add_btn = ttk.Button(btn_frame, text="➕ Καταχώρηση", command=self.add_trip)
        self.trip_add_btn.pack(pady=5, fill='x')
        
        # Table
        table_frame = ttk.LabelFrame(frame, text="Ιστορικό Διαδρομών")
        table_frame.pack(fill='both', expand=True, padx=12, pady=8)
        
        self.trip_table = self.create_scrollable_table(table_frame, 
            ("id", "Οδηγός", "Όχημα", "Αναχώρηση", "Άφιξη", "Επεξεργασία", "Διαγραφή"))
        
        self.trip_table.heading("id", text="ID", anchor='center')
        self.trip_table.heading("Οδηγός", text="Οδηγός", anchor='w')
        self.trip_table.heading("Όχημα", text="Όχημα", anchor='w')
        self.trip_table.heading("Αναχώρηση", text="Αναχώρηση", anchor='center')
        self.trip_table.heading("Άφιξη", text="Άφιξη", anchor='center')
        self.trip_table.heading("Επεξεργασία", text="Επεξεργασία", anchor='center')
        self.trip_table.heading("Διαγραφή", text="Διαγραφή", anchor='center')
        
        # Set column widths
        self.trip_table.column("id", width=50, anchor='center', stretch=False)
        self.trip_table.column("Οδηγός", width=200, anchor='w')
        self.trip_table.column("Όχημα", width=120, anchor='w')
        self.trip_table.column("Αναχώρηση", width=180, anchor='center')
        self.trip_table.column("Άφιξη", width=180, anchor='center')
        self.trip_table.column("Επεξεργασία", width=140, anchor='center')
        self.trip_table.column("Διαγραφή", width=140, anchor='center')
        self.trip_table["displaycolumns"] = ("Οδηγός", "Όχημα", "Αναχώρηση", "Άφιξη", "Επεξεργασία", "Διαγραφή")
        
        self.trip_table.bind('<Button-1>', self.trip_table_action)
        
        # Export button
        export_frame = ttk.Frame(frame)
        export_frame.pack(pady=8)
        export_btn = ttk.Button(export_frame, text="⤴️ Εξαγωγή σε PDF", command=self.export_trip_pdf)
        export_btn.pack()
        
        self.refresh_trip_table()

    def add_trip(self):
        driver = self.trip_driver.get().strip()
        vehicle = self.trip_vehicle.get().strip()
        depart_date = self.trip_depart_date.get().strip()
        depart_time = self.trip_depart_time.get().strip()
        arrive_date = self.trip_arrive_date.get().strip()
        arrive_time = self.trip_arrive_time.get().strip()
        details = self.trip_details.get('1.0', 'end-1c').strip()
        
        # Validation
        if not driver:
            messagebox.showwarning("Απαιτούμενο πεδίο", "Επιλέξτε οδηγό")
            return
            
        if not vehicle:
            messagebox.showwarning("Απαιτούμενο πεδίο", "Επιλέξτε όχημα")
            return
            
        if not validate_date(depart_date):
            messagebox.showwarning("Μη έγκυρη ημερομηνία", "Μη έγκυρη ημερομηνία αναχώρησης (YYYY-MM-DD)")
            return
            
        if not validate_time(depart_time):
            messagebox.showwarning("Μη έγκυρη ώρα", "Μη έγκυρη ώρα αναχώρησης (HH:MM)")
            return
            
        if not validate_date(arrive_date):
            messagebox.showwarning("Μη έγκυρη ημερομηνία", "Μη έγκυρη ημερομηνία άφιξης (YYYY-MM-DD)")
            return
            
        if not validate_time(arrive_time):
            messagebox.showwarning("Μη έγκυρη ώρα", "Μη έγκυρη ώρα άφιξης (HH:MM)")
            return
            
        # Create trip record
        # Generate new ID
        new_id = max([t['id'] for t in self.trips]) + 1 if self.trips else 1
            
        trip = {
            'id': new_id,
            'driver': driver,
            'vehicle': vehicle,
            'depart': f"{depart_date} {depart_time}",
            'arrive': f"{arrive_date} {arrive_time}",
            'details': details,
            'signature': f"signature_{new_id}.png"
        }
        
        # Save signature
        sig_path = os.path.join(DATA_DIR, trip['signature'])
        if not self.signature_pad.save(sig_path):
            messagebox.showwarning("Σφάλμα Αρχείου", "Σφάλμα αποθήκευσης υπογραφής")
            return
            
        self.trips.append(trip)
        if save_json('trips.json', self.trips):
            self.trip_details.delete('1.0', 'end')
            self.signature_pad.clear()
            self.refresh_trip_table()
            messagebox.showinfo("Επιτυχία", "Η διαδρομή καταχωρήθηκε επιτυχώς")

    def trip_table_action(self, event):
        item = self.trip_table.identify_row(event.y)
        if not item: return
        
        col = self.trip_table.identify_column(event.x)
        values = self.trip_table.item(item, 'values')
        row_id = int(values[0]) - 1  # ID is stored as first value
        
        # FIXED: Corrected column indices
        if col == '#5':  # Edit column (Επεξεργασία is #5)
            self.start_edit_trip(row_id)
        elif col == '#6':  # Delete column (Διαγραφή is #6)
            self.delete_trip(row_id)

    def delete_trip(self, row):
        if messagebox.askyesno("Επιβεβαίωση Διαγραφής", "Θέλετε να διαγράψετε αυτή τη διαδρομή;"):
            # Delete signature file
            sig_file = self.trips[row]['signature']
            sig_path = os.path.join(DATA_DIR, sig_file)
            if os.path.exists(sig_path):
                try:
                    os.remove(sig_path)
                except:
                    pass
                    
            self.trips.pop(row)
            if save_json('trips.json', self.trips):
                # Reindex IDs
                for idx, trip in enumerate(self.trips):
                    trip['id'] = idx + 1
                save_json('trips.json', self.trips)
                self.refresh_trip_table()

    def refresh_trip_table(self):
        self.trip_table.delete(*self.trip_table.get_children())
        for trip in self.trips:
            self.trip_table.insert('', 'end', values=(
                trip['id'],
                trip['driver'],
                trip['vehicle'],
                trip['depart'],
                trip['arrive'],
                "✏️ Επεξεργασία",
                "🗑️ Διαγραφή"
            ))

    def start_edit_trip(self, row):
        self.edit_trip_row = row
        t = self.trips[row]
        self.trip_driver.set(t['driver'])
        self.trip_vehicle.set(t['vehicle'])
        
        d_date, d_time = t['depart'].split()
        a_date, a_time = t['arrive'].split()
        
        self.trip_depart_date.delete(0, 'end')
        self.trip_depart_date.insert(0, d_date)
        self.trip_depart_time.delete(0, 'end')
        self.trip_depart_time.insert(0, d_time)
        
        self.trip_arrive_date.delete(0, 'end')
        self.trip_arrive_date.insert(0, a_date)
        self.trip_arrive_time.delete(0, 'end')
        self.trip_arrive_time.insert(0, a_time)
        
        self.trip_details.delete('1.0', 'end')
        self.trip_details.insert('1.0', t['details'])
        
        sig_path = os.path.join(DATA_DIR, t['signature'])
        self.signature_pad.load(sig_path)
        
        self.trip_add_btn.config(text="💾 Ενημέρωση", command=self.finish_edit_trip)

    def finish_edit_trip(self):
        row = self.edit_trip_row
        driver = self.trip_driver.get().strip()
        vehicle = self.trip_vehicle.get().strip()
        depart_date = self.trip_depart_date.get().strip()
        depart_time = self.trip_depart_time.get().strip()
        arrive_date = self.trip_arrive_date.get().strip()
        arrive_time = self.trip_arrive_time.get().strip()
        details = self.trip_details.get('1.0', 'end-1c').strip()
        
        # Validation
        if not driver:
            messagebox.showwarning("Απαιτούμενο πεδίο", "Επιλέξτε οδηγό")
            return
            
        if not vehicle:
            messagebox.showwarning("Απαιτούμενο πεδίο", "Επιλέξτε όχημα")
            return
            
        if not validate_date(depart_date):
            messagebox.showwarning("Μη έγκυρη ημερομηνία", "Μη έγκυρη ημερομηνία αναχώρησης (YYYY-MM-DD)")
            return
            
        if not validate_time(depart_time):
            messagebox.showwarning("Μη έγκυρη ώρα", "Μη έγκυρη ώρα αναχώρησης (HH:MM)")
            return
            
        if not validate_date(arrive_date):
            messagebox.showwarning("Μη έγκυρη ημερομηνία", "Μη έγκυρη ημερομηνία άφιξης (YYYY-MM-DD)")
            return
            
        if not validate_time(arrive_time):
            messagebox.showwarning("Μη έγκυρη ώρα", "Μη έγκυρη ώρα άφιξης (HH:MM)")
            return
            
        # Update trip record
        self.trips[row]['driver'] = driver
        self.trips[row]['vehicle'] = vehicle
        self.trips[row]['depart'] = f"{depart_date} {depart_time}"
        self.trips[row]['arrive'] = f"{arrive_date} {arrive_time}"
        self.trips[row]['details'] = details
        
        # Save signature
        sig_path = os.path.join(DATA_DIR, self.trips[row]['signature'])
        if not self.signature_pad.save(sig_path):
            messagebox.showwarning("Σφάλμα Αρχείου", "Σφάλμα αποθήκευσης υπογραφής")
            return
            
        if save_json('trips.json', self.trips):
            self.trip_details.delete('1.0', 'end')
            self.signature_pad.clear()
            self.refresh_trip_table()
            self.edit_trip_row = None
            self.trip_add_btn.config(text="➕ Καταχώρηση", command=self.add_trip)
            messagebox.showinfo("Επιτυχία", "Η διαδρομή ενημερώθηκε επιτυχώς")

    def export_trip_pdf(self):
        selected = self.trip_table.selection()
        if not selected:
            messagebox.showwarning("Δεν έχει επιλεγεί εγγραφή", "Επιλέξτε μια διαδρομή για εξαγωγή")
            return
            
        idx = self.trip_table.index(selected[0])
        trip = self.trips[idx]
        
        fname = filedialog.asksaveasfilename(
            defaultextension=".pdf", 
            filetypes=[("PDF Files", "*.pdf")],
            title="Αποθήκευση PDF"
        )
        
        if not fname:
            return
            
        try:
            # Create PDF document
            doc = SimpleDocTemplate(fname, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []
            
            # Title
            title_style = styles['Heading1']
            title_style.alignment = 1  # Center alignment
            title = Paragraph("<b>ΚΑΤΑΓΓΕΛΙΑ ΔΙΑΔΡΟΜΗΣ</b>", title_style)
            elements.append(title)
            elements.append(Spacer(1, 24))
            
            # Driver and Vehicle
            driver_text = f"<b>Οδηγός:</b> {trip['driver']}"
            vehicle_text = f"<b>Όχημα:</b> {trip['vehicle']}"
            
            info_style = styles['BodyText']
            driver_para = Paragraph(driver_text, info_style)
            vehicle_para = Paragraph(vehicle_text, info_style)
            
            elements.append(driver_para)
            elements.append(Spacer(1, 12))
            elements.append(vehicle_para)
            elements.append(Spacer(1, 24))
            
            # Departure and Arrival
            depart_text = f"<b>Αναχώρηση:</b> {trip['depart']}"
            arrive_text = f"<b>Άφιξη:</b> {trip['arrive']}"
            
            depart_para = Paragraph(depart_text, info_style)
            arrive_para = Paragraph(arrive_text, info_style)
            
            elements.append(depart_para)
            elements.append(Spacer(1, 12))
            elements.append(arrive_para)
            elements.append(Spacer(1, 24))
            
            # Details
            details_title = Paragraph("<b>Λεπτομέρειες Διαδρομής:</b>", info_style)
            elements.append(details_title)
            elements.append(Spacer(1, 8))
            
            details_style = styles['BodyText']
            details_para = Paragraph(trip['details'], details_style)
            elements.append(details_para)
            elements.append(Spacer(1, 36))
            
            # Signature
            signature_path = os.path.join(DATA_DIR, trip['signature'])
            if os.path.exists(signature_path):
                img = Image.open(signature_path)
                img_width, img_height = img.size
                aspect = img_height / float(img_width)
                max_width = 300
                max_height = max_width * aspect
                
                # Draw image
                c = canvas.Canvas(fname)
                c.drawImage(signature_path, 100, 150, width=max_width, height=max_height)
                
                # Add caption
                c.setFont("Helvetica", 10)
                c.drawString(100, 140, "Υπογραφή Οδηγού:")
                c.save()
            
            # Build PDF
            doc.build(elements)
            messagebox.showinfo("Εξαγωγή Ολοκληρώθηκε", "Το PDF δημιουργήθηκε επιτυχώς")
            
        except Exception as e:
            log_error(f"PDF export error: {str(e)}")
            messagebox.showerror("Σφάλμα Εξαγωγής", f"Σφάλμα δημιουργίας PDF: {str(e)}")

    def service_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Service")
        
        # Title
        title_frame = ttk.Frame(frame)
        title_frame.pack(fill='x', pady=(0, 10))
        tk.Label(title_frame, text="Καταγραφή Service Οχημάτων", font=self.title_font).pack(side='left', padx=12, pady=8)
        
        # Form
        form = ttk.Frame(frame)
        form.pack(fill='x', padx=12, pady=8)
        
        # Vehicle
        vehicle_frame = ttk.Frame(form)
        vehicle_frame.pack(side='left', padx=10)
        tk.Label(vehicle_frame, text="Όχημα:").pack(anchor='w')
        # CORRECTED: Changed ttt.Combobox to ttk.Combobox
        self.service_vehicle = ttk.Combobox(vehicle_frame, values=[v['plate'] for v in self.vehicles], width=15)
        self.service_vehicle.pack()
        
        # Date
        date_frame = ttk.Frame(form)
        date_frame.pack(side='left', padx=10)
        tk.Label(date_frame, text="Ημερομηνία:").pack(anchor='w')
        self.service_date = ttk.Entry(date_frame, width=12)
        self.service_date.pack()
        self.service_date.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        
        # Details
        detail_frame = ttk.Frame(form)
        detail_frame.pack(side='left', padx=10, fill='x', expand=True)
        tk.Label(detail_frame, text="Λεπτομέρειες:").pack(anchor='w')
        self.service_detail = ttk.Entry(detail_frame)
        self.service_detail.pack(fill='x', padx=(0, 10))
        
        # Buttons
        btn_frame = ttk.Frame(form)
        btn_frame.pack(side='right', padx=20)
        self.service_add_btn = ttk.Button(btn_frame, text="➕ Καταχώρηση", command=self.add_service)
        self.service_add_btn.pack(pady=5)
        
        # Table
        self.service_table = self.create_scrollable_table(frame, 
            ("id", "Όχημα", "Ημερομηνία", "Λεπτομέρειες", "Επεξεργασία", "Διαγραφή"))
        
        self.service_table.heading("id", text="ID", anchor='center')
        self.service_table.heading("Όχημα", text="Όχημα", anchor='w')
        self.service_table.heading("Ημερομηνία", text="Ημερομηνία", anchor='center')
        self.service_table.heading("Λεπτομέρειες", text="Λεπτομέρειες", anchor='w')
        self.service_table.heading("Επεξεργασία", text="Επεξεργασία", anchor='center')
        self.service_table.heading("Διαγραφή", text="Διαγραφή", anchor='center')
        
        # Set column widths
        self.service_table.column("id", width=50, anchor='center', stretch=False)
        self.service_table.column("Όχημα", width=150, anchor='w')
        self.service_table.column("Ημερομηνία", width=120, anchor='center')
        self.service_table.column("Λεπτομέρειες", width=400, anchor='w')
        self.service_table.column("Επεξεργασία", width=140, anchor='center')
        self.service_table.column("Διαγραφή", width=140, anchor='center')
        self.service_table["displaycolumns"] = ("Όχημα", "Ημερομηνία", "Λεπτομέρειες", "Επεξεργασία", "Διαγραφή")
        
        self.service_table.bind('<Button-1>', self.service_table_action)
        self.refresh_service_table()

    def add_service(self):
        vehicle = self.service_vehicle.get().strip()
        date = self.service_date.get().strip()
        details = self.service_detail.get().strip()
        
        # Validation
        if not vehicle:
            messagebox.showwarning("Απαιτούμενο πεδίο", "Επιλέξτε όχημα")
            return
            
        if not validate_date(date):
            messagebox.showwarning("Μη έγκυρη ημερομηνία", "Μη έγκυρη ημερομηνία (YYYY-MM-DD)")
            return
            
        if not details:
            messagebox.showwarning("Απαιτούμενο πεδίο", "Συμπληρώστε λεπτομέρειες service")
            return
            
        # Generate new ID
        new_id = max([s['id'] for s in self.services]) + 1 if self.services else 1
            
        self.services.append({
            'id': new_id,
            'vehicle': vehicle,
            'date': date,
            'details': details
        })
        
        if save_json('services.json', self.services):
            self.service_detail.delete(0, 'end')
            self.refresh_service_table()
            messagebox.showinfo("Επιτυχία", "Το service καταχωρήθηκε επιτυχώς")

    def service_table_action(self, event):
        item = self.service_table.identify_row(event.y)
        if not item: return
        
        col = self.service_table.identify_column(event.x)
        values = self.service_table.item(item, 'values')
        row_id = int(values[0]) - 1  # ID is stored as first value
        
        # FIXED: Corrected column indices
        if col == '#4':  # Edit column (Επεξεργασία is #4)
            self.start_edit_service(row_id)
        elif col == '#5':  # Delete column (Διαγραφή is #5)
            self.delete_service(row_id)

    def delete_service(self, row):
        if messagebox.askyesno("Επιβεβαίωση Διαγραφής", "Θέλετε να διαγράψετε αυτό το service;"):
            self.services.pop(row)
            if save_json('services.json', self.services):
                # Reindex IDs
                for idx, service in enumerate(self.services):
                    service['id'] = idx + 1
                save_json('services.json', self.services)
                self.refresh_service_table()

    def refresh_service_table(self):
        self.service_table.delete(*self.service_table.get_children())
        for service in self.services:
            self.service_table.insert('', 'end', values=(
                service['id'],
                service['vehicle'],
                service['date'],
                service['details'],
                "✏️ Επεξεργασία",
                "🗑️ Διαγραφή"
            ))

    def start_edit_service(self, row):
        self.edit_service_row = row
        s = self.services[row]
        self.service_vehicle.set(s['vehicle'])
        self.service_date.delete(0, 'end')
        self.service_date.insert(0, s['date'])
        self.service_detail.delete(0, 'end')
        self.service_detail.insert(0, s['details'])
        self.service_add_btn.config(text="💾 Ενημέρωση", command=self.finish_edit_service)

    def finish_edit_service(self):
        row = self.edit_service_row
        vehicle = self.service_vehicle.get().strip()
        date = self.service_date.get().strip()
        details = self.service_detail.get().strip()
        
        # Validation
        if not vehicle:
            messagebox.showwarning("Απαιτούμενο πεδίο", "Επιλέξτε όχημα")
            return
            
        if not validate_date(date):
            messagebox.showwarning("Μη έγκυρη ημερομηνία", "Μη έγκυρη ημερομηνία (YYYY-MM-DD)")
            return
            
        if not details:
            messagebox.showwarning("Απαιτούμενο πεδίο", "Συμπληρώστε λεπτομέρειες service")
            return
            
        self.services[row]['vehicle'] = vehicle
        self.services[row]['date'] = date
        self.services[row]['details'] = details
        
        if save_json('services.json', self.services):
            self.service_detail.delete(0, 'end')
            self.refresh_service_table()
            self.edit_service_row = None
            self.service_add_btn.config(text="➕ Καταχώρηση", command=self.add_service)
            messagebox.showinfo("Επιτυχία", "Το service ενημερώθηκε επιτυχώς")

    def search_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Αναζήτηση")
        
        # Title
        title_frame = ttk.Frame(frame)
        title_frame.pack(fill='x', pady=(0, 10))
        tk.Label(title_frame, text="🔍 Αναζήτηση Σε Όλα Τα Δεδομένα", font=self.title_font).pack(side='left', padx=12, pady=8)
        
        # Search form
        form = ttk.Frame(frame)
        form.pack(fill='x', padx=12, pady=8)
        
        tk.Label(form, text="Αναζήτηση:", width=10).pack(side='left')
        self.search_input = ttk.Entry(form)
        self.search_input.pack(side='left', padx=8, fill='x', expand=True)
        self.search_input.bind('<Return>', lambda e: self.do_search())
        
        self.search_btn = ttk.Button(form, text="🔍 Εκτέλεση Αναζήτησης", command=self.do_search)
        self.search_btn.pack(side='right', padx=8)
        
        # Results
        results_frame = ttk.LabelFrame(frame, text="Αποτελέσματα Αναζήτησης")
        results_frame.pack(fill='both', expand=True, padx=12, pady=8)
        
        self.search_results = ScrolledText(results_frame, font=self.font, state='disabled')
        self.search_results.pack(fill='both', expand=True, padx=10, pady=10)

    def do_search(self):
        query = self.search_input.get().strip().lower()
        if not query:
            messagebox.showwarning("Απαιτούμενο πεδίο", "Εισάγετε όρο αναζήτησης")
            return
            
        results = []
        
        # Search drivers
        for d in self.drivers:
            if query in d['name'].lower():
                results.append(f"ΟΔΗΓΟΣ: {d['name']}")
        
        # Search vehicles
        for v in self.vehicles:
            plate_match = query in v['plate'].lower()
            passed_match = query in v['kteo_passed'].lower()
            next_match = query in v['kteo_next'].lower()
            
            if plate_match or passed_match or next_match:
                status = self.get_kteo_status(v['kteo_next'])
                status_text, _ = self.get_status_display(status)
                results.append(f"ΟΧΗΜΑ: {v['plate']} (ΚΤΕΟ: {v['kteo_passed']} - {v['kteo_next']}, Κατάσταση: {status_text})")
        
        # Search trips
        for t in self.trips:
            driver_match = query in t['driver'].lower()
            vehicle_match = query in t['vehicle'].lower()
            details_match = query in t['details'].lower()
            depart_match = query in t['depart'].lower()
            arrive_match = query in t['arrive'].lower()
            
            if driver_match or vehicle_match or details_match or depart_match or arrive_match:
                results.append(f"ΔΙΑΔΡΟΜΗ: {t['driver']} - {t['vehicle']} ({t['depart']} → {t['arrive']})\n   Λεπτομέρειες: {t['details'][:100]}{'...' if len(t['details']) > 100 else ''}")
        
        # Search services
        for s in self.services:
            vehicle_match = query in s['vehicle'].lower()
            details_match = query in s['details'].lower()
            date_match = query in s['date'].lower()
            
            if vehicle_match or details_match or date_match:
                results.append(f"SERVICE: {s['vehicle']} ({s['date']})\n   Λεπτομέρειες: {s['details'][:100]}{'...' if len(s['details']) > 100 else ''}")
        
        # Display results
        self.search_results.config(state='normal')
        self.search_results.delete('1.0', 'end')
        
        if results:
            result_text = "\n\n".join(results)
            self.search_results.insert('1.0', f"Βρέθηκαν {len(results)} αποτελέσματα:\n\n{result_text}")
        else:
            self.search_results.insert('1.0', "Δεν βρέθηκαν αποτελέσματα για την αναζήτησή σας.")
        
        self.search_results.config(state='disabled')

    def backup_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Backup")
        
        # Title
        title_frame = ttk.Frame(frame)
        title_frame.pack(fill='x', pady=(0, 10))
        tk.Label(title_frame, text="🗄️ Backup & Εισαγωγή Δεδομένων", font=self.title_font).pack(side='left', padx=12, pady=8)
        
        # Backup section
        backup_frame = ttk.LabelFrame(frame, text="Δημιουργία Backup")
        backup_frame.pack(fill='x', padx=12, pady=8)
        
        tk.Label(backup_frame, text="Δημιουργήστε αντίγραφο ασφαλείας των δεδομένων σας:").pack(anchor='w', padx=10, pady=5)
        
        self.backup_path = ttk.Entry(backup_frame)
        self.backup_path.pack(fill='x', padx=10, pady=5)
        self.backup_path.insert(0, os.path.abspath(BACKUP_DIR))
        
        path_btn_frame = ttk.Frame(backup_frame)
        path_btn_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(path_btn_frame, text="📂 Επιλογή Φακέλου", command=self.select_backup_folder).pack(side='left', padx=(0, 10))
        
        self.backup_btn = ttk.Button(path_btn_frame, text="💾 Δημιουργία Backup", command=self.do_backup)
        self.backup_btn.pack(side='right')
        
        # Restore section
        restore_frame = ttk.LabelFrame(frame, text="Επαναφορά Δεδομένων")
        restore_frame.pack(fill='x', padx=12, pady=8)
        
        tk.Label(restore_frame, text="Επαναφέρετε δεδομένα από αντίγραφο ασφαλείας:").pack(anchor='w', padx=10, pady=5)
        
        self.restore_path = ttk.Entry(restore_frame)
        self.restore_path.pack(fill='x', padx=10, pady=5)
        
        restore_btn_frame = ttk.Frame(restore_frame)
        restore_btn_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(restore_btn_frame, text="📂 Επιλογή Backup", command=self.select_restore_file).pack(side='left', padx=(0, 10))
        
        self.restore_btn = ttk.Button(restore_btn_frame, text="🔄 Επαναφορά Δεδομένων", command=self.do_import)
        self.restore_btn.pack(side='right')
        
        # Info section
        info_frame = ttk.LabelFrame(frame, text="Πληροφορίες")
        info_frame.pack(fill='x', padx=12, pady=8)
        
        info_text = (
            "• Τα backups δημιουργούνται στον φάκελο 'vehicle_backups' από προεπιλογή\n"
            "• Η επαναφορά δεδομένων θα αντικαταστήσει τα τρέχοντα δεδομένα σας\n"
            "• Κανονικά backups εξασφαλίζουν την προστασία των δεδομένων σας"
        )
        tk.Label(info_frame, text=info_text, justify='left').pack(anchor='w', padx=10, pady=10)

    def select_backup_folder(self):
        folder = filedialog.askdirectory(
            title="Επιλογή φακέλου για backup",
            initialdir=BACKUP_DIR
        )
        if folder:
            self.backup_path.delete(0, 'end')
            self.backup_path.insert(0, folder)

    def select_restore_file(self):
        file = filedialog.askopenfilename(
            title="Επιλογή αρχείου backup",
            initialdir=BACKUP_DIR,
            filetypes=[("Backup Files", "*.zip")]
        )
        if file:
            self.restore_path.delete(0, 'end')
            self.restore_path.insert(0, file)

    def do_backup(self):
        folder = self.backup_path.get().strip()
        if not folder:
            messagebox.showwarning("Απαιτούμενο πεδίο", "Επιλέξτε φάκελο για το backup")
            return
            
        try:
            os.makedirs(folder, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"vehicle_backup_{timestamp}.zip"
            backup_file = os.path.join(folder, backup_name)
            
            # Create zip backup
            shutil.make_archive(backup_file.replace('.zip', ''), 'zip', DATA_DIR)
            
            messagebox.showinfo("Backup Ολοκληρώθηκε", f"Το backup δημιουργήθηκε επιτυχώς:\n{backup_file}")
        except Exception as e:
            log_error(f"Backup creation error: {str(e)}")
            messagebox.showerror("Σφάλμα Backup", f"Σφάλμα δημιουργίας backup: {str(e)}")

    def do_import(self):
        backup_file = self.restore_path.get().strip()
        if not backup_file:
            messagebox.showwarning("Απαιτούμενο πεδίο", "Επιλέξτε αρχείο backup")
            return
            
        if not backup_file.endswith('.zip'):
            messagebox.showwarning("Μη έγκυρο αρχείο", "Επιλέξτε έγκυρο αρχείο zip")
            return
            
        if not messagebox.askyesno(
            "Επιβεβαίωση Επαναφοράς",
            "Η επαναφορά θα αντικαταστήσει τα τρέχοντα δεδομένα σας. Θέλετε να συνεχίσετε;"
        ):
            return
            
        try:
            # Extract backup
            temp_dir = os.path.join(BACKUP_DIR, "temp_restore")
            shutil.unpack_archive(backup_file, temp_dir)
            
            # Restore files
            for fname in os.listdir(temp_dir):
                if fname.endswith('.json'):
                    src = os.path.join(temp_dir, fname)
                    dst = os.path.join(DATA_DIR, fname)
                    shutil.copy2(src, dst)
            
            # Clean up
            shutil.rmtree(temp_dir)
            
            # Reload data
            self.reload_all_data()
            messagebox.showinfo("Επαναφορά Ολοκληρώθηκε", "Τα δεδομένα επαναφέρθηκαν επιτυχώς")
        except Exception as e:
            log_error(f"Restore error: {str(e)}")
            messagebox.showerror("Σφάλμα Επαναφοράς", f"Σφάλμα επαναφοράς δεδομένων: {str(e)}")

    def about_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Πληροφορίες")
        
        # Title
        title_frame = ttk.Frame(frame)
        title_frame.pack(fill='x', pady=(0, 10))
        tk.Label(title_frame, text="Πληροφορίες Εφαρμογής", font=self.title_font).pack(side='left', padx=12, pady=8)
        
        # Content
        content_frame = ttk.Frame(frame)
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        info_text = (
            "Εφαρμογή Διαχείρισης Κίνησης Οχημάτων\n\n"
            "Έκδοση: 1.0.0\n"
            "Ημερομηνία Κυκλοφορίας: 2023-12-15\n\n"
            "Δυνατότητες Εφαρμογής:\n"
            "• Διαχείριση οδηγών και οχημάτων\n"
            "• Καταγραφή διαδρομών με υπογραφή οδηγού\n"
            "• Διαχείριση service και ΚΤΕΟ οχημάτων\n"
            "• Αναζήτηση σε όλα τα δεδομένα\n"
            "• Δημιουργία και επαναφορά backups\n\n"
            "Για υποστήριξη ή αναφορά προβλημάτων:\n"
            "support@vehiclemanager.gr"
        )
        
        tk.Label(content_frame, text=info_text, justify='left', font=self.font).pack(anchor='w', pady=10)
        
        # Footer
        footer_frame = ttk.Frame(frame)
        footer_frame.pack(side='bottom', fill='x', pady=10)
        tk.Label(footer_frame, text="© 2023 Vehicle Manager. Με επιφύλαξη παντός δικαιώματος.").pack()

    def update_driver_comboboxes(self):
        names = [d['name'] for d in self.drivers]
        if hasattr(self, "trip_driver"):
            self.trip_driver['values'] = names

    def update_vehicle_comboboxes(self):
        plates = [v['plate'] for v in self.vehicles]
        if hasattr(self, "trip_vehicle"):
            self.trip_vehicle['values'] = plates
        if hasattr(self, "service_vehicle"):
            self.service_vehicle['values'] = plates

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

    def on_close(self):
        """Handle application close event"""
        if messagebox.askyesno("Κλείσιμο Εφαρμογής", "Θέλετε να κλείσετε την εφαρμογή;"):
            self.destroy()

if __name__ == '__main__':
    app = VehicleManager()
    app.mainloop()