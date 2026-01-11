# test_models.py
from models import Model

def main():
    print("🔹 Тестируем models.py\n")

    # 1. Загрузка всех моделей
    print("1. 🔍 Model.load_all() — все модели:")
    all_models = Model.load_all()
    for m in all_models:
        print(f"   → {m}")

    # 2. Только активные
    print("\n2. ✅ Model.get_active() — активные модели:")
    active_models = Model.get_active()
    for m in active_models:
        print(f"   → {m}")

    # 3. Попробуем выключить первую модель
    if active_models:
        model_id = active_models[0].id
        print(f"\n3. 🔴 Выключаем модель с ID={model_id}")
        Model.update_status(model_id, False)

        print("   🔎 Проверяем активные модели снова:")
        new_active = Model.get_active()
        for m in new_active:
            print(f"      → {m}")
        if not new_active:
            print("   ✅ Нет активных моделей — модель выключена")

        # Включим обратно
        print(f"   🟢 Включаем обратно ID={model_id}")
        Model.update_status(model_id, True)

    print("\n✅ Тест models.py завершён.")

if __name__ == "__main__":
    main()
