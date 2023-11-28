import sqlite3

from apscheduler.triggers.cron import CronTrigger
from telegram import ReplyKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, JobQueue
import datetime
import pytz
from config import admin_id, bot_token
from helper import start_time, end_time, start_day, end_day, count_users, \
    host_time, log_day, tomorrow_day
from db_functions import create_table, add_enrollment, is_enrolled, \
    enable_enrollment, disable_enrollment, get_random_usernames_with_names, clear_enable, count_total_enrollments, \
    say_name, delete_table
from apscheduler.schedulers.background import BackgroundScheduler
from texts import text_welcome, text_info, text_cancel, text_no_enroll, text_already_enrolled, text_enroll, \
    text_no_time, text_no_name, text_greeting, text_intro

# название кнопок
button_enroll = "Я комик!"
button_cancel_enrollment = "Не хочу быть комиком"
button_info = "Полезная инфа"
button_name = "Представиться"


# Функция для команды /start
def start(update, context):
    user = update.message.from_user
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=text_welcome.format(
                                 user.first_name))
    send_keyboard(update, context)


# Функция для отправки клавиатуры с кнопками
def send_keyboard(update, context):
    keyboard = [[button_enroll, button_cancel_enrollment],
                [button_name, button_info]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Жми кнопку!", reply_markup=reply_markup)


# Функция для команды /что это за бот
def about_bot(update, context):
    print(log_day(), "Отправляю инфу о боте...")
    user = update.message.from_user
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=text_info)

# Функция для команды представься
def user_name(update, context):
    user = update.message.from_user
    user_id = user.id
    username = user.username
    conn = sqlite3.connect('enrollments.db')

    update.message.reply_text(text_intro)
    context.user_data[user_id] = {'waiting_for_name': True}
    
    # Обработка текстового ответа юзера
    def handle_introduction(update, context):
        user_id = update.message.from_user.id

        if context.user_data.get(user_id, {}).get('waiting_for_name', False):
            introduction_text = update.message.text
            user_exists, enable_status, real_name_exist = is_enrolled(conn, user_id)
            if user_exists is True:
                say_name(conn, user_id, introduction_text)
            else:
                add_enrollment(conn, user_id, username, user.first_name, enable=False)
                say_name(conn, user_id, introduction_text)
            del context.user_data[user_id]['waiting_for_name']

            # Отправляем благодарственное сообщение
            text_name = f"Спасибо за представление, {introduction_text}! Теперь ты можешь нажимать кнопку Я комик, чтобы попасть в список на запись (если запись открыта)"
            update.message.reply_text(text_name, parse_mode=ParseMode.MARKDOWN)

    # Добавляем временный обработчик для ввода имени и фамилии
    context.dispatcher.add_handler(MessageHandler(None, handle_introduction))


# Функция для отмены записи
def cancel_enrollment(update, context):
    print(log_day(), "Отменяю запись юзеру...")
    user = update.message.from_user
    user_id = user.id

    conn = sqlite3.connect('enrollments.db')

    exist, status, real_name_exist = is_enrolled(conn, user_id)

    current_time = datetime.datetime.now(pytz.timezone('Europe/Moscow')).time()
    current_day = datetime.datetime.now(pytz.timezone('Europe/Moscow'))

    if (current_day.weekday() == start_day and current_time >= start_time) or (
            current_day.weekday() == end_day and current_time <= end_time):
        if exist is True and status is True:
            disable_enrollment(conn, user_id)
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=text_cancel)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text=text_no_enroll)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=text_no_time)
    conn.close()


# Функция для команды /записаться
def enroll(update, context):
    print(log_day(), "Записываю юзера...")
    user = update.message.from_user
    user_id = user.id
    username = user.username

    # Проверка, доступна ли запись
    current_time = datetime.datetime.now(pytz.timezone('Europe/Moscow')).time()
    current_day = datetime.datetime.now(pytz.timezone('Europe/Moscow'))

    if (current_day.weekday() == start_day and current_time >= start_time) or (
            current_day.weekday() == end_day and current_time <= end_time):
        conn = sqlite3.connect('enrollments.db')
        # create_table(conn)
        exist, status, is_real_name = is_enrolled(conn, user_id)
        # print(exist, status, is_real_name)

        if exist is False:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=text_no_name)
            add_enrollment(conn, user_id, username, user.first_name, enable=False)
        elif is_real_name is False:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=text_no_name)
        elif status is True:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=text_already_enrolled)
        else:
            enable_enrollment(conn, user_id)
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=text_enroll)

        conn.close()
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=text_no_time)


# отправка рандомного списка
def send_random_enrollments(context: JobQueue):
    print(log_day(), "Отправляю список ведущему...")
    conn = sqlite3.connect('enrollments.db')

    # Получаем случайные записи
    enrollments = get_random_usernames_with_names(conn, count_users)

    # Считаем общее количество зарегистрированных пользователей
    total_enrollments = count_total_enrollments(conn)

    conn.close()
    tomorrow = tomorrow_day()

    # Отправляем всем кто в списке сообщение
    for user_id, username, user_real_name in enrollments:
        try:
            context.bot.send_message(chat_id=user_id, text=text_greeting.format(
                                 tomorrow))
            print(log_day(), f"Сообщение отправлено пользователю {user_real_name} @{username}")
        except Exception as e:
            print(log_day(), f"Не удалось отправить сообщение пользователю {user_real_name} @{username}. Ошибка: {e}")

    if len(enrollments) > 0:
        # Формируем текст сообщения
        message_text = "\n".join([f"{user_real_name}" for user_id, username, user_real_name in enrollments])

        # Добавляем информацию о общем количестве зарегистрированных пользователей
        message_text += f"\n\nВсего к тебе на дневной микрофон хотело попасть {total_enrollments} человек, прикинь!"

        context.bot.send_message(chat_id=context.job.context,
                                 text=f"Случайные никнеймы и имена из записанных пользователей:\n{message_text}")
    else:
        context.bot.send_message(chat_id=context.job.context, text="Никто не записался.")


def main():
    updater = Updater(token=bot_token, use_context=True)
    dp = updater.dispatcher
    job_queue = updater.job_queue
    # Создаем объект соединения с базой данных
    conn = sqlite3.connect('enrollments.db')

    # Создаем объект планировщика
    scheduler = BackgroundScheduler()

    # Запускаем задачу по расписанию каждый понедельник в host_time
    scheduler.add_job(clear_enable,
                      CronTrigger(day_of_week='mon', hour=12, minute=0, timezone=pytz.timezone('Europe/Moscow')),
                      args=[conn])

    # Запуск планировщика
    scheduler.start()

    # Добавляем задачу на отправку массива никнеймов в нужный день и время
    context_chat = admin_id
    # job_queue.run_repeating(send_random_enrollments, interval=3600 * result_hour + 60, first=0, context=context_chat)
    job_queue.run_daily(send_random_enrollments, time=host_time, days=(end_day,), context=context_chat)

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text(button_enroll), enroll))
    dp.add_handler(MessageHandler(Filters.text(button_info), about_bot))
    dp.add_handler(MessageHandler(Filters.text(button_name), user_name))
    dp.add_handler(MessageHandler(Filters.text(button_cancel_enrollment), cancel_enrollment))

    updater.start_polling()
    updater.idle()

    # Закрываем соединение с базой данных
    conn.close()


if __name__ == '__main__':
    main()
