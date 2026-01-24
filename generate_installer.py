# generate_installer.py
import os
import subprocess
from version import __version__

# Пути
INNO_SETUP_PATH = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(PROJECT_DIR, "dist")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "installer_output")

# Имя выходного файла
APP_NAME = "ChatList"
SETUP_EXE = f"{APP_NAME}_Installer_v{__version__}.exe"

# Проверки
if not os.path.exists(INNO_SETUP_PATH):
    print(f"[ERROR] Inno Setup не найден: {INNO_SETUP_PATH}")
    print("Убедитесь, что Inno Setup установлен по указанному пути.")
    exit(1)

if not os.path.exists(DIST_DIR):
    print(f"[ERROR] Папка dist/ не найдена. Сначала соберите приложение.")
    exit(1)

exe_path = os.path.join(DIST_DIR, f"{APP_NAME}_v{__version__}.exe")
if not os.path.exists(exe_path):
    print(f"[ERROR] Не найден файл: {exe_path}")
    print(f"Убедитесь, что сборка выполнена и файл существует.")
    exit(1)

# Создаём папку для выхода
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Генерируем .iss скрипт в памяти
iss_script = f'''
[Setup]
AppName={APP_NAME}
AppVersion={__version__}
AppPublisher=My Company
DefaultDirName={{autopf}}\\{APP_NAME}
DefaultGroupName={APP_NAME}
OutputDir={OUTPUT_DIR}
OutputBaseFilename={SETUP_EXE}
Compression=lzma
SolidCompression=yes
PrivilegesRequired=none
ChangesEnvironment=yes
AllowNoIcons=yes
LicenseFile=LICENSE.txt

[Types]
Name: "full"; Description: "Полная установка"

[Components]
Name: "program"; Description: "Программа"; Types: full; Flags: fixed

[Files]
Source: "{exe_path}"; DestDir: "{{app}}"; Components: program
Source: "{PROJECT_DIR}\\.env.example"; DestDir: "{{app}}"; Components: program
Source: "{PROJECT_DIR}\\README.md"; DestDir: "{{app}}"; Components: program
Source: "{PROJECT_DIR}\\app.ico"; DestDir: "{{app}}"; Components: program

[Icons]
Name: "{{group}}\\{APP_NAME}"; Filename: "{{app}}\\{APP_NAME}_v{__version__}.exe"; IconFilename: "{{app}}\\app.ico"
Name: "{{commondesktop}}\\{APP_NAME}"; Filename: "{{app}}\\{APP_NAME}_v{__version__}.exe"; IconFilename: "{{app}}\\app.ico"; Tasks: desktopicon

[Tasks]
Name: desktopicon; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные задачи:"

[Run]
Filename: "{{app}}\\{APP_NAME}_v{__version__}.exe"; Description: "Запустить {APP_NAME} после установки"; Flags: nowait postinstall skipifsilent

'''

# Сохраняем временный .iss файл
iss_path = os.path.join(PROJECT_DIR, "temp_setup.iss")
with open(iss_path, "w", encoding="utf-8") as f:
    f.write(iss_script)

print(f"[INFO] Генерация установщика v{__version__}...")
print(f"Файл: {os.path.join(OUTPUT_DIR, SETUP_EXE)}")

# Запускаем Inno Setup
try:
    result = subprocess.run([INNO_SETUP_PATH, iss_path], check=True, capture_output=True, text=True)
    print("[SUCCESS] Установщик успешно создан!")
    print(f"Путь: {os.path.join(OUTPUT_DIR, SETUP_EXE)}")
except subprocess.CalledProcessError as e:
    print("[ERROR] Ошибка при создании установщика:")
    print(e.stderr)
finally:
    # Удаляем временный .iss
    if os.path.exists(iss_path):
        os.remove(iss_path)
