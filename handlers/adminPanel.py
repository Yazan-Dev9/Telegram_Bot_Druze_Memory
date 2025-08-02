import logging
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
)
from telegram.ext import CallbackContext, ConversationHandler
from utils.database import database_manager
from utils.states import States


logger = logging.getLogger(__name__)


class AdminPanelHandlers:
    def __init__(self, database_manager):
        self.database_manager = database_manager

    async def show_admin_panel(self, update: Update, context: CallbackContext):
        markup = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton("إضافة مسؤول"),
                    KeyboardButton("إزالة مسؤول"),
                ],
                [
                    KeyboardButton("حظر مستخدم"),
                    KeyboardButton("إلغاء حظر مستخدم"),
                ],
                [
                    KeyboardButton("عرض قائمة الشهداء"),
                    KeyboardButton("عرض الشهداء المعلقة"),
                ],
                [
                    KeyboardButton("العودة إلى القائمة الرئيسية"),
                ],
            ],
            resize_keyboard=True,
        )
        await context.bot.send_message(
            update.effective_chat.id, "اختر إجراء المسؤول:", reply_markup=markup
        )
        return ConversationHandler.END

    async def _process_admin_action(
        self, update: Update, context: CallbackContext, action
    ):
        try:
            admin_id = int(update.message.text)
            success = action(admin_id)
            reply_text = (
                f"تم تنفيذ الإجراء بنجاح على المستخدم {admin_id}."
                if success
                else f"لم يتمكن من تنفيذ الإجراء على المستخدم {admin_id}."
            )
            await context.bot.send_message(
                update.effective_chat.id, reply_text, reply_markup=ReplyKeyboardRemove()
            )
        except ValueError:
            await context.bot.send_message(
                update.effective_chat.id,
                "معرف المستخدم يجب أن يكون رقمًا.",
                reply_markup=ReplyKeyboardRemove(),
            )
        except Exception as e:
            logger.exception(f"Error processing admin action: {e}")
            await context.bot.send_message(
                update.effective_chat.id,
                "حدث خطأ أثناء معالجة الطلب.",
                reply_markup=ReplyKeyboardRemove(),
            )
        return ConversationHandler.END

    async def add_admin_button(self, update: Update, context: CallbackContext):
        await context.bot.send_message(
            update.effective_chat.id,
            "يرجى إدخال معرف المستخدم (user ID) للمسؤول الجديد:",
        )
        context.user_data["admin_action"] = "add_admin"
        return States.PROCESS_ADMIN_ACTION

    async def process_add_admin(self, update: Update, context: CallbackContext):
        await self._process_admin_action(
            update, context, self.database_manager.add_admin
        )
        return ConversationHandler.END

    async def remove_admin_button(self, update: Update, context: CallbackContext):
        await context.bot.send_message(
            update.effective_chat.id,
            "يرجى إدخال معرف المستخدم (user ID) للمسؤول الذي تريد إزالته:",
        )
        context.user_data["admin_action"] = "remove_admin"
        return States.PROCESS_ADMIN_ACTION

    async def process_remove_admin(self, update: Update, context: CallbackContext):
        await self._process_admin_action(
            update, context, self.database_manager.remove_admin
        )
        return ConversationHandler.END

    async def block_user_button(self, update: Update, context: CallbackContext):
        await context.bot.send_message(
            update.effective_chat.id,
            "يرجى إدخال معرف المستخدم (user ID) للمستخدم الذي تريد حظره:",
        )
        context.user_data["admin_action"] = "block_user"
        return States.PROCESS_ADMIN_ACTION

    async def process_block_user(self, update: Update, context: CallbackContext):
        await self._process_admin_action(
            update, context, self.database_manager.block_user
        )
        return ConversationHandler.END

    async def unblock_user_button(self, update: Update, context: CallbackContext):
        await context.bot.send_message(
            update.effective_chat.id,
            "يرجى إدخال معرف المستخدم (user ID) للمستخدم الذي تريد إلغاء حظره:",
        )
        context.user_data["admin_action"] = "unblock_user"
        return States.PROCESS_ADMIN_ACTION

    async def process_unblock_user(self, update: Update, context: CallbackContext):
        await self._process_admin_action(
            update, context, self.database_manager.unblock_user
        )
        return ConversationHandler.END

    async def show_pending_martyrs(self, update: Update, context: CallbackContext):
        """Displays a list of pending martyrs to the admin."""
        pending_martyrs = self.database_manager.get_pending_martyrs()

        if not pending_martyrs:
            await context.bot.send_message(
                update.effective_chat.id, "لا يوجد شهداء معلقة للموافقة عليها."
            )
            return ConversationHandler.END

        keyboard = []
        for martyr in pending_martyrs:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{martyr['name']} (ID: {martyr['id']})",
                        callback_data=f"review_martyr_{martyr['id']}",
                    )
                ]
            )

        keyboard.append([InlineKeyboardButton(
            "العودة", callback_data="admin_panel")])

        markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            update.effective_chat.id,
            "الشهداء المعلقة للموافقة عليها:",
            reply_markup=markup,
        )
        return States.HANDLE_PENDING_MARTYR_SELECTION

    async def handle_pending_martyr_selection(
        self, update: Update, context: CallbackContext
    ):
        """Handles the selection of a pending martyr."""
        query = update.callback_query
        await query.answer()

        if query.data == "admin_panel":
            await self.show_admin_panel(update, context)
            return ConversationHandler.END

        if query.data.startswith("review_martyr_"):
            martyr_id = int(query.data[len("review_martyr_"):])
            martyr = database_manager.search_martyr(martyr_id)

            if not martyr:
                await query.edit_message_text("الشهيد غير موجود.")
                return ConversationHandler.END

            await self.display_martyr_for_review(update, context, martyr)

            return ConversationHandler.END

        else:
            await query.edit_message_text("أمر غير صالح.")
            return ConversationHandler.END

    async def display_martyr_for_review(
        self, update: Update, context: CallbackContext, martyr
    ):
        """Displays the martyr information with approval/rejection buttons."""
        query = update.callback_query
        message_text = (
            "<b>معلومات الشهيد (للمراجعة):</b>\n\n"
            f"الاسم: {martyr['name']}\n"
            f"اسم الأم: {martyr['mother_name']}\n"
            f"تاريخ الميلاد: {martyr['birth_date']}\n"
            f"تاريخ الوفاة: {martyr['death_date']}\n"
            f"سبب الوفاة: {martyr['death_cause']}\n"
            f"مكان الإقامة: {martyr['residence']}\n"
            f"ملاحظات: {martyr.get('notes', 'لا يوجد')}\n"
        )
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        "الموافقة", callback_data=f"approve_{martyr['id']}"
                    ),
                    InlineKeyboardButton(
                        "الرفض", callback_data=f"reject_{martyr['id']}"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "العودة إلى قائمة الانتظار", callback_data="pending_list"
                    )
                ],
            ]
        )
        try:
            if martyr["photo"]:
                with open(martyr["photo"], "rb") as photo_file:
                    await context.bot.send_photo(
                        chat_id=query.message.chat.id,
                        photo=photo_file,
                        caption=message_text,
                        parse_mode="HTML",
                        reply_markup=markup,
                    )
            else:
                await context.bot.send_message(
                    chat_id=query.message.chat.id,
                    text=message_text,
                    parse_mode="HTML",
                    reply_markup=markup,
                )

            await query.message.delete()

        except Exception as e:
            logger.exception(f"Error sending data to admin for review: {e}")
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text="حدث خطأ أثناء عرض بيانات الشهيد.",
            )

    async def handle_admin_approval_from_list(
        self, update: Update, context: CallbackContext
    ):
        """Handles the approval or rejection of a martyr from the pending list."""
        query = update.callback_query
        await query.answer()
        admin_id = query.from_user.id
        if not self.database_manager.is_admin(admin_id):
            await context.bot.send_message(
                query.message.chat.id, "ليس لديك صلاحية لتنفيذ هذا الإجراء."
            )
            return ConversationHandler.END

        action, martyr_id = query.data.split("_", 1)
        martyr_id = int(martyr_id)

        if action == "approve":
            success = self.database_manager.approve_martyr(martyr_id)
            if success:
                await query.edit_message_text("تمت الموافقة على بيانات وحفظها.")
            else:
                await query.edit_message_text("حدث خطأ أثناء حفظ البيانات.")

        elif action == "reject":
            # For simplicity, we're just deleting the entry.  You might want to add a 'rejected' flag.
            # success = self.database_manager.delete_martyr(martyr_id) # Hypothetical delete function
            # if success:
            #     await query.edit_message_text("تم رفض بيانات الشهيد وحذفها.")
            # else:
            #     await query.edit_message_text("حدث خطأ أثناء حذف البيانات.")

            await query.edit_message_text("تم رفض البيانات.")

        elif action == "pending_list":
            await self.show_pending_martyrs(update, context)
            return States.HANDLE_PENDING_MARTYR_SELECTION

        else:
            await query.edit_message_text("أمر غير صالح.")

        return ConversationHandler.END

    async def show_all_martyrs(self, update: Update, context: CallbackContext):
        """Displays a list of all approved martyrs to the admin."""
        all_martyrs = self.database_manager.get_all_martyrs()

        if not all_martyrs:
            await context.bot.send_message(
                update.effective_chat.id, "لا يوجد بيانات محفوظة."
            )
            return ConversationHandler.END

        message_text = "<b>قائمة الشهداء:</b>\n\n"
        for martyr in all_martyrs:
            message_text += (
                f"- {martyr['name']} (تاريخ الوفاة: {martyr['death_date']})\n"
            )

        message_text += "\n<i>العدد الإجمالي: {}</i>".format(len(all_martyrs))

        await context.bot.send_message(
            update.effective_chat.id, message_text, parse_mode="HTML"
        )
        return ConversationHandler.END
