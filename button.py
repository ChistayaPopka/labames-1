"""
Ноутбук №1 — КНОПКА.

Введите IP-адрес второго ноутбука (он написан внизу окна display.py)
и нажимайте кнопку — картинка на втором ноутбуке будет меняться.
Пробел или Enter тоже нажимают кнопку.
"""

import os
import socket
import threading
import tkinter as tk

PORT = 5005
SAVED_IP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_ip.txt")


def send_command(ip, command):
    """Отправляет команду экрану и возвращает его ответ."""
    with socket.create_connection((ip, PORT), timeout=3) as s:
        s.sendall(f"{command}\n".encode())
        return s.recv(64).decode().strip()


class ButtonApp:
    def __init__(self, root):
        self.root = root
        root.title("Кнопка")
        root.geometry("420x360")
        root.configure(bg="#f0f0f0")

        top = tk.Frame(root, bg="#f0f0f0")
        top.pack(pady=12)
        tk.Label(top, text="IP второго ноутбука:", bg="#f0f0f0", font=("Segoe UI", 11)).pack(side="left")
        self.ip = tk.StringVar(value=self.load_ip())
        tk.Entry(top, textvariable=self.ip, width=16, font=("Segoe UI", 12)).pack(side="left", padx=6)

        self.button = tk.Button(
            root, text="СМЕНИТЬ\nКАРТИНКУ", font=("Segoe UI", 26, "bold"),
            bg="#e53935", fg="white", activebackground="#b71c1c", activeforeground="white",
            relief="raised", bd=6, cursor="hand2", takefocus=0, command=self.press,
        )
        self.button.pack(expand=True, fill="both", padx=30, pady=10)

        self.status = tk.Label(root, text="", bg="#f0f0f0", font=("Segoe UI", 11))
        self.status.pack(pady=(0, 12))

        root.bind("<space>", lambda e: self.press())
        root.bind("<Return>", lambda e: self.press())

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

    def press(self):
        ip = self.ip.get().strip()
        if not ip:
            self.set_status("Сначала введите IP второго ноутбука", "red")
            return
        self.set_status("Отправляю...", "gray")
        # сеть — в отдельном потоке, чтобы окно не зависало
        threading.Thread(target=self.worker, args=(ip,), daemon=True).start()

    def worker(self, ip):
        try:
            send_command(ip, "NEXT")
            self.save_ip(ip)
            self.root.after(0, self.set_status, "", "black")
        except OSError as err:
            self.root.after(0, self.set_status, f"Нет связи с {ip}: {err}", "red")

    def set_status(self, text, color):
        self.status.config(text=text, fg=color)


if __name__ == "__main__":
    root = tk.Tk()
    ButtonApp(root)
    root.mainloop()
