@echo off
echo Сборка ChatList...
echo.

:: Проверяем, есть ли виртуальное окружение
if exist "venv\Scripts\python.exe" (
    echo Использую виртуальное окружение: venv
    set PYTHON=venv\Scripts\python.exe
    set PYINSTALLER=venv\Scripts\pyinstaller.exe
) else (
    echo Использую глобальный Python
    set PYTHON=python
    set PYINSTALLER=pyinstaller
)

:: Проверяем, установлен ли pyinstaller
%PYTHON% -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller не найден. Устанавливаю...
    %PYTHON% -m pip install pyinstaller
)

:: Читаем версию
for /f "tokens=*" %%i in ('%PYTHON% -c "from version import __version__; print(__version__)"') do set VERSION=%%i

echo Сборка версии: v%VERSION%

:: Генерируем файл версии (если используется)
if exist "generate_version_file.py" (
    %PYTHON% generate_version_file.py
)

:: Сборка
%PYINSTALLER% ^
    --name "ChatList_v%VERSION%" ^
    --windowed ^
    --icon=app.ico ^
    --add-data ".env.example;." ^
    --add-data "app.ico;." ^
    --version-file=version_info.txt ^
    --onefile ^
    main.py

echo.
echo === Сборка завершена: dist\ChatList_v%VERSION%.exe ===
pause

