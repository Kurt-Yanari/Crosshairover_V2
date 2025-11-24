import sys, os, json, ctypes, threading
from PyQt5 import QtCore, QtGui, QtWidgets

SETTINGS_FILE = "crosshair_settings.json"

# Win32 constants
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000


def set_window_exstyle(hwnd, add_flags=0, remove_flags=0):
    try:
        user32 = ctypes.windll.user32
        GetWindowLong = user32.GetWindowLongW
        SetWindowLong = user32.SetWindowLongW
        style = GetWindowLong(hwnd, GWL_EXSTYLE)
        style |= add_flags
        style &= ~remove_flags
        SetWindowLong(hwnd, GWL_EXSTYLE, style)
    except Exception:
        pass


class CrosshairOverlay(QtWidgets.QWidget):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings

        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground, True)

        screen = QtWidgets.QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.showFullScreen()

        QtCore.QTimer.singleShot(200, self.apply_click_through)

    # Метод click-through исправлен
    def apply_click_through(self):
        try:
            hwnd = int(self.winId())
        except Exception:
            hwnd = None
        if hwnd:
            if self.settings.get("click_through", False):
                set_window_exstyle(
                    hwnd,
                    add_flags=WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
                )
                self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
            else:
                set_window_exstyle(
                    hwnd,
                    add_flags=WS_EX_LAYERED,
                    remove_flags=WS_EX_TRANSPARENT | WS_EX_NOACTIVATE
                )
                self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)

    # Автоцентрирование при изменении окна
    def resizeEvent(self, event):
        self.update()
        super().resizeEvent(event)

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2

        r, g, b = self.settings.get("color", [255, 255, 255])
        alpha = self.settings.get("alpha", 1)
        color = QtGui.QColor(r, g, b)
        color.setAlphaF(alpha)

        pen = QtGui.QPen(color)
        pen.setWidth(self.settings.get("thickness", 1))
        pen.setCapStyle(QtCore.Qt.FlatCap)
        p.setPen(pen)

        mode = self.settings.get("mode", "cross")
        if mode == "cross":
            L = self.settings.get("length", 1)
            gap = self.settings.get("gap", 0)
            p.drawLine(cx, cy - gap, cx, cy - gap - L)
            p.drawLine(cx, cy + gap, cx, cy + gap + L)
            p.drawLine(cx - gap, cy, cx - gap - L, cy)
            p.drawLine(cx + gap, cy, cx + gap + L, cy)
            if self.settings.get("show_center_dot", False):
                dot = self.settings.get("dot_size", 6)
                p.setBrush(color)
                p.drawEllipse(QtCore.QRectF(cx - dot/2, cy - dot/2, dot, dot))
        else:
            dot = self.settings.get("dot_size", 6)
            p.setBrush(color)
            p.drawEllipse(QtCore.QRectF(cx - dot/2, cy - dot/2, dot, dot))
        p.end()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            QtWidgets.QApplication.quit()
        event.accept()


