import math
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QGridLayout, QPushButton, QVBoxLayout, QLineEdit, QSizePolicy
)
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtCore import Qt


class Calculator(QWidget):
    """
    Scientific calculator UI mirroring the iPad scientific layout.
    Required working features: sin/cos/tan, π, x², x³, digits, basic ops, parentheses,
    backspace, percent, +/- , evaluate. Other buttons exist but are inert.

    Method/variable naming is aligned with part5/cal/calculator.py where reasonable:
    - init_ui, reset_state, on_input, equal, percent, negative_positive, _input_wrapper
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scientific Calculator (PyQt5)")
        self.angle_mode = "Rad"  # or "Deg"
        self.init_ui()
        self.reset_state()

    # ---------- state ----------
    def reset_state(self):
        self._waiting_for_new = False
        self.display.setText("")

    # ---------- UI ----------
    def init_ui(self):
        root = QVBoxLayout(self)

        # Expression display
        self.display = QLineEdit()
        self.display.setReadOnly(False)
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setPlaceholderText("0")
        self.display.setFont(QFont("Menlo" if sys.platform != "win32" else "Consolas", 18))
        self.display.setStyleSheet("padding:12px; background:#111; color:#fff; border:none;")
        root.addWidget(self.display)

        grid = QGridLayout()
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)

        # Layout approximating the screenshot (10 cols + 1 operator col)
        rows = [
            ["(", ")", "mc", "m+", "m-", "mr", "⌫", "+/-", "%", "", "+"],
            ["2nd", "x²", "x³", "xʸ", "eˣ", "10ˣ", "7", "8", "9", "", "×"],
            ["1/x", "²√x", "³√x", "ʸ√x", "ln", "log₁₀", "4", "5", "6", "", "−"],
            ["x!", "sin", "cos", "tan", "e", "EE", "1", "2", "3", "", "÷"],
            ["🧮", "sinh", "cosh", "tanh", "π", "Rad", "Rand", "0", ".", "", "="]
        ]

        # Handlers
        def _inert():
            return None

        for r, row in enumerate(rows):
            for c, label in enumerate(row):
                if label == "":
                    # placeholder spacer invisible but keeps grid positions consistent
                    spacer = QPushButton("")
                    spacer.setEnabled(False)
                    spacer.setStyleSheet("background: transparent; border:none;")
                    grid.addWidget(spacer, r, c)
                    continue

                btn = QPushButton(label)
                btn.setMinimumSize(56, 48)
                btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

                # Styling buckets
                operator_col = {"+", "×", "−", "÷", "="}
                top_utils = {"(", ")", "mc", "m+", "m-", "mr", "⌫", "+/-", "%"}
                digits = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "."}

                if label in operator_col:
                    btn.setStyleSheet("background:#ff9f0a; color:#fff; border:none; border-radius:16px; font-size:20px; padding:10px;")
                elif label in top_utils:
                    btn.setStyleSheet("background:#a6a6a6; color:#000; border:none; border-radius:16px; font-size:18px; padding:10px;")
                elif label in digits:
                    btn.setStyleSheet("background:#333; color:#fff; border:none; border-radius:16px; font-size:20px; padding:10px;")
                else:
                    btn.setStyleSheet("background:#242424; color:#fff; border:none; border-radius:16px; font-size:18px; padding:10px;")

                # Connections
                if label in {"+", "−", "×", "÷", "(", ")", "."} or label.isdigit():
                    btn.clicked.connect(self._input_wrapper(label))
                elif label == "=":
                    btn.clicked.connect(self.equal)
                elif label == "⌫":
                    btn.clicked.connect(self.backspace)
                elif label == "%":
                    btn.clicked.connect(self.percent)
                elif label == "+/-":
                    btn.clicked.connect(self.negative_positive)
                elif label == "sin":
                    btn.clicked.connect(self.func_sin)
                elif label == "cos":
                    btn.clicked.connect(self.func_cos)
                elif label == "tan":
                    btn.clicked.connect(self.func_tan)
                elif label == "x²":
                    btn.clicked.connect(self.square)
                elif label == "x³":
                    btn.clicked.connect(self.cube)
                elif label == "π":
                    btn.clicked.connect(self.insert_pi)
                elif label == "Rad":
                    btn.setCheckable(True)
                    btn.clicked.connect(self.toggle_angle_mode)
                    self._rad_btn = btn
                elif label in {"e"}:  # optional: insert constant symbol (supported in eval)
                    btn.clicked.connect(self._input_wrapper("e"))
                else:
                    # inert
                    btn.clicked.connect(_inert)

                grid.addWidget(btn, r, c)

        root.addLayout(grid)
        self.setStyleSheet("background:#000;")
        self.resize(820, 420)

        # keyboard shortcuts similar to original helper
        self._shortcuts = []
        for key in [str(i) for i in range(10)] + ["+", "-", "*", "/", ".", "(", ")"]:
            sc = QShortcut(QKeySequence(key), self)
            sc.activated.connect(lambda k=key: self.on_input(k))
            self._shortcuts.append(sc)
        sc_bs = QShortcut(QKeySequence("Backspace"), self)
        sc_bs.activated.connect(self.backspace)
        self._shortcuts.append(sc_bs)
        for enter_key in ("Enter", "Return"):
            sc_enter = QShortcut(QKeySequence(enter_key), self)
            sc_enter.activated.connect(self.equal)
            self._shortcuts.append(sc_enter)

    # ---------- input helpers ----------
    def _input_wrapper(self, text):
        def _w():
            return self.on_input(text)
        return _w

    def on_input(self, text: str):
        mapping = {"×": "*", "÷": "/", "−": "-"}
        token = mapping.get(text, text)
        cur = self.display.text()
        # Replace placeholder 0 only when display looks empty
        if cur == "":
            self.display.setText(token)
            return
        # Append at cursor
        pos = self.display.cursorPosition()
        new = cur[:pos] + token + cur[pos:]
        self.display.setText(new)
        self.display.setCursorPosition(pos + len(token))

    def backspace(self):
        pos = self.display.cursorPosition()
        if pos <= 0:
            return
        t = self.display.text()
        self.display.setText(t[:pos-1] + t[pos:])
        self.display.setCursorPosition(pos-1)

    def percent(self):
        expr = self.display.text().strip()
        if not expr:
            return
        try:
            val = float(self.safe_eval(expr))
            self.display.setText(self._format_result(val / 100.0))
        except Exception:
            pass

    def negative_positive(self):
        txt = self.display.text().strip()
        if not txt:
            return
        if txt.startswith("-"):
            self.display.setText(txt[1:])
        else:
            self.display.setText("-" + txt)

    # ---------- functions ----------
    def _wrap_selection_or_all(self):
        text = self.display.text()
        sel = self.display.selectedText()
        if sel:
            start = self.display.selectionStart()
            end = start + len(sel)
            return text, start, end, sel
        return text, 0, len(text), text

    def _apply_unary(self, name: str):
        text, start, end, seg = self._wrap_selection_or_all()
        if not seg:
            return
        wrapped = f"{name}({seg})"
        self.display.setText(text[:start] + wrapped + text[end:])
        self.display.setCursorPosition(start + len(wrapped))

    def func_sin(self):
        self._apply_unary("sin")

    def func_cos(self):
        self._apply_unary("cos")

    def func_tan(self):
        self._apply_unary("tan")

    def square(self):
        text, start, end, seg = self._wrap_selection_or_all()
        if not seg:
            return
        wrapped = f"({seg})**2"
        self.display.setText(text[:start] + wrapped + text[end:])
        self.display.setCursorPosition(start + len(wrapped))

    def cube(self):
        text, start, end, seg = self._wrap_selection_or_all()
        if not seg:
            return
        wrapped = f"({seg})**3"
        self.display.setText(text[:start] + wrapped + text[end:])
        self.display.setCursorPosition(start + len(wrapped))

    def insert_pi(self):
        self.on_input(str(math.pi))

    def toggle_angle_mode(self):
        # simple toggle; update button label
        self.angle_mode = "Deg" if self.angle_mode == "Rad" else "Rad"
        self._rad_btn.setText(self.angle_mode)

    # ---------- evaluation ----------
    def equal(self):
        expr = self.display.text().strip()
        if not expr:
            return
        try:
            result = self.safe_eval(expr)
            self.display.setText(self._format_result(result))
            self.display.setCursorPosition(len(self.display.text()))
        except Exception:
            # keep it simple: show 'Error'
            self.display.setText("Error")

    def _format_result(self, value):
        try:
            fval = float(value)
        except Exception:
            return str(value)
        if abs(fval) < 1e-15:
            fval = 0.0
        # int-like formatting
        if int(fval) == fval:
            return str(int(fval))
        return ("%.*g" % (12, fval))

    def safe_eval(self, expr: str):
        # angle-aware trig
        def _sin(x):
            return math.sin(math.radians(x)) if self.angle_mode == "Deg" else math.sin(x)

        def _cos(x):
            return math.cos(math.radians(x)) if self.angle_mode == "Deg" else math.cos(x)

        def _tan(x):
            return math.tan(math.radians(x)) if self.angle_mode == "Deg" else math.tan(x)

        safe = {
            "__builtins__": {},
            "pi": math.pi,
            "e": math.e,
            "sin": _sin,
            "cos": _cos,
            "tan": _tan,
            "abs": abs,
            "round": round,
        }

        expr = expr.replace("×", "*").replace("÷", "/").replace("−", "-")
        return eval(expr, safe, {})


def main():
    app = QApplication(sys.argv)
    w = Calculator()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
