# build.py
import os
import sys

# Путь к проекту
project_dir = os.path.dirname(os.path.abspath(__file__))

# Путь к основному файлу
main_py_path = os.path.join(project_dir, "main.py")

# Проверим, существует ли main.py
if not os.path.exists(main_py_path):
    print(f"[ERROR] Не найден файл: {main_py_path}")
    sys.exit(1)

# Формируем команду в одну строку
cmd = (
    'pyinstaller '
    '--name="ChatList" '
    '--windowed '
    '--icon="app.ico" '
    '--add-data="app.ico;." '
    '--add-data="version.py;." '
    '--version-file="version_info.txt" '
    '--clean '
    '--noconfirm '
    f'"{main_py_path}"'
)

print("[INFO] Запуск команды:")
print(cmd)

# Запускаем
os.system(cmd)
