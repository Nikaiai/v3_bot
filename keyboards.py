from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import get_db, Category, Order, OrderStatus
from utils import is_cafe_open


def main_menu_keyboard(is_admin: bool = False):
    keyboard = [
        [InlineKeyboardButton("🍽️ Показать меню", callback_data="show_menu")],
        [InlineKeyboardButton("🛒 Корзина", callback_data="cart")],
        [InlineKeyboardButton("📋 Мои заказы", callback_data="my_orders")]
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton("👑 Вернуться в админ-панель", callback_data="admin_panel")])
    return InlineKeyboardMarkup(keyboard)


def admin_menu_keyboard():
    db = next(get_db())
    new_orders_count = db.query(Order).filter(Order.status == OrderStatus.NEW).count()
    db.close()

    text = f"📋 Новые заказы ({new_orders_count})" if new_orders_count > 0 else "📋 Новых заказов нет"

    keyboard = [
        [InlineKeyboardButton(text, callback_data=f"admin_view_orders_{OrderStatus.NEW}")],
        [InlineKeyboardButton("Все заказы", callback_data="admin_view_orders_ALL")],
        [InlineKeyboardButton("➕ Добавить новое блюдо", callback_data="admin_add_item")],
        [InlineKeyboardButton("➡️ Перейти в меню клиента", callback_data="start_user_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def menu_keyboard(category_id=None):
    db = next(get_db())
    if category_id is None:
        categories = db.query(Category).filter(Category.parent_id.is_(None)).all()
        keyboard = [[InlineKeyboardButton(cat.name, callback_data=f"category_{cat.id}")] for cat in categories]
        keyboard.append([InlineKeyboardButton("⬅️ В главное меню", callback_data="start")])
    else:
        current_category = db.query(Category).get(category_id)
        keyboard = []
        if current_category.subcategories:
            for sub in current_category.subcategories:
                keyboard.append([InlineKeyboardButton(sub.name, callback_data=f"category_{sub.id}")])
        elif current_category.items:
            for item in current_category.items:
                keyboard.append(
                    [InlineKeyboardButton(f"{item.name} ({item.price} руб.)", callback_data=f"item_{item.id}")])

        if current_category.parent_id is None:
            keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="show_menu")])
        else:
            keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data=f"category_{current_category.parent_id}")])

    db.close()
    return InlineKeyboardMarkup(keyboard)


def item_details_keyboard(item_id: int, quantity: int = 1, is_admin: bool = False):
    if quantity < 1: quantity = 1

    keyboard = [
        [
            InlineKeyboardButton("➖", callback_data=f"item_decr_{item_id}_{quantity - 1}"),
            InlineKeyboardButton(f"{quantity} шт.", callback_data="noop"),
            InlineKeyboardButton("➕", callback_data=f"item_incr_{item_id}_{quantity + 1}")
        ]
    ]
    if is_cafe_open() or is_admin:
        keyboard.append([InlineKeyboardButton(f"🛒 Добавить в корзину ({quantity})",
                                              callback_data=f"cart_add_many_{item_id}_{quantity}")])

    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data=f"item_back_{item_id}")])
    return InlineKeyboardMarkup(keyboard)


def cart_actions_keyboard():
    keyboard = []
    if is_cafe_open():
        keyboard.append([InlineKeyboardButton("✅ Перейти к оформлению", callback_data="place_order")])

    keyboard.extend([
        [InlineKeyboardButton("🗑️ Очистить корзину", callback_data="clear_cart")],
        [InlineKeyboardButton("⬅️ Назад в меню", callback_data="show_menu")],
    ])
    return InlineKeyboardMarkup(keyboard)


def confirm_order_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👍 Подтвердить заказ", callback_data="confirm_order")],
        [InlineKeyboardButton("⬅️ Вернуться в корзину", callback_data="cart")]
    ])


def admin_order_keyboard(order_id):
    keyboard = [
        [InlineKeyboardButton("✔️ Готовится", callback_data=f"admin_status_{order_id}_{OrderStatus.IN_PROGRESS}")],
        [InlineKeyboardButton("✅ Готов к выдаче", callback_data=f"admin_status_{order_id}_{OrderStatus.READY}")],
        [InlineKeyboardButton("🏁 Завершить", callback_data=f"admin_status_{order_id}_{OrderStatus.COMPLETED}")],
        [InlineKeyboardButton("❌ Отменить", callback_data=f"admin_status_{order_id}_{OrderStatus.CANCELLED}")],
        [InlineKeyboardButton("⬅️ Назад к списку", callback_data=f"admin_view_orders_{OrderStatus.NEW}")],
    ]
    return InlineKeyboardMarkup(keyboard)


def cancel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_action")]
    ])
