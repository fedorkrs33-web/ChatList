# test_config.py
from config import Config

if __name__ == "__main__":
    try:
        key = Config.get_api_key("OPENAI_API_KEY")
        print(f"✅ Ключ загружен: {key[:10]}...")  # Покажем только начало
    except ValueError as e:
        print(f"❌ Ошибка: {e}")
