# db.py
import sqlite3
import os
from datetime import datetime
from typing import List, Tuple, Optional

# Путь к базе данных
DB_PATH = "chatlist.db"

# SQL-запросы создания таблиц
CREATE_PROMPTS_TABLE = """
CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    prompt TEXT NOT NULL,
    tags TEXT
);
"""

CREATE_MODELS_TABLE = """
CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    api_url TEXT NOT NULL,
    api_key_var TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    provider TEXT,
    model_name TEXT
);
"""

CREATE_RESULTS_TABLE = """
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id INTEGER NOT NULL,
    model_id INTEGER NOT NULL,
    response TEXT NOT NULL,
    saved_at TEXT NOT NULL,
    FOREIGN KEY (prompt_id) REFERENCES prompts (id),
    FOREIGN KEY (model_id) REFERENCES models (id)
);
"""

CREATE_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""

# Начальные данные для моделей (можно расширить)
INITIAL_MODELS = [
    ("DeepSeek", "https://api.deepseek.com/v1/chat/completions", "DEEPSEEK_API_KEY", 1, "deepseek", "deepseek-chat"),
    ("GigaChat", "", "GIGACHAT", 1, "gigachat", "GigaChat"),
    ("Yandex GPT", "https://d5dsop9op9ghv14u968d.hsvi2zuh.apigw.yandexcloud.net", "YANDEX_OAUTH_TOKEN", 1, "yandex", "yandexgpt/latest"),
    ("OpenRouter", "https://openrouter.ai/api/v1/chat/completions", "OPENROUTER_API_KEY", 1, "openrouter", "openrouter/avto"),
]


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()

    @staticmethod
    def _dict_factory(cursor, row):
        """Превращает sqlite3.Row в словарь"""
        return dict(zip([col[0] for col in cursor.description], row))
    
    def get_connection(self):
        """Создаёт соединение с БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = self._dict_factory
        return conn

    def init_db(self):
        """Инициализирует БД: создаёт таблицы и добавляет начальные данные"""
        with self.get_connection() as conn:
            # Создаём таблицы
            conn.execute(CREATE_PROMPTS_TABLE)
            conn.execute(CREATE_MODELS_TABLE)
            conn.execute(CREATE_RESULTS_TABLE)
            conn.execute(CREATE_SETTINGS_TABLE)
            conn.commit()

            # Подсчёт моделей
            conn.row_factory = None
            cursor = conn.execute("SELECT COUNT(*) FROM models")
            count = cursor.fetchone()[0]
            conn.row_factory = self._dict_factory  # Возвращаем dict

            if count == 0:
                conn.executemany(
                    "INSERT INTO models (name, api_url, api_key_var, is_active, provider, model_name) VALUES (?, ?, ?, ?, ?, ?)",
                    INITIAL_MODELS
                )
                conn.commit()
    # === Методы для prompts ===
    def save_prompt(self, prompt: str, tags: str = "") -> int:
        """Сохраняет промт и возвращает его ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO prompts (created_at, prompt, tags) VALUES (?, ?, ?)",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), prompt, tags)
            )
            conn.commit()
            return cursor.lastrowid

    def get_all_prompts(self) -> List[Tuple]:
        """Возвращает все промты (id, created_at, prompt, tags)"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT id, created_at, prompt, tags FROM prompts ORDER BY created_at DESC")
            return cursor.fetchall()

    def search_prompts(self, query: str) -> List[Tuple]:
        """Поиск промтов по тексту или тегам"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, created_at, prompt, tags FROM prompts WHERE prompt LIKE ? OR tags LIKE ? ORDER BY created_at DESC",
                (f"%{query}%", f"%{query}%")
            )
            return cursor.fetchall()

    # === Методы для results ===
    def get_all_saved_results(self):
        """Возвращает все сохранённые результаты с промтами и именами моделей"""
        query = """
            SELECT 
                p.prompt,
                m.name as model_name,
                r.response,
                r.saved_at
            FROM results r
            JOIN prompts p ON r.prompt_id = p.id
            JOIN models m ON r.model_id = m.id
            ORDER BY r.saved_at DESC
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query)
                return cursor.fetchall()
        except Exception as e:
            print(f"[DB] Ошибка при загрузке результатов: {e}")
            return []

    # === Методы для models ===
    def get_active_models(self) -> List[Tuple]:
        """Возвращает все активные модели"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, name, api_url, api_key_var, provider, model_name FROM models WHERE is_active = 1 ORDER BY name"
            )
            return cursor.fetchall()

    def get_all_models(self) -> List[Tuple]:
        """Возвращает все модели (для настройки)"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM models ORDER BY name")
            return cursor.fetchall()

    def update_model_status(self, model_id: int, is_active: bool):
        """Включает/выключает модель"""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE models SET is_active = ? WHERE id = ?",
                (1 if is_active else 0, model_id)
            )
            conn.commit()

    def delete_prompt(self, prompt_id: int):
        """Удаляет промт и все связанные результаты"""
        with self.get_connection() as conn:
            # Удаляем сначала результаты (из-за внешнего ключа)
            conn.execute("DELETE FROM results WHERE prompt_id = ?", (prompt_id,))
            # Затем промт
            conn.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
            conn.commit()

    # === Методы для results ===
    def save_result(self, prompt_id: int, model_id: int, response: str):
        """Сохраняет результат"""
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO results (prompt_id, model_id, response, saved_at) VALUES (?, ?, ?, ?)",
                (prompt_id, model_id, response, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit()

    def get_results_by_prompt(self, prompt_id: int) -> List[Tuple]:
        """Получает все сохранённые результаты для промта"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT m.name, r.response, r.saved_at 
                   FROM results r
                   JOIN models m ON r.model_id = m.id
                   WHERE r.prompt_id = ?
                   ORDER BY r.saved_at""",
                (prompt_id,)
            )
            return cursor.fetchall()

    # === Методы для settings ===
    def set_setting(self, key: str, value: str):
        """Сохраняет настройку"""
        with self.get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
            conn.commit()

    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Получает настройку"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default
    def get_saved_results_with_models(self):
        """Возвращает список сохранённых результатов с промтами и моделями"""
        query = """
        SELECT 
            r.id,
            p.prompt,
            GROUP_CONCAT(m.name, ', ') as models,
            r.saved_at
        FROM results r
        JOIN prompts p ON r.prompt_id = p.id
        JOIN models m ON r.model_id = m.id
        GROUP BY r.id, p.prompt, r.saved_at
        ORDER BY r.saved_at DESC
        """
        with self.get_connection() as conn:
            conn.row_factory = self._dict_factory
            return conn.execute(query).fetchall()

    def get_responses_by_result_id(self, result_id: int):
        """Получает все ответы для одного сохранённого результата"""
        query = """
        SELECT 
            r.response,
            m.name as model_name,
            r.saved_at
        FROM results r
        JOIN models m ON r.model_id = m.id
        WHERE r.id = ?
        ORDER BY m.name
        """
        with self.get_connection() as conn:
            conn.row_factory = self._dict_factory
            return conn.execute(query, (result_id,)).fetchall()



# Глобальный экземпляр БД (можно импортировать в других модулях)
db = Database()
