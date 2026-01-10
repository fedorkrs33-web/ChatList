# network.py
import requests
import uuid
import json
import base64
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from typing import Dict, Any, Optional
from config import Config
from models import Model


class NetworkError(Exception):
    """Общее исключение для сетевых ошибок"""
    pass


class NetworkError(Exception):
    """Общее исключение для сетевых ошибок"""
    pass


class Network:
    @staticmethod
    def send_prompt_to_model(model: Model, prompt: str) -> str:
        """
        Отправляет промт в указанную модель и возвращает ответ или сообщение об ошибке.

        :param model: объект Model
        :param prompt: текст промта
        :return: строка — ответ или ошибка
        """
        print(f"📤 Отправляю промт в {model.name}...")

        try:
            # 🔹 GigaChat — особый случай
            if model.provider == "gigachat":
                return Network._send_to_gigachat(prompt)

            # 🔹 OpenAI-совместимые: GPT, Claude, DeepSeek, Groq и др.
            return Network._send_openai_compatible(model, prompt)

        except Exception as e:
            error_msg = f"❌ Критическая ошибка: {str(e)}"
            print(error_msg)
            return error_msg

    @staticmethod
    def _send_openai_compatible(model: Model, prompt: str) -> str:
        """Отправка в OpenAI-совместимые API"""
        try:
            # Получаем API-ключ
            try:
                api_key = Config.get_api_key(model.api_key_var)
            except ValueError as e:
                error_msg = f"🔑 Ошибка ключа: {e}"
                print(error_msg)
                return error_msg

            # Формируем заголовки
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            # Определяем модель (можно улучшить: хранить в БД)
            model_name = "gpt-4" if "gpt" in model.name.lower() else "claude-3-haiku-20240307"

            # Формируем тело запроса
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1024,
            }

            # Отправляем запрос
            print(f"   🌐 POST {model.api_url}")
            response = requests.post(
                model.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            # Логируем статус
            print(f"   🔎 Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content:
                    print("   ✅ Ответ получен")
                    return content.strip()
                return "⚠️ Ответ получен, но пустой"

            else:
                try:
                    error_detail = response.json().get("error", {}).get("message", str(response.text))
                except:
                    error_detail = response.text
                error_msg = f"❌ {response.status_code}: {error_detail}"
                print(f"   🚫 Ошибка: {error_msg}")
                return error_msg

        except requests.exceptions.Timeout:
            error_msg = "❌ Ошибка: Таймаут запроса (30 сек)"
            print(error_msg)
            return error_msg

        except requests.exceptions.ConnectionError:
            error_msg = "❌ Ошибка: Нет подключения к интернету"
            print(error_msg)
            return error_msg

        except Exception as e:
            error_msg = f"❌ Неизвестная ошибка: {str(e)}"
            print(error_msg)
            return error_msg

    @staticmethod
    def _send_to_gigachat(prompt: str) -> str:
        """Отправка запроса в GigaChat (через Сбер)"""
        try:
            client_id, client_secret = Config.get_gigachat_credentials()

            # 1. Получаем access_token
            auth_str = f"{client_id}:{client_secret}"
            encoded = base64.b64encode(auth_str.encode()).decode()

            token_response = requests.post(
                "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                    "RqUID": str(uuid.uuid4()),
                    "Authorization": f"Basic {encoded}"
                },
                data={"scope": "GIGACHAT_API_PERS"},
                verify=False  # 🔥 Отключаем проверку SSL
            )

            print(f"   🔐 Получение токена: {token_response.status_code}")

            if token_response.status_code != 200:
                error = token_response.text
                print(f"   🚫 Ошибка токена: {error}")
                return f"❌ Ошибка авторизации: {error}"

            access_token = token_response.json().get("access_token")
            if not access_token:
                msg = "Не получен access_token"
                print(f"   🚫 {msg}")
                return f"❌ {msg}"

            # 2. Отправляем промт
            chat_response = requests.post(
                "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}"
                },
                json={
                    "model": "GigaChat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1024
                },
                timeout=30,
                verify=False  # 🔥
            )

            print(f"   💬 Запрос в GigaChat: {chat_response.status_code}")

            if chat_response.status_code == 200:
                content = chat_response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                if content:
                    print("   ✅ Ответ получен")
                    return content.strip()
                return "⚠️ Ответ от GigaChat пуст"

            else:
                error = chat_response.text
                print(f"   🚫 Ошибка: {error}")
                return f"❌ Ошибка GigaChat: {error}"

        except Exception as e:
            error_msg = f"❌ GigaChat: {str(e)}"
            print(error_msg)
            return error_msg
