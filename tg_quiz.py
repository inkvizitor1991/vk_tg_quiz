import os
import json
import redis
import logging
import telegram

from collections import defaultdict
from enum import Enum
from random import choice
from dotenv import load_dotenv
from telegram.ext import (
    Updater, CommandHandler,
    MessageHandler, Filters,
    RegexHandler, ConversationHandler
)

logger = logging.getLogger(__name__)

storage_quiz_text = defaultdict()


class BOT_STATE(Enum):
    QUIZ = 1


CHOOSING = range(BOT_STATE.QUIZ.value)

custom_keyboard = [
    ['Новый вопрос', 'Сдаться'],
    ['Мой счет']
]
reply_markup = telegram.ReplyKeyboardMarkup(
    custom_keyboard,
    resize_keyboard=True,
    one_time_keyboard=True
)


def start(bot, update):
    text = 'Привет! Я бот для викторин!'
    user_id = update.message.chat_id
    storage_quiz_text[user_id] = {}
    with open('questions_answer.json', 'r') as quiz_file:
        quiz_text = json.load(quiz_file)
    storage_quiz_text[user_id]['quiz'] = quiz_text

    bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup
    )
    return CHOOSING


def handle_new_question_request(bot, update):
    user_id = update.message.chat_id
    quiz_text = storage_quiz_text[user_id].get('quiz')
    question = choice(list(quiz_text))
    redis.set(update.message.chat_id, question)
    update.message.reply_text(question)
    return CHOOSING


def handle_solution_attempt(bot, update):
    user_id = update.message.chat_id
    quiz_text = storage_quiz_text[user_id].get('quiz')
    question = redis.get(update.message.chat_id).decode("utf-8")

    if str(update.message.text).upper() == quiz_text[question]:
        text = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос».'
    else:
        text = 'Неправильно… Попробуешь ещё раз?'
    bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup
    )
    return CHOOSING


def handle_show_correct_answer(bot, update):
    user_id = update.message.chat_id
    quiz_text = storage_quiz_text[user_id].get('quiz')
    question = redis.get(update.message.chat_id).decode("utf-8")
    answer = quiz_text[question]
    bot.send_message(
        chat_id=chat_id,
        text=answer,
        reply_markup=reply_markup
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
