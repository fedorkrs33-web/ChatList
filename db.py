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
    prompt TEXT,
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
    theme TEXT,
    value TEXT
);
"""

# Начальные данные для моделей
INITIAL_MODELS = [
    ("1", "DeepSeek", "https://api.polza.ai/v1/chat/completions", "POLZA_API_KEY", 1, "Polza", "deepseek-v3.2"),
    ("2", "Anthropic", "https://api.polza.ai/v1/chat/completions", "POLZA_API_KEY", 1, "Polza", "claude-3-haiku"),
    ("3", "GigaChat", "", "GIGACHAT", 1, "gigachat", "GigaChat"),
    ("4", "Yandex GPT", "https://d5dsop9op9ghv14u968d.hsvi2zuh.apigw.yandexcloud.net", "YANDEX_OAUTH_TOKEN", 1, "yandex", "yandexgpt/latest"),
    ("5", "OpenRouter", "https://openrouter.ai/api/v1/chat/completions", "OPENROUTER_API_KEY", 1, "openrouter", "openrouter/avto"),
]


class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.init_db()

    @staticmethod
    def _dict_factory(cursor, row):
        """Превращает sqlite3.Row в словарь"""
        return dict(zip([col[0] for col in cursor.description], row))

    def init_db(self):
        """Инициализирует БД: создаёт таблицы и добавляет начальные данные"""
        try:
            # Создаём соединение
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # чтобы можно было обращаться по имени
            print(f"[DB] Подключено к {self.db_path}")

            # Создаём все таблицы
            self._create_tables()

            # Добавляем стандартные модели, если таблица пуста
            self.init_default_models()

        except Exception as e:
            print(f"[DB] Ошибка инициализации БД: {e}")
            raise

    def _create_tables(self):
        """Создаёт таблицы, если не существуют"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(CREATE_PROMPTS_TABLE)
            cursor.execute(CREATE_MODELS_TABLE)
            cursor.execute(CREATE_RESULTS_TABLE)
            cursor.execute(CREATE_SETTINGS_TABLE)
            self.conn.commit() 
            print("[DB] Таблицы проверены/созданы")
        except Exception as e:
            print(f"[DB] Ошибка создания таблиц: {e}")
            raise

    def init_default_models(self):
        """Добавляет стандартные модели, если таблица пуста"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM models")
            count = cursor.fetchone()[0]

            if count == 0:
                cursor.executemany("""
                    INSERT INTO models (id, name, api_url, api_key_var, is_active, provider, model_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, INITIAL_MODELS)

                self.conn.commit()
                print("[DB] Добавлены стандартные модели")
            else:
                print(f"[DB] Уже есть {count} моделей — стандартные не добавлены")

        except Exception as e:
            print(f"[DB] Ошибка при добавлении стандартных моделей: {e}")

    def get_model_by_id(self, model_id):
        """Полная модель — с api_key — только для отправки запроса"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, name, api_url, api_key_var, is_active, provider, model_name
                FROM models WHERE id = ?
            """, (model_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "api_url": row[2],
                    "api_key_var": row[3],
                    "is_active": row[4],
                    "provider": row[5],
                    "model_name": row[6]
                }
            return None
        except Exception as e:
            print(f"[DB] Ошибка поиска модели: {e}")
            return None

    # === Методы для prompts ===
    def save_prompt(self, prompt: str, tags: str = "") -> int:
        """Сохраняет промт и возвращает его ID"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO prompts (created_at, prompt, tags) VALUES (?, ?, ?)",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), prompt, tags)
            )
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"[DB] Ошибка сохранения промта: {e}")
            return -1

    def get_all_prompts(self) -> List[Tuple]:
        """Возвращает все промпты как список словарей"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, created_at, prompt, tags FROM prompts ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]  # ✅ Преобразуем Row → dict
        except Exception as e:
            print(f"[DB] Ошибка загрузки промтов: {e}")
            return []

    def search_prompts(self, query: str) -> List[Tuple]:
        """Поиск промтов по тексту или тегам"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id, created_at, prompt, tags FROM prompts WHERE prompt LIKE ? OR tags LIKE ? ORDER BY created_at DESC",
                (f"%{query}%", f"%{query}%")
            )
            return cursor.fetchall()
        except Exception as e:
            print(f"[DB] Ошибка поиска промтов: {e}")
            return []

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
            cursor = self.conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"[DB] Ошибка при загрузке результатов: {e}")
            return []

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
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"[DB] Ошибка: {e}")
            return []

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
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, (result_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[DB] Ошибка: {e}")
            return []

    # === Методы для models ===
    def save_models(self, models: list):
        """Полностью заменяет таблицу моделей (или обновляет)"""
        try:
            cursor = self.conn.cursor()
            # Удаляем старые (или можно обновлять по ID — зависит от логики)
            # ВАЖНО: если модели используются в results — удаление сломает связи!
            # Альтернатива: UPDATE + INSERT

            # Простой вариант: очищаем и вставляем заново
            cursor.execute("DELETE FROM models")
            for model in models:
                cursor.execute("""
                    INSERT INTO models (id, name, api_url, api_key_var, is_active, provider, model_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    model["id"],
                    model["name"],
                    model["api_url"],
                    model["api_key_var"],
                    int(model["is_active"]),
                    model["provider"],
                    model["model_name"]
                ))
            self.conn.commit()
            print(f"[DB] Сохранено {len(models)} моделей")
        except Exception as e:
            print(f"[DB] Ошибка сохранения моделей: {e}")
            raise

    def get_active_models(self):
        query = "SELECT * FROM models WHERE is_active = 1 ORDER BY id"
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"[DB] Ошибка: {e}")
            return []

    def get_all_models(self):
        """Возвращает все модели из таблицы models"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, name, api_url, api_key_var, is_active, provider, model_name
                FROM models
                ORDER BY id
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"[DB] Ошибка загрузки моделей: {e}")
            return []

    def update_model_status(self, model_id: int, is_active: bool):
        """Включает/выключает модель"""
        cursor = self.conn.cursor()  # ✅
        cursor.execute(
            "UPDATE models SET is_active = ? WHERE id = ?",
            (int(is_active), model_id)
        )
        self.conn.commit()

    def delete_prompt(self, prompt_id: int):
        """Удаляет промт и все связанные результаты"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM results WHERE prompt_id = ?", (prompt_id,))
            cursor.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
            self.conn.commit()
        except Exception as e:
            print(f"[DB] Ошибка удаления промта: {e}")

    # === Методы для results ===
    def save_result(self, prompt_id: int, model_id: int, response: str):
        """Сохраняет результат"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO results (prompt_id, model_id, response, saved_at) VALUES (?, ?, ?, ?)",
                (prompt_id, model_id, response, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            self.conn.commit()
        except Exception as e:
            print(f"[DB] Ошибка сохранения результата: {e}")

    def get_results_by_prompt(self, prompt_id: int) -> List[Tuple]:
        """Получает все сохранённые результаты для промта"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT m.name, r.response, r.saved_at 
                   FROM results r
                   JOIN models m ON r.model_id = m.id
                   WHERE r.prompt_id = ?
                   ORDER BY r.saved_at""",
                (prompt_id,)
            )
            return cursor.fetchall()
        except Exception as e:
            print(f"[DB] Ошибка: {e}")
            return []

    # === Методы для settings ===
    def get_setting(self, key: str, default: str = None) -> str:
        """Получает настройку по ключу"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default
        except Exception as e:
            print(f"[DB] Ошибка чтения настройки {key}: {e}")
            return default

    def set_setting(self, key: str, value: str):
        """Сохраняет настройку"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO settings (key, value)
                VALUES (?, ?)
            """, (key, value))
            self.conn.commit()
        except Exception as e:
            print(f"[DB] Ошибка сохранения настройки: {e}")
