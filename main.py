# main.py
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
    QCheckBox, QLabel, QLineEdit, QHeaderView, QTabWidget,
    QFileDialog, QMessageBox, QScrollArea
)
from functools import partial
from PyQt6.QtCore import Qt
from models import Model
from network import Network
from db import db
from datetime import datetime
from PyQt6.QtCore import Qt, QTimer  # Добавьте QTimer

# THEME_COLORS.py
THEME_COLORS = {
    "light": {
        "bg": "#f9f9f9",
        "text": "#333333",
        "border": "#ddd"
    },
    "dark": {
        "bg": "#3c3c3c",
        "text": "#ffffff",
        "border": "#555"
    }
}

LIGHT_BUTTON_STYLE = """
QPushButton {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 2px 4px;
    min-height: 24px;
    min-width: 82px;
    text-align: center;
    font-family: Arial;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #f8f8f8;
    border: 1px solid #bbbbbb;
}

QPushButton:pressed {
    background-color: #e0e0e0;
    border: 1px solid #999999;
}
"""


COMMON_BUTTON_STYLE_DARK = """
QPushButton {
    padding: 2px 3px;
    border: 1px solid #555;
    border-radius: 4px;
    min-height: 22px;
    min-width: 84px;
    text-align: center;
    font-family: Arial;
    font-size: 12px;
    background-color: #4a4a4a;
    color: white;
}

QPushButton:hover {
    background-color: #5a5a5a;
}

QPushButton:pressed {
    background-color: #6a6a6a;
}
"""

DARK_THEME = """
QWidget {
    background-color: #2b2b2b;
    color: #ffffff;
    font-family: Arial;
}

/* Заголовки таблиц */
QHeaderView::section {
    background-color: #3c3c3c;
    color: #ffffff;
    padding: 4px;
    border: 1px solid #555;
    font-weight: bold;
}

/* Таблица результатов */
QTableWidget {
    background-color: #3c3c3c;
    alternate-background-color: #333333;
    border: 1px solid #555;
    gridline-color: #555;
    color: #ffffff;
}

/* Ячейки таблицы */
QTableWidget::item {
    background-color: #3c3c3c;
    color: #ffffff;
    padding: 6px;
}

/* Выделенная ячейка */
QTableWidget::item:selected {
    background-color: #5a5a5a;
    color: #ffffff;
}

/* Вкладки */
QTabWidget::pane {
    border: 1px solid #3c3c3c;
}

QTabBar::tab {
    background: #3c3c3c;
    color: #ffffff;
    padding: 8px 12px;
    margin: 2px;
    border-radius: 4px;
}

QTabBar::tab:selected {
    background: #4a4a4a;
    font-weight: bold;
}

/* Поля ввода, списки */
QListWidget, QTextEdit, QLineEdit, QComboBox {
    background-color: #3c3c3c;
    border: 1px solid #555;
    color: #ffffff;
    padding: 4px;
}

QPushButton {
    background-color: #4a4a4a;
    color: white;
    border: 1px solid #555;
    padding: 6px 10px;
    border-radius: 6px;
    min-height: 30px;
    min-width: 80px;
    text-align: center;
}

QPushButton:hover {
    background-color: #5a5a5a;
}

QStatusBar {
    background-color: #333;
    color: #ccc;
}
"""


