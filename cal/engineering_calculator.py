## codyssey part5 - 2 [engineering_calculator] ##
## Mariner_정찬수 ##

import math
import sys
from decimal import Decimal, getcontext
from PyQt5.QtWidgets import (
    QApplication, QWidget, QGridLayout, QPushButton, QVBoxLayout, QLineEdit, QSizePolicy
)
from PyQt5.QtCore import Qt


class Calculator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Engineering Calculator")
        self.angle_mode = "Rad"  # or "Deg"
        self._angle_btn = None
        self._operand = None
        self._operator = None
        self._waiting_for_new = False # False: 이어서쓰기, True: 새로쓰기
        self.init_ui()
        self.reset_state()

    # ---------- state ----------
    def reset_state(self):
        self._operand = None
        self._operator = None
        self._waiting_for_new = True
        self.display.setText("0")

    # ---------- UI ----------
    def init_ui(self):
        root = QVBoxLayout(self)

        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setText("0")
        self.display.setStyleSheet("font-size:18px; padding:12px; background:#111; color:#fff; border:none;")
        root.addWidget(self.display)

        grid = QGridLayout()
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)

        rows = [
            ["(", ")", "mc", "m+", "m-", "mr", "AC", "+/-", "%", "÷"],
            ["2nd", "x²", "x³", "xʸ", "eˣ", "10ˣ", "7", "8", "9", "x"],
            ["1/x", "²√x", "³√x", "ʸ√x", "ln", "log₁₀", "4", "5", "6", "-"],
            ["x!", "sin", "cos", "tan", "e", "EE", "1", "2", "3", "+"],
            ["Deg", "sinh", "cosh", "tanh", "π", "Rand", "0", ".", "", "="],
        ]

        def _pass():
            return None

        for r, row in enumerate(rows):
            for c, label in enumerate(row):
                if label == "":
                    spacer = QPushButton("")
                    spacer.setEnabled(False)
                    spacer.setStyleSheet("background: transparent; border:none;")
                    grid.addWidget(spacer, r, c)
                    continue

                btn = QPushButton(label)
                btn.setMinimumSize(56, 48)
                btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

                operator_col = {"÷", "x", "-", "+", "="}
                top_utils = {"(", ")", "mc", "m+", "m-", "mr", "AC", "+/-", "%", "Deg"}
                digits = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "."}

                if label in operator_col:
                    btn.setStyleSheet("background:#ff9f0a; color:#fff; border:none; border-radius:16px; font-size:20px; padding:10px;")
                elif label in top_utils:
                    btn.setStyleSheet("background:#a6a6a6; color:#000; border:none; border-radius:16px; font-size:18px; padding:10px;")
                elif label in digits:
                    btn.setStyleSheet("background:#333; color:#fff; border:none; border-radius:16px; font-size:20px; padding:10px;")
                else:
                    btn.setStyleSheet("background:#242424; color:#fff; border:none; border-radius:16px; font-size:18px; padding:10px;")

                # connect button
                if label in {"+", "-", "x", "÷"}:
                    btn.clicked.connect(self._input_wrapper(label))
                elif label in digits:
                    btn.clicked.connect(self._input_wrapper(label))
                elif label == "=":
                    btn.clicked.connect(self.equal)
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
                elif label == "sinh":
                    btn.clicked.connect(self.func_sinh)
                elif label == "cosh":
                    btn.clicked.connect(self.func_cosh)
                elif label == "tanh":
                    btn.clicked.connect(self.func_tanh)
                elif label == "x²":
                    btn.clicked.connect(self.square)
                elif label == "x³":
                    btn.clicked.connect(self.cube)
                elif label == "π":
                    btn.clicked.connect(self.insert_pi)
                elif label == "e":
                    btn.clicked.connect(self.insert_e)
                elif label == "AC":
                    btn.clicked.connect(self.reset_state)
                elif label == "Deg":
                    btn.clicked.connect(self.toggle_angle_mode)
                    self._angle_btn = btn
                    self._update_angle_button_text()
                else:
                    btn.clicked.connect(_pass)

                grid.addWidget(btn, r, c)

        root.addLayout(grid)
        self.setStyleSheet("background:#000;")
        self.resize(820, 420)

    # ---------- input helpers ----------
    def _input_wrapper(self, text):
        def _wrapper():
            return self.on_input(text)
        return _wrapper

    def on_input(self, text: str):
        if text in {"+", "-", "x", "÷"}:
            self._on_operator(text)
            return

        cur = self.display.text()

        if self._waiting_for_new or cur == "0":
            if text == ".":
                self.display.setText("0.")
            elif text.isdigit():
                self.display.setText(text)
            else:
                return
            self._waiting_for_new = False
            return

        if text == "." and "." in cur: # 연속 dot 방지
            return
        if text.isdigit() or text == ".":
            self.display.setText(cur + text) # 이어 붙이기

    # ---------- unary operations ----------
    def _get_current_value(self) -> float:
        try:
            return float(self.display.text())
        except Exception:
            return 0.0

    def func_sin(self):
        x = self._get_current_value()
        val = math.sin(math.radians(x)) if self.angle_mode == "Deg" else math.sin(x)
        self.display.setText(self._format_result(val))
        self._waiting_for_new = True

    def func_cos(self):
        x = self._get_current_value()
        val = math.cos(math.radians(x)) if self.angle_mode == "Deg" else math.cos(x)
        self.display.setText(self._format_result(val))
        self._waiting_for_new = True

    def func_tan(self):
        x = self._get_current_value()
        val = math.tan(math.radians(x)) if self.angle_mode == "Deg" else math.tan(x)
        self.display.setText(self._format_result(val))
        self._waiting_for_new = True

    def func_sinh(self):
        # Hyperbolic functions do not use Deg/Rad; they take the raw value.
        x = self._get_current_value()
        try:
            val = math.sinh(x)
        except Exception:
            val = "Error"
        self.display.setText(self._format_result(val))
        self._waiting_for_new = True

    def func_cosh(self):
        x = self._get_current_value()
        try:
            val = math.cosh(x)
        except Exception:
            val = "Error"
        self.display.setText(self._format_result(val))
        self._waiting_for_new = True

    def func_tanh(self):
        x = self._get_current_value()
        try:
            val = math.tanh(x)
        except Exception:
            val = "Error"
        self.display.setText(self._format_result(val))
        self._waiting_for_new = True

    def square(self):
        x = self._get_current_value()
        self.display.setText(self._format_result(x * x))
        self._waiting_for_new = True

    def cube(self):
        x = self._get_current_value()
        self.display.setText(self._format_result(x * x * x))
        self._waiting_for_new = True

    def insert_pi(self):
        self._insert_number(math.pi)

    def insert_e(self):
        self._insert_number(math.e)

    def _insert_number(self, num: float):
        txt = self._format_result(num)
        if self._waiting_for_new or self.display.text() == "0":
            self.display.setText(txt)
        else:
            self.display.setText(txt)
        self._waiting_for_new = False

    # Angle mode toggle (button shows the other mode)
    def toggle_angle_mode(self):
        self.angle_mode = "Deg" if self.angle_mode == "Rad" else "Rad"
        self._update_angle_button_text()

    def _update_angle_button_text(self):
        if self._angle_btn is not None: 
            self._angle_btn.setText("Deg" if self.angle_mode == "Rad" else "Rad")

    # ---------- percent / sign ----------
    def percent(self):
        try:
            val = float(self.display.text())
            self.display.setText(self._format_result(val / 100.0))
            self._waiting_for_new = True
        except Exception:
            pass

    def negative_positive(self):
        s = self.display.text()
        if s == "0":
            return
        if s.startswith("-"):
            s = s[1:]
        else:
            s = "-" + s
        self.display.setText(s)

    # ---------- binary operations (sequential) ----------
    def _on_operator(self, op_symbol: str):

        cur_val = self._get_current_value()

        if self._operator is not None and not self._waiting_for_new:
            # chain previous pending op
            res = self._calculate(self._operand, cur_val, self._operator)
            self.display.setText(self._format_result(res))
            self._operand = float(res) if not isinstance(res, str) else 0.0
        else:
            self._operand = cur_val

        self._operator = op_symbol
        self._waiting_for_new = True

    def equal(self):
        if self._operator is None or self._operand is None:
            return
        right = self._get_current_value()
        result = self._calculate(self._operand, right, self._operator)
        self.display.setText(self._format_result(result))
        self._operand = None
        self._operator = None
        self._waiting_for_new = True

    # ---------- arithmetic (Decimal) ----------
    def _calculate(self, left, right, op):
        try:
            getcontext().prec = 15
            if op == "+":
                return self.add(left, right)
            elif op == "-":
                return self.subtract(left, right)
            elif op == "x":
                return self.multiply(left, right)
            elif op == "÷":
                if right == 0:
                    return "Error"
                return self.divide(left, right)
        except Exception:
            return "Error"

    def add(self, left, right) -> Decimal:
        return Decimal(left) + Decimal(right)

    def subtract(self, left, right) -> Decimal:
        return Decimal(left) - Decimal(right)

    def multiply(self, left, right) -> Decimal:
        return Decimal(left) * Decimal(right)

    def divide(self, left, right) -> Decimal:
        return Decimal(left) / Decimal(right)

    # ---------- formatting ----------
    def _format_result(self, value):
        if isinstance(value, str):
            return value
        try:
            fval = float(value)
        except Exception:
            return str(value)

        if abs(fval) >= 1e14:
            return f"{fval:.14e}"
        elif abs(fval) < 1e-15:
            return str(0)
        else:
            return f"{fval:.14g}"


def main():
    app = QApplication(sys.argv)
    w = Calculator()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
