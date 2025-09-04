#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyQt6로 구현한 iPhone(세로모드) 계산기와 '유사한' UI 데모.
- 버튼 배치/출력 형태를 iPhone과 동일하게 구성 (색/모양은 동일할 필요 없음)
- 각 버튼 클릭 시 디스플레이에 입력만 표시(계산 기능은 구현하지 않음)
  - "AC": 표시 초기화
  - "+/-": 현재 입력 중인 숫자의 부호 토글 (간단 처리)
  - 나머지 연산자/숫자/점: 그대로 표시(이어붙임)
"""

import sys
import re
from PyQt6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QPushButton, QVBoxLayout, QLineEdit, QSizePolicy
)
from PyQt6.QtCore import Qt


OPERATORS = {'÷', '×', '−', '+', '%'}


class IPhoneLikeCalculator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculator (iPhone-like, PyQt6)")
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)

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
            ["7", "8", "9", "×"],
            ["4", "5", "6", "−"],
            ["1", "2", "3", "+"],
            # 마지막 줄: 0이 두 칸 차지
            ["0", ".", "="],
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
                elif label in {"÷", "×", "−", "+", "="}:
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
                    btn.clicked.connect(self.on_clear)
                elif label == "+/-":
                    btn.clicked.connect(self.on_toggle_sign)
                else:
                    btn.clicked.connect(lambda _, t=label: self.on_input(t))

                # 0 버튼은 두 칸(가로) 차지
                if r == 4 and label == "0":
                    grid.addWidget(btn, r, 0, 1, 2)  # row, col, rowSpan, colSpan
                else:
                    # 마지막 줄은 인덱스 보정(0이 2칸이므로 .은 col=2, =은 col=3에 해당)
                    col = c if not (r == 4 and c > 0) else c + 1
                    grid.addWidget(btn, r, col)

        root.addLayout(grid)

        # 전체 배경
        self.setStyleSheet("QWidget { background:#000; }")

        # 기본 창 크기
        self.resize(380, 600)

    # ---------- 이벤트 핸들러 ----------
    def on_clear(self):
        self.display.setText("0")

    def on_input(self, text: str):
        """
        숫자/연산자/점을 디스플레이에 '표시'만 한다.
        = 버튼도 이번 과제에서는 단순히 기호를 표시만 한다.
        """
        cur = self.display.text()

        # 처음이 '0'이고 숫자 또는 '.'이 들어오면 대체
        if cur == "0":
            if text.isdigit() or text == ".":
                self.display.setText(text)
                return
            # 그 외(연산자 포함)는 이어붙임
            self.display.setText(cur + text)
            return

        # 연속된 '.' 방지(현재 마지막 토큰이 소수점 포함이면 무시)
        if text == ".":
            if self._current_number_has_dot(cur):
                return

        self.display.setText(cur + text)

    def on_toggle_sign(self):
        """
        마지막 '피연산자'의 부호를 간단히 토글한다.
        실제 계산 로직 없이, 표시 문자열만 수정.
        """
        s = self.display.text()
        if s == "0":
            return

        # 마지막 숫자 토큰(부호/소수점 포함)을 찾는다.
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
            if not s:
                s = "0"
            self.display.setText(s)

    # ---------- 헬퍼 ----------
    def _current_number_has_dot(self, text: str) -> bool:
        """마지막 숫자 토큰이 이미 소수점을 포함하는지 확인"""
        tokens = re.split(r"[÷×−+\%]", text)
        if not tokens:
            return False
        last = tokens[-1]
        return "." in last


def main():
    app = QApplication(sys.argv)
    w = IPhoneLikeCalculator()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()