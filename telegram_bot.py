import time

from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters, TypeHandler
import requests
from telegram import ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters, Updater

# массив для хранения параметров из ответа
operation = []


# начало стартуем отсюда и собираем ответы на первый вопросы + возвращаем клавиатуру с двумя кнопками
def start(update, context):
    reply_keyboard = [['Узнать баланс', 'Добавить операцию']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)

    update.message.reply_text(
        "Привет! Я бот для учета твоих расходов!\n"
        "Можно узнать сколько уже потрачено и заработано!\n"
        "А также добавить запись о новых операциях\n"
        "Что вы хотите сделать?",
        reply_markup=markup
    )

    # Число-ключ в словаре states —
    # втором параметре ConversationHandler'а.

    return 1


# принимаем решение в зависимости от выбранной кнопки
# если выбрано "Узнать баланс", то выполняем get-запрос к нашему api и выводим входящий и исходящий балансы
# если выбрано "Добавить операцию", то отрисовываем клавиатуру с выбором из 2-типов операций + ответ передаем в шаг 2
def first_response(update, context):
    # Это ответ на первый вопрос.
    # Мы можем использовать его во втором вопросе.
    text = update.message.text
    if text == "Узнать баланс":
        balance_url = "http://127.0.0.1:5000/transactions"
        response = requests.get(balance_url, params={
            "format": "json"
        })
        json_response = response.json()

        incoming_amount = 0
        outgoing_amount = 0

        for i in range(len(json_response)):
            if json_response[i]['is_incoming']:
                incoming_amount += json_response[i]['amount']
            else:
                outgoing_amount += json_response[i]['amount']

        update.message.reply_text(
            "Все траты: " + str(outgoing_amount) + " рублей!\n"
                                                   "Все доходы: " + str(incoming_amount) + " рублей!\n"
        )

    if text == "Добавить операцию":
        reply_keyboard = [['Расход', 'Доход']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)

        update.message.reply_text(
            "Добавляем новую операцию. Какая была операция?",
            reply_markup=markup
        )
        return 2

    # update.message.reply_text(
    #     "Какая погода в городе {locality}?".format(**locals()))
    # Следующее текстовое сообщение будет обработано
    # обработчиком states[2]
    # return 2


# Задаем вопрос для третьего шага - про сумму операции; В зависимости от ответа на прошлый вопрос по направлению
# операции добавляем в operation True или False - в будушем параметр is_incoming. И переходим к шагу 3
def second_response(update, context):
    # Ответ на второй вопрос.
    # Мы можем его сохранить в базе данных или переслать куда-либо.
    update.message.reply_text(
        "Какая была сумма операции?"
    )
    if update.message.text == "Расход":
        operation.append(False)
    if update.message.text == "Доход":
        operation.append(True)
    return 3

    # return ConversationHandler.END  # Константа, означающая конец диалога.
    # Все обработчики из states и fallbacks становятся неактивными.


# Получаем сумму операции - ответ на прошлий вопрос, добавляем сумму в operation
# Задаем следующий вопрос по комментарий - и переходим к 4 шагу
def third_response(update, context):
    amount = update.message.text
    operation.append(amount)
    update.message.reply_text(
        "Нужно добавить комментарий к операции)"
    )
    return 4


# Готовим клавиатуру, которая появится после добавления операции
# Добавляем в operation description
# Вызываем функцию создания операции
# Отвечаем пользователю текстом успешности и возвращаем кливиатуру + переходим к шагу 1
def fourth_response(update, context):
    reply_keyboard = [['Узнать баланс', 'Добавить операцию']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)

    description = update.message.text
    operation.append(description)
    create_transaction()
    update.message.reply_text(
        "Операция успешно добавлена!\n"
        "Что делаем дальше?\n",
        reply_markup=markup
    )

    return 1


# Создаем транзакцию - значения берем из operation, после создания operation - очищаем
# Логируем статус код, если он != 200, то выводим тело ответа, чтобы посмотреть в чем проблема
def create_transaction():
    test_uri = "http://127.0.0.1:5000/transactions"
    response = requests.post(test_uri, json={
        "amount": operation[1],
        "description": operation[2],
        "is_incoming": operation[0]
    })
    if response.status_code != 200:
        print(response.text)
    operation.clear()


def stop(update, context):
    update.message.reply_text(
        "Вы завершили работу с ботом!"
    )


def main():
    # Создаём объект updater.
    updater = Updater("1261886794:AAEeegI5h4BIF942wzXGenafagfp8oNkGiw", use_context=True)

    # Получаем из него диспетчер сообщений.
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        # Точка входа в диалог.
        # В данном случае — команда /start. Она задаёт первый вопрос.
        entry_points=[CommandHandler('start', start)],

        # Состояние внутри диалога.
        # Вариант с двумя обработчиками, фильтрующими текстовые сообщения.
        states={
            1: [MessageHandler(Filters.text, first_response)],
            2: [MessageHandler(Filters.text, second_response)],
            3: [MessageHandler(Filters.text, third_response)],
            4: [MessageHandler(Filters.text, fourth_response)]
        },

        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler("stop", stop)]
    )
    dp.add_handler(conv_handler)
    updater.start_polling()

    # Ждём завершения приложения.
    # (например, получения сигнала SIG_TERM при нажатии клавиш Ctrl+C)
    updater.idle()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()
