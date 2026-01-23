@echo off
echo Сборка ChatList...
pyinstaller ^
    --name "ChatList" ^
    --windowed ^
    --icon=app.ico ^
    --add-data ".env.example;." ^
    --add-data "app.ico;." ^
    --onefile ^
    main.py

echo Готово!
pause
