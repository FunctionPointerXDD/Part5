## codyssey part5 - 2 [calculator] ##
## Mariner_정찬수 ##

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QGridLayout, QPushButton, QVBoxLayout, QLineEdit, QSizePolicy
)
from PyQt5.QtCore import Qt


class Calculator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculator")
        self.init_ui()
        self.reset_state()

    def reset_state(self):
        self._operand = None
        self._operator = None
        self._waiting_for_new = False
        self.process_display.setText("")

    def init_ui(self):
        root = QVBoxLayout(self)

        # 연산 과정 표시용 (상단, 회색, 작은 글씨)
        self.process_display = QLineEdit()
        self.process_display.setReadOnly(True)
        self.process_display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.process_display.setText("")
        self.process_display.setStyleSheet(
            "font-size: 18px; padding: 4px 16px 0px 16px; border: none; background:#000; color:#aaa;"
        )
        root.addWidget(self.process_display)

        # 디스플레이
        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setText("0")
        self.display.setStyleSheet(
            "font-size: 36px; padding: 16px; border: none; background:#111; color:#fff;"
        )
        root.addWidget(self.display)

        # 버튼 그리드 (iPhone 세로모드와 동일한 배치)
        grid = QGridLayout()
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)

        # 버튼 구성
        rows = [
            ["AC", "+/-", "%", "÷"],
            ["7", "8", "9", "x"],
            ["4", "5", "6", "-"],
            ["1", "2", "3", "+"],
            ["T", "0", ".", "="],
        ]

        # 버튼 생성
        for r, row in enumerate(rows):
            for c, label in enumerate(row):
                btn = QPushButton(label)
                btn.setMinimumSize(80, 60)
                btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

                # 스타일링
                if label in {"AC", "+/-", "%"}:
                    btn.setStyleSheet(
                        "background:#a6a6a6; color:#000; border:none; border-radius:16px; font-size:22px; padding:10px;"
                    )
                elif label in {"÷", "x", "-", "+", "="}:
                    btn.setStyleSheet(
                        "background:#ff9f0a; color:#fff; border:none; border-radius:16px; font-size:26px; padding:10px;"
                    )
                else:
                    btn.setStyleSheet(
                        "background:#333; color:#fff; border:none; border-radius:16px; font-size:24px; padding:10px;"
                    )
                    
                # 이벤트 연결
                if label == "AC":
                    btn.clicked.connect(self.reset)
                elif label == "+/-":
                    btn.clicked.connect(self.negative_positive)
                elif label == 'T':
                    pass
                else:
                    btn.clicked.connect(self._input_wrapper(label))

                grid.addWidget(btn, r, c)

        root.addLayout(grid) # 위에서 구현한 모든 그리드 추가

        # 전체 배경
        self.setStyleSheet("background: #000")

        # 기본 창 크기
        self.resize(380, 600)
    
    # on_input 메서드 래핑 -> 함수 객체 반환
    def _input_wrapper(self, text):
        def _wrapper():
            return self.on_input(text)
        return _wrapper  

    # ---------- 이벤트 핸들러 ----------
    def reset(self):
        self.display.setText("0")
        self.reset_state()

    def on_input(self, text: str):
        if text in {"+", "-", "x", "÷"}:
            self._on_operator(text)
            return
        elif text == "=":
            self.equal()
            return
        elif text == "%":
            self.percent()
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
            self.display.setText(cur + text)

    def _on_operator(self, op):
        cur = self.display.text()
        try:
            value = float(cur)
        except Exception:
            value = 0.0
        if self._operator and not self._waiting_for_new:
            # 연산자 연속 입력이 아니면 이전 연산 처리
            self.equal()
            value = float(self.display.text())
        self._operand = value
        self._operator = op
        self._waiting_for_new = True
        self.process_display.setText(f"{self._format_result(self._operand)} {op}")

    def equal(self):
        if self._operator is None or self._operand is None:
            return
        try:
            right = float(self.display.text())
        except Exception:
            right = 0.0
        result = self._calculate(self._operand, right, self._operator)
        self.process_display.setText(f"{self._format_result(self._operand)} {self._operator} {self._format_result(right)} =")
        self.display.setText(self._format_result(result))
        self._operand = None
        self._operator = None
        self._waiting_for_new = True

    def percent(self):
        cur = self.display.text()
        try:
            value = float(cur)
            value = value / 100.0
            self.display.setText(self._format_result(value))
        except Exception:
            pass

    def _calculate(self, left, right, op):
        try:
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
    
    def add(self, left, right):
        return (left) + (right)

    def subtract(self, left, right):
        return (left) - (right)
    
    def multiply(self, left, right):
        return (left) * (right)
    
    def divide(self, left, right):
        return (left) / (right)   

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

    def negative_positive(self):
        s = self.display.text()
        if s == "0":
            return
        if s.startswith("-"):
            s = s[1:]
        else:
            s = "-" + s
        self.display.setText(s)


def main():
    app = QApplication(sys.argv)
    w = Calculator()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
