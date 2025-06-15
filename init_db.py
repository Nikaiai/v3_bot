# init_db.py
import os
from database import create_db_and_tables, SessionLocal, Category, MenuItem


def populate_initial_data():
    """
    Удаляет старую БД и заполняет ее новыми, разнообразными данными
    с подкатегориями и детализированными описаниями.
    """
    db_file = "cafe_bot.db"
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"Старая база данных '{db_file}' удалена.")

    create_db_and_tables()

    db = SessionLocal()

    print("Заполнение базы данных новыми данными...")

    # ================================================================
    # 1. Создание категорий и подкатегорий
    # ================================================================

    # --- Родительские категории ---
    cat_drinks = Category(name="🥤 Напитки")
    cat_food = Category(name="🥩 Мясо на вес")
    cat_desserts = Category(name="🍰 Десерты")
    db.add_all([cat_drinks, cat_food, cat_desserts])
    db.commit()

    # --- Подкатегории для Напитков ---
    sub_hot_drinks = Category(name="Горячие", parent_id=cat_drinks.id)
    sub_cold_drinks = Category(name="Холодные", parent_id=cat_drinks.id)
    sub_soda = Category(name="Газировка", parent_id=cat_drinks.id)

    # --- Подкатегории для Мяса ---
    sub_chicken = Category(name="Курица", parent_id=cat_food.id)
    sub_pork = Category(name="Свинина", parent_id=cat_food.id)
    sub_beef = Category(name="Говядина", parent_id=cat_food.id)

    # --- Подкатегории для Десертов ---
    sub_bakery = Category(name="Выпечка", parent_id=cat_desserts.id)
    sub_cakes = Category(name="Торты и пирожные", parent_id=cat_desserts.id)

    db.add_all([
        sub_hot_drinks, sub_cold_drinks, sub_soda,
        sub_chicken, sub_pork, sub_beef,
        sub_bakery, sub_cakes
    ])
    db.commit()

    # ================================================================
    # 2. Создание позиций меню (блюд и напитков)
    # ================================================================

    menu_items = [
        # --- Горячие напитки ---
        MenuItem(name="Эспрессо", price=120, description="Классический крепкий кофе. Объем: 40 мл.",
                 category_id=sub_hot_drinks.id),
        MenuItem(name="Американо", price=140, description="Эспрессо с добавлением горячей воды. Объем: 180 мл.",
                 category_id=sub_hot_drinks.id),
        MenuItem(name="Капучино", price=180, description="Кофе с нежной молочной пенкой. Объем: 250 мл.",
                 category_id=sub_hot_drinks.id),
        MenuItem(name="Латте", price=200, description="Больше молока, чем в капучино. Объем: 300 мл.",
                 category_id=sub_hot_drinks.id),
        MenuItem(name="Какао", price=170, description="Горячий шоколад с молоком. Объем: 250 мл.",
                 category_id=sub_hot_drinks.id),
        MenuItem(name="Чай черный", price=100, description="Ассам или Эрл Грей. Объем: 400 мл.",
                 category_id=sub_hot_drinks.id),
        MenuItem(name="Чай зеленый", price=100, description="Сенча или улун. Объем: 400 мл.",
                 category_id=sub_hot_drinks.id),
        MenuItem(name="Масала чай", price=220, description="Пряный индийский чай с молоком. Объем: 300 мл.",
                 category_id=sub_hot_drinks.id),

        # --- Холодные напитки ---
        MenuItem(name="Айс Латте", price=220, description="Охлажденный кофе с молоком и льдом. Объем: 350 мл.",
                 category_id=sub_cold_drinks.id),
        MenuItem(name="Холодный чай", price=150, description="Черный или зеленый, со льдом и лимоном. Объем: 400 мл.",
                 category_id=sub_cold_drinks.id),
        MenuItem(name="Лимонад 'Классика'", price=160, description="Свежевыжатый лимон, мята, содовая. Объем: 400 мл.",
                 category_id=sub_cold_drinks.id),
        MenuItem(name="Сок свежевыжатый", price=250, description="Апельсиновый, яблочный или морковный. Объем: 300 мл.",
                 category_id=sub_cold_drinks.id),
        MenuItem(name="Морс ягодный", price=120, description="Домашний морс из клюквы и брусники. Объем: 400 мл.",
                 category_id=sub_cold_drinks.id),

        # --- Газировка ---
        MenuItem(name="Coca-Cola", price=130, description="Классическая, в стекле. Объем: 0,33 л.",
                 category_id=sub_soda.id),
        MenuItem(name="Fentimans Rose", price=280, description="Натуральный лимонад с ароматом розы. Объем: 0,275 л.",
                 category_id=sub_soda.id),
        MenuItem(name="Club-Mate", price=250, description="Тонизирующий напиток с экстрактом мате. Объем: 0.5 л.",
                 category_id=sub_soda.id),
        MenuItem(name="Evervess Tonic", price=120, description="Классический тоник. Объем: 0.25 л.",
                 category_id=sub_soda.id),
        MenuItem(name="Вода 'Acqua Panna'", price=200, description="Негазированная минеральная вода. Объем: 0.5 л.",
                 category_id=sub_soda.id),

        # --- Мясо (Курица) ---
        MenuItem(name="Куриное филе", price=90, description="Цена указана за 100 г. Нежная грудка без кости.",
                 category_id=sub_chicken.id),
        MenuItem(name="Куриные крылья", price=65, description="Цена указана за 100 г. Идеально для гриля.",
                 category_id=sub_chicken.id),
        MenuItem(name="Куриные бедра", price=75, description="Цена указана за 100 г. Сочное мясо на кости.",
                 category_id=sub_chicken.id),
        MenuItem(name="Куриная голень", price=70, description="Цена указана за 100 г. Отлично для запекания.",
                 category_id=sub_chicken.id),
        MenuItem(name="Цыпленок табака", price=110, description="Цена указана за 100 г. Тушка целиком.",
                 category_id=sub_chicken.id),

        # --- Мясо (Свинина) ---
        MenuItem(name="Свиная шея", price=150, description="Цена указана за 100 г. Идеальный выбор для шашлыка.",
                 category_id=sub_pork.id),
        MenuItem(name="Свиная корейка", price=140, description="Цена указана за 100 г. Постное мясо на кости.",
                 category_id=sub_pork.id),
        MenuItem(name="Свиная вырезка", price=180, description="Цена указана за 100 г. Самая нежная часть.",
                 category_id=sub_pork.id),
        MenuItem(name="Свиные ребра BBQ", price=130, description="Цена указана за 100 г. Мясистые ребра для гриля.",
                 category_id=sub_pork.id),
        MenuItem(name="Рулька свиная", price=100, description="Цена указана за 100 г. Для запекания в пиве.",
                 category_id=sub_pork.id),

        # --- Мясо (Говядина) ---
        MenuItem(name="Стейк Рибай", price=450, description="Цена указана за 100 г. Мраморная говядина.",
                 category_id=sub_beef.id),
        MenuItem(name="Стейк Стриплойн", price=420, description="Цена указана за 100 г. Яркий говяжий вкус.",
                 category_id=sub_beef.id),
        MenuItem(name="Говяжья вырезка", price=550, description="Цена указана за 100 г. Для филе-миньон.",
                 category_id=sub_beef.id),
        MenuItem(name="Бефстроганов", price=350, description="Цена указана за 100 г. Нарезанное мясо для жарки.",
                 category_id=sub_beef.id),
        MenuItem(name="Говяжий фарш", price=250, description="Цена указана за 100 г. 80/20, для бургеров.",
                 category_id=sub_beef.id),

        # --- Десерты (Выпечка) ---
        MenuItem(name="Круассан классический", price=110, description="Хрустящий, воздушный. Масса: ~70 г.",
                 category_id=sub_bakery.id),
        MenuItem(name="Круассан с миндалем", price=150, description="С миндальным кремом и лепестками. Масса: ~90 г.",
                 category_id=sub_bakery.id),
        MenuItem(name="Улитка с изюмом", price=130, description="Слойка с заварным кремом и изюмом. Масса: ~120 г.",
                 category_id=sub_bakery.id),
        MenuItem(name="Маффин шоколадный", price=140, description="С кусочками темного шоколада. Масса: ~110 г.",
                 category_id=sub_bakery.id),
        MenuItem(name="Синнабон", price=220,
                 description="Знаменитая булочка с корицей и сливочным сыром. Масса: ~180 г.",
                 category_id=sub_bakery.id),

        # --- Десерты (Торты и пирожные) ---
        MenuItem(name="Чизкейк 'Нью-Йорк'", price=280,
                 description="Классический чизкейк на песочной основе. Масса: 150 г.", category_id=sub_cakes.id),
        MenuItem(name="Тирамису", price=260, description="Итальянский десерт с маскарпоне и кофе. Масса: 140 г.",
                 category_id=sub_cakes.id),
        MenuItem(name="Торт 'Медовик'", price=240,
                 description="Домашний торт с тонкими медовыми коржами. Масса: 160 г.", category_id=sub_cakes.id),
        MenuItem(name="Пирожное 'Картошка'", price=120,
                 description="Классика из бисквитной крошки и какао. Масса: 80 г.", category_id=sub_cakes.id),
        MenuItem(name="Панакота", price=250, description="Сливочное желе с ягодным соусом. Объем: 200 мл.",
                 category_id=sub_cakes.id),
        MenuItem(name="Макарон", price=90,
                 description="Французское миндальное печенье, 1 шт. Вкус в ассортименте. Масса: ~20 г.",
                 category_id=sub_cakes.id),
    ]

    db.add_all(menu_items)
    db.commit()

    db.close()
    print("Заполнение базы данных новыми данными завершено.")


if __name__ == "__main__":
    populate_initial_data()