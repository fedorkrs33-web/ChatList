# Схема базы данных ChatList
## 1. Таблица `prompts` — сохранённые промты

| Поле       | Тип         | Описание                                      |
|------------|-------------|------------------------------|
| id         | INTEGER     | Первичный ключ, автоинкремент |
| created_at | TEXT        | Дата и время: `YYYY-MM-DD HH:MM:SS` |
| prompt     | TEXT        | Текст промта                 |
| tags       | TEXT        | Теги через запятую (опционально) |


## 2. Таблица `models` — нейросети
| Поле        | Тип         | Описание                                     | 
|-------------|-------------|----------------------------------------------|
| id          | INTEGER     | Первичный ключ, автоинкремент |
| name        | TEXT        | Название модели: GPT-4, Claude 3, DeepSeek | 
| api_url     | TEXT       | URL для POST-запроса, например: https://api.openai.com/v1/chat/completions |
| api_key_var | TEXT       | Имя переменной из .env: OPENAI_API_KEY, DEEPSEEK_API_KEY | 
| is_active   | INTEGER     | 1 — активна, 0 — отключена | 
| provider    | TEXT        | Провайдер: openai, anthropic, deepseek (опционально) |


## 3. Таблица `results` — сохранённые ответы
 Поле         | Тип         | Описание | 
|--------------|-------------|----------------------------------------------| 
| id | INTEGER | Первичный ключ, автоинкремент | 
| prompt_id | INTEGER | Ссылка на prompts.id |
| model_id | INTEGER | Ссылка на models.id | 
| response | TEXT | Текст ответа модели | 
| saved_at | TEXT | Время сохранения: YYYY-MM-DD HH:MM:SS |


## 4. Таблица settings — настройки программы
| Поле | Тип | Описание |
|--------------|-------------|----------------------------------------------|
| key | TEXT | Ключ настройки: last_prompt, theme, auto_send |
| value | TEXT | Значение |