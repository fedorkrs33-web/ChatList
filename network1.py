# network.py
import base64
import requests
import json
import uuid 
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from typing import Dict, Any, Optional
from config import Config
from db import db


class NetworkError(Exception):
    """Исключение для ошибок сети и API"""
    pass


class Network:
    @staticmethod
    def send_prompt_to_model(model: Dict[str, Any], prompt: str) -> str:
        """
        Отправляет промт в модель и возвращает ответ или сообщение об ошибке

        :param model: словарь с данными модели (из db.get_active_models)
        :param prompt: текст промта
        :return: текст ответа или строка с ошибкой
        """
        name = model["name"]
        api_url = model["api_url"]
        api_key_var = model["api_key_var"]
        provider = model.get("provider", "").lower()

        # 🔹 Особая обработка GigaChat
        if provider == "gigachat":
            return Network._send_to_gigachat(prompt)
        
        try:
            api_url = model["api_url"]
            # Получаем API-ключ
            api_key = Config.get_api_key(api_key_var)

            # Формируем заголовки
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            # Специфичные настройки по провайдеру
            if provider == "anthropic":
                # Anthropic требует явного указания max_tokens
                payload = {
                    "model": "claude-3-haiku-20240307",  # можно улучшить: хранить в БД
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1024
                }
            else:
                # OpenAI-совместимые: GPT, DeepSeek, Groq и др.
                payload = {
                    "model": "gpt-4",  # можно улучшить: хранить в БД
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1024
                }

            # Отправляем POST-запрос
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            # Проверяем статус
            if response.status_code != 200:
                try:
                    error_msg = response.json().get("error", {}).get("message", str(response.json()))
                except:
                    error_msg = response.text[:200]  # если не JSON
                return f"❌ Ошибка {response.status_code}: {error_msg}"

            # Парсим JSON
            try:
                data = response.json()
            except json.JSONDecodeError:
                return f"❌ Ошибка: Ответ не JSON. Текст: {response.text[:500]}"

            if not isinstance(data, dict):
                return f"❌ Ошибка: Ответ — не объект, а {type(data).__name__}: {str(data)[:500]}"

            # Извлекаем ответ
            try:
                if provider == "anthropic":
                    content = data.get("content", [{}])[0].get("text", "")
                else:
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                if not content:
                    return "⚠ Ответ получен, но пустой"

                return content

            except Exception as e:
                return f"❌ Ошибка при парсинге ответа: {str(e)}"
        except requests.exceptions.Timeout:
            return "❌ Ошибка: Таймаут запроса"
        except requests.exceptions.ConnectionError:
            return "❌ Ошибка: Нет подключения к интернету"
        except Exception as e:
            return f"❌ Ошибка: {str(e)}"
        
    def _send_to_gigachat(prompt: str) -> str:
        import requests
        import json
        from config import Config

        try:
            # 1. Получаем credentials
            client_id, client_secret = Config.get_gigachat_credentials()

            # 2. Кодируем в base64
            auth_str = f"{client_id}:{client_secret}"
            encoded = base64.b64encode(auth_str.encode()).decode()

            # 🔴 Отправляем без проверки SSL
            # 3. Получаем access_token
            token_response = requests.post(
                "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                    "RqUID": str(uuid.uuid4()),
                    "Authorization": f"Basic {encoded}"
                },
                data={"scope": "GIGACHAT_API_PERS"},
                verify=False  # 🔴 И здесь
            )

            if token_response.status_code != 200:
                return f"❌ Ошибка получения токена: {token_response.text}"

            access_token = token_response.json().get("access_token")
            if not access_token:
                return "❌ Не удалось получить access_token"

            # 4. Отправляем промт
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
                verify=False
            )

            if chat_response.status_code != 200:
                return f"❌ Ошибка в чате: {chat_response.text}"

            data = chat_response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return content if content else "Пустой ответ от GigaChat"

        except Exception as e:
            return f"❌ Ошибка GigaChat: {str(e)}"

