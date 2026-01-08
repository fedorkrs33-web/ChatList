import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt  # ✅ Добавлен импорт

# Создаём приложение
app = QApplication(sys.argv)

# Создаём окно
window = QWidget()
window.setWindowTitle("Минимальная программа")
window.setGeometry(300, 300, 300, 200)  # Ширина 300, высота 200

# Создаём кнопку и метку (для текста)
button = QPushButton("Нажми меня")
label = QLabel("Нажмите кнопку...")  # Начальный текст
label.setStyleSheet("font-size: 16px; color: blue;")  # Стиль текста
label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Выравнивание по центру

# Функция, которая сработает при нажатии
def on_click():
    label.setText("Минимальная программа на Python")

# Привязываем функцию к кнопке
button.clicked.connect(on_click)

# Размещаем элементы в окне
layout = QVBoxLayout()
layout.addWidget(label)   # Сначала метка
layout.addWidget(button)  # Потом кнопка
window.setLayout(layout)

# Показываем окно
window.show()

# Запускаем приложение
sys.exit(app.exec())
