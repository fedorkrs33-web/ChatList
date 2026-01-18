# models.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QLabel,
    QMessageBox, QHeaderView, QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt

class ModelsManager:
    """Редактор моделей с поддержкой БД"""

    def __init__(self, db, parent=None):
        self.db = db
        self.parent = parent
        self.models = []

    def open_editor(self):
        """Открывает редактор моделей"""
        dialog = QDialog(self.parent)
        dialog.setWindowTitle("Редактировать модели")
        dialog.resize(850, 500)
        layout = QVBoxLayout()

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Имя", "API URL", "Модель", "Провайдер", "Активна", ""])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # URL — растягиваем
        layout.addWidget(self.table)

        # Кнопки
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Добавить")
        del_btn = QPushButton("🗑 Удалить")
        save_btn = QPushButton("✅ Сохранить")

        btn_layout.addStretch()
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        dialog.setLayout(layout)
        self.dialog = dialog

        # Загружаем модели из БД
        self.load_from_db()
        self.refresh_table()

        # Подключаем сигналы
        add_btn.clicked.connect(self.add_model)
        del_btn.clicked.connect(self.delete_model)
        save_btn.clicked.connect(self.save_to_db)

        dialog.exec()

    def load_from_db(self):
        """Загружает модели из БД"""
        try:
            print("[ModelsManager] Загружаю модели из БД...")
            models = self.db.get_all_models()  # ✅ Правильный вызов
            print(f"[ModelsManager] Получено моделей: {len(models)}")
            if models is None:
                models = []
            self.models = models
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self.parent, "Ошибка", f"Не удалось загрузить модели из базы данных:\n{e}")
            self.models = []

    def refresh_table(self):
        """Обновляет таблицу"""
        self.table.setRowCount(0)
        for row, model in enumerate(self.models):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(model["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(model["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(model["api_url"]))
            self.table.setItem(row, 3, QTableWidgetItem(model["model_name"]))
            self.table.setItem(row, 4, QTableWidgetItem(model["provider"]))

            # Активна
            active = QCheckBox()
            active.setChecked(model["is_active"] == 1)
            self.table.setCellWidget(row, 5, active)

            # Управление — пусто (можно добавить кнопки, если нужно)
            # item = QTableWidgetItem("Править")
            # item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            # self.table.setItem(row, 6, item)

    def add_model(self):
        """Добавляет новую пустую модель"""
        new_model = {
            "id": 0,  # будет присвоен при сохранении
            "name": "Новая модель",
            "api_url": "",
            "api_key_var": "",
            "is_active": 1,
            "provider": "custom",
            "model_name": "custom"  
        }
        self.models.append(new_model)
        self.refresh_table()

    def delete_model(self):
        """Удаляет выбранную модель"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self.parent, "Ошибка", "Выберите строку для удаления")
            return
        del self.models[row]
        self.refresh_table()

    def save_to_db(self):
        """Сохраняет все модели в БД"""
        try:
            # Собираем данные из таблицы
            models_to_save = []
            for row in range(self.table.rowCount()):
                try:
                    model_id = int(self.table.item(row, 0).text()) if self.table.item(row, 0) else 0
                    name = self.table.item(row, 1).text().strip()
                    api_url = self.table.item(row, 2).text().strip()
                    api_key_var = self.table.item(row, 3).text().strip()
                    is_active = self.table.cellWidget(row, 4).isChecked()
                    provider = self.table.item(row, 5).text().strip()
                    model_name = self.table.item(row, 6).text().strip()
                    if not name:
                        QMessageBox.warning(self.parent, "Ошибка", f"Имя модели в строке {row + 1} не может быть пустым")
                        return

                    models_to_save.append({
                        "id": model_id,
                        "name": name,
                        "api_url": api_url,
                        "api_key_var": api_key_var,
                        "is_active": is_active,
                        "provider": provider,
                        "model_name": model_name
                    })
                except Exception as e:
                    QMessageBox.critical(self.parent, "Ошибка", f"Ошибка в строке {row + 1}: {e}")
                    return

            # Сохраняем в БД
            self.db.save_models(models_to_save)
            QMessageBox.information(self.parent, "Успех", "Модели сохранены!")
            self.dialog.accept()

            # Опционально: обновить таблицу в основном окне
            if hasattr(self.parent, "refresh_models_table"):
                self.parent.refresh_models_table()

        except Exception as e:
            QMessageBox.critical(self.parent, "Ошибка", f"Не удалось сохранить:\n{e}")
