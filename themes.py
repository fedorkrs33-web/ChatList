# themes.py
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


# 🎨 Стили тем
STYLES = {
    "light": """
        QMainWindow, QWidget {
            background-color: #f0f0f0;
            color: #000000;
            font-family: Arial;
        }
        QTabWidget::pane {
            border: 1px solid #ccc;
        }
        QTabBar::tab {
            background: #e0e0e0;
            color: #000;
            padding: 10px;
            border: 1px solid #ccc;
            border-bottom: none;
        }
        QTabBar::tab:selected {
            background: #ffffff;
        }
        QPushButton {
            background-color: #d0d0d0;
            border: 1px solid #aaa;
            padding: 5px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #c0c0c0;
        }
        QTableWidget {
            background-color: white;
            alternate-background-color: #f8f8f8;
            gridline-color: #ddd;
            selection-background-color: #c0e0ff;
        }
        QHeaderView::section {
            background-color: #e0e0e0;
            color: #000;
            padding: 4px;
            border: 1px solid #ccc;
        }
        QLineEdit, QTextEdit, QComboBox, QSpinBox {
            background-color: white;
            color: #000;
            border: 1px solid #aaa;
            padding: 5px;
        }
        QLabel {
            color: #000;
        }
    """,
    "dark": """
        QMainWindow, QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
            font-family: Arial;
        }
        QTabWidget::pane {
            border: 1px solid #444;
        }
        QTabBar::tab {
            background: #3c3c3c;
            color: #ffffff;
            padding: 10px;
            border: 1px solid #444;
            border-bottom: none;
        }
        QTabBar::tab:selected {
            background: #555;
        }
        QPushButton {
            background-color: #3c3c3c;
            border: 1px solid #555;
            padding: 5px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #4c4c4c;
        }
        QTableWidget {
            background-color: #2b2b2b;
            alternate-background-color: #333;
            gridline-color: #444;
            selection-background-color: #5a5a5a;
        }
        QHeaderView::section {
            background-color: #3c3c3c;
            color: white;
            padding: 4px;
            border: 1px solid #444;
        }
        QLineEdit, QTextEdit, QComboBox, QSpinBox {
            background-color: #3c3c3c;
            color: #ffffff;
            border: 1px solid #555;
            padding: 5px;
        }
        QLabel {
            color: #ffffff;
        }
    """
}


# 🖋 Шрифты
def get_font(size: int) -> QFont:
    """Возвращает шрифт с заданным размером"""
    font = QFont("Arial")
    font.setPointSize(size)
    return font

def apply_font_size(self, size: int):
    print(f"🔧 Применяю размер шрифта: {size}")  # ← Отладка
    font = QFont("Arial", size)
    self.setFont(font)

    for widget in self.findChildren(QWidget):
        widget.setFont(font)

# 🎯 Применить тему
def apply_theme(widget, theme_name: str):
    """
    Применяет стиль к виджету (обычно — главное окно)

    :param widget: QWidget (например, QMainWindow)
    :param theme_name: "light" или "dark"
    """
    style = STYLES.get(theme_name, STYLES["light"])
    widget.setStyleSheet(style)

def get_label_style() -> str:  # ✅ Без self
    """Возвращает CSS-стиль для метки с ответом модели"""
    return """
        QLabel {
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 6px;
            padding: 10px;
            color: #000;
            font-size: 12px;
        }
    """
