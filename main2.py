import tkinter as tk
from tkinter import simpledialog, Menu, messagebox
from datetime import datetime, timedelta
import random
import ctypes
from ctypes import wintypes
import screeninfo
import paramiko
import json
import os


import tkinter as tk
from tkinter import simpledialog, Menu, messagebox
from datetime import datetime, timedelta
import random
import ctypes
from ctypes import wintypes
import screeninfo
import paramiko
import json
import os

# For Windows 10/11 acrylic effect
try:
    from ctypes import windll
    # Set DPI awareness for crisp visuals
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

def make_rounded(hwnd, radius=20):
    hwnd = ctypes.windll.user32.GetParent(hwnd)
    hRgn = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, 250, 150, radius, radius)
    ctypes.windll.user32.SetWindowRgn(hwnd, hRgn, True)

def set_acrylic_effect(hwnd, gradient_color="101010", opacity=0.96):
    """Windows 10/11 acrylic effect"""
    try:
        # Constants for Windows API
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        DWMWA_SYSTEMBACKDROP_TYPE = 38
        
        # Values for acrylic effect
        DWMSBT_ACRYLIC = 3
        DWMSBT_MAINWINDOW = 2
        
        # Set dark mode
        windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int)
        )
        
        # Set acrylic effect
        windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_SYSTEMBACKDROP_TYPE,
            ctypes.byref(ctypes.c_int(DWMSBT_ACRYLIC)), ctypes.sizeof(ctypes.c_int)
        )
        
        # Set opacity (0-255)
        opacity_value = int(opacity * 255)
        accent = bytes((*bytes.fromhex(gradient_color), opacity_value))
        accent_size = ctypes.sizeof(wintypes.DWORD)
        accent_policy = wintypes.ACCENT_POLICY()
        accent_policy.AccentState = 3  # ACCENT_ENABLE_ACRYLICBLURBEHIND
        accent_policy.AccentFlags = 2  # Draw left + right borders
        accent_policy.GradientColor = int.from_bytes(accent, 'little')
        wpattr = wintypes.WINDOWCOMPOSITIONATTRIBDATA()
        wpattr.Attrib = 19  # WCA_ACCENT_POLICY
        wpattr.pvData = ctypes.cast(ctypes.pointer(accent_policy), ctypes.c_void_p)
        wpattr.cbData = ctypes.sizeof(accent_policy)
        windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(wpattr))
    except Exception as e:
        print(f"Couldn't set acrylic effect: {e}")

class ClockWindow(tk.Toplevel):
    def __init__(self, root, clock_id, use_server_time=False, ssh_config=None):
        super().__init__(root)
        self.clock_id = clock_id
        self.custom_time = datetime.now()
        self.use_server_time = use_server_time
        self.ssh_config = ssh_config or {}
        
        # Window styling
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.attributes('-transparentcolor', '#1e1e1e')  # Match your bg color
        self.configure(bg='#1e1e1e')
        self.geometry(f"250x150+{100 + clock_id*270}+100")

        # Apply acrylic effect (Windows only)
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            set_acrylic_effect(hwnd)
        except:
            # Fallback for non-Windows or if acrylic fails
            self.attributes('-alpha', 0.92)  # Slight transparency
            self.configure(bg='#252525')  # Matte dark background

        # Canvas with glass effect
        self.canvas = tk.Canvas(self, width=250, height=150, bg='#252525', 
                              highlightthickness=0, bd=0)
        self.canvas.pack()

        # Create glass effect with rectangles
        self.canvas.create_rectangle(0, 0, 250, 150, 
                                   fill='#252525', outline='', 
                                   stipple='gray50', alpha=0.7)
        
        # Floating bubbles (now more subtle for glass effect)
        self.bubbles = []
        for _ in range(8):  # Fewer bubbles
            x = random.randint(0, 250)
            y = random.randint(0, 150)
            r = random.randint(5, 20)
            color = random.choice(["#00FFFF88", "#66CCFF88", "#99FFCC88"])
            bubble = self.canvas.create_oval(x, y, x + r, y + r, 
                                           fill=color, outline="", 
                                           stipple="gray12")
            self.bubbles.append((bubble, random.uniform(0.3, 1.0), r))

        # Clock text with subtle shadow
        self.time_label = self.canvas.create_text(125, 60, text="", 
                                                font=("Consolas", 24, 'bold'), 
                                                fill="white")
        self.canvas.create_text(125, 60, text="", 
                              font=("Consolas", 24, 'bold'), 
                              fill="#ffffff44", tags=("shadow",))



