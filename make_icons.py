"""
Рисует иконки для exe-файлов: icons/button.ico и icons/display.ico.
Нужен Pillow: pip install pillow
"""

import os

from PIL import Image, ImageDraw

ICONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
SIZE = 256  # рисуем крупно, потом Pillow сам уменьшит до 16..256
ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def button_icon():
    """Большая красная круглая кнопка на сером основании."""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # основание
    d.rounded_rectangle((16, 120, 240, 236), radius=40, fill="#424242")
    d.rounded_rectangle((16, 110, 240, 220), radius=40, fill="#757575")
    # боковина кнопки
    d.ellipse((44, 84, 212, 196), fill="#b71c1c")
    d.rectangle((44, 112, 212, 140), fill="#b71c1c")
    # верх кнопки
    d.ellipse((44, 40, 212, 152), fill="#e53935")
    # блик
    d.ellipse((76, 58, 140, 92), fill="#ef9a9a")
    return img


def display_icon():
    """Картинка в рамке: небо, солнце, горы."""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # рамка
    d.rounded_rectangle((8, 28, 248, 228), radius=24, fill="#5d4037")
    # небо
    d.rectangle((28, 48, 228, 208), fill="#4fc3f7")
    # солнце
    d.ellipse((150, 64, 202, 116), fill="#ffd600")
    # горы
    d.polygon([(28, 208), (100, 108), (172, 208)], fill="#2e7d32")
    d.polygon([(110, 208), (170, 140), (228, 196), (228, 208)], fill="#43a047")
    d.polygon([(100, 108), (84, 131), (116, 131)], fill="white")
    return img


def save_icons():
    os.makedirs(ICONS_DIR, exist_ok=True)
    for name, draw in (("button", button_icon), ("display", display_icon)):
        img = draw()
        img.save(os.path.join(ICONS_DIR, f"{name}.ico"), sizes=ICO_SIZES)
        img.save(os.path.join(ICONS_DIR, f"{name}.png"))


if __name__ == "__main__":
    save_icons()
    print("Иконки сохранены в", ICONS_DIR)
