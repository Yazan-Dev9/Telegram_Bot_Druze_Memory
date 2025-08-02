from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from utils.config import config
from utils.database import database_manager
from handlers.bot import BotHandlers, States, logging, Update, ConversationHandler


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    application = ApplicationBuilder().token(config.BOT_TOKEN).build()
    bot_handlers = BotHandlers(database_manager)

    application.add_handler(CommandHandler("start", bot_handlers.start))
    application.add_handler(CommandHandler("cancel", bot_handlers.cancel))

    martyr_conversation_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex("^(إضافة شهيد)$"),
                bot_handlers.martyr_handler.add_martyr_button,
            )
        ],
        states={
            States.CHECK_MARTYR_EXISTS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    bot_handlers.martyr_handler.check_martyr_exists,
                )
            ],
            States.STATE_MOTHER_NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    bot_handlers.martyr_handler._handle_mother_name,
                )
            ],
            States.STATE_BIRTH_DATE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    bot_handlers.martyr_handler._handle_birth_date,
                )
            ],
            States.STATE_DEATH_DATE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    bot_handlers.martyr_handler._handle_death_date,
                )
            ],
            States.STATE_DEATH_CAUSE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    bot_handlers.martyr_handler._handle_death_cause,
                )
            ],
            States.STATE_RESIDENCE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    bot_handlers.martyr_handler._handle_residence,
                )
            ],
            States.STATE_PHOTO: [
                MessageHandler(filters.PHOTO, bot_handlers.martyr_handler.handle_photo)
            ],
            States.STATE_NOTES: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    bot_handlers.martyr_handler._handle_notes,
                )
            ],
            States.STATE_CONFIRM: [
                CallbackQueryHandler(
                    bot_handlers.martyr_handler.handle_confirmation)
            ],
            States.STATE_EDIT: [
                CallbackQueryHandler(
                    bot_handlers.martyr_handler.handle_edit_callback)
            ],
            States.EDIT_FIELD: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    bot_handlers.martyr_handler.edit_field,
                )
            ],
            States.STATE_DISPLAY: [
                CallbackQueryHandler(
                    bot_handlers.martyr_handler.handle_edit_callback)
            ],

        },
        fallbacks=[CommandHandler("cancel", bot_handlers.cancel)],
    )
    application.add_handler(martyr_conversation_handler)

    admin_conversation_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex("^(لوحة التحكم)$"),
                bot_handlers.admin_panel_handler.show_admin_panel,
            )
        ],
        states={
            States.PROCESS_ADMIN_ACTION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    bot_handlers.admin_panel_handler.process_add_admin,
                )
            ],
            States.HANDLE_PENDING_MARTYR_SELECTION: [
                CallbackQueryHandler(
                    bot_handlers.admin_panel_handler.handle_pending_martyr_selection,
                ),
                CallbackQueryHandler(
                    bot_handlers.admin_panel_handler.handle_admin_approval_from_list,
                ),
            ],
        },
        fallbacks=[CommandHandler("cancel", bot_handlers.cancel)],
    )
    application.add_handler(admin_conversation_handler)

    search_conversation_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
            filters.Regex("^(البحث عن شهيد)$"),
            bot_handlers.martyr_handler.search_martyr_button,
            )
        ],
        states={
            States.PROCESS_SEARCH_MARTYR: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    bot_handlers.martyr_handler.process_search_martyr,
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", bot_handlers.cancel)],
    )
    application.add_handler(search_conversation_handler)
    
    application.add_handler(
        MessageHandler(
            filters.Regex("^(عرض قائمة الشهداء)$"),
            bot_handlers.admin_panel_handler.show_all_martyrs,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex("^(عرض الشهداء المعلقة)$"),
            bot_handlers.admin_panel_handler.show_pending_martyrs,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex("^(إضافة مسؤول)$"),
            bot_handlers.admin_panel_handler.add_admin_button,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex("^(إزالة مسؤول)$"),
            bot_handlers.admin_panel_handler.remove_admin_button,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex("^(حظر مستخدم)$"),
            bot_handlers.admin_panel_handler.block_user_button,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex("^(إلغاء حظر مستخدم)$"),
            bot_handlers.admin_panel_handler.unblock_user_button,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.Regex("^(العودة إلى القائمة الرئيسية)$"),
            bot_handlers.show_main_menu,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            bot_handlers.martyr_handler.handle_admin_approval,
            pattern="^approve_|^reject_",
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            bot_handlers.martyr_handler.handle_edit_callback,
            pattern="^edit_|^skip_|^confirm_all",
        )
    )

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, bot_handlers.handle_text)
    )
    # application.add_handler(MessageHandler(
    #     filters.PHOTO, bot_handlers.handle_photo))

    application.add_error_handler(bot_handlers.error_handler)

    try:
        database_manager.connect()
        if config.FIRST_ADMIN_ID:
            try:
                admin_id = int(config.FIRST_ADMIN_ID)
                database_manager.add_admin(admin_id)
                logger.info(f"Added first admin with ID: {admin_id}")
            except ValueError:
                logger.error(
                    "FIRST_ADMIN_ID في ملف config يجب أن يكون رقمًا صحيحًا.")
            except Exception as e:
                logger.error(f"Failed to add first admin: {e}")

        logger.info("Bot started successfully.")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.exception("Bot failed to start: {e} ")
    finally:
        database_manager.close()


if __name__ == "__main__":
    main()
