# test_yandex_sdk.py
from yandex.cloud.ai.llm.v1.llm_service_pb2 import CompletionOptions
from yandex.cloud.ai.llm.v1.llm_service_pb2_grpc import LlmServiceStub
import yandexcloud

# Загрузка конфигурации из .env
import os
from dotenv import load_dotenv
load_dotenv()

# Установка переменных для SDK
os.environ["YC_TOKEN"] = ""  # не нужен, если используем сервисный аккаунт
os.environ["YC_FOLDER_ID"] = os.getenv("YC_FOLDER_ID")
os.environ["YC_SERVICE_ACCOUNT_ID"] = os.getenv("YC_SERVICE_ACCOUNT_ID")
os.environ["YC_SERVICE_ACCOUNT_KEY_ID"] = os.getenv("YC_SERVICE_ACCOUNT_KEY_ID")
os.environ["YC_PRIVATE_KEY"] = os.getenv("YC_PRIVATE_KEY")

def main():
    # Создаём клиента
    sdk = yandexcloud.SDK()
    llm = sdk.client(LlmServiceStub)

    # Отправляем запрос
    response = llm.Completion(
        model_uri=f"gpt://{os.getenv('YC_FOLDER_ID')}/yandexgpt/latest",
        completion_options=CompletionOptions(
            temperature=0.7,
            max_tokens=1024
        ),
        messages=[{"role": "user", "text": "Привет! Напиши, что ты умеешь."}]
    )

    # Выводим ответ
    for choice in response.choices:
        print(choice.message.text)

if __name__ == "__main__":
    main()
