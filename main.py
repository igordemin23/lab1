import tkinter as tk
from tkinter import colorchooser

# ==========================================
# 1. MODEL (Чистая математика)
# ==========================================

def clamp(val, min_val, max_val):
    return max(min_val, min(val, max_val))

def _gamma_correct(val):
    return ((val + 0.055) / 1.055) ** 2.4 if val >= 0.04045 else val / 12.92

def _gamma_inverse(val):
    return 1.055 * (val ** (1.0 / 2.4)) - 0.055 if val >= 0.0031308 else 12.92 * val

def rgb_to_xyz(r, g, b):
    r_norm, g_norm, b_norm = _gamma_correct(r / 255.0), _gamma_correct(g / 255.0), _gamma_correct(b / 255.0)
    x = (0.412453 * r_norm + 0.357580 * g_norm + 0.180423 * b_norm) * 100
    y = (0.212671 * r_norm + 0.715160 * g_norm + 0.072169 * b_norm) * 100
    z = (0.019334 * r_norm + 0.119193 * g_norm + 0.950227 * b_norm) * 100
    return x, y, z

def xyz_to_rgb(x, y, z):
    x, y, z = x / 100.0, y / 100.0, z / 100.0
    r_norm = 3.2406 * x - 1.5372 * y - 0.4986 * z
    g_norm = -0.9689 * x + 1.8758 * y + 0.0415 * z
    b_norm = 0.0557 * x - 0.2040 * y + 1.0570 * z

    r = _gamma_inverse(r_norm) * 255.0
    g = _gamma_inverse(g_norm) * 255.0
    b = _gamma_inverse(b_norm) * 255.0

    out_of_bounds = False
    if r < 0 or r > 255 or g < 0 or g > 255 or b < 0 or b > 255:
        out_of_bounds = True

    return clamp(r, 0, 255), clamp(g, 0, 255), clamp(b, 0, 255), out_of_bounds

