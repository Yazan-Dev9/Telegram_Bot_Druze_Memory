import uuid
import os
import logging
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
)
from telegram.ext import CallbackContext, ConversationHandler
from utils.dateValidator import DateValidator
from utils.config import config
from utils.states import States


logger = logging.getLogger(__name__)


class MartyrHandlers:
    def __init__(self, database_manager):
        self.database_manager = database_manager
        self.MAX_TEXT_LENGTH = 200

    async def add_martyr_button(self, update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        if self.database_manager.is_blocked(user_id):
            await context.bot.send_message(
                update.effective_chat.id, "أنت محظور من استخدام هذا البوت."
            )
            return ConversationHandler.END

        await context.bot.send_message(
            update.effective_chat.id, "يرجى إدخال اسم الشهيد كاملاً للتحقق:"
        )
        return States.CHECK_MARTYR_EXISTS

    async def check_martyr_exists(self, update: Update, context: CallbackContext):
        martyr_name = update.message.text.strip()
        martyr = self.database_manager.search_martyr(martyr_name)
        if martyr:
            await context.bot.send_message(
                update.effective_chat.id,
                "هذا الشهيد موجود بالفعل في قاعدة البيانات.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return ConversationHandler.END
        else:
            context.user_data["martyr_data"] = {"name": martyr_name}
            await context.bot.send_message(
                update.effective_chat.id,
                "الشهيد غير موجود، يرجى إكمال البيانات:",
                reply_markup=ReplyKeyboardRemove(),
            )
            await context.bot.send_message(
                update.effective_chat.id, "يرجى إدخال اسم الأم الكامل:"
            )
            return States.STATE_MOTHER_NAME

    async def search_martyr_button(self, update: Update, context: CallbackContext):
        await context.bot.send_message(
            update.effective_chat.id, "يرجى إدخال اسم الشهيد للبحث:"
        )
        return States.PROCESS_SEARCH_MARTYR

    async def process_search_martyr(self, update: Update, context: CallbackContext):
        martyr_name = update.message.text.strip()
        martyr = self.database_manager.search_martyr(martyr_name)
        print(martyr)
        if martyr:
            martyr_info = (
                "<b>معلومات الشهيد:</b>\n"
                f"الاسم: {martyr['name']}\n"
                f"اسم الأم: {martyr['mother_name']}\n"
                f"تاريخ الميلاد: {martyr['birth_date']}\n"
                f"تاريخ الوفاة: {martyr['death_date']}\n"
                f"سبب الوفاة: {martyr['death_cause']}\n"
                f"مكان الإقامة: {martyr['residence']}\n"
                f"ملاحظات: {martyr.get('notes', 'لا يوجد')}\n"
            )
            if martyr["photo"]:
                try:
                    with open(martyr["photo"], "rb") as photo_file:
                        await context.bot.send_photo(
                            update.effective_chat.id,
                            photo_file,
                            caption=martyr_info,
                            parse_mode="HTML",
                        )
                except FileNotFoundError:
                    await context.bot.send_message(
                        update.effective_chat.id,
                        "الصورة غير موجودة.",
                        parse_mode="HTML",
                    )
                except Exception as e:
                    logger.exception(f"Error sending photo: {e}")
                    await context.bot.send_message(
                        update.effective_chat.id,
                        "حدث خطأ أثناء عرض الصورة.",
                        parse_mode="HTML",
                    )

            else:
                await context.bot.send_message(
                    update.effective_chat.id, martyr_info, parse_mode="HTML"
                )
        else:
            await context.bot.send_message(
                update.effective_chat.id, "لم يتم العثور على شهيد بهذا الاسم."
            )
        return ConversationHandler.END

    async def _handle_mother_name(self, update: Update, context: CallbackContext):
        if len(update.message.text) > self.MAX_TEXT_LENGTH:
            await context.bot.send_message(
                update.effective_chat.id, "اسم الأم طويل جداً. يرجى تقصيره."
            )
            return States.STATE_MOTHER_NAME

        context.user_data["martyr_data"]["mother_name"] = update.message.text.strip(
        )
        await context.bot.send_message(
            update.effective_chat.id, "يرجى إدخال تاريخ الميلاد (YYYY-MM-DD):"
        )
        return States.STATE_BIRTH_DATE

    async def _handle_birth_date(self, update: Update, context: CallbackContext):
        birth_date = update.message.text
        if DateValidator.validate_date(birth_date):
            if not DateValidator.is_future_date(birth_date):
                context.user_data["martyr_data"]["birth_date"] = birth_date
                await context.bot.send_message(
                    update.effective_chat.id, "يرجى إدخال تاريخ الوفاة (YYYY-MM-DD):"
                )
                return States.STATE_DEATH_DATE
            else:
                await context.bot.send_message(
                    update.effective_chat.id,
                    "تاريخ الميلاد يجب ألا يكون في المستقبل. يرجى إدخاله بالتنسيق YYYY-MM-DD:",
                )
                return States.STATE_BIRTH_DATE
        else:
            await context.bot.send_message(
                update.effective_chat.id,
                "تاريخ الميلاد غير صحيح. يرجى إدخاله بالتنسيق YYYY-MM-DD:",
            )
            return States.STATE_BIRTH_DATE

    async def _handle_death_date(self, update: Update, context: CallbackContext):
        death_date = update.message.text
        if DateValidator.validate_date(death_date):
            if not DateValidator.is_future_date(death_date):
                context.user_data["martyr_data"]["death_date"] = death_date
                await context.bot.send_message(
                    update.effective_chat.id, "يرجى إدخال سبب الوفاة:"
                )
                return States.STATE_DEATH_CAUSE
            else:
                await context.bot.send_message(
                    update.effective_chat.id,
                    "تاريخ الوفاة يجب ألا يكون في المستقبل. يرجى إدخاله بالتنسيق YYYY-MM-DD:",
                )
                return States.STATE_DEATH_DATE
        else:
            await context.bot.send_message(
                update.effective_chat.id,
                "تاريخ الوفاة غير صحيح. يرجى إدخاله بالتنسيق YYYY-MM-DD:",
            )
            return States.STATE_DEATH_DATE

    async def _handle_death_cause(self, update: Update, context: CallbackContext):
        if len(update.message.text) > self.MAX_TEXT_LENGTH:
            await context.bot.send_message(
                update.effective_chat.id, "سبب الوفاة طويل جداً. يرجى تقصيره."
            )
            return States.STATE_DEATH_CAUSE
        context.user_data["martyr_data"]["death_cause"] = update.message.text.strip(
        )
        await context.bot.send_message(
            update.effective_chat.id, "يرجى إدخال مكان الإقامة:"
        )
        return States.STATE_RESIDENCE

    async def _handle_residence(self, update: Update, context: CallbackContext):
        if len(update.message.text) > self.MAX_TEXT_LENGTH:
            await context.bot.send_message(
                update.effective_chat.id, "مكان الإقامة طويل جداً. يرجى تقصيره."
            )
            return States.STATE_RESIDENCE
        context.user_data["martyr_data"]["residence"] = update.message.text.strip()
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    "تخطي الصورة", callback_data="skip_photo")]
            ]
        )
        await context.bot.send_message(
            update.effective_chat.id,
            "يرجى إرسال صورة الشهيد أو تخطي الصورة:",
            reply_markup=markup,
        )
        return States.STATE_PHOTO

    async def _handle_notes(self, update: Update, context: CallbackContext):
        if len(update.message.text) > self.MAX_TEXT_LENGTH:
            await context.bot.send_message(
                update.effective_chat.id, "الملاحظات طويلة جداً. يرجى تقصيرها."
            )
            return States.STATE_NOTES
        context.user_data["martyr_data"]["notes"] = update.message.text.strip()
        await self.show_display_info(update, context)
        return States.STATE_DISPLAY

    async def handle_photo(self, update: Update, context: CallbackContext):
        try:
            os.makedirs(config.UPLOAD_PATH, exist_ok=True)
            photo_file = await update.message.photo[-1].get_file()
            photo_name = f"{uuid.uuid4()}.jpg"
            photo_path = os.path.join(config.UPLOAD_PATH, photo_name)

            await photo_file.download_to_drive(photo_path)

            context.user_data["martyr_data"]["photo"] = photo_path
            await context.bot.delete_message(
                update.effective_chat.id, update.message.message_id
            )
            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(
                        "تخطي الملاحظات", callback_data="skip_notes")]
                ]
            )
            await context.bot.send_message(
                update.effective_chat.id,
                "تم استلام الصورة. يرجى إدخال أي ملاحظات إضافية أو تخطي الملاحظات:",
                reply_markup=markup,
            )
            return States.STATE_NOTES
        except Exception as e:
            logger.exception(f"Error handling photo: {e}")
            await context.bot.send_message(
                update.effective_chat.id, "حدث خطأ أثناء معالجة الصورة."
            )
            return States.STATE_PHOTO

    async def show_confirmation_keyboard(
        self, update: Update, context: CallbackContext
    ):
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton("تأكيد", callback_data="confirm"),
                    InlineKeyboardButton("تعديل", callback_data="edit"),
                ]
            ],
        )
        await context.bot.send_message(
            update.effective_chat.id,
            "هل أنت متأكد من صحة البيانات؟",
            reply_markup=markup,
        )
        return States.STATE_CONFIRM

    async def handle_confirmation(self, update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer("جاري ارسال البيانات")
        if query.data == "confirm":
            admin_user_id = config.ADMIN_USER_ID
            if admin_user_id:
                await self.send_data_to_admin(update, context, admin_user_id)
                await context.bot.send_message(
                    update.effective_chat.id,
                    "تم إرسال البيانات إلى المسؤول للمراجعة.",
                    reply_markup=ReplyKeyboardRemove(),
                )
                return ConversationHandler.END
            else:
                await context.bot.send_message(
                    update.effective_chat.id,
                    "لم يتم العثور على معرف المسؤول يرجى المحاولة مرة أخرى",
                    reply_markup=ReplyKeyboardRemove(),
                )
                return ConversationHandler.END
        elif query.data == "edit":
            await self.show_edit_options(update, context)
            return States.STATE_EDIT
        else:
            await context.bot.send_message(
                update.effective_chat.id,
                "أمر غير صالح.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return States.STATE_CONFIRM

    async def send_data_to_admin(
        self, update: Update, context: CallbackContext, config_admin_user_id
    ):
        data = context.user_data["martyr_data"]
        message_text = (
            "<b>معلومات الشهيد (للمراجعة):</b>\n\n"
            f"الاسم: {data['name']}\n"
            f"اسم الأم: {data['mother_name']}\n"
            f"تاريخ الميلاد: {data['birth_date']}\n"
            f"تاريخ الوفاة: {data['death_date']}\n"
            f"سبب الوفاة: {data['death_cause']}\n"
            f"مكان الإقامة: {data['residence']}\n"
            f"ملاحظات: {data.get('notes', 'لا يوجد')}\n"
        )
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        "الموافقة", callback_data=f"approve_{update.effective_user.id}"
                    ),
                    InlineKeyboardButton(
                        "الرفض", callback_data=f"reject_{update.effective_user.id}"
                    ),
                ]
            ]
        )
        try:
            if "photo" in data and data["photo"]:
                photo_path = data["photo"]
                if os.path.exists(photo_path):
                    with open(photo_path, "rb") as photo_file:
                        await context.bot.send_photo(
                            config_admin_user_id,
                            photo_file,
                            caption=message_text,
                            parse_mode="HTML",
                            reply_markup=markup,
                        )
                else:
                    await context.bot.send_message(
                        update.effective_chat.id,
                        "الصورة غير موجودة.",
                        reply_markup=ReplyKeyboardRemove(),
                    )
            else:
                await context.bot.send_message(
                    config_admin_user_id,
                    message_text,
                    parse_mode="HTML",
                    reply_markup=markup,
                )
        except Exception as e:
            logger.exception(
                f"Error sending data to admin (user_id={update.effective_user.id}, admin_id={config_admin_user_id}): {e}"
            )
            await context.bot.send_message(
                update.effective_chat.id,
                "حدث خطأ أثناء إرسال البيانات إلى المسؤول.",
                reply_markup=ReplyKeyboardRemove(),
            )

    async def handle_admin_approval(self, update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()
        admin_id = query.from_user.id
        if not self.database_manager.is_admin(admin_id):
            await context.bot.send_message(
                update.effective_chat.id, "ليس لديك صلاحية لتنفيذ هذا الإجراء."
            )
            return

        action, user_id = query.data.split("_", 1)
        user_id = int(user_id)

        try:
            if action == "approve":
                data = context.user_data["martyr_data"]
                success = self.database_manager.save_martyr_data(data)
                if success:
                    await context.bot.send_message(
                        user_id,
                        "تمت الموافقة على بياناتك وحفظها.",
                        reply_markup=ReplyKeyboardRemove(),
                    )
                else:
                    await context.bot.send_message(
                        user_id,
                        "حدث خطأ أثناء حفظ البيانات أو أن الشهيد موجود بالفعل.",
                        reply_markup=ReplyKeyboardRemove(),
                    )
            elif action == "reject":
                await context.bot.send_message(
                    user_id,
                    "تم رفض بياناتك. يرجى المحاولة مرة أخرى.",
                    reply_markup=ReplyKeyboardRemove(),
                )
            else:
                await context.bot.send_message(
                    update.effective_chat.id, "خطأ غير متوقع."
                )

            del context.user_data["martyr_data"]
            await context.bot.edit_message_reply_markup(
                chat_id=query.message.chat.id,
                message_id=query.message.message_id,
                reply_markup=None,
            )
            await context.bot.send_message(
                update.effective_chat.id, "تم تنفيذ الإجراء."
            )

        except Exception as e:
            logger.exception(f"Error handling admin approval: {e}")
            await context.bot.send_message(
                update.effective_chat.id, "حدث خطأ أثناء معالجة الطلب."
            )

    async def show_edit_options(self, update: Update, context: CallbackContext):
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton("الاسم", callback_data="edit_name"),
                    InlineKeyboardButton(
                        "اسم الأم", callback_data="edit_mother_name"),
                ],
                [
                    InlineKeyboardButton(
                        "تاريخ الميلاد", callback_data="edit_birth_date"
                    ),
                    InlineKeyboardButton(
                        "تاريخ الوفاة", callback_data="edit_death_date"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "سبب الوفاة", callback_data="edit_death_cause"
                    ),
                    InlineKeyboardButton(
                        "مكان الإقامة", callback_data="edit_residence"
                    ),
                ],
                [
                    InlineKeyboardButton("الصورة", callback_data="edit_photo"),
                    InlineKeyboardButton(
                        "الملاحظات", callback_data="edit_notes"),
                ],
                [
                    InlineKeyboardButton("رجوع", callback_data="back"),
                ]
            ]
        )
        await context.bot.send_message(
            update.effective_chat.id,
            "اختر الحقل الذي تريد تعديله:",
            reply_markup=markup,
        )
        return States.STATE_EDIT

    async def handle_edit_callback(self, update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()
        data = query.data
        if data == "edit_all":
            await self.show_edit_options(update, context)
            return States.STATE_EDIT
        elif data == "confirm_all":
            await self.show_confirmation_keyboard(update, context)
            return States.STATE_CONFIRM
        elif data == "skip_photo":
            context.user_data["martyr_data"]["photo"] = None
            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(
                        "تخطي الملاحظات", callback_data="skip_notes")]
                ]
            )
            await context.bot.send_message(
                update.effective_chat.id,
                " يرجى إدخال أي ملاحظات إضافية أو تخطي الملاحظات:",
                reply_markup=markup,
            )
            return States.STATE_NOTES
        elif data == "skip_notes":
            context.user_data["martyr_data"]["notes"] = None
            await self.show_display_info(update, context)
            return States.STATE_DISPLAY
        elif data == "back":
            await self.show_display_info(update, context)
            return States.STATE_DISPLAY
        elif data.startswith("edit_"):
            field = data[5:]
            await context.bot.send_message(
                update.effective_chat.id, f"أدخل {field} جديد:"
            )
            context.user_data["edit_field"] = field
            return States.EDIT_FIELD
        else:
            await context.bot.send_message(
                update.effective_chat.id, "لا يوجد إجراء مطابق."
            )
            return States.STATE_EDIT

    async def edit_field(self, update: Update, context: CallbackContext):
        field = context.user_data.get("edit_field")
        text = update.message.text.strip()
        context.user_data["martyr_data"][field] = text
        await self.show_display_info(update, context)
        return States.STATE_DISPLAY

    async def show_display_info(self, update: Update, context: CallbackContext):
        data = context.user_data["martyr_data"]
        message_text = (
            "<b>معلومات الشهيد:</b>\n\n"
            f"الاسم: {data['name']}\n"
            f"اسم الأم: {data['mother_name']}\n"
            f"تاريخ الميلاد: {data['birth_date']}\n"
            f"تاريخ الوفاة: {data['death_date']}\n"
            f"سبب الوفاة: {data['death_cause']}\n"
            f"مكان الإقامة: {data['residence']}\n"
            f"ملاحظات: {data.get('notes', 'لا يوجد')}\n"
        )
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton("تعديل", callback_data="edit_all"),
                    InlineKeyboardButton("إرسال", callback_data="confirm_all"),
                ]
            ]
        )
        if "photo" in data and data["photo"]:
            photo_path = data["photo"]
            if os.path.exists(photo_path):
                try:
                    with open(photo_path, "rb") as photo_file:
                        await context.bot.send_photo(
                            update.effective_chat.id,
                            photo_file,
                            caption=message_text,
                            parse_mode="HTML",
                            reply_markup=markup,
                        )
                except FileNotFoundError:
                    await context.bot.send_message(
                        update.effective_chat.id,
                        "الصورة غير موجودة.",
                        reply_markup=markup,
                    )

                except Exception as e:
                    logger.exception(f"Error sending photo: {e}")
                    await context.bot.send_message(
                        update.effective_chat.id,
                        "حدث خطأ أثناء عرض الصورة.",
                        reply_markup=markup,
                    )

            else:
                await context.bot.send_message(
                    update.effective_chat.id,
                    "الصورة غير موجودة.",
                    reply_markup=markup,
                )
        else:
            await context.bot.send_message(
                update.effective_chat.id,
                message_text,
                parse_mode="HTML",
                reply_markup=markup,
            )
        return States.STATE_DISPLAY

    def is_valid_user_id(self, user_id):
        try:
            user_id = int(user_id)
            return user_id > 0
        except ValueError:
            return False
