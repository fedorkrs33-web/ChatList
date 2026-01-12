# Инструкция по настройке Git и GitHub для проекта ChatList

## Текущее состояние

✅ Git репозиторий инициализирован  
✅ .gitignore настроен (игнорирует .env, *.db, venv, __pycache__ и т.д.)  
✅ Пользователь Git настроен: `fedorkrs33-web` <fedorkrs.33@gmail.com>

## Шаг 1: Проверка игнорируемых файлов

Убедитесь, что важные файлы игнорируются:

```powershell
# Проверка, что .env и chatlist.db не попадут в коммит
git status --ignored
```

## Шаг 2: Добавление файлов в индекс

Добавьте все нужные файлы (игнорируемые файлы добавлены не будут):

```powershell
# Добавить все файлы проекта
git add .

# Или добавить конкретные файлы
git add .gitignore
git add *.py
git add *.md
git add LICENSE
```

## Шаг 3: Проверка статуса перед коммитом

```powershell
# Проверить, что добавлено
git status

# Проверить краткий статус
git status --short
```

## Шаг 4: Первый коммит

```powershell
# Создать первый коммит
git commit -m "Начальный коммит: базовая структура проекта ChatList"

# Или более подробное сообщение
git commit -m "Начальный коммит: базовая структура проекта ChatList

- Добавлены основные модули (main.py, db.py, models.py, network.py, config.py)
- Настроен GUI на PyQt6
- Поддержка OpenAI-совместимых API, GigaChat, Yandex GPT, OpenRouter
- База данных SQLite с таблицами для промтов, моделей и результатов
- Добавлен .gitignore для Python проектов"
```

## Шаг 5: Создание репозитория на GitHub

1. Перейдите на [GitHub.com](https://github.com)
2. Войдите в свой аккаунт (fedorkrs33-web)
3. Нажмите кнопку **"New"** или **"+"** → **"New repository"**
4. Заполните форму:
   - **Repository name**: `ChatList` (или другое имя)
   - **Description**: `Минимальная программа на Python с графическим интерфейсом на PyQt6 для сравнения ответов AI-моделей`
   - **Visibility**: Public или Private (на ваше усмотрение)
   - **НЕ ИНИЦИАЛИЗИРУЙТЕ** репозиторий (не добавляйте README, .gitignore или лицензию)
5. Нажмите **"Create repository"**

## Шаг 6: Подключение локального репозитория к GitHub

После создания репозитория GitHub покажет инструкции. Выполните:

```powershell
# Добавить удаленный репозиторий (замените YOUR_USERNAME на ваш GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/ChatList.git

# Или через SSH (если настроен SSH ключ)
git remote add origin git@github.com:YOUR_USERNAME/ChatList.git

# Проверить, что remote добавлен
git remote -v
```

## Шаг 7: Отправка кода на GitHub

```powershell
# Отправить код на GitHub (первая отправка)
git push -u origin main

# В последующих коммитах можно просто использовать
git push
```

## Последующие коммиты

Для последующих изменений используйте стандартный workflow:

```powershell
# 1. Проверить статус изменений
git status

# 2. Добавить измененные файлы
git add .
# или конкретные файлы
git add main.py network.py

# 3. Создать коммит с описательным сообщением
git commit -m "Описание изменений на русском"

# 4. Отправить на GitHub
git push
```

## Полезные команды

```powershell
# Просмотр истории коммитов
git log
git log --oneline

# Просмотр изменений в файлах
git diff

# Просмотр изменений конкретного файла
git diff main.py

# Отмена изменений в файле (до git add)
git checkout -- filename.py

# Удаление файла из индекса (но сохранение на диске)
git rm --cached filename.py
```

## Важные замечания

⚠️ **Никогда не коммитьте:**
- `.env` файлы (содержат API-ключи)
- `*.db` файлы (база данных)
- `venv/` или `__pycache__/` директории
- Личные данные и секреты

✅ **Всегда коммитьте:**
- Исходный код (`.py` файлы)
- Документацию (`.md` файлы)
- Конфигурационные файлы (без секретов)
- `.gitignore`

## Если что-то пошло не так

```powershell
# Отменить последний коммит (но сохранить изменения)
git reset --soft HEAD~1

# Отменить последний коммит и все изменения
git reset --hard HEAD~1

# Изменить последнее сообщение коммита
git commit --amend -m "Новое сообщение"
```
