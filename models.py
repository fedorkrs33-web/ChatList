# models.py
from typing import List, Dict
from db import db


class Model:
    """
    Класс для работы с нейросетевыми моделями.
    Поля: id, name, api_url, api_key_var, is_active, provider, model_name
    """
    def __init__(self, id: int, name: str, api_url: str, api_key_var: str, is_active: bool, provider: str = None, model_name=None):
        self.id = id
        self.name = name
        self.api_url = api_url
        self.api_key_var = api_key_var
        self.is_active = is_active
        self.provider = provider
        self.model_name = model_name or ""  # ← гарантируем строку

    @staticmethod
    def load_all() -> List['Model']:
        """
        Загружает все модели из БД
        """
        rows = db.get_all_models()
        return [
            Model(
                id=row["id"],
                name=row["name"],
                api_url=row["api_url"],
                api_key_var=row["api_key_var"],
                is_active=bool(row["is_active"]),
                provider=row["provider"],
                model_name=row["model_name"]
            )
            for row in rows
        ]

    @staticmethod
    def get_active() -> List['Model']:
        """
        Возвращает только активные модели
        """
        rows = db.get_active_models()  # Уже возвращает dict
        return [
            Model(
                id=row["id"],
                name=row["name"],
                api_url=row["api_url"],
                api_key_var=row["api_key_var"],
                is_active=True,
                provider=row["provider"],
                model_name=row["model_name"]
            )
            for row in rows
        ]

    @classmethod
    def update_field(cls, model_id: int, field: str, value: str):
        """Обновляет одно поле модели"""
        allowed_fields = {"name", "api_url", "model_name", "provider", "api_key_var", "is_active"}
        if field not in allowed_fields:
            raise ValueError(f"Нельзя обновить поле: {field}")

        query = f"UPDATE models SET {field} = ? WHERE id = ?"
        with db.get_connection() as conn:
            conn.execute(query, (value, model_id))
            conn.commit()

    @staticmethod
    def update_status(model_id: int, is_active: bool):
        """
        Включает или выключает модель
        """
        db.update_model_status(model_id, is_active)

    def save(self):
        """
        Сохраняет модель в БД (для новых моделей — можно расширить)
        Пока не используется, так как модели управляются через DB.
        """
        # Можно реализовать INSERT/UPDATE при необходимости
        raise NotImplementedError("Сохранение новой модели не реализовано в этом этапе")

    def __repr__(self):
        return f"<Model id={self.id} name='{self.name}' active={self.is_active} provider='{self.provider}'>"
