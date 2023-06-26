import os

from django.core.management.base import BaseCommand
from environs import Env
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Updater,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
)
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

    update.message.reply_text(
        'Добро пожаловать! Данный сервис позволит Вам управлять митапами. '
        'Выберите интересующий Вас митап!',
        reply_markup=inline_keyboard,
    )

    return 'MEETUP'


def meetup_handler(update, context):
    meetup = Meetup.objects.get(id=update.callback_query.data)
    context.user_data['meetup'] = meetup
    update.callback_query.message.reply_text(meetup.description)
    role_buttons = [
        InlineKeyboardButton(text='Организатор', callback_data='Организатор'),
        InlineKeyboardButton(text='Докладчик', callback_data='Speaker'),
        InlineKeyboardButton(
            text='Пользователь', callback_data='Пользователь'
        ),
    ]
    keyboard = InlineKeyboardMarkup([role_buttons])
    update.callback_query.message.reply_text(
        'Выберите роль для использования сервиса!',
        reply_markup=keyboard,
    )

    return 'ROLES'


def get_speaker_options(update, context):
    role_buttons = [
        [
            InlineKeyboardButton(
                text='Показать заданные вопросы', callback_data='questions'
            )
        ],
        [
            InlineKeyboardButton(
                text='Подать заявку на доклад', callback_data='apply'
            )
        ],
        [
            InlineKeyboardButton(
                text='Начать доклад', callback_data='start_report'
            )
        ],
    ]
    keyboard = InlineKeyboardMarkup(role_buttons)
    update.callback_query.message.reply_text(
        'Данные режим предназначен для использования функций докладчика. '
        'Здесь подают заявку на выступление, отмечают начало и конец доклада'
        ', смотрят вопросы заданные аудиторией.',
        reply_markup=keyboard,
    )

    return 'SPEAKER_OPTIONS'


def speaker_apply(update, context):
    text = 'Укажите пожалуйста тему Вашего доклада'
    button = [
        [
            InlineKeyboardButton(
                text='Назад', callback_data='back'
            )
        ]
    ]
    keyboard = InlineKeyboardMarkup(button)
    update.callback_query.message.reply_text(text, reply_markup=keyboard)

    return 'HANDLE_TOPIC'


def handle_topic(update, context):
    context.user_data['topic'] = update.message.text
    text = 'Укажите длительность доклада'
    buttons = [
        [
            InlineKeyboardButton(
                text='15 минут', callback_data='15'
            )
        ],
        [
            InlineKeyboardButton(
                text='30 минут', callback_data='30'
            )
        ],
        [
            InlineKeyboardButton(
                text='45 минут', callback_data='45'
            )
        ],
        [
            InlineKeyboardButton(
                text='60 минут', callback_data='60'
            )
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    update.message.reply_text(text, reply_markup=keyboard)

    return 'HANDLE_DURATION'


def handle_duration(update, context):
    context.user_data['duration'] = update.callback_query.data
    text = 'На текущий момент доступны следующие временные промежутки'
    buttons = [
        [
            InlineKeyboardButton(
                text='10:00 - 11:00', callback_data='0'
            )
        ],
        [
            InlineKeyboardButton(
                text='12:00 - 13:00', callback_data='1'
            )
        ],
        [
            InlineKeyboardButton(
                text='14:00 - 15:00', callback_data='2'
            )
        ],
        [
            InlineKeyboardButton(
                text='15:00 - 16:00', callback_data='3'
            )
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    update.callback_query.message.reply_text(text, reply_markup=keyboard)

    return 'SUMMARIZE_APPLICATION'


def summarize_application(update, context):
    context.user_data['timeslot'] = update.callback_query.data
    update.callback_query.message.reply_text(f'Ваш id {update.effective_user.id}')
    update.callback_query.message.reply_text(f'Ваш username {update.effective_user.username}')
    update.callback_query.message.reply_text(f'Вы подали заявку на доклад митапа {context.user_data["meetup"]}')
    update.callback_query.message.reply_text(f'Тема доклада {context.user_data["topic"]}')
    update.callback_query.message.reply_text(f'Длительность доклада {context.user_data["duration"]}')
    update.callback_query.message.reply_text(f'Временной промежуток {context.user_data["timeslot"]}')


def handle_speaker_scenario_choice(update, context):
    update.callback_query.message.reply_text(
        'handle_speaker_scenario_choice',
    )


def stop_nested_conv(update, context):
    get_speaker_options(update, context)

    return 'END'


def stop(update, context) -> int:
    """End Conversation by command."""
    update.message.reply_text('Okay, bye.')

    return ConversationHandler.END


class Command(BaseCommand):
    def handle(self, *args, **options):
        updater = get_updater()
        dispatcher = updater.dispatcher

        speaker_apply_conv = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(speaker_apply, pattern='^apply$')
            ],
            states={
                'HANDLE_TOPIC': [
                    MessageHandler(
                        Filters.text & ~Filters.command, handle_topic
                    )
                ],
                'HANDLE_DURATION': [
                    CallbackQueryHandler(handle_duration)
                ],
                'SUMMARIZE_APPLICATION': [
                    CallbackQueryHandler(summarize_application)
                ]
            },
            fallbacks=[CallbackQueryHandler(stop_nested_conv, pattern='^back$')],
            map_to_parent={'END': 'SPEAKER_OPTIONS'}
        )

        speaker_conv = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(get_speaker_options, pattern='^Speaker$')
            ],
            states={
                'SPEAKER_OPTIONS': [
                    speaker_apply_conv,
                    # CallbackQueryHandler(handle_speaker_scenario_choice, pattern='')
                ],
            },
            fallbacks=[CommandHandler('stop', stop)],
        )

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                'MEETUP': [CallbackQueryHandler(meetup_handler)],
                'ROLES': [speaker_conv],
                # 'SPEAKER': [speaker_conv],
            },
            fallbacks=[CommandHandler('stop', stop)],
        )

        dispatcher.add_handler(conv_handler)

        updater.start_polling()

        updater.idle()
