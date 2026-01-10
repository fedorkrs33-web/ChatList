# test_network.py
from models import Model
from network import Network

def main():
    print("🔹 Тест network.py: отправка промтов\n")

    # Загружаем активные модели
    models = Model.get_active()
    if not models:
        print("❌ Нет активных моделей. Проверьте db.py и .env")
        return

    prompt = "Напиши коротко: что такое нейросеть?"

    for model in models:
        print(f"\n" + "="*50)
        response = Network.send_prompt_to_model(model, prompt)
        print(f"\n💬 ОТВЕТ от {model.name}:\n{response[:500]}...")
        if len(response) > 500:
            print("(обрезано)")

    print("\n" + "="*50)
    print("✅ Тест network.py завершён")

if __name__ == "__main__":
    main()

