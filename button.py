"""
Ноутбук №1 — КНОПКА.

Введите IP-адрес второго ноутбука (он написан внизу окна display.py)
и нажимайте кнопку — картинка на втором ноутбуке будет меняться.
Пробел или Enter тоже нажимают кнопку.
"""

import os
import socket
import sys
import threading
import time
import tkinter as tk

PORT = 5005
# в собранном exe файлы лежат рядом с exe, а не рядом с .py
APP_DIR = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
SAVED_IP_FILE = os.path.join(APP_DIR, "last_ip.txt")
ICON_FILE = os.path.join(getattr(sys, "_MEIPASS", APP_DIR), "icons", "button.ico")

# цвета интерфейса
BG = "#1f2430"
CARD = "#2a3040"
FIELD = "#353c4f"
TEXT = "#f1f5f9"
MUTED = "#94a3b8"
SHADOW = "#161a23"
RED = "#ef4444"
RED_HOVER = "#f87171"
RED_DARK = "#991b1b"
RED_SHINE = "#fca5a5"
GREEN = "#22c55e"
YELLOW = "#facc15"
GRAY = "#64748b"
FONT = "Segoe UI"


def send_command(ip, command):
    """Отправляет команду экрану и возвращает его ответ."""
    with socket.create_connection((ip, PORT), timeout=3) as s:
        s.sendall(f"{command}\n".encode())
        return s.recv(64).decode().strip()


