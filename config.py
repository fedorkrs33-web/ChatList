# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    @staticmethod
    def get_api_key(key_var: str) -> str:
        key = os.getenv(key_var)
        if not key:
            raise ValueError(f"API-ключ не найден: {key_var}. Проверьте файл .env")
        return key

    # 🔹 Новые методы для GigaChat
    @staticmethod
    def get_gigachat_credentials():
        client_id = os.getenv("GIGACHAT_CLIENT_ID")
        client_secret = os.getenv("GIGACHAT_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise ValueError("GIGACHAT_CLIENT_ID или GIGACHAT_CLIENT_SECRET не найден в .env")
        return client_id, client_secret

    @staticmethod
    def get_yandex_credentials():
        """Возвращает IAM-токен и Folder ID для Yandex GPT"""
        iam_token = os.getenv("YANDEX_IAM_TOKEN")
        folder_id = os.getenv("YANDEX_FOLDER_ID")
    
        if not iam_token:
            raise ValueError("YANDEX_IAM_TOKEN не найден в .env")
        if not folder_id:
            raise ValueError("YANDEX_FOLDER_ID не найден в .env")
        
        return iam_token, folder_id

    @staticmethod
    def ensure_env_file():
        if not os.path.exists(".env"):
            with open(".env", "w", encoding="utf-8") as f:
                f.write(
                    "# API-ключи для нейросетей\n"
                    "OPENAI_API_KEY=sk-...\n"
                    "ANTHROPIC_API_KEY=...\n"
                    "DEEPSEEK_API_KEY=...\n"
                    "GROQ_API_KEY=...\n"
                    "\n# GigaChat — от Сбера\n"
                    "GIGACHAT_CLIENT_ID=ваш_id\n"
                    "GIGACHAT_CLIENT_SECRET=ваш_secret\n"
                )
            print("✅ Создан файл .env (заполните API-ключи)")
