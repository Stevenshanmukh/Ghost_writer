"""
GhostWriter GUI Application
A complete desktop GUI for voice-to-text dictation on Windows 11.
Wraps whisper.exe in a user-friendly interface with settings and system tray support.
"""

# ============== SPLASH SCREEN (LOADS FIRST!) ==============
# This must come BEFORE heavy imports to show immediately
import tkinter as tk
import sys
import os

def get_script_directory():
    """Get the directory where this script is located"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

# Global splash reference
_splash_window = None

def show_splash():
    """Show a lightweight splash screen immediately"""
    global _splash_window
    
    root = tk.Tk()
    root.withdraw()  # Hide the default window
    
    # Create splash as Toplevel
    splash = tk.Toplevel(root)
    splash.title("")
    splash.overrideredirect(True)  # No window decorations
    splash.attributes('-topmost', True)
    
    # Size and center
    width, height = 300, 150
    screen_w = splash.winfo_screenwidth()
    screen_h = splash.winfo_screenheight()
    x = (screen_w - width) // 2
    y = (screen_h - height) // 2
    splash.geometry(f"{width}x{height}+{x}+{y}")
    
    # Dark theme background
    splash.configure(bg='#1a1a2e')
    
    # Ghost emoji and text
    ghost_label = tk.Label(splash, text="👻", font=("Segoe UI Emoji", 48), 
                          bg='#1a1a2e', fg='white')
    ghost_label.pack(pady=(20, 5))
    
    loading_label = tk.Label(splash, text="Loading GhostWriter...", 
                            font=("Segoe UI", 12), bg='#1a1a2e', fg='#888888')
    loading_label.pack()
    
    # Force display
    splash.update()
    
    _splash_window = (root, splash)
    return root, splash

def close_splash():
    """Close the splash screen"""
    global _splash_window
    if _splash_window:
        root, splash = _splash_window
        try:
            splash.destroy()
            root.destroy()
        except:
            pass
        _splash_window = None

# Show splash immediately!
if __name__ == "__main__":
    show_splash()

# ============== HEAVY IMPORTS START HERE ==============
import customtkinter as ctk
# ctk configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")  # Themes: "blue" (default), "green", "dark-blue"

import tkinter as tk
from tkinter import ttk
import threading
import json
import os
import sys
import winsound
import tempfile
import subprocess
import queue
import winreg

import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import pyperclip
from pynput import keyboard
from pynput.keyboard import Key, Controller
import pystray
from PIL import Image, ImageDraw

# ============== CONSTANTS ==============
APP_NAME = "GhostWriter"
SETTINGS_FILE = "settings.json"
WHISPER_EXE = "whisper-cli.exe"
MODEL_PATH = "ggml-tiny.bin"
SAMPLE_RATE = 16000

DEFAULT_SETTINGS = {
    "hotkey": "F8",
    "sound_enabled": True,
    "paste_delay": 0.15,
    "start_minimized": False,
    "run_on_startup": False
}

HOTKEY_OPTIONS = [
    "F1", "F2", "F3", "F4", "F5", "F6",
    "F7", "F8", "F9", "F10", "F11", "F12",
    "Ctrl+Shift+R", "Ctrl+Shift+D", "Ctrl+Alt+V"
]

PASTE_DELAY_OPTIONS = [
    ("Fast (0.05s)", 0.05),
    ("Normal (0.10s)", 0.10),
    ("Default (0.15s)", 0.15),
    ("Slow (0.25s)", 0.25),
    ("Very Slow (0.50s)", 0.50)
]

# Sound settings
START_BEEP = (1000, 150)  # Higher pitch
STOP_BEEP = (600, 150)    # Lower pitch

# Status states
STATUS_READY = "ready"
STATUS_RECORDING = "recording"
STATUS_TRANSCRIBING = "transcribing"
STATUS_ERROR = "error"




# Set working directory to script location
SCRIPT_DIR = get_script_directory()
os.chdir(SCRIPT_DIR)


class GhostIndicator:
    """Ghost-themed animated floating indicator"""
    
    def __init__(self, parent_root):
        self.parent = parent_root
        self.popup = None
        self._drag_x = 0
        self._drag_y = 0
        self.animation_id = None
        self.alpha_step = 0
        self.status = "idle"
        
        self._create_popup()
    
    def _create_popup(self):
        """Create the popup window with transparency"""
        self.popup = tk.Toplevel(self.parent)
        self.popup.overrideredirect(True) # ENABLE FRAMELESS
        self.popup.attributes('-topmost', True)
        
        # Make the entire window semi-transparent (See-through!)
        self.popup.attributes('-alpha', 0.95) # High visibility
        
        # Transparent background magic
        transparent_color = '#000001'
        self.popup.attributes('-transparentcolor', transparent_color)
        self.popup.config(bg=transparent_color)
        
        self.popup.withdraw()
        
        # Sizing (70% smaller)
        self.width = 126
        self.height = 32
        
        # Initial resize
        self.popup.update_idletasks()
        
        # Calculate safer center position
        screen_width = self.popup.winfo_screenwidth()
        screen_height = self.popup.winfo_screenheight()
        
        x = (screen_width - self.width) // 2
        y = (screen_height - self.height) // 2  # DEAD CENTER for now to finding it
        
        self.popup.geometry(f"{self.width}x{self.height}+{x}+{y}")
        
        # Canvas for drawing custom shapes
        self.canvas = tk.Canvas(self.popup, width=self.width, height=self.height, 
                               bg=transparent_color, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        # Draw initial shape (hidden anyway)
        # Main Pill Body
        self.pill = self._draw_rounded_rect(2, 2, self.width-4, self.height-4, 
                                           radius=15, fill='#121212', outline='#555555', width=1)
        
        # Status Text
        font_family = 'Segoe UI Variable Display'
        try:
            pass 
        except:
            font_family = 'Segoe UI'
            
        self.text_id = self.canvas.create_text(
            self.width // 2, self.height // 2,
            text="👻 Ready",
            font=(font_family, 9, 'bold'), # Smaller font
            fill='white'
        )
        
        # Make draggable
        self.canvas.bind('<Button-1>', self._start_drag)
        self.canvas.bind('<B1-Motion>', self._on_drag)
    
    def _draw_rounded_rect(self, x, y, w, h, radius=25, **kwargs):
        """Draw a rounded rectangle on the canvas"""
        points = [
            x + radius, y,
            x + w - radius, y,
            x + w, y,
            x + w, y + radius,
            x + w, y + h - radius,
            x + w, y + h,
            x + w - radius, y + h,
            x + radius, y + h,
            x, y + h,
            x, y + h - radius,
            x, y + radius,
            x, y
        ]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)
    
    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y
    
    def _on_drag(self, event):
        x = self.popup.winfo_x() + event.x - self._drag_x
        y = self.popup.winfo_y() + event.y - self._drag_y
        self.popup.geometry(f"+{x}+{y}")
    
    def _animate(self):
        """Animation loop for breathing effect"""
        if self.status == 'idle':
            return
            
        self.alpha_step += 0.15
        
        import math
        # 0.0 to 1.0 sine wave
        intensity = (math.sin(self.alpha_step) + 1) / 2
        
        # Color interpolation helper
        def interpolate_color(c1, c2, factor):
            r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
            r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
            r = int(r1 + (r2 - r1) * factor)
            g = int(g1 + (g2 - g1) * factor)
            b = int(b1 + (b2 - b1) * factor)
            return f'#{r:02x}{g:02x}{b:02x}'
            
        if self.status == 'recording':
            # Pulse between Bright Green and Darker Green
            color = interpolate_color('#7fff7f', '#2e8b57', intensity)
            self.canvas.itemconfig(self.text_id, fill=color)
            
            # Pulse subtle background border glow?
            # For now just text pulse is clean
            
        elif self.status == 'transcribing':
            # Pulse between Yellow and Orange
            color = interpolate_color('#ffeb3b', '#ff9800', intensity)
            self.canvas.itemconfig(self.text_id, fill=color)
            
        self.animation_id = self.popup.after(30, self._animate)
    
    def show(self, status):
        """Show popup with given status"""
        self.status = status
        
        # Configure look based on status
        if status == 'recording':
            self.canvas.itemconfig(self.text_id, text="👻 Listening...", fill='#7fff7f')
            self.canvas.itemconfig(self.pill, fill='#121212') 
        elif status == 'transcribing':
            self.canvas.itemconfig(self.text_id, text="👻 Thinking...", fill='#ffeb3b')
            self.canvas.itemconfig(self.pill, fill='#1e1e1e') # Slightly lighter for "active"
            
        # Position at DEAD CENTER (Safe)
        self.popup.update_idletasks()
        try:
            sw = self.popup.winfo_screenwidth()
            sh = self.popup.winfo_screenheight()
            x = (sw - self.width) // 2
            
            # 3/4th down (1/4th from bottom)
            # FIX: Adjust for DPI Scaling
            try:
                scaling = ctk.ScalingTracker.get_widget_scaling(self.popup)
            except:
                scaling = 1.0
                
            y = int(sh * 0.75) 
            
            # Apply scaling manually if needed (heuristic)
            if scaling > 1.0:
                 # If screen reports logical but geometry expects physical
                 # Or vice versa. Usually geometry expects logical on DPI-aware apps.
                 pass 

            # Force specific fallback if it looks wrong
            # User says "Vertical Middle" (0.5) when we set 0.75.
            # This implies we should target 1.0 to get 0.75? 
            # Let's try pushing it further down.
            y = int(sh * 0.85) 
            
            self.popup.geometry(f"+{x}+{y}")
        except:
            self.popup.geometry("+500+500") # Fallback
            
        self.popup.deiconify()
        self.popup.lift()
        self.popup.attributes('-topmost', True)
        
        # Start animation
        if self.animation_id:
            self.popup.after_cancel(self.animation_id)
        self._animate()
    
    def hide(self):
        """Hide the popup"""
        self.status = 'idle'
        if self.animation_id:
            self.popup.after_cancel(self.animation_id)
        if self.popup:
            self.popup.withdraw()

class GhostWriterApp:
    """Main application class for GhostWriter GUI"""

    def __init__(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self.load_settings()

        # State
        self.is_recording = False
        self.audio_data = []
        self.last_transcription = ""
        self.current_status = STATUS_READY
        self.error_message = ""

        # Threading
        self.kb = Controller()
        self.keyboard_listener = None
        self.audio_stream = None
        self.tray_icon = None
        self.update_queue = queue.Queue()

        # Modifier key tracking for combo hotkeys
        self.ctrl_pressed = False
        self.shift_pressed = False
        self.alt_pressed = False

        # GUI
        self.root = None
        self.status_canvas = None
        self.status_circle = None
        self.status_label = None
        self.transcription_text = None
        self.ghost_indicator = None  # Floating popup (created after root)

        # Check for required files
        self.files_ok = self.check_files_exist()

    def load_settings(self):
        """Load settings from settings.json or create defaults"""
        settings_path = os.path.join(SCRIPT_DIR, SETTINGS_FILE)
        try:
            if os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults to handle missing keys
                    for key in DEFAULT_SETTINGS:
                        if key in loaded:
                            self.settings[key] = loaded[key]
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_settings(self):
        """Save current settings to settings.json"""
        settings_path = os.path.join(SCRIPT_DIR, SETTINGS_FILE)
        try:
            with open(settings_path, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def check_files_exist(self):
        """Verify that required files are present"""
        whisper_path = os.path.join(SCRIPT_DIR, WHISPER_EXE)
        model_path = os.path.join(SCRIPT_DIR, MODEL_PATH)

        missing = []
        if not os.path.exists(whisper_path):
            missing.append(WHISPER_EXE)
        if not os.path.exists(model_path):
            missing.append(MODEL_PATH)

        if missing:
            self.error_message = f"Missing: {', '.join(missing)}"
            return False
        return True

    def start_move(self, event):
        self._x = event.x
        self._y = event.y

    def do_move(self, event):
        deltax = event.x - self._x
        deltay = event.y - self._y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def create_gui(self):
        """Build the modern GUI with customtkinter"""
        # FIX: Taskbar Icon for Windows
        try:
            import ctypes
            myappid = 'antigravity.ghostwriter.gui.1.0' # Arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass
            
        self.root = ctk.CTk()
        self.root.title("GhostWriter")
        try:
            self.root.iconbitmap("ghost_icon.ico")
        except:
            pass # Icon missing, use default
            
        self.root.geometry("400x620")
        
        # Grid configuration for centered layout
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        # Main container with padding
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # ===== HEADER & STATUS =====
        # Status "Dot" (Rounded Frame)
        status_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        status_container.pack(pady=(10, 5))
        
        self.status_dot = ctk.CTkFrame(status_container, width=16, height=16, corner_radius=8, 
                                      fg_color="#888888") # Fix height arg
        # CTkFrame size is sometimes tricky with pack, so we force it or use empty label
        self.status_dot.pack(side='left', padx=(0, 10))
        # Prevent resizing to 0
        self.status_dot.pack_propagate(False) 
        
        self.status_label = ctk.CTkLabel(status_container, text="Ready", 
                                        font=("Segoe UI Variable Display", 24, "bold"))
        self.status_label.pack(side='left')

        # Last Transcription
        self.transcription_text = ctk.CTkTextbox(main_frame, height=80, corner_radius=15, 
                                                fg_color="#2b2b2b", text_color="#eeeeee",
                                                font=("Segoe UI", 12))
        self.transcription_text.pack(fill='x', pady=(20, 20))
        self.transcription_text.insert("0.0", "Press F8 to dictate...")
        self.transcription_text.configure(state="disabled")

        # ===== SETTINGS CARD =====
        settings_frame = ctk.CTkFrame(main_frame, corner_radius=20)
        settings_frame.pack(fill='x', pady=10)
        
        ctk.CTkLabel(settings_frame, text="SETTINGS", font=("Segoe UI", 12, "bold"), 
                    text_color="gray").pack(pady=(15, 10))

        # Helper to make rows
        def add_row(parent, label):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.pack(fill='x', padx=20, pady=8)
            ctk.CTkLabel(f, text=label, font=("Segoe UI", 14)).pack(side='left')
            return f

        # Hotkey
        r1 = add_row(settings_frame, "Hotkey")
        self.hotkey_var = ctk.StringVar(value=self.settings.get("hotkey", "F8"))
        hotkey_combo = ctk.CTkComboBox(r1, variable=self.hotkey_var, values=HOTKEY_OPTIONS, 
                                      width=100, corner_radius=10, state="readonly",
                                      text_color="white", button_color="#555555",
                                      button_hover_color="#666666", dropdown_text_color="white")
        hotkey_combo.pack(side='right')
        hotkey_combo.configure(command=self.on_hotkey_changed) # CTk uses command for callback

        # Paste Speed
        r2 = add_row(settings_frame, "Paste Speed")
        current_delay = self.settings.get("paste_delay", 0.15)
        # Map values to labels
        delay_map = {v: k for k, v in PASTE_DELAY_OPTIONS}
        current_label = delay_map.get(current_delay, "Normal (0.15s)")
        
        self.delay_var = ctk.StringVar(value=current_label)
        # Extract just labels for the combobox
        delay_labels = [k for k, v in PASTE_DELAY_OPTIONS]
        
        delay_combo = ctk.CTkComboBox(r2, variable=self.delay_var, values=delay_labels, 
                                     width=140, corner_radius=10, state="readonly",
                                     text_color="white", button_color="#555555",
                                     button_hover_color="#666666", dropdown_text_color="white")
        delay_combo.pack(side='right')
        # We need a custom wrapper for the delay command because CTk passes the value
        def on_delay_change_wrapper(choice):
            self.on_delay_changed() 
        delay_combo.configure(command=on_delay_change_wrapper)

        # Divider
        ctk.CTkFrame(settings_frame, height=2, fg_color="#333333").pack(fill='x', padx=20, pady=10)

        # Toggles
        def add_switch(label, var, cmd):
            r = ctk.CTkFrame(settings_frame, fg_color="transparent")
            r.pack(fill='x', padx=20, pady=8)
            ctk.CTkLabel(r, text=label, font=("Segoe UI", 14)).pack(side='left')
            s = ctk.CTkSwitch(r, text="", variable=var, command=cmd, 
                             progress_color="#7fff7f")
            s.pack(side='right')

        self.sound_var = ctk.BooleanVar(value=self.settings.get("sound_enabled", True))
        add_switch("Sound Effects", self.sound_var, self.on_sound_changed)

        self.minimized_var = ctk.BooleanVar(value=self.settings.get("start_minimized", False))
        add_switch("Start in Tray", self.minimized_var, self.on_minimized_changed)

        self.startup_var = ctk.BooleanVar(value=self.settings.get("run_on_startup", False))
        add_switch("Run on Startup", self.startup_var, self.on_startup_changed)
        
        # Spacer inside card
        ctk.CTkFrame(settings_frame, height=10, fg_color="transparent").pack()

        # ===== ACTION BUTTONS =====
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill='x', pady=(20, 0))
        
        ctk.CTkButton(btn_frame, text="Minimize", command=self.minimize_to_tray, 
                     fg_color="#333333", hover_color="#444444", corner_radius=10).pack(side='left', expand=True, fill='x', padx=(0, 10))
        
        ctk.CTkButton(btn_frame, text="Quit App", command=self.quit_app, 
                     fg_color="#3a1c1c", hover_color="#502020", text_color="#ffaaaa", corner_radius=10).pack(side='right', expand=True, fill='x', padx=(10, 0))

        # System Protocol
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        # Initial Status Update
        self.poll_updates()
        if not self.files_ok:
            self.update_status(STATUS_ERROR, self.error_message)

    def _update_status_ui(self, state, message=""):
        """Update status indicator"""
        colors = {
            STATUS_READY: '#888888',
            STATUS_RECORDING: '#4CAF50',
            STATUS_TRANSCRIBING: '#FFC107',
            STATUS_ERROR: '#F44336'
        }
        
        color = colors.get(state, '#888888')
        # Update dot color (CTkFrame fg_color)
        self.status_dot.configure(fg_color=color)

        hotkey = self.settings.get("hotkey", "F8")
        
        if state == STATUS_READY:
            self.status_label.configure(text="Ready", text_color="white")
            self.transcription_text.configure(state="normal")
            self.transcription_text.delete("0.0", "end")
            self.transcription_text.insert("0.0", f"Press {hotkey} to start listening...")
            self.transcription_text.configure(state="disabled")
        elif state == STATUS_RECORDING:
            self.status_label.configure(text="Listening...", text_color="#4CAF50")
        elif state == STATUS_TRANSCRIBING:
            self.status_label.configure(text="Thinking...", text_color="#FFC107")
        elif state == STATUS_ERROR:
            self.status_label.configure(text="Error", text_color="#F44336")
            self.transcription_text.configure(state="normal")
            self.transcription_text.delete("0.0", "end")
            self.transcription_text.insert("0.0", message)
            self.transcription_text.configure(state="disabled")

    def _update_transcription_ui(self, text):
        self.transcription_text.configure(state="normal")
        self.transcription_text.delete("0.0", "end")
        self.transcription_text.insert("0.0", text)
        self.transcription_text.configure(state="disabled")

    def poll_updates(self):
        """Poll the update queue for thread-safe GUI updates"""
        try:
            while True:
                update = self.update_queue.get_nowait()
                if update[0] == "status":
                    self._update_status_ui(update[1], update[2])
                elif update[0] == "transcription":
                    self._update_transcription_ui(update[1])
        except queue.Empty:
            pass

        # Schedule next poll
        if self.root:
            self.root.after(50, self.poll_updates)



    def update_status(self, state, message=""):
        """Thread-safe status update"""
        self.current_status = state
        self.update_queue.put(("status", state, message))

    def update_transcription(self, text):
        """Thread-safe transcription update"""
        self.last_transcription = text
        self.update_queue.put(("transcription", text))

    # ===== SETTINGS HANDLERS =====

    def on_hotkey_changed(self, choice):
        """Handle hotkey selection change"""
        new_hotkey = choice  # Use the passed argument directly
        
        self.settings["hotkey"] = new_hotkey
        self.save_settings()

        # Update hint text
        self._update_status_ui(self.current_status)

        # Restart keyboard listener with new hotkey
        self.restart_keyboard_listener()

    def on_sound_changed(self):
        """Handle sound toggle change"""
        self.settings["sound_enabled"] = self.sound_var.get()
        self.save_settings()

    def on_delay_changed(self, event=None):
        """Handle paste delay change"""
        label = self.delay_var.get()
        for lbl, val in PASTE_DELAY_OPTIONS:
            if lbl == label:
                self.settings["paste_delay"] = val
                break
        self.save_settings()

    def on_minimized_changed(self):
        """Handle start minimized toggle"""
        self.settings["start_minimized"] = self.minimized_var.get()
        self.save_settings()

    def on_startup_changed(self):
        """Handle run on startup toggle"""
        enabled = self.startup_var.get()
        self.settings["run_on_startup"] = enabled
        self.save_settings()
        self.update_startup_registry(enabled)

    def update_startup_registry(self, enabled):
        """Add or remove app from Windows startup registry"""
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "GhostWriter"

        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)

            if enabled:
                # Get pythonw.exe path and script path
                if getattr(sys, 'frozen', False):
                    # Running as compiled executable
                    app_path = sys.executable
                else:
                    # Running as script
                    pythonw = sys.executable.replace('python.exe', 'pythonw.exe')
                    script_path = os.path.abspath(__file__)
                    app_path = f'"{pythonw}" "{script_path}"'

                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass  # Already doesn't exist

            winreg.CloseKey(key)
        except Exception as e:
            print(f"Error updating registry: {e}")

    # ===== SYSTEM TRAY =====

    def create_tray_icon_image(self, color='#888888'):
        """Create a simple colored circle icon for the tray"""
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Parse color
        if color.startswith('#'):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
        else:
            r, g, b = 136, 136, 136  # Default gray

        # Draw filled circle with border for better visibility
        draw.ellipse([2, 2, size-2, size-2], fill=(r, g, b, 255), outline=(255, 255, 255, 200), width=2)

        return image

    def create_tray_icon(self):
        """Create system tray icon with pystray"""
        image = self.create_tray_icon_image()

        menu = pystray.Menu(
            pystray.MenuItem("Show Window", self.show_window, default=True),
            pystray.MenuItem(
                lambda item: "Stop Recording" if self.is_recording else "Start Recording",
                self.toggle_recording
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self.quit_app)
        )

        self.tray_icon = pystray.Icon(APP_NAME, image, "GhostWriter - Click to show", menu)

    def update_tray_icon_color(self, color):
        """Update the tray icon color"""
        if self.tray_icon and self.tray_icon.visible:
            try:
                self.tray_icon.icon = self.create_tray_icon_image(color)
            except Exception:
                pass  # Ignore errors if tray not ready

    def run_tray_icon(self):
        """Run the tray icon (in separate thread)"""
        if self.tray_icon:
            try:
                self.tray_icon.run_detached()
            except Exception as e:
                print(f"Tray icon error: {e}")

    def minimize_to_tray(self):
        """Hide window and show in system tray"""
        if self.root:
            self.root.withdraw()

    def show_window(self, icon=None, item=None):
        """Show window from tray"""
        if self.root:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()

    def toggle_recording(self, icon=None, item=None):
        """Toggle recording from tray menu"""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    # ===== AUDIO & RECORDING =====

    def audio_callback(self, indata, frames, time_info, status):
        """Called by sounddevice for each audio chunk"""
        if self.is_recording:
            self.audio_data.append(indata.copy())

    def start_recording(self):
        """Begin audio capture"""
        if not self.files_ok:
            return

        self.is_recording = True
        self.audio_data = []
        self.update_status(STATUS_RECORDING)

        # Show ghost indicator
        if self.ghost_indicator:
            self.root.after(0, lambda: self.ghost_indicator.show('recording'))

        # Play start sound
        if self.settings.get("sound_enabled", True):
            threading.Thread(target=lambda: winsound.Beep(*START_BEEP), daemon=True).start()

    def stop_recording(self):
        """Stop audio capture and transcribe"""
        if not self.is_recording:
            return

        self.is_recording = False

        # Play stop sound
        if self.settings.get("sound_enabled", True):
            threading.Thread(target=lambda: winsound.Beep(*STOP_BEEP), daemon=True).start()

        # Process in background thread
        threading.Thread(target=self.process_recording, daemon=True).start()

    def process_recording(self):
        """Process recorded audio"""
        if len(self.audio_data) == 0:
            self.update_status(STATUS_READY)
            if self.ghost_indicator:
                self.root.after(0, self.ghost_indicator.hide)
            return

        recording = np.concatenate(self.audio_data, axis=0)
        duration = len(recording) / SAMPLE_RATE

        if duration < 0.5:
            self.update_status(STATUS_READY)
            if self.ghost_indicator:
                self.root.after(0, self.ghost_indicator.hide)
            return

        self.update_status(STATUS_TRANSCRIBING)
        
        # Update ghost indicator to transcribing
        if self.ghost_indicator:
            self.root.after(0, lambda: self.ghost_indicator.show('transcribing'))

        temp_wav = tempfile.mktemp(suffix=".wav")

        try:
            wav.write(temp_wav, SAMPLE_RATE, recording)
            text = self.transcribe(temp_wav)

            if text:
                self.update_transcription(text)
                self.type_text(text)
        except Exception as e:
            self.update_status(STATUS_ERROR, str(e))
            if self.ghost_indicator:
                self.root.after(0, self.ghost_indicator.hide)
            return
        finally:
            if os.path.exists(temp_wav):
                os.remove(temp_wav)

        self.update_status(STATUS_READY)
        
        # Hide ghost indicator when done
        if self.ghost_indicator:
            self.root.after(0, self.ghost_indicator.hide)

    def transcribe(self, audio_file):
        """Run whisper.exe and return text"""
        try:
            command = [
                os.path.join(SCRIPT_DIR, WHISPER_EXE),
                "-m", os.path.join(SCRIPT_DIR, MODEL_PATH),
                "-f", audio_file,
                "-nt",
                "-np"
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if result.returncode != 0:
                return None

            return result.stdout.strip()

        except Exception as e:
            print(f"Transcription error: {e}")
            return None

    def type_text(self, text):
        """Paste text using clipboard method"""
        if not text or text.isspace():
            return

        text = text.strip()

        # Save old clipboard
        try:
            old_clipboard = pyperclip.paste()
        except:
            old_clipboard = ""

        # Copy new text
        pyperclip.copy(text)
        time.sleep(self.settings.get("paste_delay", 0.15))

        # Paste with Ctrl+V
        with self.kb.pressed(Key.ctrl):
            self.kb.press('v')
            self.kb.release('v')

    # ===== KEYBOARD LISTENER =====

    def get_hotkey_key(self):
        """Convert hotkey string to pynput Key object(s)"""
        hotkey = self.settings.get("hotkey", "F8")

        # Function keys
        if hotkey.startswith("F") and hotkey[1:].isdigit():
            return getattr(Key, hotkey.lower(), Key.f8)

        # Combo keys - return the main key, modifiers handled separately
        if hotkey == "Ctrl+Shift+R":
            return "r"
        elif hotkey == "Ctrl+Shift+D":
            return "d"
        elif hotkey == "Ctrl+Alt+V":
            return "v"

        return Key.f8

    def is_hotkey_pressed(self, key):
        """Check if the pressed key matches the current hotkey"""
        hotkey = self.settings.get("hotkey", "F8")

        # Function keys
        if hotkey.startswith("F") and hotkey[1:].isdigit():
            expected = getattr(Key, hotkey.lower(), Key.f8)
            return key == expected

        # Combo keys
        if hotkey == "Ctrl+Shift+R":
            return self.ctrl_pressed and self.shift_pressed and hasattr(key, 'char') and key.char == 'r'
        elif hotkey == "Ctrl+Shift+D":
            return self.ctrl_pressed and self.shift_pressed and hasattr(key, 'char') and key.char == 'd'
        elif hotkey == "Ctrl+Alt+V":
            return self.ctrl_pressed and self.alt_pressed and hasattr(key, 'char') and key.char == 'v'

        return False

    def on_key_press(self, key):
        """Handle key press events"""
        # Track modifier keys
        if key == Key.ctrl_l or key == Key.ctrl_r:
            self.ctrl_pressed = True
        elif key == Key.shift_l or key == Key.shift_r or key == Key.shift:
            self.shift_pressed = True
        elif key == Key.alt_l or key == Key.alt_r or key == Key.alt_gr:
            self.alt_pressed = True

        # Check if hotkey pressed
        if self.is_hotkey_pressed(key):
            if not self.is_recording:
                self.start_recording()
            else:
                self.stop_recording()

    def on_key_release(self, key):
        """Handle key release events"""
        if key == Key.ctrl_l or key == Key.ctrl_r:
            self.ctrl_pressed = False
        elif key == Key.shift_l or key == Key.shift_r or key == Key.shift:
            self.shift_pressed = False
        elif key == Key.alt_l or key == Key.alt_r or key == Key.alt_gr:
            self.alt_pressed = False

    def start_keyboard_listener(self):
        """Start the keyboard listener"""
        try:
            # Start audio stream
            self.audio_stream = sd.InputStream(
                callback=self.audio_callback,
                channels=1,
                samplerate=SAMPLE_RATE,
                dtype=np.float32
            )
            self.audio_stream.start()

            # Start keyboard listener
            self.keyboard_listener = keyboard.Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            )
            self.keyboard_listener.start()
        except Exception as e:
            self.update_status(STATUS_ERROR, f"Failed to start: {e}")

    def stop_keyboard_listener(self):
        """Stop the keyboard listener"""
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None

        if self.audio_stream:
            self.audio_stream.stop()
            self.audio_stream.close()
            self.audio_stream = None

    def restart_keyboard_listener(self):
        """Restart keyboard listener with new hotkey"""
        self.stop_keyboard_listener()
        self.start_keyboard_listener()

    # ===== APP LIFECYCLE =====
    
    def quit_app(self, icon=None, item=None):
        """Clean shutdown"""
        # Stop recording if active
        if self.is_recording:
            self.is_recording = False

        # Stop listeners
        self.stop_keyboard_listener()

        # Stop tray icon
        if self.tray_icon:
            self.tray_icon.stop()

        # Save settings
        self.save_settings()

        # Close window
        if self.root:
            self.root.quit()
            self.root.destroy()

    def run(self):
        """Start the application"""
        # Create GUI
        self.create_gui()
        
        # Close the splash screen now that main UI is ready
        close_splash()
        
        # Create ghost indicator (floating popup)
        self.ghost_indicator = GhostIndicator(self.root)

        # Create and start tray icon (run_detached handles its own thread)
        self.create_tray_icon()
        self.run_tray_icon()

        # Start keyboard listener
        self.start_keyboard_listener()

        # Handle start minimized
        if self.settings.get("start_minimized", False):
            self.root.withdraw()

        # Run tkinter main loop
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.quit_app()


# Need to import time for paste delay
import time


# ============== ENTRY POINT ==============
if __name__ == "__main__":
    app = GhostWriterApp()
    app.run()
