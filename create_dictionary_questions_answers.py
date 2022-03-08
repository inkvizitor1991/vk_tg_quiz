import os
import re
import string


def get_questions_answer():
    questions_path = 'quiz_questions'
    for file in os.listdir(questions_path):
        if file.endswith('.txt'):
            quiz_questions = os.path.join(questions_path, file)
            with open(quiz_questions, 'r', encoding='KOI8-R') as quiz_file:
                quiz_text = quiz_file.read()

    questions = []
    answers = []
    for text in quiz_text.split('\n\n'):
        if text.startswith('\nВопрос') or text.startswith('Вопрос'):
            questions.append(text)
        if text.startswith('Ответ:'):
            answer_raw = re.sub(r'\[[^)]*\]', '', text.split('\n')[1])
            answer = answer_raw.strip(
                string.whitespace + string.punctuation).upper()
            answers.append(answer)

    questions_answer = dict(zip(questions, answers))
    return questions_answer


if __name__ == '__main__':
    questions_answer = get_questions_answer()