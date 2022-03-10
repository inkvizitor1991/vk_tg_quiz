import os
import json
import redis
import logging
import telegram

from random import choice
from dotenv import load_dotenv
from telegram.ext import (
    Updater, CommandHandler,
    MessageHandler, Filters,
    RegexHandler, ConversationHandler
)

from create_dictionary_questions_answers import get_questions_answer


logger = logging.getLogger(__name__)


CHOOSING = range(1)

CUSTOM_KEYBOARD = [
    ['Новый вопрос', 'Сдаться'],
    ['Мой счет']
]
REPLY_MARKUP = telegram.ReplyKeyboardMarkup(
    CUSTOM_KEYBOARD,
    resize_keyboard=True,
    one_time_keyboard=True
)


def start(bot, update):
    text = 'Привет! Я бот для викторин!'
    bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=REPLY_MARKUP
    )
    questions_answer = json.dumps(get_questions_answer())
    redis.set('questions_answer', questions_answer)
    return CHOOSING


def handle_new_question_request(bot, update):
    questions_answer = json.loads(
        redis.get('questions_answer').decode("utf-8")
    )
    question = choice(list(questions_answer))
    redis.set(update.message.chat_id, question)
    update.message.reply_text(question)
    return CHOOSING


def handle_solution_attempt(bot, update):
    questions_answer = json.loads(
        redis.get('questions_answer').decode("utf-8")
    )
    question = redis.get(update.message.chat_id).decode("utf-8")
    if update.message.text.upper() == questions_answer[question]:
        text = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос».'
    else:
        text = 'Неправильно… Попробуешь ещё раз?'
    bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=REPLY_MARKUP
    )
    return CHOOSING


def handle_show_correct_answer(bot, update):
    questions_answer = get_questions_answer()
    question = redis.get(update.message.chat_id).decode("utf-8")
    answer = questions_answer[question]
    bot.send_message(
        chat_id=chat_id,
        text=answer,
        reply_markup=REPLY_MARKUP
    )
    return CHOOSING


def cancel(bot, update):
    return ConversationHandler.END


if __name__ == '__main__':
    load_dotenv()
    chat_id = os.environ['CHAT_ID']
    bot_token = os.environ['TG_BOT_TOKEN']
    database_password = os.environ['REDIS_DATABASE_PASSWORD']
    redis_port = os.environ['REDIS_PORT']
    redis_host = os.environ['REDIS_HOST']

    redis = redis.Redis(
        host=redis_host, port=redis_port,
        password=database_password
    )
    logging.basicConfig(level=logging.ERROR)
    logger.setLevel(logging.DEBUG)

    updater = Updater(bot_token)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [RegexHandler('^Новый вопрос$',
                                    handle_new_question_request,
                                    ),
                       RegexHandler('^Сдаться$',
                                    handle_show_correct_answer,
                                    ),
                       MessageHandler(Filters.text, handle_solution_attempt)
                       ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()