class ButtonApp:
    def __init__(self, root):
        self.root = root
        self.pressed = False
        self.hover = False
        self.current_ip = ""

        root.title("Кнопка")
        root.geometry("440x580")
        root.minsize(340, 460)
        root.configure(bg=BG)
        try:
            root.iconbitmap(ICON_FILE)
        except tk.TclError:
            pass

        tk.Label(root, text="Пульт", bg=BG, fg=TEXT, font=(FONT, 22, "bold")).pack(pady=(18, 2))
        tk.Label(root, text="меняет картинку на другом ноутбуке", bg=BG, fg=MUTED,
                 font=(FONT, 10)).pack()

        # карточка с IP и индикатором связи
        card = tk.Frame(root, bg=CARD, padx=16, pady=12)
        card.pack(fill="x", padx=20, pady=16)
        tk.Label(card, text="IP ноутбука с картинкой", bg=CARD, fg=MUTED,
                 font=(FONT, 10)).pack(anchor="w")
        self.ip = tk.StringVar(value=self.load_ip())
        self.ip.trace_add("write", lambda *_: self.on_ip_change())
        self.entry = tk.Entry(
            card, textvariable=self.ip, font=(FONT, 16), bg=FIELD, fg=TEXT,
            insertbackground=TEXT, relief="flat", highlightthickness=2,
            highlightbackground=FIELD, highlightcolor=RED,
        )
        self.entry.pack(fill="x", pady=(4, 8), ipady=4)

        status_row = tk.Frame(card, bg=CARD)
        status_row.pack(anchor="w")
        self.dot = tk.Canvas(status_row, width=12, height=12, bg=CARD, highlightthickness=0)
        self.dot.pack(side="left", padx=(0, 6))
        self.status = tk.Label(status_row, text="", bg=CARD, fg=MUTED, font=(FONT, 10))
        self.status.pack(side="left")

        # большая круглая кнопка рисуется на холсте
        self.canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=20)
        self.canvas.bind("<Configure>", lambda e: self.draw_button())
        self.canvas.tag_bind("btn", "<Button-1>", lambda e: self.press())
        self.canvas.tag_bind("btn", "<Enter>", lambda e: self.set_hover(True))
        self.canvas.tag_bind("btn", "<Leave>", lambda e: self.set_hover(False))

        self.counter = tk.Label(root, text="Нажмите кнопку или пробел", bg=BG, fg=MUTED,
                                font=(FONT, 14))
        self.counter.pack(pady=(4, 20))

        root.bind("<space>", self.on_key)
        root.bind("<Return>", self.on_key)
        # клик мимо поля ввода убирает из него курсор, чтобы пробел нажимал кнопку
        root.bind("<Button-1>", lambda e: e.widget is not self.entry and root.focus_set())

        self.on_ip_change()
        threading.Thread(target=self.watch_link, daemon=True).start()

    # --- кнопка ---

    def draw_button(self):
        c = self.canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        r = max(min(w, h) * 0.40, 20)
        depth = r * 0.12
        cx, cy = w / 2, h / 2 - depth / 2
        shift = depth * 0.8 if self.pressed else 0

        c.create_oval(cx - r * 1.05, cy - r * 0.95 + depth * 1.6, cx + r * 1.05, cy + r * 1.05 + depth * 1.6,
                      fill=SHADOW, outline="")
        c.create_oval(cx - r, cy - r + depth, cx + r, cy + r + depth, fill=RED_DARK, outline="", tags="btn")
        top = RED_HOVER if self.hover and not self.pressed else RED
        c.create_oval(cx - r, cy - r + shift, cx + r, cy + r + shift, fill=top, outline="", tags="btn")
        c.create_oval(cx - r * 0.55, cy - r * 0.78 + shift, cx - r * 0.05, cy - r * 0.48 + shift,
                      fill=RED_SHINE, outline="", tags="btn")
        c.create_text(cx, cy + shift, text="ЖМИ!", fill="white",
                      font=(FONT, max(int(r * 0.28), 10), "bold"), tags="btn")

    def set_hover(self, value):
        self.hover = value
        self.canvas.config(cursor="hand2" if value else "")
        self.draw_button()

    def on_key(self, event):
        # пробел в поле ввода — это просто пробел; Enter жмёт кнопку всегда
        if event.keysym == "space" and self.root.focus_get() is self.entry:
            return
        self.press()

    def press(self):
        self.pressed = True
        self.draw_button()
        self.root.after(140, self.release)

        ip = self.current_ip
        if not ip:
            self.set_status("Сначала введите IP", RED)
            self.entry.focus_set()
            return
        threading.Thread(target=self.worker, args=(ip,), daemon=True).start()

    def release(self):
        self.pressed = False
        self.draw_button()

    def worker(self, ip):
        # сеть — в отдельном потоке, чтобы окно не зависало
        try:
            reply = send_command(ip, "NEXT")
            self.save_ip(ip)
            self.root.after(0, self.on_sent, reply)
        except OSError:
            self.root.after(0, self.set_status, "Нет связи — проверьте IP и Wi-Fi", RED)

    def on_sent(self, reply):
        self.set_status("На связи", GREEN)
        number = reply[3:] if reply.startswith("OK ") else ""
        if "/" in number:
            current, total = number.split("/", 1)
            self.counter.config(text=f"Картинка {current} из {total}", fg=TEXT)
        elif number:
            self.counter.config(text=f"Картинка {number}", fg=TEXT)

    # --- связь ---

    def on_ip_change(self):
        self.current_ip = self.ip.get().strip()
        if self.current_ip:
            self.set_status("Проверяю связь...", YELLOW)
        else:
            self.set_status("Введите IP — он написан внизу окна с картинкой", GRAY)

    def watch_link(self):
        """Раз в пару секунд проверяет, отвечает ли экран."""
        while True:
            ip = self.current_ip
            if ip:
                try:
                    ok = send_command(ip, "PING") == "PONG"
                except OSError:
                    ok = False
                if ip == self.current_ip:
                    self.root.after(0, self.show_link, ok)
            time.sleep(2)

    def show_link(self, ok):
        if ok:
            self.set_status("На связи", GREEN)
        else:
            self.set_status("Нет связи — проверьте IP и Wi-Fi", RED)

    def set_status(self, text, color):
        self.status.config(text=text, fg=TEXT if color in (GREEN, RED) else MUTED)
        self.dot.delete("all")
        self.dot.create_oval(1, 1, 11, 11, fill=color, outline="")

    def load_ip(self):
        try:
            with open(SAVED_IP_FILE, encoding="utf-8") as f:
                return f.read().strip()
        except OSError:
            return ""

    def save_ip(self, ip):
        try:
            with open(SAVED_IP_FILE, "w", encoding="utf-8") as f:
                f.write(ip)
        except OSError:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    ButtonApp(root)
    root.mainloop()
