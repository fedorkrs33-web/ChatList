# test_yandex.py
from models import Model
from network import Network

models = Model.get_active()
for m in models:
    if "Yandex" in m.name:
        print(f"\n🚀 {m}")
        response = Network.send_prompt_to_model(m, "Привет! Напиши, что ты умеешь.")
        print(f"💬 Ответ:\n{response}")
