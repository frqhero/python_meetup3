import os

from environs import Env
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, ConversationHandler, CommandHandler, CallbackQueryHandler
import django


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meetup_management.settings')
django.setup()

from management.models import Meetup

MEETUP = 0


def get_updater():
    env = Env()
    env.read_env()
    tg_bot_token = env('TG_BOT_TOKEN')
    return Updater(token=tg_bot_token)


def start(update, context):
    inline_keyboard_buttons = [
        [InlineKeyboardButton(meetup.title, callback_data=meetup.id)]
        for meetup in Meetup.objects.all()
    ]
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard_buttons)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Выберете мероприятие!",
        reply_markup=inline_keyboard,
    )

    return MEETUP


def meetup_handler(update, context):
    meetup = Meetup.objects.get(id=update.callback_query.data)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=meetup.description
    )

    # update.message.reply_text(meetup.description)


def stop(update, context) -> int:
    """End Conversation by command."""
    update.message.reply_text('Okay, bye.')

    return ConversationHandler.END


if __name__ == '__main__':
    updater = get_updater()
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={MEETUP: [CallbackQueryHandler(meetup_handler)]},
        fallbacks=[CommandHandler('stop', stop)]
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()

    updater.idle()

    # print(Event.objects.create())