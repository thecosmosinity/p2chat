# p2chat

## having windows defender errors? check out this detailed description about the error: https://thecosmosinity.github.io/p2chat.html/

**p2chat** is a secure, lightweight, peer-to-peer (P2P) chat utility designed for local networks. This version is specifically optimized for high-performance usage on modern Windows systems while maintaining a **640x480 hard-locked resolution** for CRT monitor compatibility and retro-aesthetic workflows.
this project was written in pure **python**
---
p2chat is encrypted using aes-128. unreadable to packet-sniffers, isp's and people trying to snoop through your chats. nothing leaves your machine. not even connecting to the web is required, as long as you're on the same wi-fi, whether no internet is provided, it will still work.
---
## 🚀 Key Features

* **End-to-End Encryption (E2EE):** All communication is secured using the Fernet (AES-128) specification. Encryption and decryption happen locally; plain text never leaves your machine.
* **Zero-Server Architecture:** Uses UDP local discovery to find peers on your network automatically. No central server means no downtime and no data harvesting.
* **CRT-Optimized UI:** Hard-locked 640x480 resolution ensures that the interface is perfectly scannable on vintage displays without losing access to controls (like the Send button).
* **Identity Protection:** Features a "Pre-Flight Identity Scan" that prevents two users from using the same username on the same network, stopping hijacking attempts before they start.
* **High-Contrast Theme:** Dark-mode interface designed for high visibility on both modern LED and legacy CRT panels.

---

## 🛠️ Setup & Requirements

* **OS:** Windows 10 / Windows 11.
* **Python Version:** 3.10 or higher.
* **Primary Dependency:** `cryptography`

### Installation from source

1. Install the required encryption library via terminal:
   pip install cryptography

2. Make sure main.py is in the current folder, then run python3 main.py

3. Or, go for the **easy** way out and download the pre-made .exe file

## ⚠️ Connectivity Troubleshooting
Windows Firewall: You must allow the application through the Windows Defender Firewall. If peers cannot see you, ensure Inbound Rules for ports 5556 and 5557 are active for "Private" networks.
Subnet Issues: Peer discovery works strictly on the local subnet. If using a Virtual Machine, ensure your network adapter is set to Bridged Mode rather than NAT.
