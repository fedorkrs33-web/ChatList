# main.py
import sys
import os
import markdown
import re
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
    QCheckBox, QLabel, QLineEdit, QHeaderView, QTabWidget,
    QFileDialog, QMessageBox, QScrollArea, QComboBox,
    QInputDialog, QDialog, QSpinBox
)
from db1 import Database
from themes import apply_theme, get_font, get_label_style
from functools import partial
from PyQt6.QtCore import Qt
from network import Network
from datetime import datetime
from PyQt6.QtCore import Qt, QTimer  # Добавьте QTimer
from PyQt6.QtGui import QCursor, QGuiApplication, QIcon, QPixmap  # ✅ Добавлен QPixmap
from PyQt6.QtCore import Qt
from models import ModelsManager

# Импорт версии
try:
    from version import __version__
except ImportError:
    __version__ = "dev"  # fallback, если нет файла

class ChatListApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()

        # Загружаем настройки
        theme = self.db.get_setting("theme", "light")
        font_size = int(self.db.get_setting("font_size", "12"))  # ✅ Превращаем в число  # Дефолт: 12
        
        import themes
        self.themes = themes

        # Применяем
        apply_theme(self, theme)           # ← Из themes.py
        
        self.setWindowTitle(f"ChatList — Сравнение AI-ответов (v{__version__})")
        self.setWindowIcon(QIcon("app.ico"))
        self.resize(1000, 700)
        self.statusBar()  # Инициализирует statusBar
        self.all_results_data = []  # Для хранения результатов (поиск, сортировка)

        self.init_ui()
        self.apply_font_size(font_size)

        # Загружаем промты и модели
        self.load_prompts()
        self.load_models()

        # Хранение временных результатов: model_id → (response, checkbox)
        self.temp_results = {}

    def load_logo(self):
            """Если нужно использовать изображение в интерфейсе"""
            self.logo_label = QLabel()
            pixmap = QPixmap("logo.png")
            if not pixmap.isNull():
                self.logo_label.setPixmap(pixmap.scaled(100, 100))
            else:
                self.logo_label.setText("Логотип не найден")

    def load_theme(self):
        """Загружает тему из БД и применяет"""
        theme = self.db.get_setting("theme", "light")
        self.apply_theme(theme)

    def apply_font_size(self, size: int):
        """Применяет размер шрифта ко всему интерфейсу"""
        font = self.font()
        font.setPointSize(size)
        self.setFont(font)

        for widget in self.findChildren(QWidget):
            widget.setFont(font)

    def filter_results_table(self):
        """Фильтрует и отображает результаты (временная заглушка)"""
        pass  # Пока пусто — или реализуйте на основе all_results_data

    def update_preview_on_theme_change(self):
        """Если вкладка 'Предпросмотр' активна — перезагружает текущий просмотр"""
        # Проверяем, открыта ли вкладка "Предпросмотр Markdown"
        current_tab_index = self.tab_widget.currentIndex()
        if current_tab_index != 3:  # 🔢 Убедитесь, что это индекс вкладки "Предпросмотр"
            return  # Не на той вкладке — выходим

        # Проверяем, есть ли выбранная строка
        selected_row = self.preview_table.currentRow()
        if selected_row < 0:
            return

        # Перезапускаем предпросмотр (это вызовет перегенерацию HTML с новой темой)
        self.load_preview(selected_row, 0)

    def init_ui(self):
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # ============= ВКЛАДКИ =============
        tabs = QTabWidget()
        self.tab_widget = tabs
        self.tab_prompts = QWidget()
        self.tab_results = QWidget()
        tabs.addTab(self.tab_prompts, "Промты")
        tabs.addTab(self.tab_results, "Результаты")
        tabs.addTab(self.create_models_tab(), "Модели")
        tabs.addTab(self.create_preview_tab(), "Предпросмотр Markdown")
        tabs.addTab(self.create_settings_tab(), "Настройки")
        tabs.addTab(self.create_help_tab(), "Справка")

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
        self.enhance_prompt_btn = QPushButton("✨ Улучшить промт")
        self.enhance_prompt_btn.clicked.connect(self.enhance_prompt)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.enhance_prompt_btn)
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

    def enhance_prompt(self):
        """Запускает AI-ассистент для улучшения промта"""
        original = self.prompt_input.toPlainText().strip()
        if not original:
            QMessageBox.warning(self, "Пусто", "Введите промт для улучшения.")
            return

        # Диалог выбора модели
        model = self.select_model_for_enhancement()
        if not model:
            return

        # Формируем системный промт
        system_prompt = f"""
    Пожалуйста, улучши следующий промт:

    "{original}"

    Твоя задача:
    1. Сделай его чётким, конкретным, без двусмысленностей.
    2. Предложи 3 альтернативные формулировки.
    3. Адаптируй промт под:
    - 🧠 Глубокий анализ
    - 💻 Кодирование
    - 🎨 Креативное мышление

    Формат ответа:

    УЛУЧШЕННЫЙ ПРОМТ:
    [улучшенный текст]

    ВАРИАНТЫ:
    1. [вариант 1]
    2. [вариант 2]
    3. [вариант 3]

    АДАПТАЦИЯ:
    🔹 Анализ: [текст]
    🔹 Код: [текст]
    🔹 Креатив: [текст]
    """

        # Показываем "ожидание"
        self.show_wait_cursor()
        try:
            enhanced = Network.send_prompt_to_model(model, system_prompt)
            print("🔹 [DEBUG] Полный ответ от AI:")
            print(enhanced)  # ← Выводим весь ответ
        finally:
            self.restore_cursor()

        if not enhanced or not enhanced.strip():
            QMessageBox.critical(self, "Ошибка", "Не удалось получить улучшенный промт.")
            return

        print("🔹 [DEBUG] Перед вызовом show_enhancement_result")  # ← Добавьте это
        # Показываем результат
        self.show_enhancement_result(original, enhanced)

    def select_model_for_enhancement(self):
        try:
            models = self.db.get_active_models()  # ✅ Через self.db
            if not models:
                QMessageBox.warning(self, "Нет моделей", "Нет активных моделей для улучшения промта.")
                return None

            items = [model["name"] for model in models]
            item, ok = QInputDialog.getItem(self, "Выбор модели", "Выберите модель для улучшения промта:", items, 0, False)
            if ok and item:
                selected_model = next(m for m in models if m["name"] == item)
                return selected_model
            return None
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось выбрать модель:\n{e}")
            return None


    def show_enhancement_result(self, original: str, enhanced: str):
        """Показывает улучшенный промт, варианты и адаптации — каждый в отдельном блоке с кнопкой 'Принять'"""
        from PyQt6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
            QPushButton, QFrame, QScrollArea, QWidget
        )
        from PyQt6.QtCore import Qt

        # Парсим ответ
        result = self.parse_enhancement_response(enhanced)

        dialog = QDialog(self)
        dialog.setWindowTitle("🧠 AI-ассистент: Улучшение промта")
        dialog.resize(900, 600)

        # Главный layout
        main_layout = QVBoxLayout()

        # Скролл-область
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        def add_block(title: str, text: str):
            """Добавляет один блок: заголовок, текст, кнопку 'Принять' — с поддержкой тёмной темы"""
            if not text or not text.strip():
                return

            # Фрейм
            frame = QFrame()
            frame.setFrameShape(QFrame.Shape.Box)
            frame.setStyleSheet("""
                QFrame {
                    margin: 4px;
                    padding: 8px;
                    border: 1px solid #555;
                    border-radius: 6px;
                    background: #2d2d2d;  /* Тёмный фон фрейма */
                }
            """)

            layout = QHBoxLayout()

            # Левая часть: заголовок + текст
            left_layout = QVBoxLayout()

            label = QLabel(title)
            label.setStyleSheet("font-weight: bold; color: #ffffff; background: transparent;")
            label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            left_layout.addWidget(label)

            text_edit = QTextEdit()
            text_edit.setPlainText(text.strip())
            text_edit.setReadOnly(True)
            text_edit.setMaximumHeight(80)
            text_edit.setStyleSheet("""
                QTextEdit {
                    background: #ffffff;        /* Светлый фон */
                    color: #222222;             /* Тёмный текст */
                    border: 1px solid #dddddd;  /* Лёгкая рамка */
                    border-radius: 4px;
                    padding: 4px;
                    font-size: 12px;
                }
            """)
            left_layout.addWidget(text_edit)

            layout.addLayout(left_layout)

            # Кнопка "Принять"
            accept_btn = QPushButton("✅ Принять")
            accept_btn.setFixedWidth(100)
            accept_btn.setStyleSheet("""
                QPushButton {
                    background: #007acc;
                    color: white;
                    border: none;
                    padding: 6px 10px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #005a9e;
                }
                QPushButton:pressed {
                    background: #004578;
                }
            """)
            accept_btn.clicked.connect(lambda: self.prompt_input.setPlainText(text.strip()))
            layout.addWidget(accept_btn)

            frame.setLayout(layout)
            scroll_layout.addWidget(frame)


        # === Добавляем блоки ===

        # 1. Улучшенный промт
        add_block("🎯 Улучшенный промт", result["enhanced"])

        # 2. Каждый вариант — отдельно
        for i, variant in enumerate(result["variants"], 1):
            add_block(f"🔄 Вариант {i}", variant)

        # 3. Адаптации
        adapted = result["adapted"]
        if "Анализ" in adapted:
            add_block("🔹 Адаптация: Анализ", adapted["Анализ"])
        if "Код" in adapted:
            add_block("💻 Адаптация: Код", adapted["Код"])
        if "Креатив" in adapted:
            add_block("🎨 Адаптация: Креатив", adapted["Креатив"])

        # ===

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # Кнопка "Закрыть" — внизу
        close_btn = QPushButton("❌ Закрыть")
        close_btn.clicked.connect(dialog.reject)
        main_layout.addWidget(close_btn)

        dialog.setLayout(main_layout)
        dialog.exec()

    def parse_enhancement_response(self, text: str):
        """Разбирает ответ от AI — устойчиво к markdown, форматированию"""
        text = text.strip()
        result = {
            "enhanced": "",
            "variants": [],
            "adapted": {}
        }

        # Удаляем markdown-заголовки, если есть
        text = re.sub(r"^##\s*", "", text, flags=re.MULTILINE)

        lines = text.splitlines()
        current = ""

        for line in lines:
            line = line.strip()

            # Улучшенный промт
            if re.search(r"УЛУЧШЕННЫЙ ПРОМТ", line, re.IGNORECASE):
                current = "enhanced"
                continue

            # Варианты
            if re.search(r"ВАРИАНТЫ", line, re.IGNORECASE):
                current = "variants"
                continue

            # Адаптация
            if re.search(r"АДАПТАЦИЯ", line, re.IGNORECASE):
                current = "adapted"
                continue

            # Обработка контента
            if current == "enhanced" and line and not re.search(r"(ВАРИАНТЫ|АДАПТАЦИЯ)", line, re.IGNORECASE):
                result["enhanced"] += line + "\n"

            elif current == "variants" and re.match(r"\d+\.", line):
                variant_text = re.sub(r"^\d+\.\s*", "", line)
                result["variants"].append(variant_text)

            elif current == "adapted" and "🔹" in line:
                # Убираем **, __ и лишние символы
                line = re.sub(r"[*_]{2}", "", line)
                if ":" in line:
                    k, v = line.split(":", 1)
                    clean_key = k.strip("🔹 ").strip()
                    clean_value = v.strip()  # ✅ Сначала создаём переменную
                    if "анализ" in clean_key.lower():
                        result["adapted"]["Анализ"] = clean_value
                        print(f"[PARSER] Анализ: тип={type(clean_value)}, значение={repr(clean_value)}")
                    elif "код" in clean_key.lower():
                        result["adapted"]["Код"] = clean_value
                        print(f"[PARSER] Код: тип={type(clean_value)}, значение={repr(clean_value)}")
                    elif "креатив" in clean_key.lower():
                        result["adapted"]["Креатив"] = clean_value
                        print(f"[PARSER] Креатив: тип={type(clean_value)}, значение={repr(clean_value)}")

            # Продолжение предыдущего блока (если нет ключа, но в режиме adapted)
            elif current == "adapted" and result["adapted"] and line:
                last_key = list(result["adapted"].keys())[-1]
                result["adapted"][last_key] += "\n" + line

        result["enhanced"] = result["enhanced"].strip()
        print("🔍 Доступные адаптации:", list(result["adapted"].keys()))
        return result

    def use_variant_from_list(self, variants: list, callback):
        """Показывает список вариантов для выбора"""
        items = [f"{i+1}. {v[:100]}..." if len(v) > 100 else f"{i+1}. {v}" for i, v in enumerate(variants)]
        item, ok = QInputDialog.getItem(
            self,
            "Выберите вариант",
            "Использовать:",
            items,
            0,
            False
        )
        if ok and item:
            # Извлекаем текст (убираем номер)
            selected_text = variants[items.index(item)]
            callback(selected_text)

    def extract_enhanced(self, text: str) -> str:
        """Извлекает текст после 'УЛУЧШЕННЫЙ ПРОМТ:'"""
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if "УЛУЧШЕННЫЙ ПРОМТ:" in line:
                return "\n".join(lines[i+1:]).strip().split("ВАРИАНТЫ:")[0].strip()
        return text.strip()
    
    def show_wait_cursor(self):
        """Показывает курсор ожидания"""
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

    def restore_cursor(self):
        """Восстанавливает курсор"""
        QApplication.restoreOverrideCursor()


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
                    label.setStyleSheet(get_label_style())

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
            label.setStyleSheet(get_label_style())

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
        # 🔹 Объявляем переменные
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

        # 🔹 Теперь безопасно создаём html
        html = f'''<!DOCTYPE html>
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
            <p><strong>Версия:</strong> {__version__}</p>
            <hr class="divider">
    '''

        # Добавляем ответы
        for model_name, response in responses:
            response_escaped = (
                response
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\n", "<br>")
            )
            html += f'''
            <h2>{model_name}</h2>
            <blockquote>
                {response_escaped}
            </blockquote>
            <hr class="divider">
    '''

        # Завершение HTML
        html += f'''
            <div class="footer">
                Экспорт сгенерирован ChatList • <a href="https://github.com/fedorkrs33-web/ChatList" style="color: {accent}; text-decoration: none;">GitHub</a>
            </div>
        </div>
    </body>
    </html>
    '''

        return html


        
     #============= ВКЛАДКА 3: МОДЕЛИ =============

    def create_models_tab(self):
        """Создаёт вкладку 'Модели'"""
        models_layout = QVBoxLayout()
        self.tab_models = QWidget()
        self.tab_models.setLayout(models_layout)

        # Таблица моделей
        self.models_table = QTableWidget()
        self.models_table.setSortingEnabled(True)  # ✅ сортировка
        self.models_table.setColumnCount(7)
        self.models_table.setHorizontalHeaderLabels(["ID", "Имя", "API URL", "Модель", "Провайдер", "Активна", "Управление"])
        header = self.models_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Имя
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # API URL
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Модель 
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Провайдер
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)             # Активна
        self.models_table.setColumnWidth(5, 60)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Управление                                  
        models_layout.addWidget(self.models_table)

        # Кнопки
        btn_layout = QHBoxLayout()

        # Кнопка "Редактировать"
        self.edit_models_btn = QPushButton("✒ Редактировать")
        self.edit_models_btn.clicked.connect(self.open_models_editor)
        btn_layout.addWidget(self.edit_models_btn)
        
        btn_layout.addStretch()
        models_layout.addLayout(btn_layout)

        return self.tab_models
    
    def open_models_editor(self):
        """Открывает редактор моделей"""
        from models import ModelsManager
        editor = ModelsManager(db=self.db, parent=self)  # ✅ Передаём self.db
        editor.open_editor()
    
    def load_models(self):
        """Загружает все модели из БД через self.db"""
        try:
            models = self.db.get_all_models()  # ✅ Должен быть в db.py
            self.models_table.setRowCount(0)
            for model in models:
                row = self.models_table.rowCount()
                self.models_table.insertRow(row)
                self.models_table.setItem(row, 0, QTableWidgetItem(str(model["id"])))
                self.models_table.setItem(row, 1, QTableWidgetItem(model["name"]))
                self.models_table.setItem(row, 2, QTableWidgetItem(model["api_url"]))
                self.models_table.setItem(row, 3, QTableWidgetItem(model["model_name"]))
                self.models_table.setItem(row, 4, QTableWidgetItem(model["provider"]))

                active_text = "Да" if model["is_active"] else "Нет"
                active_item = QTableWidgetItem(active_text)
                active_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.models_table.setItem(row, 5, active_item)

                # Управление — заглушка
                self.models_table.setItem(row, 6, QTableWidgetItem("..."))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить модели из БД:\n{e}")


    def update_model_field(self, model_id: int, field: str, value: str):
        """Обновляет поле модели в БД"""
        try:
            # Обновляем в БД
            Model.update_field(model_id, field, value)
            # Обновляем статус
            self.statusBar().showMessage(f"✅ Поле '{field}' модели обновлено", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить поле:\n{str(e)}")


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
        prompts = self.db.get_all_prompts()

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
        """Загружает и отображает Markdown-предпросмотр с поддержкой форматирования"""
        result_id = int(self.preview_table.item(row, 0).text())
        prompt = self.preview_table.item(row, 1).text()

        responses = self.db.get_responses_by_result_id(result_id)
        if not responses:
            self.preview_text.setHtml("<p><i>Нет данных</i></p>")
            return

        # Формируем Markdown
        md_lines = []
        md_lines.append(f"# {prompt.strip()}")
        md_lines.append(f"*Дата: {responses[0]['saved_at']}*")
        md_lines.append("")  # Пустая строка

        for r in responses:
            md_lines.append(f"## {r['model_name']}")
            response_text = r['response'].strip()
            # Экранируем, чтобы не сломать Markdown
            lines = response_text.splitlines()
            for line in lines:
                if line.strip() == '':
                    md_lines.append("")  # Пустая строка
                else:
                    md_lines.append(f"> {line}")
            md_lines.append("")  # Отступ между моделями

        # 🔥 Здесь определяем md_text
        md_text = "\n".join(md_lines)

        # Используем библиотеку markdown
        import markdown
        html = markdown.markdown(md_text, extensions=[
            'fenced_code',
            'tables',
            'codehilite'  # ← подсветка синтаксиса
        ])

        # Добавляем стили и обёртку
        theme = self.db.get_setting("theme", "light")
        
        if theme == "dark":
            bg = "#2b2b2b"
            text = "#ffffff"
            code_bg = "#1e1e1e"
            code_color = "#dcdcdc"
            blockquote_bg = "#3c3c3c"
            blockquote_border = "#007acc"
            heading = "#00aaff"
            link = "#64b5f6"
        else:
            bg = "#ffffff"
            text = "#333333"
            code_bg = "#f5f5f5"
            code_color = "#000000"
            blockquote_bg = "#f9f9f9"
            blockquote_border = "#ccc"
            heading = "#007acc"
            link = "#1976d2"

        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body, html {{
                    margin: 0;
                    padding: 20px;
                    background: {bg};
                    color: {text};
                    font-family: 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    font-size: 14px;
                }}
                h1, h2, h3 {{
                    color: {heading};
                    border-bottom: 1px solid {blockquote_border};
                    padding-bottom: 5px;
                }}
                a {{
                    color: {link};
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                code {{
                    font-family: 'Consolas', 'Courier New', monospace;
                    background: {code_bg};
                    color: {code_color};
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 0.9em;
                }}
                pre {{
                    background: {code_bg};
                    color: {code_color};
                    padding: 15px;
                    border-radius: 6px;
                    overflow: auto;
                    margin: 10px 0;
                    border: 1px solid {blockquote_border};
                }}
                pre code {{
                    background: none;
                    color: inherit;
                    padding: 0;
                    font-size: inherit;
                }}
                blockquote {{
                    background: {blockquote_bg};
                    border-left: 4px solid {blockquote_border};
                    margin: 15px 0;
                    padding: 12px 15px;
                    font-style: italic;
                    border-radius: 0 4px 4px 0;
                }}
                ul, ol {{
                    margin: 10px 0;
                    padding-left: 25px;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 15px 0;
                }}
                table th, table td {{
                    border: 1px solid {blockquote_border};
                    padding: 8px;
                    text-align: left;
                }}
                table th {{
                    background: {blockquote_bg};
                    color: {heading};
                }}
            </style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """
        self.preview_text.setHtml(styled_html)

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


    def load_prompts(self):
        """Загружает все промты в таблицу"""
        self.prompts_table.setRowCount(0)
        prompts = self.db.get_all_prompts()

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
            QMessageBox.warning(self, "Внимание", "Введите промт!")
            return

        # Сохраняем промт в БД
        prompt_id = self.db.save_prompt(prompt)

        # Очищаем предыдущие результаты
        self.clear_results()

        # Получаем активные модели
        models = self.db.get_active_models()
        if not models:
            QMessageBox.warning(self, "Ошибка", "Нет активных моделей. Проверьте настройки.")
            return

        # Отправляем во все модели
        self.results_table.setRowCount(len(models))
        self.temp_results.clear()

        for row_idx, model in enumerate(models):
            response = Network.send_prompt_to_model(model, prompt)

            print(f"[DEBUG] {model["name"]}: response={repr(response[:100] if response else None)}")

            # Нормализуем ответ
            if not response or not response.strip():
                response = f"[Ошибка] Пустой ответ от {model["name"]}"
            else:
                response = response.strip()

            # Устанавливаем имя модели
            item = QTableWidgetItem(model["name"])
            item.setTextAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            self.results_table.setItem(row_idx, 0, item)
            # Создаём QLabel
            label = QLabel(response)
            label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            label.setStyleSheet(get_label_style())
            
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

            self.temp_results[row_idx] = (model["id"], response, checkbox)

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

#============= ВКЛАДКА 5: Настройки =============
    def create_settings_tab(self):
        """Создаёт вкладку 'Настройки'"""
        tab = QWidget()
        layout = QVBoxLayout()

        # Заголовок
        title = QLabel("Настройки приложения")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Таблица настроек
        self.settings_table = QTableWidget()
        self.settings_table.setColumnCount(2)
        self.settings_table.setRowCount(2)
        self.settings_table.setHorizontalHeaderLabels(["Параметр", "Значение"])
        self.settings_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.settings_table.verticalHeader().setVisible(False)
        self.settings_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Только через виджеты

        # 1. Тема
        theme_label = QTableWidgetItem("Тема")
        theme_label.setFlags(theme_label.flags() ^ Qt.ItemFlag.ItemIsEditable)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        self.theme_combo.setCurrentText(self.db.get_setting("theme", "light"))
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)

        self.settings_table.setItem(0, 0, theme_label)
        self.settings_table.setCellWidget(0, 1, self.theme_combo)

        # 2. Размер шрифта
        font_label = QTableWidgetItem("Размер шрифта")
        font_label.setFlags(font_label.flags() ^ Qt.ItemFlag.ItemIsEditable)
        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 20)
        self.font_spin.setValue(int(self.db.get_setting("font_size", 12)))
        self.font_spin.valueChanged.connect(self.on_font_size_changed)

        self.settings_table.setItem(1, 0, font_label)
        self.settings_table.setCellWidget(1, 1, self.font_spin)

        layout.addWidget(self.settings_table)
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def on_theme_changed(self, theme: str):
        """Смена темы"""
        self.db.set_setting("theme", theme)
        apply_theme(self, theme)

    def on_font_size_changed(self, size: int):
        """Изменение размера шрифта"""
        self.db.set_setting("font_size", str(size))
        self.apply_font_size(size)

    def apply_font_size(self, size: int):
        """Применяет шрифт ко всему приложению"""
        font = get_font(size)
        self.setFont(font)
        
        for widget in self.findChildren(QWidget):
            widget.setFont(font)

#============= ВКЛАДКА 6: Справка =============
    def create_help_tab(self):
        """Создаёт вкладку 'Справка'"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Заголовок
        title = QLabel("ChatList")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #007acc; margin: 10px 0;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Версия
        version = QLabel(f"Версия {__version__}")
        version.setStyleSheet("font-size: 14px; color: #666; margin-bottom: 20px;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        # Описание
        description = QLabel(
            "ChatList — это приложение для сравнения ответов различных AI-моделей.\n"
            "Вы можете:\n"
            "• Писать промты и отправлять их в несколько моделей одновременно\n"
            "• Сравнивать ответы\n"
            "• Сохранять результаты\n"
            "• Экспортировать в Markdown и HTML\n"
            "• Улучшать промты с помощью AI-ассистента"
        )
        description.setWordWrap(True)
        description.setStyleSheet("font-size: 14px; margin: 10px 0; color: #555;")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description)

        # Логотип (если есть app.ico или logo.png)
        if os.path.exists("app.ico") or os.path.exists("logo.png"):
            icon_path = "app.ico" if os.path.exists("app.ico") else "logo.png"
            try:
                logo = QLabel()
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    logo.setPixmap(pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio))
                    logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    layout.addWidget(logo)
            except:
                pass  # Если не удалось загрузить — пропустим

        # Ссылка на GitHub
        link = QLabel('<a href="https://github.com/fedorkrs33-web/ChatList" style="color: #007acc; text-decoration: none;">GitHub</a>')
        link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        link.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        link.setOpenExternalLinks(True)
        layout.addWidget(link)

        # Информация о лицензии
        license_label = QLabel("Лицензия: MIT")
        license_label.setStyleSheet("font-size: 12px; color: #999; margin-top: 30px;")
        license_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(license_label)

        # Растяжка
        layout.addStretch()

        return tab

# ============= ЗАПУСК ПРИЛОЖЕНИЯ =============
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatListApp()
    window.show()
    sys.exit(app.exec())