# Configuration file path
CONFIG_FILE = "clock_config.json"

def make_rounded(hwnd, radius=20):
    hwnd = ctypes.windll.user32.GetParent(hwnd)
    
    hRgn = ctypes.windll.gdi32.CreateRoundRectRgn(
            0, 0, 250, 150, radius, radius
    )
    ctypes.windll.user32.SetWindowRgn(hwnd, hRgn, True)

class ClockWindow(tk.Toplevel):
    def __init__(self, root, clock_id, use_server_time=False, ssh_config=None):
        super().__init__(root)
        self.clock_id = clock_id
        self.custom_time = datetime.now()
        self.use_server_time = use_server_time
        self.ssh_config = ssh_config or {}
        
        self.bind("<Enter>", self.on_hover_enter)
        self.bind("<Leave>", self.on_hover_leave)
        self.hover_timer = None
        self.current_corner = 0  # 0=TopLeft, 1=TopRight, 2=BottomRight, 3=BottomLeft

        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.configure(bg="#1e1e1e")
        self.geometry(f"250x150+{100 + clock_id*270}+100")

        # Canvas for animation
        self.canvas = tk.Canvas(self, width=250, height=150, bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack()

        # Floating bubbles
        self.bubbles = []
        for _ in range(10):
            x = random.randint(0, 250)
            y = random.randint(0, 150)
            r = random.randint(10, 30)
            color = random.choice(["#00FFFF", "#66CCFF", "#99FFCC", "#CCFFFF"])
            bubble = self.canvas.create_oval(x, y, x + r, y + r, fill=color, outline="", stipple="gray25")
            self.bubbles.append((bubble, random.uniform(0.5, 1.5), r))

        # Clock text
        self.time_label = self.canvas.create_text(125, 60, text="", font=("Consolas", 24, 'bold'), fill="white")

        # Set time button
        self.set_time_button = tk.Button(
            self, text="Set Time", command=self.set_time,
            font=("Arial", 10), bg="#333", fg="#FFF", relief="flat"
        )
        self.set_time_button_window = self.canvas.create_window(125, 110, window=self.set_time_button)

        # Sync button (only for server time clocks)
        self.sync_button = None
        self.sync_button_window = None
        if self.use_server_time:
            self.sync_button = tk.Button(
                self, text="Sync", command=self.refresh_server_time,
                font=("Arial", 10), bg="#3366FF", fg="#FFF", relief="flat"
            )
            self.sync_button_window = self.canvas.create_window(200, 110, window=self.sync_button)

        # Right-click menu
        self.bind("<Button-3>", self.show_menu)
        self.menu = Menu(self, tearoff=0)
        self.menu.add_command(label="Close Clock", command=self.destroy)
        if use_server_time:
            self.menu.add_command(label="Sync Server Time", command=self.refresh_server_time)

        # Drag window
        self.bind("<ButtonPress-1>", self.start_drag)
        self.bind("<B1-Motion>", self.do_drag)

        # Trigger Animation button
        self.animation_button = tk.Button(
            self, text="Trigger Animation", command=self.trigger_random_animation,
            font=("Arial", 10), bg="#444", fg="#FFF", relief="flat"
        )
        self.animation_button_window = self.canvas.create_window(125, 135, window=self.animation_button)

        # Schedule random animation every 5 minutes
        self.after(5 * 60 * 1000, self.trigger_random_animation)

        # Hide buttons after 10 seconds
        self.after(10000, self.hide_buttons)

        # Initial sync for server time
        if self.use_server_time:
            self.refresh_server_time()

        self.update_clock()
        self.animate_bubbles()
        make_rounded(self.winfo_id(), radius=60)

    def refresh_server_time(self):
     if self.use_server_time and self.ssh_config:
        try:
            server_time = get_server_time(
                self.ssh_config['host'],
                self.ssh_config['port'],
                self.ssh_config['username'],
                self.ssh_config['password']
            )
            if not server_time.startswith("Error"):
                # Extract just the time part after "Server Time: "
                time_str = server_time.split(": ", 1)[1]
                
                # Try multiple possible date formats
                date_formats = [
                    "%A %d %B %Y %I:%M:%S %p %Z",  # Wednesday 02 July 2025 05:04:32 PM IST
                    "%a %b %d %H:%M:%S %Z %Y",     # Wed Jul 02 17:04:32 IST 2025
                    "%c"                           # Locale's appropriate date and time representation
                ]
                
                parsed_time = None
                for fmt in date_formats:
                    try:
                        parsed_time = datetime.strptime(time_str, fmt)
                        break
                    except ValueError:
                        continue
                
                if parsed_time:
                    self.custom_time = parsed_time
                    messagebox.showinfo("Sync Successful", "Server time synchronized successfully!")
                else:
                    # If all formats fail, try a more flexible approach
                    try:
                        # Remove timezone and parse without it
                        time_str_no_tz = ' '.join(time_str.split()[:-1])
                        parsed_time = datetime.strptime(time_str_no_tz, "%A %d %B %Y %I:%M:%S %p")
                        self.custom_time = parsed_time
                        messagebox.showinfo("Sync Successful", "Server time synchronized (timezone ignored)!")
                    except Exception as e:
                        messagebox.showerror("Sync Failed", f"Unrecognized time format: {time_str}\nError: {str(e)}")
            else:
                messagebox.showerror("Sync Failed", server_time)
        except Exception as e:
            messagebox.showerror("Sync Error", f"Failed to sync with server: {str(e)}")

    def trigger_random_animation(self):
        animation_type = random.choice(["shake", "pulse", "spin", "rotate"])

        if animation_type == "shake":
            self.shake_clock_text()
        elif animation_type == "pulse":
            self.pulse_clock_color()
        elif animation_type == "spin":
            self.spin_bubbles()

        # Reschedule after 5 minutes
        self.after(5 * 60 * 1000, self.trigger_random_animation)

    def shake_clock_text(self, count=0):
        if count >= 10:
            self.canvas.coords(self.time_label, 125, 60)
            return
        offset = (-5 if count % 2 == 0 else 5)
        self.canvas.move(self.time_label, offset, 0)
        self.after(50, lambda: self.shake_clock_text(count + 1))

    def pulse_clock_color(self, step=0):
        colors = ["#FFFFFF", "#FFAAAA", "#FFFFFF", "#AAFFAA", "#FFFFFF", "#AAAAFF", "#FFFFFF"]
        if step >= len(colors):
            return
        self.canvas.itemconfigure(self.time_label, fill=colors[step])
        self.after(200, lambda: self.pulse_clock_color(step + 1))

    def spin_bubbles(self, step=0):
        if step >= 30:
            return
        for bubble, _, _ in self.bubbles:
            self.canvas.move(bubble, 3 * random.choice([-1, 1]), 3 * random.choice([-1, 1]))
        self.after(50, lambda: self.spin_bubbles(step + 1))

    def animate_bubbles(self):
        for i, (bubble, speed, r) in enumerate(self.bubbles):
            self.canvas.move(bubble, 0, -speed)
            coords = self.canvas.coords(bubble)
            if coords[1] < -r:
                x = random.randint(0, 250)
                new_y = 150 + r
                self.canvas.coords(bubble, x, new_y, x + r, new_y + r)
        self.after(40, self.animate_bubbles)

    def show_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def start_drag(self, event):
        self.x_offset = event.x
        self.y_offset = event.y

    def do_drag(self, event):
        x = self.winfo_pointerx() - self.x_offset
        y = self.winfo_pointery() - self.y_offset
        self.geometry(f"+{x}+{y}")

    def set_time(self):
        user_input = simpledialog.askstring("Set Time", "Enter time (HH:MM:SS):", parent=self)
        try:
            now = datetime.now()
            custom = datetime.strptime(user_input, "%H:%M:%S")
            self.custom_time = now.replace(hour=custom.hour, minute=custom.minute, second=custom.second)
            self.use_server_time = False  # Switch to local time after manual setting
            # Remove sync button if it exists
            if self.sync_button_window:
                self.canvas.delete(self.sync_button_window)
                self.sync_button_window = None
        except Exception:
            self.canvas.itemconfigure(self.time_label, text="Invalid Format")

    def update_clock(self):
        if self.use_server_time:
            # For server time, we just let it run normally after initial sync
            self.custom_time += timedelta(seconds=1)
        else:
            self.custom_time = datetime.now()
            
        self.canvas.itemconfigure(self.time_label, text=self.custom_time.strftime("%H:%M:%S"))
        self.after(1000, self.update_clock)

    def hide_buttons(self):
        self.canvas.itemconfigure(self.set_time_button_window, state='hidden')
        self.canvas.itemconfigure(self.animation_button_window, state='hidden')
        if self.sync_button_window:
            self.canvas.itemconfigure(self.sync_button_window, state='hidden')
        
    def on_hover_enter(self, event):
        # Start hover timer (500 ms)
        if not self.hover_timer:
            self.hover_timer = self.after(500, self.move_to_next_corner)

    def on_hover_leave(self, event):
        # Cancel hover timer if user leaves before 500ms
        if self.hover_timer:
            self.after_cancel(self.hover_timer)
            self.hover_timer = None

    def move_to_next_corner(self):
        self.hover_timer = None  # Reset hover timer
        monitor = screeninfo.get_monitors()[0]  # primary screen
        width = 250
        height = 150

        corners = [
            (0, 0),  # Top-left
            (monitor.width - width, 0),  # Top-right
            (monitor.width - width, monitor.height - height),  # Bottom-right
            (0, monitor.height - height),  # Bottom-left
        ]

        self.current_corner = (self.current_corner + 1) % 4
        x, y = corners[self.current_corner]
        self.geometry(f"{width}x{height}+{x}+{y}")

def get_server_time(host, port, username, password):
    try:
        # Initialize SSH client
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the server
        client.connect(hostname=host, port=port, username=username, password=password)

        # Get time in a consistent format including weekday, date, and timezone
        stdin, stdout, stderr = client.exec_command('date +"%A %d %B %Y %I:%M:%S %p %Z"')
        server_time = stdout.read().decode().strip()

        # Close the connection
        client.close()

        return f"Server Time: {server_time}"

    except Exception as e:
        return f"Error: {e}"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return None

def save_config(host, port, username, password):
    config = {
        'host': host,
        'port': port,
        'username': username,
        'password': password
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def ask_ssh_credentials():
    host = simpledialog.askstring("SSH Connection", "Enter server host:")
    if not host:
        return None
        
    port = simpledialog.askinteger("SSH Connection", "Enter port (default 22):", minvalue=1, maxvalue=65535)
    if not port:
        port = 22
        
    username = simpledialog.askstring("SSH Connection", "Enter username:")
    if not username:
        return None
        
    password = simpledialog.askstring("SSH Connection", "Enter password:", show='*')
    if not password:
        return None
        
    return {
        'host': host,
        'port': port,
        'username': username,
        'password': password
    }

class ClockLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Clock Launcher")
        self.root.geometry("300x120")
        self.root.configure(bg="#222")
        self.clock_id = 0

        tk.Button(
            self.root, text="Add Local Clock", font=("Arial", 12),
            command=lambda: self.add_clock(False), bg="#555", fg="white", relief="flat"
        ).pack(pady=5)

        tk.Button(
            self.root, text="Add Server Clock", font=("Arial", 12),
            command=lambda: self.add_clock(True), bg="#555", fg="white", relief="flat"
        ).pack(pady=5)

    def add_clock(self, use_server_time):
        ssh_config = None
        if use_server_time:
            # Try to load saved config first
            ssh_config = load_config()
            
            # If no saved config or user wants to change, ask for credentials
            if not ssh_config or messagebox.askyesno("SSH Config", "Use saved SSH configuration?"):
                ssh_config = ask_ssh_credentials()
                if ssh_config:
                    save_config(**ssh_config)
                else:
                    return
            
            # Test the connection
            result = get_server_time(
                ssh_config['host'],
                ssh_config['port'],
                ssh_config['username'],
                ssh_config['password']
            )
            
            if result.startswith("Error"):
                messagebox.showerror("Connection Failed", result)
                return

        ClockWindow(self.root, self.clock_id, use_server_time, ssh_config)
        self.clock_id += 1

if __name__ == "__main__":
    root = tk.Tk()
    app = ClockLauncher(root)
    root.mainloop()



