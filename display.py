"""
Ноутбук №2 — ЭКРАН С КАРТИНКОЙ.

Запускается первым. Ждёт сигнала по сети от button.py и при каждом нажатии
кнопки показывает следующую картинку.

Картинки берутся из папки "images" рядом с этим файлом.
  * PNG и GIF работают всегда.
  * JPG/BMP и подгонка под размер окна — если установлен Pillow (pip install pillow).
  * Если папка пустая — рисуются встроенные цветные картинки.

Клавиши: F11 — полный экран, Esc — выход из полного экрана.
"""

import math
import os
import queue
import socket
import threading
import tkinter as tk

PORT = 5005
IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

EXTENSIONS = (".png", ".gif", ".jpg", ".jpeg", ".bmp", ".webp") if HAS_PIL else (".png", ".gif")

# Встроенные картинки на случай, если папка images пустая: (фон, фигура, цвет фигуры)
BUILTIN = [
    ("#ffeb3b", "sun", "#ff9800"),
    ("#81d4fa", "circle", "#1565c0"),
    ("#c8e6c9", "tree", "#2e7d32"),
    ("#f8bbd0", "heart", "#d81b60"),
    ("#1a237e", "star", "#ffd600"),
    ("#ffe0b2", "house", "#6d4c41"),
]


def get_local_ip():
    """IP этого ноутбука в локальной сети (его нужно ввести на ноутбуке с кнопкой)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))  # пакет реально не отправляется
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def run_server(events):
    """Фоновый поток: принимает подключения от кнопки и кладёт команды в очередь."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", PORT))
    srv.listen()
    while True:
        conn, addr = srv.accept()
        with conn:
            conn.settimeout(3)
            try:
                command = conn.recv(64).decode("utf-8", "ignore").strip().upper()
            except OSError:
                continue
            if command in ("NEXT", "PREV"):
                reply = queue.Queue()
                events.put((command, reply))
                try:
                    number = reply.get(timeout=3)
                    conn.sendall(f"OK {number}\n".encode())
                except (queue.Empty, OSError):
                    pass
            elif command == "PING":
                conn.sendall(b"PONG\n")


class DisplayApp:
    def __init__(self, root):
        self.root = root
        self.events = queue.Queue()
        self.index = 0
        self.photo = None  # держим ссылку, иначе tkinter "потеряет" картинку

        self.files = sorted(
            os.path.join(IMAGES_DIR, f)
            for f in (os.listdir(IMAGES_DIR) if os.path.isdir(IMAGES_DIR) else [])
            if f.lower().endswith(EXTENSIONS)
        )
        self.count = len(self.files) or len(BUILTIN)

        root.title("Картинка")
        root.geometry("900x650")
        root.configure(bg="black")
        root.bind("<F11>", lambda e: root.attributes("-fullscreen", not root.attributes("-fullscreen")))
        root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))

        self.canvas = tk.Canvas(root, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.status = tk.Label(
            root,
            text=f"IP этого ноутбука: {get_local_ip()}   порт: {PORT}",
            bg="#222", fg="white", font=("Segoe UI", 11), pady=4,
        )
        self.status.pack(fill="x")

        self.canvas.bind("<Configure>", lambda e: self.show())
        threading.Thread(target=run_server, args=(self.events,), daemon=True).start()
        self.poll()

    def poll(self):
        """Забираем команды из сетевого потока (tkinter можно трогать только из главного потока)."""
        while not self.events.empty():
            command, reply = self.events.get()
            step = 1 if command == "NEXT" else -1
            self.index = (self.index + step) % self.count
            self.show()
            reply.put(self.index + 1)
        self.root.after(50, self.poll)

    def show(self):
        c = self.canvas
        c.delete("all")
        w, h = max(c.winfo_width(), 1), max(c.winfo_height(), 1)
        if self.files:
            self.show_file(self.files[self.index], w, h)
        else:
            self.draw_builtin(BUILTIN[self.index], w, h)
        c.create_text(w - 10, 10, anchor="ne", text=f"{self.index + 1} / {self.count}",
                      fill="white", font=("Segoe UI", 14, "bold"))

    def show_file(self, path, w, h):
        try:
            if HAS_PIL:
                img = Image.open(path)
                img.thumbnail((w, h))
                self.photo = ImageTk.PhotoImage(img)
            else:
                self.photo = tk.PhotoImage(file=path)
            self.canvas.create_image(w // 2, h // 2, image=self.photo)
        except Exception as err:
            self.canvas.create_text(w // 2, h // 2, text=f"Не удалось открыть\n{os.path.basename(path)}\n{err}",
                                    fill="red", font=("Segoe UI", 16), justify="center")

    def draw_builtin(self, item, w, h):
        bg, shape, color = item
        c = self.canvas
        c.create_rectangle(0, 0, w, h, fill=bg, outline="")
        cx, cy, r = w / 2, h / 2, min(w, h) / 3.2
        if shape == "sun":
            for i in range(12):
                a =math.radians(i * 30)
                c.create_line(cx + r * 0.9 * math.cos(a), cy + r * 0.9 * math.sin(a),
                              cx + r * 1.3 * math.cos(a), cy + r * 1.3 * math.sin(a), fill=color, width=8)
            c.create_oval(cx - r * 0.8, cy - r * 0.8, cx + r * 0.8, cy + r * 0.8, fill=color, outline="")
        elif shape == "circle":
            c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color, outline="")
            c.create_oval(cx - r * 0.5, cy - r * 0.6, cx - r * 0.1, cy - r * 0.2, fill="white", outline="")
        elif shape == "tree":
            for k in range(3):
                top = cy - r + k * r * 0.5
                c.create_polygon(cx, top, cx - r * (0.5 + k * 0.25), top + r * 0.8,
                                 cx + r * (0.5 + k * 0.25), top + r * 0.8, fill=color)
            c.create_rectangle(cx - r * 0.12, cy + r * 0.8, cx + r * 0.12, cy + r * 1.1, fill="#5d4037", outline="")
        elif shape == "heart":
            c.create_oval(cx - r, cy - r * 0.7, cx, cy + r * 0.3, fill=color, outline="")
            c.create_oval(cx, cy - r * 0.7, cx + r, cy + r * 0.3, fill=color, outline="")
            c.create_polygon(cx - r * 0.97, cy - r * 0.05, cx + r * 0.97, cy - r * 0.05, cx, cy + r * 1.1, fill=color)
        elif shape == "star":
            pts = []
            for i in range(10):
                rr = r if i % 2 == 0 else r * 0.4
                a = math.radians(-90 + i * 36)
                pts += [cx + rr * math.cos(a), cy + rr * math.sin(a)]
            c.create_polygon(pts, fill=color)
        elif shape == "house":
            c.create_rectangle(cx - r * 0.8, cy - r * 0.1, cx + r * 0.8, cy + r, fill="#ffcc80", outline=color, width=4)
            c.create_polygon(cx - r, cy - r * 0.1, cx + r, cy - r * 0.1, cx, cy - r, fill=color)
            c.create_rectangle(cx - r * 0.2, cy + r * 0.4, cx + r * 0.2, cy + r, fill=color, outline="")


if __name__ == "__main__":
    root = tk.Tk()
    DisplayApp(root)
    root.mainloop()
