from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from mj_prompt_studio.domain.matrix import MatrixPlan, MatrixVariant


class MatrixLabWidget(QWidget):
    plan_requested = Signal(str)
    generate_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.current_plan: MatrixPlan | None = None
        self.variants: list[MatrixVariant] = []
        self.objective_edit = QPlainTextEdit()
        self.objective_edit.setPlaceholderText("実験目的を入力")
        self.plan_button = QPushButton("AIで実験計画")
        self.generate_button = QPushButton("Variant生成")
        self.csv_button = QPushButton("CSV出力")
        self.markdown_button = QPushButton("Markdown出力")
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["#", "Prompt", "Parameters", "Notes"])
        top = QHBoxLayout()
        top.addWidget(self.objective_edit, 1)
        top.addWidget(self.plan_button)
        top.addWidget(self.generate_button)
        top.addWidget(self.csv_button)
        top.addWidget(self.markdown_button)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Matrix Lab"))
        layout.addLayout(top)
        layout.addWidget(self.table, 1)
        self.plan_button.clicked.connect(
            lambda: self.plan_requested.emit(self.objective_edit.toPlainText().strip())
        )
        self.generate_button.clicked.connect(self.generate_requested.emit)

    def set_plan(self, plan: MatrixPlan) -> None:
        self.current_plan = plan
        self.objective_edit.setPlainText(plan.objective)

    def set_variants(self, variants: list[MatrixVariant]) -> None:
        self.variants = variants
        self.table.setRowCount(len(variants))
        for row, variant in enumerate(variants):
            self.table.setItem(row, 0, QTableWidgetItem(str(variant.index)))
            self.table.setItem(row, 1, QTableWidgetItem(variant.prompt))
            self.table.setItem(row, 2, QTableWidgetItem(str(variant.parameters)))
            self.table.setItem(row, 3, QTableWidgetItem(variant.notes))
