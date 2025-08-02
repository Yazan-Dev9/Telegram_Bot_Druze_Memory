from telegram import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from handlers.martyr import (
    MartyrHandlers,
    logging,
    Update,
    CallbackContext,
    ConversationHandler,
)
from handlers.adminPanel import AdminPanelHandlers
from utils.filters import spam_filter


logger = logging.getLogger(__name__)


class BotHandlers:
    def __init__(self, database_manager):
        self.database_manager = database_manager
        self.martyr_handler = MartyrHandlers(database_manager)
        self.admin_panel_handler = AdminPanelHandlers(database_manager)

    async def start(self, update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        if self.database_manager.is_blocked(user_id):
            await context.bot.send_message(
                update.effective_chat.id, "أنت محظور من استخدام هذا البوت."
            )
            return ConversationHandler.END

        await self.show_main_menu(update, context)
        return ConversationHandler.END

    async def show_main_menu(self, update: Update, context: CallbackContext):
        keyboard = [
            [
                KeyboardButton("إضافة شهيد"),
                KeyboardButton("البحث عن شهيد")
            ],
        ]
        if self.database_manager.is_admin(update.effective_user.id):
            keyboard.append([KeyboardButton("لوحة التحكم")])
        markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
        await context.bot.send_message(
            update.effective_chat.id, "اختر إجراء:", reply_markup=markup
        )
        return ConversationHandler.END

    async def handle_text(self, update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        if spam_filter.is_spam(update.message):
            self.database_manager.block_user(user_id)
            await context.bot.send_message(
                update.effective_chat.id, "تم حظرك بسبب إرسال رسائل متكررة."
            )
            return ConversationHandler.END

        if self.database_manager.is_blocked(user_id):
            await context.bot.send_message(
                update.effective_chat.id, "أنت محظور من استخدام هذا البوت."
            )
            return ConversationHandler.END

        text = update.message.text
        if text == "إضافة شهيد":
            return await self.martyr_handler.add_martyr_button(update, context)
        elif text == "البحث عن شهيد":
            return await self.martyr_handler.search_martyr_button(update, context)
        elif text == "لوحة التحكم":
            return await self.admin_panel_handler.show_admin_panel(update, context)

        elif text == "عرض قائمة الشهداء" and self.database_manager.is_admin(
            update.effective_user.id
        ):
            return await self.admin_panel_handler.show_all_martyrs(update, context)

        elif text == "عرض الشهداء المعلقة" and self.database_manager.is_admin(
            update.effective_user.id
        ):
            return await self.admin_panel_handler.show_pending_martyrs(update, context)

        else:
            await context.bot.send_message(
                update.effective_chat.id,
                "عفواً، لا يمكنني فهم ما طلبته. الرجاء استخدام القائمة.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return ConversationHandler.END

    async def error_handler(self, update: Update, context: CallbackContext):
        "Handle errors in bot"
        pass

    async def cancel(self, update: Update, context: CallbackContext):
        """Cancels and ends the conversation."""
        context.user_data.clear()
        await update.message.reply_text(
            "تم إلغاء العملية وتم مسح جميع البيانات.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END
