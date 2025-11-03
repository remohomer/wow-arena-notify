# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog
from PySide6.QtCore import Qt
from infrastructure.config import load_config, save_config

class StepGameFolder(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg = load_config()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 24, 32, 24)
        lay.setSpacing(14)

        self.title = QLabel("Select your World of Warcraft folder")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-size:16px; font-weight:800;")
        self.info = QLabel(self._fmt_path())
        self.info.setAlignment(Qt.AlignCenter)
        self.info.setWordWrap(True)
        self.info.setStyleSheet("color:#c9bda7;")

        self.btn = QPushButton("Browse…")
        self.btn.setFixedHeight(36)
        self.btn.clicked.connect(self.choose_folder)

        lay.addStretch()
        lay.addWidget(self.title)
        lay.addWidget(self.info)
        lay.addWidget(self.btn, alignment=Qt.AlignCenter)
        lay.addStretch()

    def _fmt_path(self):
        p = self.cfg.get("game_folder", "")
        return f"Current: <b>{p or '[not selected]'}</b>"

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select your World of Warcraft folder")
        if not folder:
            return
        self.cfg["game_folder"] = folder
        save_config(self.cfg)
        self.info.setText(self._fmt_path())

    def can_continue(self):
        ok = bool(self.cfg.get("game_folder"))
        if not ok:
            # soft block: możesz pozwolić przejść bez folderu – ale trzymamy twardy wymóg
            self.info.setText(self._fmt_path() + "<br><span style='color:#ff7777'>Please select your WoW folder.</span>")
        return ok, "Select WoW folder"