class ControlPanel(QtWidgets.QWidget):
    def __init__(self, settings, overlay):
        super().__init__()
        self.settings = settings
        self.overlay = overlay

        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        self.setWindowTitle("Crosshair Controls")
        self.setStyleSheet("""
            QWidget { background: rgba(20,20,20,200); color: white; border-radius: 8px; font-size: 12px; }
            QPushButton { background-color: #444; border-radius: 5px; padding: 4px; }
            QPushButton:hover { background-color: #666; }
        """)
        self.init_ui()
        self.setGeometry(60, 60, 260, 360)

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8,8,8,8)

        layout.addWidget(QtWidgets.QLabel("Mode:"))
        self.mode = QtWidgets.QComboBox()
        self.mode.addItems(["cross", "dot"])
        self.mode.setCurrentText(self.settings.get("mode","cross"))
        layout.addWidget(self.mode)

        self.color_btn = QtWidgets.QPushButton("Choose color")
        self.color_btn.clicked.connect(self.choose_color)
        layout.addWidget(self.color_btn)

        def add_slider(label, key, mn, mx):
            layout.addWidget(QtWidgets.QLabel(label))
            s = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            s.setRange(mn, mx)
            val = self.settings.get(key)
            if key == "alpha":
                s.setValue(int(val*100))
            else:
                s.setValue(val)
            layout.addWidget(s)
            return s

        self.alpha = add_slider("Opacity", "alpha", 10, 100)
        self.thickness = add_slider("Thickness", "thickness", 1, 20)
        self.length = add_slider("Length", "length", 1, 300)
        self.gap = add_slider("Gap", "gap", 0, 100)
        self.dot_size = add_slider("Dot size", "dot_size", 1, 50)

        self.center_dot = QtWidgets.QCheckBox("Show center dot")
        self.center_dot.setChecked(self.settings.get("show_center_dot", False))
        layout.addWidget(self.center_dot)

        self.click_btn = QtWidgets.QPushButton("Toggle click-through (F9)")
        self.click_btn.clicked.connect(self.toggle_click)
        layout.addWidget(self.click_btn)

        self.hide_btn = QtWidgets.QPushButton("Hide panel (F8)")
        self.hide_btn.clicked.connect(self.hide)
        layout.addWidget(self.hide_btn)

        self.save_btn = QtWidgets.QPushButton("Save settings")
        self.save_btn.clicked.connect(self.save)
        layout.addWidget(self.save_btn)

        self.mode.currentTextChanged.connect(self.apply_changes)
        self.alpha.valueChanged.connect(self.apply_changes)
        self.thickness.valueChanged.connect(self.apply_changes)
        self.length.valueChanged.connect(self.apply_changes)
        self.gap.valueChanged.connect(self.apply_changes)
        self.dot_size.valueChanged.connect(self.apply_changes)
        self.center_dot.stateChanged.connect(self.apply_changes)

    def choose_color(self):
        initial = QtGui.QColor(*self.settings.get("color",[255,255,255]))
        c = QtWidgets.QColorDialog.getColor(initial, self, "Choose crosshair color")
        if c.isValid():
            self.settings["color"] = [c.red(), c.green(), c.blue()]
            self.overlay.update()

    def toggle_click(self):
        self.settings["click_through"] = not self.settings.get("click_through", False)
        self.overlay.apply_click_through()

    def apply_changes(self, *args):
        self.settings["mode"] = self.mode.currentText()
        self.settings["alpha"] = self.alpha.value() / 100.0
        self.settings["thickness"] = self.thickness.value()
        self.settings["length"] = self.length.value()
        self.settings["gap"] = self.gap.value()
        self.settings["dot_size"] = self.dot_size.value()
        self.settings["show_center_dot"] = bool(self.center_dot.isChecked())
        self.overlay.update()

    def save(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            QtWidgets.QMessageBox.information(self, "Saved", "Settings saved to " + SETTINGS_FILE)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to save: {e}")


def load_settings():
    default = {
        "mode": "cross",
        "color": [255, 255, 255],
        "alpha": 1,
        "thickness": 1,
        "length": 1,
        "gap": 0,
        "dot_size": 6,
        "show_center_dot": False,
        "click_through": False
    }
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            s = json.load(f)
        default.update(s)
    except Exception:
        pass
    return default


def start_hotkeys(panel, overlay, settings):
    try:
        import keyboard
    except Exception:
        print("Модуль 'keyboard' не установлен. pip install keyboard")
        return

    keyboard.add_hotkey('f8', lambda: panel.setVisible(not panel.isVisible()))
    keyboard.add_hotkey('f9', lambda: [settings.update({"click_through": not settings.get("click_through", False)}),
                                        overlay.apply_click_through()])
    keyboard.add_hotkey('esc', lambda: QtWidgets.QApplication.quit())
    keyboard.wait()


def main():
    app = QtWidgets.QApplication(sys.argv)
    settings = load_settings()

    overlay = CrosshairOverlay(settings)
    panel = ControlPanel(settings, overlay)
    panel.show()
    overlay.show()

    hk_thread = threading.Thread(target=start_hotkeys, args=(panel, overlay, settings), daemon=True)
    hk_thread.start()

    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: overlay.apply_click_through())
    timer.start(1000)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
