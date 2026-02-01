import socket
import threading
import time
import re
import tkinter as tk
from tkinter import scrolledtext, messagebox
from cryptography.fernet import Fernet

# --- VERSIONING ---
VERSION = "1.1.9" 

# --- CONFIG ---
SHARED_KEY = b'uV9_78X3yJ8Xm5-rXWn8X2Z8X1Y8X2Z8X1Y8X2Z8X1Y=' 
cipher = Fernet(SHARED_KEY)
DISCOVERY_PORT = 5556
BASE_CHAT_PORT = 5557 

COLORS = {
    "bg": "#0f0f0f",
    "panel": "#1a1a1a",
    "input": "#252525",
    "text": "#ececec",
    "accent": "#007acc",
    "green": "#4ade80",
    "dim": "#666666"
}

class p2chat:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        
        try:
            self.icon = tk.PhotoImage(file="logo.png")
            self.root.iconphoto(False, self.icon)
        except: pass

        self.username = ""
        self.my_port = BASE_CHAT_PORT
        self.peers = {} # {username: (ip, port)}
        self.show_briefing(is_initial=True)

    def show_briefing(self, is_initial=False):
        b_win = tk.Toplevel(self.root)
        b_win.title("Security" if is_initial else "Deep Dive")
        b_win.geometry("450x420")
        b_win.configure(bg=COLORS["bg"])
        b_win.attributes("-topmost", True)
        b_win.resizable(False, False)

        # Disable "X" close button
        b_win.protocol("WM_DELETE_WINDOW", lambda: None)

        title = "SECURITY BRIEFING" if is_initial else "TECHNICAL ARCHIVE"
        body = (
            "E2EE ENCRYPTION ACTIVE\n\n"
            "p2chat uses P2P discovery. Identity Protection is enabled: "
            "The system verifies name uniqueness before entry.\n\n"
            "v1.1.9: Recipient box converted to high-contrast OptionMenu to "
            "fix Windows theme color bugs."
        )

        tk.Label(b_win, text=title, bg=COLORS["bg"], fg=COLORS["accent"], font=("Arial", 12, "bold")).pack(pady=20)
        tk.Message(b_win, text=body, bg=COLORS["bg"], fg=COLORS["text"], width=380, font=("Arial", 10)).pack(pady=10)

        # FIXED: The button now actually triggers the close/launch logic
        def on_click():
            b_win.destroy()
            if is_initial:
                self.show_login()

        tk.Button(b_win, text="I ACCEPT" if is_initial else "CLOSE", bg=COLORS["accent"], 
                  fg="white", relief="flat", command=on_click, width=15).pack(pady=20)

    def show_login(self):
        login = tk.Toplevel(self.root)
        login.geometry("300x180")
        login.title("Login")
        login.configure(bg=COLORS["bg"])
        tk.Label(login, text="ENTER USERNAME", bg=COLORS["bg"], fg=COLORS["accent"], font=("Arial", 10, "bold")).pack(pady=15)
        entry = tk.Entry(login, bg=COLORS["input"], fg="white", justify="center", borderwidth=0)
        entry.pack(pady=5, padx=30, fill=tk.X)

        def check_and_launch():
            name = entry.get().strip()
            if not re.match(r"^\w+$", name): return
            
            # Hijack Check
            scan_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            scan_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            scan_sock.settimeout(1.2)
            try: scan_sock.bind(('', DISCOVERY_PORT))
            except: pass 

            start_time = time.time()
            while time.time() - start_time < 1.5:
                try:
                    data, _ = scan_sock.recvfrom(1024)
                    if f":{name}:" in data.decode():
                        messagebox.showerror("Error", "Username taken.")
                        scan_sock.close()
                        return
                except: pass
            
            scan_sock.close()
            self.username = name
            login.destroy()
            self.build_main()

        tk.Button(login, text="LAUNCH", bg=COLORS["accent"], fg="white", relief="flat", command=check_and_launch, width=12).pack(pady=20)

    def build_main(self):
        self.root.deiconify()
        self.root.title(f"p2chat v{VERSION}")
        self.root.geometry("640x480")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS["bg"])

        # Header
        top = tk.Frame(self.root, bg=COLORS["panel"])
        top.pack(fill=tk.X)
        tk.Label(top, text=f"ID: {self.username}", bg=COLORS["panel"], fg=COLORS["green"], font=("Consolas", 10, "bold")).pack(side=tk.LEFT, padx=10, pady=8)
        tk.Button(top, text="ⓘ", bg=COLORS["panel"], fg=COLORS["dim"], relief="flat", command=lambda: self.show_briefing(False)).pack(side=tk.RIGHT, padx=5)

        # Chat Log
        self.log = scrolledtext.ScrolledText(self.root, bg=COLORS["bg"], fg=COLORS["text"], borderwidth=0, font=("Consolas", 11), height=18)
        self.log.pack(padx=10, pady=10, fill=tk.X)

        # Bottom Tray
        bottom = tk.Frame(self.root, bg=COLORS["bg"])
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 20))

        # THE BIG FIX: Using OptionMenu instead of ttk.Combobox to force colors
        self.peer_var = tk.StringVar(value="Peers")
        self.peer_drop = tk.OptionMenu(bottom, self.peer_var, "Searching...")
        self.peer_drop.config(bg=COLORS["panel"], fg="white", activebackground=COLORS["accent"], 
                              activeforeground="white", highlightthickness=0, relief="flat", width=12)
        self.peer_drop["menu"].config(bg=COLORS["panel"], fg="white")
        self.peer_drop.grid(row=0, column=0, padx=(0, 5))

        # Entry Box
        self.entry = tk.Entry(bottom, bg=COLORS["input"], fg="white", borderwidth=0, font=("Arial", 12), insertbackground="white")
        self.entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.entry.bind("<Return>", self.send_msg)

        # Send Button
        tk.Button(bottom, text="SEND MESSAGE", bg=COLORS["accent"], fg="white", relief="flat", 
                  font=("Arial", 10, "bold"), command=self.send_msg, padx=15).grid(row=0, column=2, padx=(5, 0))

        bottom.columnconfigure(1, weight=1)
        self.setup_net()

    def setup_net(self):
        self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                self.tcp.bind(('0.0.0.0', self.my_port))
                break
            except: self.my_port += 1
        self.tcp.listen(5)
        threading.Thread(target=self.recv_loop, daemon=True).start()

        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try: self.udp.bind(('', DISCOVERY_PORT))
        except: pass
        
        threading.Thread(target=self.broadcast, daemon=True).start()
        threading.Thread(target=self.discover, daemon=True).start()

    def broadcast(self):
        while True:
            data = f"P2P_V119:{self.username}:{self.my_port}".encode()
            self.udp.sendto(data, ('255.255.255.255', DISCOVERY_PORT))
            self.udp.sendto(data, ('127.0.0.1', DISCOVERY_PORT))
            time.sleep(3)

    def discover(self):
        while True:
            try:
                data, addr = self.udp.recvfrom(1024)
                parts = data.decode().split(":")
                if parts[0] == "P2P_V119" and parts[1] != self.username:
                    self.peers[parts[1]] = (addr[0], int(parts[2]))
                    self.root.after(0, self.update_drop)
            except: pass

    def update_drop(self):
        menu = self.peer_drop["menu"]
        menu.delete(0, "end")
        for user in self.peers.keys():
            menu.add_command(label=user, command=lambda value=user: self.peer_var.set(value))
        if self.peer_var.get() == "Peers" or self.peer_var.get() == "Searching...":
            if self.peers: self.peer_var.set(list(self.peers.keys())[0])

    def recv_loop(self):
        while True:
            conn, _ = self.tcp.accept()
            try:
                data = conn.recv(8192)
                msg = cipher.decrypt(data).decode()
                self.root.after(0, self.display, msg)
            except: pass
            conn.close()

    def send_msg(self, e=None):
        target = self.peer_var.get()
        if target in ["Peers", "Searching..."]: return
        content = self.entry.get().strip()
        if not content: return
        ip, port = self.peers[target]
        dest_ip = '127.0.0.1' if ip == socket.gethostbyname(socket.gethostname()) else ip
        try:
            enc = cipher.encrypt(f"[{self.username}]: {content}".encode())
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((dest_ip, port))
            s.send(enc)
            s.close()
            self.display(f"[ME -> {target}]: {content}")
            self.entry.delete(0, tk.END)
        except: messagebox.showerror("Error", "Peer unreachable.")

    def display(self, m):
        self.log.configure(state='normal')
        self.log.insert(tk.END, m + "\n")
        self.log.configure(state='disabled')
        self.log.yview(tk.END)

if __name__ == "__main__":
    app = p2chat()
    app.root.mainloop()