#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
from PyQt5.QtWidgets import (
    QApplication, QWidget, QGridLayout, QPushButton, QVBoxLayout, QLineEdit, QSizePolicy
)
from PyQt5.QtCore import Qt
from functools import partial
from decimal import Decimal, getcontext


OPERATORS = {'÷', 'x', '-', '+', '%'}


class IPhoneLikeCalculator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculator (iPhone-like, PyQt5)")
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
            "QLineEdit {"
            "  font-size: 18px; padding: 4px 16px 0px 16px; border: none; "
            "  background:#000; color:#aaa;"
            "}"
        )
        root.addWidget(self.process_display)

        # 디스플레이 (우측 정렬, 읽기 전용)
        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setText("0")
        self.display.setStyleSheet(
            "QLineEdit {"
            "  font-size: 36px; padding: 16px; border: none; "
            "  background:#111; color:#fff;"
            "}"
        )
        root.addWidget(self.display)

        # 버튼 그리드 (iPhone 세로모드와 동일한 배치)
        grid = QGridLayout()
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)

        # 행 구성
        rows = [
            ["AC", "+/-", "%", "÷"],
            ["7", "8", "9", "x"],
            ["4", "5", "6", "-"],
            ["1", "2", "3", "+"],
            # 마지막 줄: 0이 두 칸 차지
            ["T", "0", ".", "="],
        ]

        # 버튼 생성
        for r, row in enumerate(rows):
            for c, label in enumerate(row):
                btn = QPushButton(label)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setMinimumSize(72, 64)
                btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

                # 간단한 스타일링: 상단 유틸/숫자/연산자 구분
                if label in {"AC", "+/-", "%"}:
                    btn.setStyleSheet(
                        "QPushButton {background:#a6a6a6; color:#000; border:none; border-radius:16px; font-size:22px; padding:10px;}"
                        "QPushButton:pressed {background:#8e8e8e;}"
                    )
                elif label in {"÷", "x", "-", "+", "="}:
                    btn.setStyleSheet(
                        "QPushButton {background:#ff9f0a; color:#fff; border:none; border-radius:16px; font-size:26px; padding:10px;}"
                        "QPushButton:pressed {background:#d18208;}"
                    )
                else:
                    btn.setStyleSheet(
                        "QPushButton {background:#333; color:#fff; border:none; border-radius:16px; font-size:24px; padding:10px;}"
                        "QPushButton:pressed {background:#262626;}"
                    )

                # 이벤트 연결
                if label == "AC":
                    btn.clicked.connect(self.reset)
                elif label == "+/-":
                    btn.clicked.connect(self.negative_positive)
                else:
                    btn.clicked.connect(partial(self.on_input, label))

                grid.addWidget(btn, r, c)

        root.addLayout(grid)

        # 전체 배경
        self.setStyleSheet("QWidget { background:#000; }")

        # 기본 창 크기
        self.resize(380, 600)

    # ---------- 이벤트 핸들러 ----------
    def reset(self):
        self.display.setText("0")
        self.reset_state()

    def on_input(self, text: str):
        if text in {"+", "-", "x", "÷"}:
            self._on_operator(text)
            return
        elif text == "=":
            self._on_equal()
            return
        elif text == "%":
            self.percent()
            return

        cur = self.display.text()
        # 새 입력 시작(연산자 직후)
        if self._waiting_for_new:
            if text == ".":
                self.display.setText("0.")
            else:
                self.display.setText(text)
            self._waiting_for_new = False
            return

        # 처음이 '0'이고 숫자 또는 '.'이 들어오면 대체
        if cur == "0":
            if text.isdigit():
                self.display.setText(text)
                return
            if text == ".":
                self.display.setText("0.")
                return

            self.display.setText(cur + text)
            return

        # 연속된 '.' 방지(현재 마지막 토큰이 소수점 포함이면 무시)
        if text == ".":
            if self._current_number_has_dot(cur):
                return

        self.display.setText(cur + text)

    def _on_operator(self, op):
        cur = self.display.text()
        try:
            value = float(cur)
        except Exception:
            value = 0.0
        if self._operator and not self._waiting_for_new:
            # 연산자 연속 입력이 아니면 이전 연산 처리
            self._on_equal()
            value = float(self.display.text())
        self._operand = value
        self._operator = op
        self._waiting_for_new = True
        self.process_display.setText(f"{self._format_result(self._operand)} {op}")

    def _on_equal(self):
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
            getcontext().prec = 15 # 정밀도는 소수점 자리까지 설정
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

    def _format_result(self, value):
        if isinstance(value, str):
            return value
        try:
            fval = float(value)
            if int(fval) == fval:
                return str(int(fval))
            else:
                return f"{fval:.10g}"
        except Exception:
            return str(value)

        

    def negative_positive(self):
        s = self.display.text()
        if s == "0":
            return

        # 마지막 숫자 토큰(부호/소수점 포함)을 찾는다.
        # 연산자(÷ × − + %)를 기준으로 split하되, 마지막 토큰을 대상으로 한다.
        tokens = re.split(r"[÷×−+\%]", s)
        if not tokens:
            return
        last = tokens[-1]
        if not last:
            return

        # 토큰 시작에 '-'가 있으면 제거, 없으면 추가
        if last.startswith("-"):
            new_last = last[1:]
        else:
            new_last = "-" + last

        # s의 뒤에서 last를 찾아 치환(오른쪽만 1회 대체)
        idx = s.rfind(last)
        if idx != -1:
            s = s[:idx] + new_last + s[idx + len(last):]
            # 맨 앞이 비어버렸다면 안전 처리
            if not s:
                s = "0"
            self.display.setText(s)

    def _current_number_has_dot(self, text: str) -> bool:
        # 마지막 숫자 토큰이 이미 소수점을 포함하는지 확인
        tokens = re.split(r"[÷×−+\%]", text)
        if not tokens:
            return False
        last = tokens[-1]
        return "." in last


def main():
    app = QApplication(sys.argv)
    w = IPhoneLikeCalculator()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
