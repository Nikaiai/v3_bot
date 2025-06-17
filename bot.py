import logging
import telegram
from telegram import Update, constants, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
)

from config import BOT_TOKEN, ADMIN_IDS
from keyboards import (
    main_menu_keyboard,
    admin_menu_keyboard,
    menu_keyboard,
    item_details_keyboard,
    cart_actions_keyboard,
    confirm_order_keyboard,
    admin_order_keyboard,
    cancel_keyboard,
)
from database import (
    get_db,
    User,
    Order,
    OrderItem,
    MenuItem,
    Category,
    OrderStatus,
)
from utils import is_cafe_open, get_closed_message

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
ADD_ITEM_CATEGORY, ADD_ITEM_NAME, ADD_ITEM_DESC, ADD_ITEM_PRICE = range(4)


def escape_markdown(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return "".join(f'\\{char}' if char in escape_chars else char for char in text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db = next(get_db())
    db_user = db.query(User).filter(User.id == user.id).first()
    if not db_user:
        new_user = User(
            id=user.id, username=user.username, first_name=user.first_name
        )
        db.add(new_user)
        db.commit()
    db.close()

    context.user_data.setdefault('cart', {})
    is_admin = user.id in ADMIN_IDS

    if not is_cafe_open() and not is_admin and not update.callback_query:
        await update.message.reply_text(get_closed_message())
        return

    text = f"Здравствуйте, {escape_markdown(user.first_name)}"
    if is_admin:
        text += " \\(Админ\\)"
    text += "\\!"

    keyboard = admin_menu_keyboard() if is_admin else main_menu_keyboard(is_admin)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode=constants.ParseMode.MARKDOWN_V2,
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=keyboard,
            parse_mode=constants.ParseMode.MARKDOWN_V2,
        )


async def render_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cart = context.user_data.get('cart', {})
    db = next(get_db())
    query = update.callback_query

    if not cart:
        await query.edit_message_text("Ваша корзина пуста.", reply_markup=menu_keyboard())
    else:
        text = "🛒 *Ваша корзина:*\n\n"
        total_price = 0
        for item_id, quantity in cart.items():
            item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
            if item:
                item_total = quantity * item.price
                total_price += item_total
                safe_name = escape_markdown(item.name)
                text += f"▪️ *{safe_name}*\n_{escape_markdown(quantity)} шт\\. x {escape_markdown(item.price)}" \
                        f" руб\\. \\= {escape_markdown(item_total)} руб\\._\n"

        text += f"\n💰 *Итого:* {escape_markdown(total_price)} руб\\."
        await query.edit_message_text(
            text,
            parse_mode=constants.ParseMode.MARKDOWN_V2,
            reply_markup=cart_actions_keyboard(),
        )
    db.close()


async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = next(get_db())
    orders = (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .limit(10)
        .all()
    )

    if not orders:
        text = "У вас еще нет заказов."
    else:
        text = "📋 *Ваши последние 10 заказов:*\n\n"
        for order in orders:
            order_date = escape_markdown(order.created_at.strftime('%d.%m.%y %H:%M'))
            safe_status = escape_markdown(order.status)
            text += f"Заказ `#{order.id}` от {order_date}\n"
            text += f"Статус: *{safe_status}* \\| Сумма: *{escape_markdown(order.total_price)} руб*\n\n"

    try:
        await update.callback_query.edit_message_text(
            text,
            parse_mode=constants.ParseMode.MARKDOWN_V2 if orders else None,
            reply_markup=main_menu_keyboard(is_admin=user_id in ADMIN_IDS),
        )
    except telegram.error.BadRequest as e:
        if "Message is not modified" in str(e):
            pass
        else:
            logger.error(f"Ошибка при обновлении 'Моих заказов': {e}")

    db.close()


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data

    if data == 'admin_add_item':
        await query.answer()
        return

    is_admin = query.from_user.id in ADMIN_IDS
    if not is_cafe_open() and not is_admin:
        await query.answer(get_closed_message(), show_alert=True)
        return

    await query.answer()
    db = next(get_db())
    context.user_data.setdefault('cart', {})

    if data == "start":
        await start(update, context)
    elif data == "start_user_menu":
        await query.edit_message_text(
            "Главное меню клиента:", reply_markup=main_menu_keyboard(is_admin=is_admin)
        )
    elif data == "show_menu":
        await query.edit_message_text(
            "Выберите категорию:", reply_markup=menu_keyboard()
        )
    elif data.startswith("category_"):
        category_id = int(data.split("_")[1])
        category = db.query(Category).get(category_id)
        if category:
            text = (
                f"Выбрана категория '{category.name}'. Выберите подкатегорию:"
                if category.subcategories
                else f"Товары в категории '{category.name}':"
            )
            if not category.subcategories and not category.items:
                text += "\n\nЗдесь пока нет товаров."
            await query.edit_message_text(
                text=text, reply_markup=menu_keyboard(category_id)
            )
        else:
            await query.edit_message_text(
                "Категория не найдена.", reply_markup=menu_keyboard()
            )

    elif data.startswith("item_"):
        parts = data.split('_')
        if len(parts) == 2:
            item_id = int(parts[1])
            item = db.query(MenuItem).get(item_id)
            if item:
                text = f"*{escape_markdown(item.name)}* \\({escape_markdown(item.price)} руб\\.\\)\n\n_{escape_markdown(item.description or 'Описание отсутствует')}_"
                await query.edit_message_text(
                    text,
                    parse_mode=constants.ParseMode.MARKDOWN_V2,
                    reply_markup=item_details_keyboard(item_id, is_admin=is_admin),
                )
        elif len(parts) == 3 and parts[1] == "back":
            item_id = int(parts[2])
            item = db.query(MenuItem).get(item_id)
            if item:
                await query.edit_message_text(
                    text=f"Товары в категории '{item.category.name}':",
                    reply_markup=menu_keyboard(item.category.id),
                )
        elif len(parts) == 4 and parts[1] in ["incr", "decr"]:
            item_id = int(parts[2])
            quantity = int(parts[3])
            if quantity > 0:
                await query.edit_message_reply_markup(
                    reply_markup=item_details_keyboard(item_id, quantity, is_admin)
                )

    elif data.startswith("cart_"):
        parts = data.split('_')
        action = parts[1]
        cart = context.user_data['cart']
        if action == "add" and parts[2] == "many":
            item_id = int(parts[3])
            quantity = int(parts[4])
            cart[item_id] = cart.get(item_id, 0) + quantity
            await query.answer(
                f"✅ {quantity} шт. добавлено в корзину!", show_alert=False
            )
            item = db.query(MenuItem).get(item_id)
            if item:
                await query.edit_message_text(
                    text=f"Товары в категории '{item.category.name}':",
                    reply_markup=menu_keyboard(item.category.id),
                )

    elif data == "noop":
        pass

    elif data == "cart":
        await render_cart(update, context)
    elif data == "clear_cart":
        context.user_data['cart'] = {}
        await query.edit_message_text(
            "Корзина очищена.",
            reply_markup=main_menu_keyboard(is_admin=is_admin),
        )

    elif data == "place_order":
        cart = context.user_data.get('cart', {})
        if not cart:
            await query.edit_message_text("Корзина пуста.", reply_markup=menu_keyboard())
        else:
            text = "🔍 *Проверьте ваш заказ*\n\n"
            total_price = 0
            for item_id, quantity in cart.items():
                item = db.query(MenuItem).get(item_id)
                if item:
                    item_total = quantity * item.price
                    total_price += item_total
                    text += f"▪️ *{escape_markdown(item.name)}* \\({escape_markdown(quantity)} шт\\.\\) \\= {escape_markdown(item_total)} руб\\.\n"
            text += f"\n💰 *Итого к оплате:* {escape_markdown(total_price)} руб\\."
            await query.edit_message_text(
                text,
                parse_mode=constants.ParseMode.MARKDOWN_V2,
                reply_markup=confirm_order_keyboard(),
            )

    elif data == "confirm_order":
        cart = context.user_data.get('cart', {})
        user_id = query.from_user.id
        if cart:
            total_price = sum(
                db.query(MenuItem).get(item_id).price * quantity
                for item_id, quantity in cart.items()
                if db.query(MenuItem).get(item_id)
            )
            new_order = Order(
                user_id=user_id, total_price=total_price, status=OrderStatus.NEW
            )
            db.add(new_order)
            db.flush()

            details_text = f"🔔 *Новый заказ `#{new_order.id}`*\n\nОт: {escape_markdown(query.from_user.first_name)} \\(@{escape_markdown(query.from_user.username or 'N/A')}\\)\n\n"
            for item_id, quantity in cart.items():
                item = db.query(MenuItem).get(item_id)
                if item:
                    db.add(
                        OrderItem(
                            order_id=new_order.id,
                            item_name=item.name,
                            quantity=quantity,
                            price=item.price,
                        )
                    )
                    details_text += f"▪️ {escape_markdown(item.name)}: {escape_markdown(quantity)} шт\\.\n"
            details_text += f"\n💰 *Итого:* {escape_markdown(total_price)} руб\\."
            db.commit()

            context.user_data['cart'] = {}
            await query.edit_message_text(
                f"✅ Ваш заказ `#{new_order.id}` принят\\!",
                parse_mode=constants.ParseMode.MARKDOWN_V2,
                reply_markup=main_menu_keyboard(is_admin=is_admin),
            )

            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=details_text,
                        parse_mode=constants.ParseMode.MARKDOWN_V2,
                        reply_markup=admin_order_keyboard(new_order.id),
                    )
                except Exception as e:
                    logger.error(
                        f"Не удалось отправить уведомление админу {admin_id}: {e}"
                    )

    elif data == "my_orders":
        await my_orders(update, context)

    elif data == "admin_panel":
        if is_admin:
            await query.edit_message_text(
                "Панель администратора:", reply_markup=admin_menu_keyboard()
            )

    elif data.startswith("admin_view_orders_"):
        status_filter = data.split('_')[-1]
        orders_query = db.query(Order).order_by(Order.created_at.desc())
        if status_filter != "ALL":
            orders = orders_query.filter(Order.status == status_filter).all()
            text = f"📋 Заказы в статусе '{status_filter}':\n\n"
        else:
            orders = orders_query.limit(10).all()
            text = "📋 Последние 10 заказов:\n\n"
        if not orders:
            text += "Заказов в этой категории нет."
        else:
            for order in orders:
                user_first_name = order.user.first_name if order.user else "Удален"
                text += f"Заказ #{order.id} от {user_first_name}\n"
                text += f"Статус: {order.status}\nСумма: {order.total_price} руб.\n"
                text += f"Детали: /details_{order.id}\n\n"
        try:
            await query.edit_message_text(text, reply_markup=admin_menu_keyboard())
        except telegram.error.BadRequest as e:
            if "Message is not modified" in str(e):
                pass
            else:
                logger.error(f"ОШИБКА BadRequest при отправке текста: {text}\n{e}")

    elif data.startswith("admin_status_"):
        _, _, order_id_str, new_status = data.split("_")
        order = db.query(Order).get(int(order_id_str))
        if order:
            order.status = new_status
            db.commit()
            safe_status = escape_markdown(new_status)
            await query.edit_message_text(
                f"Статус заказа `#{order.id}` изменен на *{safe_status}*",
                parse_mode=constants.ParseMode.MARKDOWN_V2,
                reply_markup=admin_menu_keyboard(),
            )
            user_message = f"Статус вашего заказа `#{order.id}` изменен на: *{safe_status}*"
            if new_status == OrderStatus.READY:
                user_message += "\n\nВы можете забрать ваш заказ\\!"
            try:
                await context.bot.send_message(
                    chat_id=order.user_id,
                    text=user_message,
                    parse_mode=constants.ParseMode.MARKDOWN_V2,
                )
            except Exception as e:
                logger.error(
                    f"Не удалось отправить уведомление клиенту {order.user_id}: {e}"
                )

    db.close()


