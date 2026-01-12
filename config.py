# config.py
import os
import json 
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
        """
        Возвращает IAM-токен и Folder ID.
        При необходимости — автоматически обновляет IAM-токен через OAuth.
        """
        import os
        import requests
        from datetime import datetime, timezone

        # Получаем OAuth-токен из .env
        oauth_token = os.getenv("YANDEX_OAUTH_TOKEN")
        if not oauth_token:
            raise ValueError("YANDEX_OAUTH_TOKEN не найден в .env")

        # Путь к кэшу IAM-токена (можно использовать временный файл)
        cache_file = ".yandex_iam_cache.json"

        # Попробуем прочитать закэшированный токен
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                iam_token = cache.get("iam_token")
                expires_at_str = cache.get("expires_at")

                if iam_token and expires_at_str:
                    expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
                    now = datetime.now(timezone.utc)

                    if now < expires_at:
                        print("✅ Используем закэшированный IAM-токен")
                        folder_id = os.getenv("YANDEX_FOLDER_ID")
                        if not folder_id:
                            raise ValueError("YANDEX_FOLDER_ID не найден в .env")
                        return iam_token, folder_id
            except Exception as e:
                print(f"⚠ Кэш нечитаем: {e}")

        # Если кэш отсутствует или устарел — обновляем
        print("🔄 Получаем новый IAM-токен через OAuth...")
        response = requests.post(
            "https://iam.api.cloud.yandex.net/iam/v1/tokens",
            json={"yandexPassportOauthToken": oauth_token}
        )

        if response.status_code != 200:
            error = response.json().get("error", "Неизвестная ошибка")
            raise Exception(f"Не удалось обновить IAM-токен: {error}")

        data = response.json()
        iam_token = data["iamToken"]
        expires_at = data["expiresAt"]  # Например: "2025-04-05T12:34:56Z"

        # Сохраняем в кэш
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"iam_token": iam_token, "expires_at": expires_at}, f)

        print("✅ Новый IAM-токен сохранён в кэш")

        folder_id = os.getenv("YANDEX_FOLDER_ID")
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
                    "\n# GigaChat — от Сбера\n"
                    "GIGACHAT_CLIENT_ID=ваш_id\n"
                    "GIGACHAT_CLIENT_SECRET=ваш_secret\n"
                    "OPENROUTER_API_KEY=...\n"
                    "\n# GigaChat — от Сбера\n"
                    "GIGACHAT_CLIENT_ID=ваш_id\n"
                    "GIGACHAT_CLIENT_SECRET=ваш_secret\n"
                    "\n# Yandex GPT\n"
                    "YANDEX_OAUTH_TOKEN=ваш_токен\n"
                    "YANDEX_FOLDER_ID=ваш_folder_id\n"
                )
            print("✅ Создан файл .env (заполните API-ключи)")