def rgb_to_hls(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    max_val, min_val = max(r, g, b), min(r, g, b)
    h, s, l = 0, 0, (max_val + min_val) / 2.0

    if max_val != min_val:
        d = max_val - min_val
        s = d / (2.0 - max_val - min_val) if l > 0.5 else d / (max_val + min_val)
        if max_val == r:
            h = (g - b) / d + (6 if g < b else 0)
        elif max_val == g:
            h = (b - r) / d + 2
        elif max_val == b:
            h = (r - g) / d + 4
        h /= 6.0

    return h * 360.0, l * 100.0, s * 100.0

def hls_to_rgb(h, l, s):
    h, l, s = h / 360.0, l / 100.0, s / 100.0
    if s == 0:
        return l * 255.0, l * 255.0, l * 255.0

    def hue2rgb(p, q, t):
        if t < 0: t += 1
        if t > 1: t -= 1
        if t < 1/6: return p + (q - p) * 6 * t
        if t < 1/2: return q
        if t < 2/3: return p + (q - p) * (2/3 - t) * 6
        return p

    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    r = hue2rgb(p, q, h + 1/3)
    g = hue2rgb(p, q, h)
    b = hue2rgb(p, q, h - 1/3)
    return r * 255.0, g * 255.0, b * 255.0

# ==========================================
# 2. CONTROLLER (Связующее звено)
# ==========================================

class ColorController:
    def __init__(self):
        self.rgb = (255, 0, 0)
        self.xyz = (0, 0, 0)
        self.hls = (0, 0, 0)
        self.warning = ""
        self.set_rgb(*self.rgb)

    def set_rgb(self, r, g, b):
        # ЗАЩИТА: Принудительно загоняем значения в диапазон 0-255
        r = clamp(int(r), 0, 255)
        g = clamp(int(g), 0, 255)
        b = clamp(int(b), 0, 255)
        
        self.rgb = (r, g, b)
        self.xyz = rgb_to_xyz(r, g, b)
        self.hls = rgb_to_hls(r, g, b)
        self.warning = ""

    def set_xyz(self, x, y, z):
        self.xyz = (int(x), int(y), int(z))
        r, g, b, clipped = xyz_to_rgb(x, y, z)
        if clipped:
            self.warning = "Внимание: цвет вышел за границы RGB. Значения обрезаны!"
        else:
            self.warning = ""
        self.rgb = (round(r), round(g), round(b))
        self.hls = rgb_to_hls(*self.rgb)

    def set_hls(self, h, l, s):
        # ЗАЩИТА: Ограничиваем H (0-360), L (0-100), S (0-100)
        h = clamp(int(h), 0, 360)
        l = clamp(int(l), 0, 100)
        s = clamp(int(s), 0, 100)
        
        self.hls = (h, l, s)
        r, g, b = hls_to_rgb(h, l, s)
        self.rgb = (round(clamp(r, 0, 255)), round(clamp(g, 0, 255)), round(clamp(b, 0, 255)))
        self.xyz = rgb_to_xyz(*self.rgb)
        self.warning = ""

# ==========================================
# 3. VIEW (Интерфейс Tkinter)
# ==========================================

class ColorApp(tk.Tk):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.title("Цветовые модели (Вариант 12)")
        self.geometry("550x450")
        self.resizable(False, False)
        
        self.vars = {}
        
        self._create_widgets()
        self._update_ui()

    def _create_widgets(self):
        self.canvas = tk.Canvas(self, width=530, height=50, bg="red", highlightthickness=1, highlightbackground="black")
        self.canvas.pack(pady=10, padx=10)

        tk.Button(self, text="Выбрать из палитры", command=self._pick_color, width=20).pack(pady=5)

        # Создаем блоки с кнопками "Применить"
        self._create_section("RGB", ["R", "G", "B"], self._on_rgb_change)
        self._create_section("XYZ", ["X", "Y", "Z"], self._on_xyz_change)
        self._create_section("HLS", ["H", "L", "S"], self._on_hls_change)

        self.warning_label = tk.Label(self, text="", fg="red", font=("Arial", 10, "bold"))
        self.warning_label.pack(pady=10)

    def _create_section(self, title, labels, callback):
        frame = tk.LabelFrame(self, text=title, padx=10, pady=5)
        frame.pack(fill="x", padx=10, pady=5)
        
        row = tk.Frame(frame)
        row.pack(fill="x", pady=2)
        
        for label in labels:
            tk.Label(row, text=label, width=3).pack(side="left")
            var = tk.StringVar()
            self.vars[f"{title}_{label}"] = var
            
            # Только цифры
            vcmd = (self.register(self._validate_int), '%P')
            entry = tk.Entry(row, textvariable=var, width=6, validate="key", validatecommand=vcmd, justify="center")
            entry.pack(side="left", padx=5)
            # Привязываем Enter к применению
            entry.bind("<Return>", lambda e, cb=callback: cb())

        # Кнопка "Применить", чтобы не пересчитывать цвет прямо во время ввода
        tk.Button(row, text="Применить", command=callback).pack(side="right", padx=10)

    def _validate_int(self, val):
        if val == "" or val == "-": return True
        try:
            int(val)
            return True
        except ValueError:
            return False

    def _update_ui(self):
        # Обновляем превью
        r, g, b = self.controller.rgb
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        self.canvas.config(bg=hex_color)

        # Обновляем текстовые поля
        states = {
            "RGB": self.controller.rgb,
            "XYZ": self.controller.xyz,
            "HLS": self.controller.hls
        }
        
        for model, values in states.items():
            labels = ["R", "G", "B"] if model == "RGB" else ["X", "Y", "Z"] if model == "XYZ" else ["H", "L", "S"]
            for label, val in zip(labels, values):
                int_val = int(round(val))
                key = f"{model}_{label}"
                
                # Обновляем поле только если там отличается значение (защита от затирания)
                if self.vars[key].get() != str(int_val):
                    self.vars[key].set(str(int_val))

        self.warning_label.config(text=self.controller.warning)

    def _get_values(self, title, labels):
        try:
            return [int(float(self.vars[f"{title}_{label}"].get())) for label in labels]
        except ValueError:
            return None

    def _on_rgb_change(self):
        vals = self._get_values("RGB", ["R", "G", "B"])
        if vals:
            self.controller.set_rgb(*vals)
            self._update_ui()

    def _on_xyz_change(self):
        vals = self._get_values("XYZ", ["X", "Y", "Z"])
        if vals:
            self.controller.set_xyz(*vals)
            self._update_ui()

    def _on_hls_change(self):
        vals = self._get_values("HLS", ["H", "L", "S"])
        if vals:
            self.controller.set_hls(*vals)
            self._update_ui()

    def _pick_color(self):
        color = colorchooser.askcolor(color=self.canvas.cget("bg"))
        if color[0]:
            r, g, b = map(int, color[0])
            self.controller.set_rgb(r, g, b)
            self._update_ui()

# ==========================================
# 4. ТЕСТЫ
# ==========================================

def run_tests():
    print("--- Запуск микро-тестов ---")
    def check(cond, msg):
        print(f"[{'PASSED' if cond else 'FAILED'}] {msg}")

    x, y, z = rgb_to_xyz(255, 0, 0)
    r, g, b, _ = xyz_to_rgb(x, y, z)
    check(round(r) == 255 and round(g) == 0 and round(b) == 0, "RGB(255,0,0) -> XYZ -> RGB")

    h, l, s = rgb_to_hls(0, 255, 0)
    r, g, b = hls_to_rgb(h, l, s)
    check(round(h) == 120 and round(l) == 50 and round(s) == 100, "RGB(0,255,0) -> HLS")
    check(round(r) == 0 and round(g) == 255 and round(b) == 0, "HLS -> RGB(0,255,0)")

    r, g, b, clipped = xyz_to_rgb(120, 50, 50)
    check(clipped == True and 0 <= round(r) <= 255, "Обнаружение выхода за границы RGB")

    print("---------------------------\n")

if __name__ == "__main__":
    run_tests()
    app = ColorApp(ColorController())
    app.mainloop()