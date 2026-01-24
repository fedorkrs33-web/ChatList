# generate_version_file.py
from version import __version__
import os

# Формируем содержимое версии для PyInstaller
content = f'''# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({__version__.replace('.', ', ')}, 0),
    prodvers=({__version__.replace('.', ', ')}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'041904B0',
        [StringStruct(u'CompanyName', u''),
         StringStruct(u'FileDescription', u'ChatList — Сравнение AI-ответов'),
         StringStruct(u'InternalName', u'ChatList'),
         StringStruct(u'LegalCopyright', u'© 2025. Все права защищены.'),
         StringStruct(u'ProductName', u'ChatList'),
         StringStruct(u'ProductVersion', u'{__version__}'),
         StringStruct(u'FileVersion', u'{__version__}')
        ])
      ]),
    VarFileInfo([VarStruct(u'Translation', [0x0419, 1200])])
  ]
)
'''

with open("version_info.txt", "w", encoding="utf-8") as f:
    f.write(content)

print(f"[BUILD] Файл версии создан: v{__version__}")
