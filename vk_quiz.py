import os
import json
import redis
import logging
import vk_api as vk

from dotenv import load_dotenv
from random import choice
from vk_api.utils import get_random_id
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

logger = logging.getLogger(__file__)


def handle_new_question_request(event, vk_api, question, redis, keyboard):
    redis.set(event.user_id, question)
    vk_api.messages.send(
        peer_id=event.user_id,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
        message=question
    )


def handle_solution_attempt(event, vk_api, quiz_text, redis, keyboard):
    question = redis.get(event.user_id).decode("utf-8")
    answer = quiz_text[question]
    if event.text == answer:
        text = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос».'
    else:
        text = 'Неправильно… Попробуешь ещё раз?'
    vk_api.messages.send(
        peer_id=event.user_id,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
        message=text
    )


def handle_show_correct_answer(event, vk_api, quiz_text, redis, keyboard):
    question = redis.get(event.user_id).decode("utf-8")
    answer = quiz_text[question]
    vk_api.messages.send(
        peer_id=event.user_id,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
        message=answer
    )


def command_handler(vk_token, quiz_text):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Мой счет', color=VkKeyboardColor.NEGATIVE)
    vk_session = vk.VkApi(token=vk_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        question = choice(list(quiz_text))
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == 'Новый вопрос':
                handle_new_question_request(
                    event, vk_api, question,
                    redis, keyboard
                )
            elif event.text == 'Сдаться':
                handle_show_correct_answer(
                    event, vk_api, quiz_text,
                    redis, keyboard
                )
            else:
                handle_solution_attempt(
                    event, vk_api,
                    quiz_text, redis,
                    keyboard
                )


if __name__ == "__main__":
    load_dotenv()
    vk_token = os.environ['VK_API_KEY']
    database_password = os.environ['REDIS_DATABASE_PASSWORD']
    redis_port = os.environ['REDIS_PORT']
    redis_host = os.environ['REDIS_HOST']
    logging.basicConfig(level=logging.ERROR)
    logger.setLevel(logging.DEBUG)
    redis = redis.Redis(
        host=redis_host, port=redis_port,
        password=database_password
    )

    with open('questions_answer.json', 'r') as quiz_file:
        quiz_text = json.load(quiz_file)
    command_handler(vk_token, quiz_text)
