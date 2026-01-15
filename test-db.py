# test-db.py
import sys
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel,
    QFileDialog, QMessageBox, QComboBox, QHeaderView, QAbstractItemView,
    QDialog, QFormLayout, QLineEdit, QInputDialog
)
from PyQt6.QtCore import Qt


class DatabaseViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SQLite Инспектор — Просмотр базы данных")
        self.resize(1000, 600)

        self.connection = None
        self.current_table = ""
        self.current_page = 0
        self.rows_per_page = 20
        self.total_rows = 0
        self.primary_key = None

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # ============ ВЕРХНЯЯ ПАНЕЛЬ ============
        top_layout = QHBoxLayout()

        self.file_label = QLabel("Файл не выбран")
        top_layout.addWidget(self.file_label)

        self.btn_open_file = QPushButton("📂 Выбрать SQLite файл")
        self.btn_open_file.clicked.connect(self.open_database)
        top_layout.addWidget(self.btn_open_file)

        layout.addLayout(top_layout)

        # ============ ВЫБОР ТАБЛИЦЫ ============
        table_layout = QHBoxLayout()
        table_layout.addWidget(QLabel("Таблица:"))
        self.combo_tables = QComboBox()
        self.combo_tables.setEnabled(False)
        table_layout.addWidget(self.combo_tables)

        self.btn_load_table = QPushButton("🔍 Открыть")
        self.btn_load_table.clicked.connect(self.load_table_data)
        self.btn_load_table.setEnabled(False)
        table_layout.addWidget(self.btn_load_table)

        layout.addLayout(table_layout)

        # ============ ТАБЛИЦА ============
        self.table_widget = QTableWidget()
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table_widget)

        # ============ ПАГИНАЦИЯ ============
        pagination_layout = QHBoxLayout()
        self.btn_prev = QPushButton("◀ Назад")
        self.btn_prev.clicked.connect(self.prev_page)
        self.btn_prev.setEnabled(False)
        pagination_layout.addWidget(self.btn_prev)

        self.page_label = QLabel("Страница: 0 из 0")
        pagination_layout.addWidget(self.page_label)

        self.btn_next = QPushButton("Вперёд ▶")
        self.btn_next.clicked.connect(self.next_page)
        self.btn_next.setEnabled(False)
        pagination_layout.addWidget(self.btn_next)

        layout.addLayout(pagination_layout)

        # ============ КНОПКИ CRUD ============
        crud_layout = QHBoxLayout()
        self.btn_create = QPushButton("➕ Создать")
        self.btn_create.clicked.connect(self.create_record)
        self.btn_create.setEnabled(False)
        crud_layout.addWidget(self.btn_create)

        self.btn_edit = QPushButton("✏️ Редактировать")
        self.btn_edit.clicked.connect(self.edit_record)
        self.btn_edit.setEnabled(False)
        crud_layout.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("🗑️ Удалить")
        self.btn_delete.clicked.connect(self.delete_record)
        self.btn_delete.setEnabled(False)
        crud_layout.addWidget(self.btn_delete)

        self.btn_duplicate = QPushButton("⧉ Копировать как новую")
        self.btn_duplicate.clicked.connect(self.duplicate_record)
        self.btn_duplicate.setEnabled(False)
        crud_layout.addWidget(self.btn_duplicate)

        layout.addLayout(crud_layout)

        # Подключение события выбора строки
        self.table_widget.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def open_database(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите SQLite файл", "", "SQLite Files (*.db *.sqlite *.db3)"
        )
        if not file_path:
            return

        try:
            self.connection = sqlite3.connect(file_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            self.file_label.setText(f"Файл: {file_path}")
            self.load_table_list()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть БД:\n{str(e)}")

    def load_table_list(self):
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            self.combo_tables.clear()
            for table in tables:
                self.combo_tables.addItem(table["name"])
            self.combo_tables.setEnabled(True)
            self.btn_load_table.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить таблицы:\n{str(e)}")

    def load_table_data(self):
        self.current_table = self.combo_tables.currentText()
        # Определяем первичный ключ
        self.find_primary_key()
        self.current_page = 0
        self.refresh_table()

    def find_primary_key(self):
        """Определяем столбец с первичным ключом"""
        cursor = self.connection.cursor()
        cursor.execute(f"PRAGMA table_info({self.current_table})")
        columns = cursor.fetchall()
        for col in columns:
            if col[5] == 1:  # pk=1 означает первичный ключ
                self.primary_key = col[1]
                return
        # Если нет явного PK, используем ROWID
        self.primary_key = "ROWID"

    def refresh_table(self):
        if not self.current_table:
            return

        offset = self.current_page * self.rows_per_page

        try:
            # Получаем общее количество строк
            if self.primary_key == "ROWID":
                count_query = f"SELECT COUNT(*) AS cnt FROM {self.current_table};"
            else:
                count_query = f"SELECT COUNT(*) AS cnt FROM {self.current_table};"
            total = self.connection.execute(count_query).fetchone()["cnt"]
            self.total_rows = total

            # Получаем данные
            columns_query = f"PRAGMA table_info({self.current_table})"
            columns_info = self.connection.execute(columns_query).fetchall()
            columns_names = [col[1] for col in columns_info]

            # Формируем SELECT с ROWID, если нет PK
            if self.primary_key == "ROWID":
                select_cols = "ROWID, *" if self.primary_key not in columns_names else "*"
            else:
                select_cols = "*"

            query = f"SELECT {select_cols} FROM {self.current_table} LIMIT ? OFFSET ?;"
            cursor = self.connection.cursor()
            cursor.execute(query, (self.rows_per_page, offset))
            rows = cursor.fetchall()

            # Заполняем таблицу
            self.table_widget.setRowCount(0)
            if rows:
                # Если используем ROWID, добавляем его как первый столбец
                if self.primary_key == "ROWID" and "ROWID" in rows[0].keys() and rows[0].keys().index("ROWID") == 0:
                    self.table_widget.setColumnCount(len(rows[0]))
                    self.table_widget.setHorizontalHeaderLabels(list(rows[0].keys()))
                else:
                    self.table_widget.setColumnCount(len(rows[0]))
                    self.table_widget.setHorizontalHeaderLabels([self.primary_key] + list(rows[0].keys()) if self.primary_key == "ROWID" else list(rows[0].keys()))

                for row_data in rows:
                    row_idx = self.table_widget.rowCount()
                    self.table_widget.insertRow(row_idx)
                    # Если используем ROWID, он будет в данных
                    for col_idx, value in enumerate(row_data):
                        item = QTableWidgetItem(str(value))
                        item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                        self.table_widget.setItem(row_idx, col_idx, item)

            # Обновляем пагинацию
            total_pages = (self.total_rows + self.rows_per_page - 1) // self.rows_per_page
            current_page_1_indexed = self.current_page + 1

            self.page_label.setText(f"Страница: {current_page_1_indexed} из {total_pages}")
            self.btn_prev.setEnabled(self.current_page > 0)
            self.btn_next.setEnabled((self.current_page + 1) * self.rows_per_page < self.total_rows)

            # Включаем CRUD
            self.btn_create.setEnabled(True)
            self.btn_edit.setEnabled(True)
            self.btn_delete.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных:\n{str(e)}")

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_table()

    def next_page(self):
        if (self.current_page + 1) * self.rows_per_page < self.total_rows:
            self.current_page += 1
            self.refresh_table()

    def on_selection_changed(self):
        selected = self.table_widget.currentRow()
        self.btn_edit.setEnabled(selected >= 0)
        self.btn_delete.setEnabled(selected >= 0)
        self.btn_duplicate.setEnabled(selected >= 0)

    def create_record(self):
        if not self.current_table:
            return

        # Получаем структуру таблицы
        cursor = self.connection.cursor()
        cursor.execute(f"PRAGMA table_info({self.current_table})")
        columns = cursor.fetchall()

        # Создаем диалог ввода
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Создать запись в {self.current_table}")
        layout = QFormLayout()

        inputs = {}
        for col in columns:
            if col[5] == 1:  # PK
                continue
            input_field = QLineEdit()
            layout.addRow(f"{col[1]} ({col[2]})", input_field)
            inputs[col[1]] = input_field

        # Кнопки
        buttons = QHBoxLayout()
        btn_ok = QPushButton("Сохранить")
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(dialog.reject)
        buttons.addWidget(btn_ok)
        buttons.addWidget(btn_cancel)

        layout.addRow(buttons)
        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                # Формируем запрос
                columns_names = []
                placeholders = []
                values = []
                for col in columns:
                    if col[5] == 1:  # Пропускаем PK
                        continue
                    col_name = col[1]
                    col_value = inputs[col_name].text()
                    columns_names.append(col_name)
                    placeholders.append("?")
                    values.append(col_value if col_value else None)

                query = f"INSERT INTO {self.current_table} ({', '.join(columns_names)}) VALUES ({', '.join(placeholders)})"
                cursor = self.connection.cursor()
                cursor.execute(query, values)
                self.connection.commit()

                QMessageBox.information(self, "Успех", "Запись создана!")
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать запись:\n{str(e)}")

    def edit_record(self):
        selected = self.table_widget.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите строку для редактирования.")
            return

        # Получаем значения строки
        row_data = []
        for col in range(self.table_widget.columnCount()):
            item = self.table_widget.item(selected, col)
            row_data.append(item.text() if item else "")

        # Определяем PK значение
        if self.primary_key == "ROWID":
            pk_value = row_data[0]  # ROWID в первом столбце
            start_col = 1
        else:
            # Находим индекс PK
            header_labels = [self.table_widget.horizontalHeaderItem(i).text() for i in range(self.table_widget.columnCount())]
            pk_index = header_labels.index(self.primary_key)
            pk_value = row_data[pk_index]
            start_col = 0

        # Получаем структуру таблицы
        cursor = self.connection.cursor()
        cursor.execute(f"PRAGMA table_info({self.current_table})")
        columns = cursor.fetchall()

        # Создаем диалог редактирования
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Редактировать запись в {self.current_table}")
        layout = QFormLayout()

        inputs = {}
        col_index = 0
        for col in columns:
            if col[5] == 1:  # PK
                continue
            # Находим значение для этого столбца
            if self.primary_key == "ROWID":
                value = row_data[col_index + start_col]
            else:
                header_labels = [self.table_widget.horizontalHeaderItem(i).text() for i in range(self.table_widget.columnCount())]
                try:
                    value_index = header_labels.index(col[1])
                    value = row_data[value_index]
                except ValueError:
                    value = ""
            input_field = QLineEdit(value)
            layout.addRow(f"{col[1]} ({col[2]})", input_field)
            inputs[col[1]] = input_field
            col_index += 1

        # Кнопки
        buttons = QHBoxLayout()
        btn_ok = QPushButton("Сохранить")
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(dialog.reject)
        buttons.addWidget(btn_ok)
        buttons.addWidget(btn_cancel)

        layout.addRow(buttons)
        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                # Формируем запрос
                set_clause = []
                values = []
                for col in columns:
                    if col[5] == 1:  # Пропускаем PK
                        continue
                    col_name = col[1]
                    col_value = inputs[col_name].text()
                    set_clause.append(f"{col_name} = ?")
                    values.append(col_value if col_value else None)
                values.append(pk_value)

                query = f"UPDATE {self.current_table} SET {', '.join(set_clause)} WHERE {self.primary_key} = ?"
                cursor = self.connection.cursor()
                cursor.execute(query, values)
                self.connection.commit()

                QMessageBox.information(self, "Успех", "Запись обновлена!")
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить запись:\n{str(e)}")

    def delete_record(self):
        selected = self.table_widget.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите строку для удаления.")
            return

        # Получаем значение PK
        row_data = []
        for col in range(self.table_widget.columnCount()):
            item = self.table_widget.item(selected, col)
            row_data.append(item.text() if item else "")

        if self.primary_key == "ROWID":
            pk_value = row_data[0]
        else:
            header_labels = [self.table_widget.horizontalHeaderItem(i).text() for i in range(self.table_widget.columnCount())]
            try:
                pk_index = header_labels.index(self.primary_key)
                pk_value = row_data[pk_index]
            except ValueError:
                QMessageBox.critical(self, "Ошибка", "Не удалось найти первичный ключ")
                return

        reply = QMessageBox.question(
            self, "Удалить", f"Вы уверены, что хотите удалить запись с {self.primary_key} = {pk_value}?"
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                query = f"DELETE FROM {self.current_table} WHERE {self.primary_key} = ?"
                cursor = self.connection.cursor()
                cursor.execute(query, (pk_value,))
                self.connection.commit()

                QMessageBox.information(self, "Успех", "Запись удалена!")
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить запись:\n{str(e)}")

    def duplicate_record(self):
        """Копирует выбранную запись как новую (с опциональным новым ID)"""
        selected = self.table_widget.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите строку для копирования.")
            return

        # Получаем данные строки
        row_data = []
        for col in range(self.table_widget.columnCount()):
            item = self.table_widget.item(selected, col)
            row_data.append(item.text() if item else "")

        # Определяем PK
        if self.primary_key == "ROWID":
            pk_index = 0
            pk_value = row_data[0]
        else:
            header_labels = [self.table_widget.horizontalHeaderItem(i).text() for i in range(self.table_widget.columnCount())]
            try:
                pk_index = header_labels.index(self.primary_key)
                pk_value = row_data[pk_index]
            except ValueError:
                QMessageBox.critical(self, "Ошибка", "Не удалось найти столбец с первичным ключом")
                return

        # Получаем структуру таблицы
        cursor = self.connection.cursor()
        cursor.execute(f"PRAGMA table_info({self.current_table})")
        columns = cursor.fetchall()

        # Создаём диалог редактирования
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Копировать запись — {self.current_table}")
        layout = QFormLayout()

        inputs = {}
        col_index = 0
        for col in columns:
            if col[5] == 1:  # PK
                current_value = ""  # Оставим пустым, чтобы пользователь сам ввёл ID
            else:
                value = row_data[col_index + (1 if self.primary_key == "ROWID" else 0)]
                current_value = value

            input_field = QLineEdit(current_value)
            label = f"{col[1]} ({col[2]})"
            if col[5] == 1:  # PK
                label += " (новый ID)"
            layout.addRow(label, input_field)
            inputs[col[1]] = input_field
            col_index += 1

        # Кнопки
        buttons = QHBoxLayout()
        btn_ok = QPushButton("Создать копию")
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(dialog.reject)
        buttons.addWidget(btn_ok)
        buttons.addWidget(btn_cancel)
        layout.addRow(buttons)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                # Собираем данные
                values = []
                columns_names = []
                for col in columns:
                    col_name = col[1]
                    col_value = inputs[col_name].text()

                    # Если это PK и пусто — ставим NULL (автоинкремент)
                    if col[5] == 1:
                        if not col_value.strip():
                            col_value = None  # Позволим автоинкременту сработать
                        else:
                            try:
                                col_value = int(col_value)
                            except ValueError:
                                QMessageBox.warning(self, "Ошибка", f"Значение {col_name} должно быть целым числом")
                                return

                    columns_names.append(col_name)
                    values.append(col_value)

                # Формируем запрос
                placeholders = ["?" for _ in values]
                query = f"INSERT INTO {self.current_table} ({', '.join(columns_names)}) VALUES ({', '.join(placeholders)})"

                cursor = self.connection.cursor()
                cursor.execute(query, values)
                self.connection.commit()

                QMessageBox.information(self, "Успех", "Запись скопирована как новая!")
                self.refresh_table()

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать копию:\n{str(e)}")

    def closeEvent(self, event):
        if self.connection:
            self.connection.close()
        event.accept()


# ============= ЗАПУСК =============
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DatabaseViewer()
    window.show()
    sys.exit(app.exec())
