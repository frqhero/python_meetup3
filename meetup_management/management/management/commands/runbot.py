import os

from django.core.management.base import BaseCommand
from environs import Env
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, ConversationHandler, CommandHandler, CallbackQueryHandler
import django


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meetup_management.settings')
django.setup()

from management.models import Meetup


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

    # context.bot.send_message(
    #     chat_id=update.effective_chat.id,
    #     text="Выберете мероприятие!",
    #     reply_markup=inline_keyboard,
    # )

    update.message.reply_text(
        "Hi! My name is Doctor Botter. I will hold a more complex conversation with you. "
        "Why don't you tell me something about yourself?",
        reply_markup=inline_keyboard,
    )

    return 'MEETUP'


def meetup_handler(update, context):
    meetup = Meetup.objects.get(id=update.callback_query.data)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=meetup.description
    )

    return 'ROLES'


def roles_handler(update, context):
    text = 'Выберете желаемую роль'
    role_buttons = [
        InlineKeyboardButton(text='Организатор', callback_data='Организатор'),
        InlineKeyboardButton(text='Докладчик', callback_data='Докладчик'),
        InlineKeyboardButton(text='Пользователь', callback_data='Пользователь')
    ]
    keyboard = InlineKeyboardMarkup(role_buttons)
    update.message.reply_text('asf')

    return 'ROLES'


def stop(update, context) -> int:
    """End Conversation by command."""
    update.message.reply_text('Okay, bye.')

    return ConversationHandler.END


class Command(BaseCommand):
    def handle(self, *args, **options):
        updater = get_updater()
        dispatcher = updater.dispatcher

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                'MEETUP': [CallbackQueryHandler(meetup_handler)],
                'ROLES': [CallbackQueryHandler(roles_handler)],
            },
            fallbacks=[CommandHandler('stop', stop)]
        )

        dispatcher.add_handler(conv_handler)

        updater.start_polling()

        updater.idle()