async def add_item_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query:
        return ConversationHandler.END
    await query.answer()

    if update.effective_user.id not in ADMIN_IDS:
        await query.answer("У вас нет прав для этого действия.", show_alert=True)
        return ConversationHandler.END

    db = next(get_db())
    leaf_categories = db.query(Category).filter(~Category.subcategories.any()).all()
    db.close()

    keyboard = [
        [InlineKeyboardButton(cat.name, callback_data=str(cat.id))]
        for cat in leaf_categories
    ]
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_action")])

    await query.edit_message_text(
        "Выберите КОНЕЧНУЮ категорию для нового блюда:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return ADD_ITEM_CATEGORY


async def add_item_category(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['new_item'] = {'category_id': int(query.data)}
    await query.edit_message_text(
        "Отлично! Теперь введите название нового блюда:",
        reply_markup=cancel_keyboard(),
    )
    return ADD_ITEM_NAME


async def add_item_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['new_item']['name'] = update.message.text
    await update.message.reply_text(
        "Название сохранено.\nТеперь введите описание (или отправьте /skip):",
        reply_markup=cancel_keyboard(),
    )
    return ADD_ITEM_DESC


async def add_item_description(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data['new_item']['description'] = update.message.text
    await update.message.reply_text(
        "Описание сохранено. Теперь введите цену в рублях (только цифры):",
        reply_markup=cancel_keyboard(),
    )
    return ADD_ITEM_PRICE


async def add_item_skip_description(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data['new_item']['description'] = None
    await update.message.reply_text(
        "Описание пропущено. Теперь введите цену в рублях (только цифры):",
        reply_markup=cancel_keyboard(),
    )
    return ADD_ITEM_PRICE


async def add_item_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    price_text = update.message.text
    if not price_text.isdigit() or int(price_text) <= 0:
        await update.message.reply_text(
            "Цена некорректна. Введите целое положительное число:",
            reply_markup=cancel_keyboard(),
        )
        return ADD_ITEM_PRICE

    new_item_data = context.user_data['new_item']
    new_item_data['price'] = int(price_text)

    db = next(get_db())
    db.add(MenuItem(**new_item_data))
    db.commit()
    db.close()

    await update.message.reply_text(
        f"✅ Новое блюдо '{new_item_data['name']}' успешно добавлено!"
    )
    del context.user_data['new_item']
    await update.message.reply_text(
        "Админ-панель:", reply_markup=admin_menu_keyboard()
    )
    return ConversationHandler.END


async def cancel_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if 'new_item' in context.user_data:
        del context.user_data['new_item']

    is_admin = update.effective_user.id in ADMIN_IDS
    keyboard = admin_menu_keyboard() if is_admin else main_menu_keyboard()

    if update.callback_query:
        await update.callback_query.edit_message_text(
            "Действие отменено.", reply_markup=keyboard
        )
    else:
        await update.message.reply_text(
            "Действие отменено.", reply_markup=keyboard
        )
    return ConversationHandler.END


async def handle_details_link(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if not (
        update.message and update.message.text and update.effective_user.id in ADMIN_IDS
    ):
        return

    order_id_str = update.message.text.split('_')[-1]
    if not order_id_str.isdigit():
        return

    db = next(get_db())
    order = db.query(Order).get(int(order_id_str))

    if not order:
        await update.message.reply_text(f"Заказ #{order_id_str} не найден.")
    else:
        user_first_name = order.user.first_name if order.user else "Удален"
        user_username = order.user.username if order.user else "N/A"
        text = f"📝 Детали заказа #{order.id}\n\n"
        text += f"Статус: {order.status}\n"
        text += f"Клиент: {user_first_name} (@{user_username})\n"
        text += f"Сумма: {order.total_price} руб.\n\nСостав:\n"
        for item in order.items:
            text += f"▪️ {item.item_name}: {item.quantity} шт.\n"
        await update.message.reply_text(
            text, reply_markup=admin_order_keyboard(order.id)
        )

    db.close()


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    add_item_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_item_start, pattern='^admin_add_item$')
        ],
        states={
            ADD_ITEM_CATEGORY: [
                CallbackQueryHandler(add_item_category, pattern=r'^\d+$')
            ],
            ADD_ITEM_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_item_name)
            ],
            ADD_ITEM_DESC: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, add_item_description
                ),
                CommandHandler('skip', add_item_skip_description),
            ],
            ADD_ITEM_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_item_price)
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_action, pattern='^cancel_action$'),
            CommandHandler('cancel', cancel_action),
        ],
        per_message=False,
    )

    application.add_handler(add_item_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.Regex(r'^\/details_\d+$'), handle_details_link)
    )
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Бот запущен...")
    application.run_polling()


if __name__ == "__main__":
    main()
    