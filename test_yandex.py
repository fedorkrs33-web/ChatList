from models import Model
from network import Network

model = Model(3, "Yandex GPT", "", "YANDEX", True, "yandex")
response = Network.send_prompt_to_model(model, "Привет! Как дела?")
print(f"Ответ: {response}")

