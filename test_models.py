# test_models.py
from models import Model

models = Model.load_all()
for m in models:
    print(f"ID: {m.id}")
    print(f"Имя: {m.name}")
    print(f"API URL: {m.api_url}")
    print(f"API Key Var: {m.api_key_var}")
    print(f"Провайдер: {m.provider}")
    print(f"Внутреннее имя: {m.model_name}")
    print(f"Активна: {m.is_active}")
    print("-" * 40)

