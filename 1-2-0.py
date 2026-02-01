import socket
import threading
import time
import re
import base64
import tkinter as tk
from tkinter import scrolledtext, messagebox
from cryptography.fernet import Fernet

# --- CONFIG ---
VERSION = "1.2.0-STABLE"
SHARED_KEY = b'uV9_78X3yJ8Xm5-rXWn8X2Z8X1Y8X2Z8X1Y8X2Z8X1Y=' 
cipher = Fernet(SHARED_KEY)
DISCOVERY_PORT = 5556
START_PORT = 5557 # We will increment if this is busy

COLORS = {
    "bg": "#0f0f0f", "panel": "#1a1a1a", "input": "#252525",
    "text": "#ececec", "accent": "#007acc", "green": "#4ade80", "dim": "#666666"
}

class p2chat:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.username = ""
        self.my_port = START_PORT
        self.peers = {} # {name: (ip, port)}
        self.show_login()

    def show_login(self):
        login = tk.Toplevel(self.root)
        login.title("p2chat v1.2")
        login.geometry("300x180")
        login.configure(bg=COLORS["bg"])
        tk.Label(login, text="SECURE IDENTITY", bg=COLORS["bg"], fg=COLORS["accent"], font=("Arial", 10, "bold")).pack(pady=15)
        entry = tk.Entry(login, bg=COLORS["input"], fg="white", justify="center", borderwidth=0)
        entry.pack(pady=5, padx=30, fill=tk.X)
        entry.focus_set()

        def launch():
            name = entry.get().strip()
            if name and re.match(r"^\w+$", name):
                self.username = name
                login.destroy()
                self.build_main()
        tk.Button(login, text="LAUNCH HUB", bg=COLORS["accent"], fg="white", command=launch).pack(pady=20)

    def build_main(self):
        self.root.deiconify()
        self.root.title(f"p2chat {VERSION}")
        self.root.geometry("600x520")
        self.root.configure(bg=COLORS["bg"])

        top = tk.Frame(self.root, bg=COLORS["panel"], height=40)
        top.pack(fill=tk.X)
        self.id_label = tk.Label(top, text=f"ID: {self.username}", bg=COLORS["panel"], fg=COLORS["green"], font=("Consolas", 10))
        self.id_label.pack(side=tk.LEFT, padx=10)

        self.log = scrolledtext.ScrolledText(self.root, bg=COLORS["bg"], fg=COLORS["text"], borderwidth=0, font=("Consolas", 11), state='disabled')
        self.log.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        bottom = tk.Frame(self.root, bg=COLORS["bg"])
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 20))

        self.peer_var = tk.StringVar(value="GROUP CHAT")
        self.peer_drop = tk.OptionMenu(bottom, self.peer_var, "GROUP CHAT")
        self.peer_drop.config(bg=COLORS["panel"], fg="white", width=12)
        self.peer_drop.grid(row=0, column=0, padx=(0, 5))

        self.entry = tk.Entry(bottom, bg=COLORS["input"], fg="white", borderwidth=0, font=("Arial", 12), insertbackground="white")
        self.entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.entry.bind("<Return>", self.send_msg)

        tk.Button(bottom, text="SEND", bg=COLORS["accent"], fg="white", command=self.send_msg, padx=20).grid(row=0, column=2)
        bottom.columnconfigure(1, weight=1)

        self.setup_network()

    def setup_network(self):
        # FIX: Try multiple ports so we can run multiple instances on one PC
        self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                self.tcp.bind(('0.0.0.0', self.my_port))
                break
            except OSError:
                self.my_port += 1
        
        self.id_label.config(text=f"ID: {self.username} (Port: {self.my_port})")
        self.tcp.listen(5)
        threading.Thread(target=self.tcp_listen, daemon=True).start()

        # FIX: Initialize UDP before threads start to avoid AttributeError
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.udp.bind(('', DISCOVERY_PORT))
        except OSError:
            # If discovery port is busy, we can still send, just maybe not listen on same port
            pass
        
        threading.Thread(target=self.broadcast_presence, daemon=True).start()
        threading.Thread(target=self.udp_listen, daemon=True).start()

    def broadcast_presence(self):
        while True:
            # We must broadcast our dynamic port so peers know where to connect
            msg = f"HI:{self.username}:{self.my_port}".encode()
            self.udp.sendto(msg, ('255.255.255.255', DISCOVERY_PORT))
            time.sleep(5)

    def udp_listen(self):
        # Create a separate socket for listening to avoid port conflicts
        l_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        l_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            l_sock.bind(('', DISCOVERY_PORT))
        except: return

        while True:
            try:
                data, addr = l_sock.recvfrom(4096)
                msg = data.decode()
                if msg.startswith("HI:"):
                    parts = msg.split(":")
                    name, port = parts[1], int(parts[2])
                    if name != self.username:
                        self.peers[name] = (addr[0], port)
                        self.update_peer_list()
                elif msg.startswith("GRP:"):
                    try:
                        decrypted = cipher.decrypt(msg[4:].encode()).decode()
                        if not decrypted.startswith(f"[{self.username}]"):
                            self.display(f"👥 {decrypted}")
                    except: pass
            except: pass

    def tcp_listen(self):
        while True:
            try:
                conn, _ = self.tcp.accept()
                data = conn.recv(4096)
                decrypted = cipher.decrypt(data).decode()
                self.display(f"🔒 {decrypted}")
                conn.close()
            except: pass

    def update_peer_list(self):
        menu = self.peer_drop["menu"]
        menu.delete(0, "end")
        menu.add_command(label="GROUP CHAT", command=lambda: self.peer_var.set("GROUP CHAT"))
        for name in sorted(self.peers.keys()):
            menu.add_command(label=name, command=lambda v=name: self.peer_var.set(v))

    def send_msg(self, event=None):
        target = self.peer_var.get()
        content = self.entry.get().strip()
        if not content: return

        raw_payload = f"[{self.username}]: {content}"
        encrypted = cipher.encrypt(raw_payload.encode())

        if target == "GROUP CHAT":
            self.udp.sendto(f"GRP:".encode() + encrypted, ('255.255.255.255', DISCOVERY_PORT))
            self.display(f"👥 [ME]: {content}")
        else:
            try:
                ip, port = self.peers[target]
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                s.connect((ip, port))
                s.send(encrypted)
                s.close()
                self.display(f"🔒 [TO {target}]: {content}")
            except:
                self.display(f"[SYSTEM]: {target} is offline.")
        
        self.entry.delete(0, tk.END)

    def display(self, msg):
        self.log.config(state='normal')
        self.log.insert(tk.END, msg + "\n")
        self.log.config(state='disabled')
        self.log.see(tk.END)

if __name__ == "__main__":
    p2chat().root.mainloop()