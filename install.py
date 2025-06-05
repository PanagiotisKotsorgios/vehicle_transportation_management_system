import os
import time
import threading
import random
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttkb
from tkinter.scrolledtext import ScrolledText

GITHUB_REPO_URL = "https://github.com/PanagiotisKotsorgios/vehicle_transportation_management_system.git"  # Replace with your actual repo

class InstallerApp(ttkb.Window):
    def __init__(self):
        super().__init__(themename="minty")
        self.title("App Installation Wizard")
        self.geometry("600x400")
        self.resizable(False, False)

        self.folder_path = tk.StringVar()
        self.step = 0
        self.frames = []
        self.nav_frame = None

        self.create_widgets()

    def create_widgets(self):
        self.create_welcome_page()
        self.create_folder_selection_page()
        self.create_license_page()
        self.create_installation_page()
        self.create_post_install_options_page()
        self.create_finish_page()
        self.update_frame()

    def create_welcome_page(self):
        frame = ttkb.Frame(self)
        ttkb.Label(frame, text="Welcome to the App Installer", font=("Arial", 16)).pack(pady=40)
        ttkb.Label(frame, text="This wizard will guide you through the installation.").pack(pady=10)
        self.frames.append(frame)

    def create_folder_selection_page(self):
        frame = ttkb.Frame(self)
        ttkb.Label(frame, text="Select Installation Folder", font=("Arial", 14)).pack(pady=20)
        folder_frame = ttkb.Frame(frame)
        folder_frame.pack(pady=10)
        folder_entry = ttkb.Entry(folder_frame, textvariable=self.folder_path, width=50)
        folder_entry.pack(side="left", padx=5)
        ttkb.Button(folder_frame, text="Browse", command=self.browse_folder).pack(side="left")
        self.frames.append(frame)

    def create_license_page(self):
        frame = ttkb.Frame(self)
        ttkb.Label(frame, text="License Agreement", font=("Arial", 14)).pack(pady=20)
        license_text = ScrolledText(frame, height=10, width=70, wrap=tk.WORD)
        license_text.insert(tk.END, self.get_license_text())
        license_text.config(state=tk.DISABLED)
        license_text.pack(pady=10)
        self.agree_var = tk.BooleanVar()
        ttkb.Checkbutton(frame, text="I agree to the Terms of Service", variable=self.agree_var).pack(pady=10)
        self.frames.append(frame)

    def create_installation_page(self):
        frame = ttkb.Frame(self)
        ttkb.Label(frame, text="Installing...", font=("Arial", 14)).pack(pady=10)
        self.progress = ttkb.Progressbar(frame, mode='determinate', length=400)
        self.progress.pack(pady=20)
        self.log_text = ScrolledText(frame, height=10, width=70, state='disabled')
        self.log_text.pack(pady=10)
        self.frames.append(frame)

    def create_post_install_options_page(self):
        frame = ttkb.Frame(self)
        ttkb.Label(frame, text="Post-Installation Options", font=("Arial", 14)).pack(pady=20)

        self.run_after_var = tk.BooleanVar()
        self.shortcut_var = tk.BooleanVar()

        ttkb.Checkbutton(frame, text="Run application after installation", variable=self.run_after_var).pack(anchor="w", padx=30, pady=10)
        ttkb.Checkbutton(frame, text="Create desktop shortcut", variable=self.shortcut_var).pack(anchor="w", padx=30, pady=10)

        ttkb.Label(frame, text="Click 'Finish' to complete the setup.").pack(pady=20)
        self.frames.append(frame)

    def create_finish_page(self):
        frame = ttkb.Frame(self)
        ttkb.Label(frame, text="Installation Complete!", font=("Arial", 16)).pack(pady=40)
        ttkb.Label(frame, text="The application has been installed successfully.").pack(pady=10)
        self.frames.append(frame)

    def update_frame(self):
        for frame in self.frames:
            frame.pack_forget()
        self.frames[self.step].pack(fill="both", expand=True)
        self.update_buttons()

    def update_buttons(self, disable_next=False):
        if self.nav_frame:
            self.nav_frame.destroy()

        self.nav_frame = ttkb.Frame(self, name="nav_frame")
        self.nav_frame.pack(side="bottom", fill="x", pady=10)

        if self.step > 0:
            ttkb.Button(self.nav_frame, text="Back", command=self.back_step).pack(side="left", padx=20)

        if self.step < len(self.frames) - 1:
            self.next_btn = ttkb.Button(self.nav_frame, text="Next", command=self.next_step)
            self.next_btn.pack(side="right", padx=20)
            self.next_btn['state'] = 'disabled' if disable_next else 'normal'
        elif self.step == len(self.frames) - 1:
            ttkb.Button(self.nav_frame, text="Finish", command=self.finish_app).pack(side="right", padx=20)

    def back_step(self):
        self.step -= 1
        self.update_frame()

    def next_step(self):
        if self.step == 1 and not self.folder_path.get():
            messagebox.showerror("Error", "Please select an installation folder.")
            return
        if self.step == 2 and not self.agree_var.get():
            messagebox.showerror("Error", "You must agree to the Terms of Service.")
            return

        if self.step == 1 and not self.folder_path.get():
            self.folder_path.set(os.path.expanduser("~\\AppData\\Local\\MyApp"))

        self.step += 1
        self.update_frame()

        if self.step == 3:
            self.update_buttons(disable_next=True)
            self.start_installation()

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)

    def start_installation(self):
        threading.Thread(target=self.run_installation).start()

    def run_installation(self):
        install_steps = [
            "Checking system requirements...",
            "Preparing environment...",
            "Creating installation directory...",
            "Downloading required files...",
            "Setting permissions...",
            "Extracting files...",
            "Finalizing setup..."
        ]

        total_steps = len(install_steps)
        for i, step_msg in enumerate(install_steps):
            delay = random.uniform(0.5, 2.5)
            time.sleep(delay)
            percent = int((i + 1) / total_steps * 100)
            self.progress['value'] = percent
            self.log(f"[{time.strftime('%H:%M:%S')}] {step_msg}")

        self.log(f"[{time.strftime('%H:%M:%S')}] Cloning repo from GitHub...")
        time.sleep(random.uniform(1.0, 2.0))
        self.log(f"[{time.strftime('%H:%M:%S')}] Simulated: Cloned {GITHUB_REPO_URL} to {self.folder_path.get()}")
        self.log(f"[{time.strftime('%H:%M:%S')}] Installation completed successfully.")

        self.progress['value'] = 100
        time.sleep(1)
        self.step += 1  # move to post-install options
        self.update_frame()

    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def finish_app(self):
        if self.shortcut_var.get():
            self.log(f"[{time.strftime('%H:%M:%S')}] (Simulated) Desktop shortcut created.")
        if self.run_after_var.get():
            self.log(f"[{time.strftime('%H:%M:%S')}] (Simulated) Launching application...")

        messagebox.showinfo("Setup Complete", "Installation is complete. You may now close this window.")
        self.step += 1
        self.update_frame()

    def get_license_text(self):
        return """
MIT License

Copyright (c) 2025 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

if __name__ == "__main__":
    app = InstallerApp()
    app.mainloop()
