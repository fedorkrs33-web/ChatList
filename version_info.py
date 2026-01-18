# version_info.py
from version import __version__ as version

# Структура версии
version_info = {
    "version": version,
    "file_version": version.replace(".", ",") + ",0",
    "product_version": version.replace(".", ",") + ",0",
    "file_description": "ChatList — Сравнение AI-ответов",
    "product_name": "ChatList",
    "company_name": "Fedorkrs33",
    "copyright": "© 2026"
}