class ChatListApp(QMainWindow):
    def get_label_style(self):
        """Возвращает CSS для QLabel в зависимости от текущей темы"""
        theme = self.db.get_setting("theme", "light")
        colors = THEME_COLORS.get(theme, THEME_COLORS["light"])
        return f"""
        QLabel {{
            background: {colors['bg']};
            color: {colors['text']};
            padding: 8px;
            border-radius: 4px;
        }}
        """
 
    def __init__(self):
        super().__init__()
        self.db = db  # Инициализация БД

        self.setWindowTitle("ChatList — Сравнение AI-ответов")
        self.resize(1000, 700)
        self.statusBar()  # Инициализирует statusBar

        # Хранение временных результатов: model_id → (response, checkbox)
        self.temp_results = {}

        self.init_ui()
        # Добавляем кнопку в статус-бар
        self.theme_btn = QPushButton("🌙 Тёмная тема")
        self.theme_btn.setCheckable(True)
        self.theme_btn.clicked.connect(self.toggle_theme)

        # Добавляем в статус-бар
        self.statusBar().addPermanentWidget(self.theme_btn)

        # Загружаем сохранённую тему
        self.load_theme()

        # Загружаем промты и модели
        self.load_prompts()
        self.load_models()

    def toggle_theme(self):
        is_dark = self.theme_btn.isChecked()
        if is_dark:
            # Применяем тёмный фон + тёмные кнопки
            full_style = DARK_THEME + COMMON_BUTTON_STYLE_DARK
            self.setStyleSheet(full_style)
            self.theme_btn.setText("☀ Светлая тема")
            self.db.set_setting("theme", "dark")
        else:
            # Применяем только стиль кнопок (светлый)
            self.setStyleSheet(LIGHT_BUTTON_STYLE)
            self.theme_btn.setText("🌙 Тёмкая тема")
            self.db.set_setting("theme", "light")
        # 🔥 Обновляем стили внутри ячеек
        self.update_response_styles()

    def load_theme(self):
        theme = self.db.get_setting("theme", "light")
        if theme == "dark":
            self.theme_btn.setChecked(True)
            self.setStyleSheet(DARK_THEME)
            self.theme_btn.setText("☀ Светлая тема")
        else:
            self.theme_btn.setChecked(False)
            self.setStyleSheet(LIGHT_BUTTON_STYLE)
            self.theme_btn.setText("🌙 Тёмкая тема")
        # 🔥 Обновляем стили при старте
        self.update_response_styles()


    def init_ui(self):
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # ============= ВКЛАДКИ =============
        tabs = QTabWidget()
        self.tab_prompts = QWidget()
        self.tab_results = QWidget()
        tabs.addTab(self.tab_prompts, "Промты")
        tabs.addTab(self.tab_results, "Результаты")
        tabs.addTab(self.create_models_tab(), "Модели")
        tabs.addTab(self.create_preview_tab(), "Предпросмотр Markdown")

        layout.addWidget(tabs)

        # ============= ВКЛАДКА 1: ПРОМТЫ =============
        prompts_layout = QVBoxLayout()
        self.tab_prompts.setLayout(prompts_layout)


        # Поиск
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по промтам и тегам...")
        self.search_input.textChanged.connect(self.on_search)
        search_layout.addWidget(QLabel("Поиск:"))
        search_layout.addWidget(self.search_input)
        prompts_layout.addLayout(search_layout)

        # Таблица промтов
        self.prompts_table = QTableWidget()
        self.prompts_table.setColumnCount(5)
        self.prompts_table.setHorizontalHeaderLabels(["ID", "Дата", "Промт", "Теги", "Действия"])
        header = self.prompts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Дата
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # Промт
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)             # Теги
        self.prompts_table.setColumnWidth(3,40)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)             # Действия
        self.prompts_table.setColumnWidth(4, 210)
        self.prompts_table.setWordWrap(True)
        self.prompts_table.resizeRowsToContents()
        self.prompts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        prompts_layout.addWidget(self.prompts_table)

        # Поле ввода промта
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Введите промт...")
        prompts_layout.addWidget(QLabel("Новый или выбранный промт:"))
        prompts_layout.addWidget(self.prompt_input)

        # Кнопки
        btn_layout = QHBoxLayout()
        self.send_btn = QPushButton("📤 Отправить во все активные модели")
        self.send_btn.clicked.connect(self.send_prompt)
        btn_layout.addWidget(self.send_btn)
        prompts_layout.addLayout(btn_layout)

        # ============= ВКЛАДКА 2: РЕЗУЛЬТАТЫ =============
        results_layout = QVBoxLayout()
        self.tab_results.setLayout(results_layout)

        # Таблица результатов
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Модель", "Ответ", "Выбрать"])
        # Разрешить перенос текста в ячейке "Ответ"
        self.results_table.setWordWrap(True)
        self.results_table.setTextElideMode(Qt.TextElideMode.ElideNone)

        # Включить автоматическую высоту строк
        self.results_table.resizeRowsToContents()

        # Опционально: включить прокрутку внутри ячейки
        self.results_table.verticalHeader().setVisible(True)



        # 🔧 Настройка ширины
        results_header = self.results_table.horizontalHeader()
        results_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        results_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        results_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self.results_table.cellDoubleClicked.connect(self.view_full_response)
        results_layout.addWidget(self.results_table)


        # Кнопки управления
        action_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 Сохранить выбранные")
        self.save_btn.clicked.connect(self.save_selected)
        action_layout.addWidget(self.save_btn)

        self.clear_btn = QPushButton("🗑️ Очистить")
        self.clear_btn.clicked.connect(self.clear_results)
        action_layout.addWidget(self.clear_btn)

        self.export_btn = QPushButton("📄 Экспорт в Markdown")
        self.export_btn.clicked.connect(self.export_to_markdown)
        action_layout.addWidget(self.export_btn)

        self.load_saved_btn = QPushButton("📥 Загрузить сохранённые")
        self.load_saved_btn.clicked.connect(self.load_saved_results)
        action_layout.addWidget(self.load_saved_btn)

        self.export_html_btn = QPushButton("🌐 Экспорт в HTML")
        self.export_html_btn.clicked.connect(self.export_to_html)
        action_layout.addWidget(self.export_html_btn)

        results_layout.addLayout(action_layout)

    def update_response_styles(self):
        theme = self.db.get_setting("theme", "light")
        if theme == "dark":
            bg_color = "#3c3c3c"
            border_color = "#555"
            scroll_bg = "#333"
            handle_color = "#888"
        else:
            bg_color = "#ffffff"
            border_color = "#ddd"
            scroll_bg = "#f0f0f0"
            handle_color = "#c0c0c0"

        for row in range(self.results_table.rowCount()):
            scroll_area = self.results_table.cellWidget(row, 1)
            if isinstance(scroll_area, QScrollArea):
                scroll_area.setStyleSheet(f"""
                    QScrollArea {{
                        border: 1px solid {border_color};
                        border-radius: 4px;
                        background: {bg_color};
                    }}
                    QScrollBar:vertical {{
                        width: 12px;
                        background: {scroll_bg};
                        border-left: 1px solid {border_color};
                    }}
                    QScrollBar::handle:vertical {{
                        background: {handle_color};
                        border-radius: 6px;
                    }}
                """)
                label = scroll_area.widget()
                if isinstance(label, QLabel):
                    label.setStyleSheet(self.get_label_style())

    def load_saved_results(self):
        """Загружает сохранённые результаты из БД в таблицу"""
        # Очищаем текущие результаты
        self.clear_results()

        # Получаем все сохранённые результаты
        saved_results = db.get_all_saved_results()

        if not saved_results:
            QMessageBox.information(self, "Нет данных", "Нет сохранённых результатов.")
            return

        # Устанавливаем количество строк
        self.results_table.setRowCount(len(saved_results))

        self.temp_results.clear()

        for row_idx, result in enumerate(saved_results):
            prompt_text = result["prompt"]
            model_name = result["model_name"]
            response = result["response"]
            saved_at = result["saved_at"]

            # Столбец 0: Модель
            self.results_table.setItem(row_idx, 0, QTableWidgetItem(model_name))

            # Столбец 1: Ответ — с прокруткой
            label = QLabel(response)
            label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            label.setStyleSheet(self.get_label_style())

            scroll = QScrollArea()
            scroll.setWidget(label)
            scroll.setWidgetResizable(True)
            scroll.setMaximumHeight(200)
            scroll.setMinimumHeight(60)
            self.results_table.setCellWidget(row_idx, 1, scroll)

            # Столбец 2: Чекбокс (уже сохранено)
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            checkbox.setEnabled(False)  # Нельзя снять — уже в БД
            checkbox_widget = QWidget()
            layout = QHBoxLayout(checkbox_widget)
            layout.addWidget(checkbox)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            checkbox_widget.setLayout(layout)
            self.results_table.setCellWidget(row_idx, 2, checkbox_widget)

            # Сохраняем в temp_results для совместимости (например, экспорт)
            self.temp_results[row_idx] = (None, response, checkbox)

        # Подстраиваем высоту строк
        QTimer.singleShot(50, self.resize_all_rows)

        # Обновляем статус
        self.statusBar().showMessage(f"Загружено {len(saved_results)} сохранённых ответов", 3000)

    def export_to_html(self):
        """Экспортирует выбранные ответы в HTML-файл"""
        if not self.temp_results:
            QMessageBox.warning(self, "Экспорт", "Нет результатов для экспорта.")
            return

        # Собираем выбранные ответы
        selected_responses = []
        for row_idx, (model_id, response, checkbox) in self.temp_results.items():
            if checkbox.isChecked():
                model_name = self.results_table.item(row_idx, 0).text()
                selected_responses.append((model_name, response))

        if not selected_responses:
            QMessageBox.warning(self, "Экспорт", "Ничего не выбрано для экспорта.")
            return

        # Диалог сохранения
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить как HTML",
            "results.html",
            "HTML Files (*.html);;All Files (*)"
        )
        if not file_path:
            return

        # Получаем текущую тему для стилей
        theme = self.db.get_setting("theme", "light")
        html_content = self.generate_html(selected_responses, theme)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            QMessageBox.information(self, "Готово", f"Экспорт в HTML сохранён:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{str(e)}")

    def generate_html(self, responses: list, theme: str) -> str:
        """Генерирует HTML с встроенными стилями"""
        # Цвета в зависимости от темы
        if theme == "dark":
            bg = "#2b2b2b"
            text = "#ffffff"
            block_bg = "#3c3c3c"
            border = "#555"
            accent = "#007acc"
        else:
            bg = "#ffffff"
            text = "#333333"
            block_bg = "#f9f9f9"
            border = "#ddd"
            accent = "#0056b3"

            # Начало HTML
            html = f"""<!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>ChatList — Результаты</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                background-color: {bg};
                color: {text};
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1 {{
                color: {accent};
                border-bottom: 2px solid {accent};
                padding-bottom: 10px;
            }}
            h2 {{
                color: {accent};
                margin-top: 20px;
            }}
            blockquote {{
                background-color: {block_bg};
                border-left: 4px solid {accent};
                margin: 15px 0;
                padding: 12px 15px;
                border-radius: 0 4px 4px 0;
                font-style: italic;
            }}
            .footer {{
                margin-top: 30px;
                color: #777;
                font-size: 0.9em;
                text-align: center;
            }}
            .divider {{
                border: 0;
                border-top: 1px solid {border};
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>ChatList — Результаты</h1>
            <p><strong>Дата:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <hr class="divider">
    """

            # Добавляем ответы
            for model_name, response in responses:
                response_escaped = (
                    response
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace("\n", "<br>")
                )
                html += f"""
            <h2>{model_name}</h2>
            <blockquote>
                {response_escaped}
            </blockquote>
            <hr class="divider">
    """

            # Завершение HTML
            html += f"""
            <div class="footer">
                Экспорт сгенерирован ChatList • <a href="https://github.com/fedorkrs33-web/ChatList" style="color: {accent}; text-decoration: none;">GitHub</a>
            </div>
        </div>
    </body>
    </html>
    """
        return html

        
     #============= ВКЛАДКА 3: МОДЕЛИ =============
    def create_models_tab(self):
        """Создаёт вкладку 'Модели'"""
        models_layout = QVBoxLayout()
        self.tab_models = QWidget()
        self.tab_models.setLayout(models_layout)
        # Таблица моделей
        self.models_table = QTableWidget()
        self.models_table.setColumnCount(7)
        self.models_table.setHorizontalHeaderLabels(["ID", "Имя", "API URL", "Внутреннее имя", "Провайдер", "Активна", "Управление"])
        header = self.models_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Имя
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # API URL
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Внутреннее имя
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Провайдер
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)             # Активна
        self.models_table.setColumnWidth(5, 60)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)             # Управление
        self.models_table.setColumnWidth(6, 110)                                  
        models_layout.addWidget(self.models_table)

        # Кнопка обновления
        refresh_btn = QPushButton("🔄 Обновить список")
        refresh_btn.clicked.connect(self.load_models)
        models_layout.addWidget(refresh_btn)

        return self.tab_models
    #============= ВКЛАДКА 4: Предпросмотр Markdown =============
    def create_preview_tab(self):
        """Создаёт вкладку 'Предпросмотр Markdown'"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Заголовок
        layout.addWidget(QLabel("Сохранённые результаты — предпросмотр Markdown"))

        # Таблица с результатами
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(4)
        self.preview_table.setHorizontalHeaderLabels(["ID", "Промт", "Модели", "Дата"])
        header = self.preview_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.preview_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.preview_table.setWordWrap(True)
        self.preview_table.resizeRowsToContents()

        # Подключение: при выборе строки — обновить предпросмотр
        self.preview_table.cellClicked.connect(self.load_preview)

        layout.addWidget(self.preview_table)

        # Поле предпросмотра
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet("font-family: Arial; font-size: 12px;")
        layout.addWidget(self.preview_text)

        # Кнопка: обновить список
        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.clicked.connect(self.load_preview_list)
        layout.addWidget(refresh_btn)

        return tab

    def load_preview_list(self):
        """Загружает список сохранённых результатов в таблицу"""
        self.preview_table.setRowCount(0)
        data = self.db.get_saved_results_with_models()

        for row_idx, item in enumerate(data):
            self.preview_table.insertRow(row_idx)

            self.preview_table.setItem(row_idx, 0, QTableWidgetItem(str(item["id"])))
            self.preview_table.setItem(row_idx, 1, QTableWidgetItem(item["prompt"]))
            self.preview_table.setItem(row_idx, 2, QTableWidgetItem(item["models"]))
            self.preview_table.setItem(row_idx, 3, QTableWidgetItem(item["saved_at"]))

    def load_preview(self, row, column):
        """Загружает и отображает Markdown-предпросмотр с отступами"""
        result_id = int(self.preview_table.item(row, 0).text())
        prompt = self.preview_table.item(row, 1).text()

        responses = self.db.get_responses_by_result_id(result_id)
        if not responses:
            self.preview_text.setHtml("<p><i>Нет данных</i></p>")
            return

        # Формируем Markdown с пустыми строками для отступов
        md_lines = []
        md_lines.append(f"# {prompt.strip()}")
        md_lines.append(f"*Дата: {responses[0]['saved_at']}*")
        md_lines.append("")  # Пустая строка — отступ

        for r in responses:
            md_lines.append(f"## {r['model_name']}")
            # Сохраняем переносы и пустые строки
            response_text = r['response'].strip()
            # Разбиваем на строки и обрабатываем
            lines = response_text.splitlines()
            for line in lines:
                if line.strip() == '':
                    md_lines.append(">")  # Пустая строка в цитате
                else:
                    md_lines.append(f"> {line}")
            md_lines.append("")  # Отступ между моделями

        html = self.md_to_simple_html("\n".join(md_lines))
        self.preview_text.setHtml(html)

    def escape_html(self, text: str) -> str:
        """Экранирует HTML-символы"""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#039;"))

    def md_to_simple_html(self, md: str) -> str:
        """Улучшенный упрощённый конвертер Markdown → HTML с поддержкой отступов и абзацев"""
        lines = md.split('\n')
        html_lines = []
        in_block = False  # Находимся ли внутри <blockquote>

        # Стили темы
        theme = self.db.get_setting("theme", "light")
        if theme == "dark":
            block_bg = "#3c3c3c"
            border = "#555"
            text = "#ffffff"
        else:
            block_bg = "#f9f9f9"
            border = "#ddd"
            text = "#333333"

        for line in lines:
            stripped = line.rstrip()  # Убираем пробелы справа

            # Обработка заголовков
            if stripped.startswith('# '):
                if in_block:
                    html_lines.append('</blockquote>')
                    in_block = False
                html_lines.append(f"<h1 style='color: #007acc;'>{self.escape_html(stripped[2:])}</h1>")
            elif stripped.startswith('## '):
                if in_block:
                    html_lines.append('</blockquote>')
                    in_block = False
                html_lines.append(f"<h2 style='color: #007acc;'>{self.escape_html(stripped[3:])}</h2>")

            # Обработка цитат
            elif stripped.startswith('> '):
                content = stripped[2:]  # Убираем "> "

                if not in_block:
                    # Начинаем цитату
                    html_lines.append(f'<blockquote style="background: {block_bg}; '
                                    f'border-left: 4px solid #007acc; margin: 10px 0; padding: 12px 15px; '
                                    f'font-style: italic; color: {text}; border-radius: 0 4px 4px 0;">')
                    in_block = True

                if content == '':
                    # Пустая строка в цитате — добавим пустой абзац для отступа
                    html_lines.append('<br>')
                else:
                    # Экранируем и добавляем текст
                    html_lines.append(f"{self.escape_html(content)}<br>")

            else:
                # Обычный текст или пустая строка
                if in_block:
                    html_lines.append('</blockquote>')
                    in_block = False

                if stripped == '':
                    # Пустая строка — отступ между абзацами
                    html_lines.append('<br>')
                else:
                    # Обычный абзац
                    html_lines.append(f"<p style='color: {text}; margin: 8px 0;'>{self.escape_html(stripped)}</p>")

        # Закрываем блок, если остались открытыми
        if in_block:
            html_lines.append('</blockquote>')

        # Объединяем всё
        return ''.join(html_lines)

    def load_models(self):
        """Загружает модели из БД в таблицу"""
        self.models_table.setRowCount(0)
        models = Model.load_all()  # Все модели

        for row_idx, model in enumerate(models):
            self.models_table.insertRow(row_idx)
            self.models_table.setRowHeight(row_idx, 45)

            # ID
            self.models_table.setItem(row_idx, 0, QTableWidgetItem(str(model.id)))
            # Имя
            # Колонка 1: Имя — редактируемое
            name_edit = QLineEdit(model.name)
            name_edit.setPlaceholderText("Имя модели")
            name_edit.editingFinished.connect(
                lambda m=model, le=name_edit: self.update_model_field(m.id, "name", le.text())
            )
            self.models_table.setCellWidget(row_idx, 1, name_edit)

            # Колонка 2: API URL — редактируемое
            url_edit = QLineEdit(model.api_url or "")
            url_edit.setPlaceholderText("https://...")
            url_edit.editingFinished.connect(
                lambda m=model, le=url_edit: self.update_model_field(m.id, "api_url", le.text())
            )
            self.models_table.setCellWidget(row_idx, 2, url_edit)

            # Колонка 3: Внутреннее имя — редактируемое
            model_name_edit = QLineEdit(model.model_name or "")
            model_name_edit.setPlaceholderText("gpt-4, claude-3-haiku и т.п.")
            model_name_edit.editingFinished.connect(
                lambda m=model, le=model_name_edit: self.update_model_field(m.id, "model_name", le.text())
            )
            self.models_table.setCellWidget(row_idx, 3, model_name_edit)

            # Колонка 4: Провайдер — можно тоже редактировать (опционально)
            provider_edit = QLineEdit(model.provider or "")
            provider_edit.setPlaceholderText("openai, anthropic...")
            provider_edit.editingFinished.connect(
                lambda m=model, le=provider_edit: self.update_model_field(m.id, "provider", le.text())
            )
            self.models_table.setCellWidget(row_idx, 4, provider_edit)

            # Чекбокс "Активна"
            active_checkbox = QCheckBox()
            active_checkbox.setChecked(model.is_active)
            active_cell = QWidget()
            active_layout = QHBoxLayout(active_cell)
            active_layout.addWidget(active_checkbox)
            active_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            active_layout.setContentsMargins(0, 0, 0, 0)
            active_cell.setLayout(active_layout)
            self.models_table.setCellWidget(row_idx, 5, active_cell)

            # Кнопка "Обновить статус"
            update_btn = QPushButton("✅ Сохранить")
            update_btn.setMinimumHeight(30)
            update_btn.setMinimumWidth(100)
            update_btn.setStyleSheet("")  # Убедитесь, что не переопределяется где-то
            update_btn.clicked.connect(
                lambda _, mid=model.id, cb=active_checkbox: self.update_model_status(mid, cb)
            )
            btn_cell = QWidget()
            btn_layout = QHBoxLayout(btn_cell)
            btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            btn_layout.setContentsMargins(0, 0, 0, 0) # Отступы
            btn_cell.setLayout(btn_layout)
            btn_layout.addWidget(update_btn)
            self.models_table.setCellWidget(row_idx, 6, btn_cell)

    def update_model_field(self, model_id: int, field: str, value: str):
        """Обновляет поле модели в БД"""
        try:
            # Обновляем в БД
            Model.update_field(model_id, field, value)
            # Обновляем статус
            self.statusBar().showMessage(f"✅ Поле '{field}' модели обновлено", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить поле:\n{str(e)}")


    def on_model_status_changed(self, model_id: int, state: int):
        """Вызывается при изменении состояния чекбокса модели"""
        # Метод для отслеживания изменений (можно расширить логикой при необходимости)
        # state: 0 = Unchecked, 2 = Checked (Qt.CheckState)
        pass

    def update_model_status(self, model_id: int, checkbox: QCheckBox):
        """Обновляет статус модели в БД"""
        is_active = checkbox.isChecked()
        try:
            Model.update_status(model_id, is_active)
            status_text = "активна" if is_active else "неактивна"
            self.statusBar().showMessage(f"Модель обновлена: статус '{status_text}'", 3000)
            QMessageBox.information(self, "Готово", f"Статус модели изменён на '{status_text}'")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить статус модели:\n{str(e)}")

    def load_prompts(self):
        """Загружает все промты в таблицу"""
        self.prompts_table.setRowCount(0)
        prompts = db.get_all_prompts()

        for row_idx, p in enumerate(prompts):
            self.prompts_table.insertRow(row_idx)

            self.prompts_table.setItem(row_idx, 0, QTableWidgetItem(str(p["id"])))
            self.prompts_table.setItem(row_idx, 1, QTableWidgetItem(p["created_at"]))
            self.prompts_table.setItem(row_idx, 2, QTableWidgetItem(p["prompt"]))
            self.prompts_table.setItem(row_idx, 3, QTableWidgetItem(p["tags"] or ""))

            self.prompts_table.setRowHeight(row_idx, 45)

            # Контейнер для кнопок
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 0, 0, 2)
            btn_layout.setSpacing(3)
            btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Создаём кнопки
            copy_btn = QPushButton("📋 Копировать")
            copy_btn.setFixedSize(90, 30)

            delete_btn = QPushButton("🗑️ Удалить")
            delete_btn.setFixedSize(90, 30)
            delete_btn.setStyleSheet("QPushButton { color: #a00; }")

            # Сохраняем ссылки на кнопки внутри виджета, чтобы Python не удалил
            btn_widget.copy_btn = copy_btn
            btn_widget.delete_btn = delete_btn

            # Подключаем сигналы
            from functools import partial
            copy_btn.clicked.connect(partial(self.copy_prompt_to_input, p["prompt"]))
            delete_btn.clicked.connect(partial(self.delete_prompt, p["id"]))

            # Добавляем в макет
            btn_layout.addWidget(copy_btn)
            btn_layout.addWidget(delete_btn)
            btn_widget.setLayout(btn_layout)

            # Устанавливаем в таблицу
            self.prompts_table.setCellWidget(row_idx, 4, btn_widget)


    def on_search(self):
        """Поиск в промтах"""
        query = self.search_input.text().strip()
        if not query:
            self.load_prompts()
            return

        self.prompts_table.setRowCount(0)
        results = db.search_prompts(query)
        for row_idx, p in enumerate(results):
            self.prompts_table.insertRow(row_idx)
            self.prompts_table.setItem(row_idx, 0, QTableWidgetItem(str(p["id"])))
            self.prompts_table.setItem(row_idx, 1, QTableWidgetItem(p["created_at"]))
            self.prompts_table.setItem(row_idx, 2, QTableWidgetItem(p["prompt"]))
            self.prompts_table.setItem(row_idx, 3, QTableWidgetItem(p["tags"] or ""))

            # Контейнер для кнопок
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(6)
            btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Создаём кнопки
            copy_btn = QPushButton("📋 Копировать")
            copy_btn.setFixedSize(90, 26)

            delete_btn = QPushButton("🗑️ Удалить")
            delete_btn.setFixedSize(90, 26)
            delete_btn.setStyleSheet("QPushButton { color: #a00; }")

            # Сохраняем ссылки на кнопки внутри виджета, чтобы Python не удалил
            btn_widget.copy_btn = copy_btn
            btn_widget.delete_btn = delete_btn

            # Подключаем сигналы
            from functools import partial
            copy_btn.clicked.connect(partial(self.copy_prompt_to_input, p["prompt"]))
            delete_btn.clicked.connect(partial(self.delete_prompt, p["id"]))

            # Добавляем в макет
            btn_layout.addWidget(copy_btn)
            btn_layout.addWidget(delete_btn)
            btn_widget.setLayout(btn_layout)

            # Устанавливаем в таблицу
            self.prompts_table.setCellWidget(row_idx, 4, btn_widget)


    def copy_prompt_to_input(self, text):
        """Копирует переданный текст промта в поле ввода"""
        self.prompt_input.setPlainText(text)
        self.statusBar().showMessage("Промт скопирован в поле ввода", 3000)
        
    def load_prompt_to_input(self):
        """Загружает выбранный промт в поле ввода"""
        selected = self.prompts_table.currentRow()
        if selected >= 0:
            prompt_item = self.prompts_table.item(selected, 2)
            if prompt_item:
                self.prompt_input.setPlainText(prompt_item.text())

    def send_prompt(self):
        """Отправляет промт во все активные модели"""
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Ошибка", "Введите промт!")
            return

        # Сохраняем промт в БД
        prompt_id = db.save_prompt(prompt)

        # Очищаем предыдущие результаты
        self.clear_results()

        # Получаем активные модели
        models = Model.get_active()
        if not models:
            QMessageBox.warning(self, "Ошибка", "Нет активных моделей. Проверьте настройки.")
            return

        # Отправляем во все модели
        self.results_table.setRowCount(len(models))
        self.temp_results.clear()

        for row_idx, model in enumerate(models):
            response = Network.send_prompt_to_model(model, prompt)

            print(f"[DEBUG] {model.name}: response={repr(response[:100] if response else None)}")

            # Нормализуем ответ
            if not response or not response.strip():
                response = f"[Ошибка] Пустой ответ от {model.name}"
            else:
                response = response.strip()

            # Устанавливаем имя модели
            item = QTableWidgetItem(model.name)
            item.setTextAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            self.results_table.setItem(row_idx, 0, item)
            # Создаём QLabel
            label = QLabel(response)
            label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            label.setStyleSheet(self.get_label_style())
            
            # Создаём QScrollArea
            scroll = QScrollArea()
            scroll.setWidget(label)
            scroll.setWidgetResizable(True)

            # 🔧 Определяем цвета
            theme = self.db.get_setting("theme", "light")
            if theme == "dark":
                bg_color = "#3c3c3c"
                border_color = "#555"
                scroll_bg = "#333"
                handle_color = "#888"
            else:
                bg_color = "#ffffff"
                border_color = "#ddd"
                scroll_bg = "#f0f0f0"
                handle_color = "#c0c0c0"

            scroll.setStyleSheet(f"""
                QScrollArea {{
                border: 1px solid {border_color};
                border-radius: 4px;
                background: {bg_color};
            }}
            QScrollBar:vertical {{
                width: 12px;
                background: {scroll_bg};
                border-left: 1px solid {border_color};
            }}
            QScrollBar::handle:vertical {{
                background: {handle_color};
                border-radius: 6px;
                }}
            """)


            # Устанавливаем высоту прокручиваемой области
            scroll.setMaximumHeight(200)  # Максимальная высота — можно настроить
            scroll.setMinimumHeight(60)

            # Устанавливаем в ячейку
            self.results_table.setCellWidget(row_idx, 1, scroll)  # Высота поля ответа

            # Чекбокс
            checkbox = QCheckBox()
            checkbox_widget = QWidget()
            layout = QHBoxLayout(checkbox_widget)
            layout.addWidget(checkbox)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            checkbox_widget.setLayout(layout)
            self.results_table.setCellWidget(row_idx, 2, checkbox_widget)

            self.temp_results[row_idx] = (model.id, response, checkbox)

        # После цикла
        QTimer.singleShot(100, self.resize_all_rows)

    def delete_prompt(self, prompt_id: int):
        """Удаляет промт и все его результаты"""
        reply = QMessageBox.question(
            self,
            "Удалить промт?",
            "Вы уверены, что хотите удалить этот промт и все его ответы?\n\nЭто действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return

        try:
            # Удаляем через БД
            db.delete_prompt(prompt_id)
            # Обновляем таблицу
            self.load_prompts()
            self.statusBar().showMessage("✅ Промт удалён", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить промт:\n{str(e)}")


    def save_selected(self):
        """Сохраняет выбранные результаты в БД"""
        prompt_text = self.prompt_input.toPlainText().strip()
        if not prompt_text:
            return

        # Сохраняем промт (если ещё не сохранён)
        prompt_id = db.save_prompt(prompt_text)

        saved_count = 0
        for row_idx, (model_id, response, checkbox) in self.temp_results.items():
            if checkbox.isChecked():
                db.save_result(prompt_id, model_id, response)
                saved_count += 1

        if saved_count > 0:
            QMessageBox.information(self, "Готово", f"Сохранено {saved_count} ответов!")
        else:
            QMessageBox.information(self, "Внимание", "Ничего не выбрано.")
    
    def export_to_markdown(self):
        """Экспортирует выбранные ответы в Markdown-файл"""
        if not self.temp_results:
            QMessageBox.warning(self, "Экспорт", "Нет результатов для экспорта.")
            return

        # Собираем выбранные чекбоксы
        selected_responses = []
        for row_idx, (model_id, response, checkbox) in self.temp_results.items():
            if checkbox.isChecked():
                model_name = self.results_table.item(row_idx, 0).text()
                selected_responses.append((model_name, response))

        if not selected_responses:
            QMessageBox.warning(self, "Экспорт", "Ничего не выбрано для экспорта.")
            return

        # Диалог выбора файла
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить как",
            "results.md",
            "Markdown Files (*.md);;Text Files (*.txt)"
        )

        if not file_path:
            return  # Отменили

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("# Результаты ChatList\n\n")
                f.write(f"**Дата:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("---\n\n")

                for model_name, response in selected_responses:
                    f.write(f"## Модель: {model_name}\n\n")
                    f.write(f"> {response.replace(chr(10), '  \n> ')}\n\n")
                    f.write("---\n\n")

            QMessageBox.information(self, "Готово", f"Результаты экспортированы в:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{str(e)}")

    def clear_results(self):
        """Очищает таблицу результатов и удаляет виджеты"""
        # Очищаем все ячейки с виджетами
        for row in range(self.results_table.rowCount()):
            for col in range(self.results_table.columnCount()):
                widget = self.results_table.cellWidget(row, col)
                if widget:
                    widget.deleteLater()

        # Очищаем содержимое и количество строк
        self.results_table.clearContents()
        self.results_table.setRowCount(0)
        self.temp_results.clear()

    def resize_all_rows(self):
        """Подстраивает высоту всех строк под содержимое"""
        for row in range(self.results_table.rowCount()):
            self.results_table.resizeRowToContents(row)
        # Принудительно обновляем отображение
        self.results_table.viewport().update()

    def closeEvent(self, event):
        """При закрытии"""
        reply = QMessageBox.question(self, 'Выход', 'Закрыть приложение?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

    def view_full_response(self, row, column):
        if column == 1:  # Только по столбцу "Ответ"
            scroll_area = self.results_table.cellWidget(row, 1)
            if scroll_area and isinstance(scroll_area, QScrollArea):
                label = scroll_area.widget()
                if label and isinstance(label, QLabel):
                    model_name = self.results_table.item(row, 0).text()
                    response_text = label.text()

                    msg_box = QMessageBox(self)
                    msg_box.setWindowTitle(f"Полный ответ: {model_name}")
                    msg_box.setText("Ответ скопирован в буфер. Нажмите 'Показать подробности' для просмотра.")
                    msg_box.setDetailedText(response_text)
                    msg_box.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                    msg_box.setIcon(QMessageBox.Icon.Information)
                    msg_box.exec()

# ============= ЗАПУСК ПРИЛОЖЕНИЯ =============
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatListApp()
    window.show()
    sys.exit(app.exec())

