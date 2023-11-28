import datetime
import pytz
import locale


# узнать текущее время и дату
def log_day():
    return datetime.datetime.now(pytz.timezone('Europe/Moscow'))


def tomorrow_day():
    locale.setlocale(locale.LC_TIME, 'ru_RU')
    # Определяем завтрашнюю дату
    tomorrow = datetime.datetime.now(pytz.timezone('Europe/Moscow')) + datetime.timedelta(days=1)
    # Форматируем дату в нужный формат
    formatted_date = tomorrow.strftime("%d %B").capitalize()
    return formatted_date


# начало записи
start_hour = 18
start_minute = 00
start_time = datetime.time(start_hour, start_minute)

# конец записи
end_time_hour = 18
end_time_minute = 00
end_time = datetime.time(end_time_hour, end_time_minute)

# дата (день недели минус 1, пн=0, вт=1 ... вс=6)
start_day = 4
end_day = 5

# когда прислать список ведущему
host_time_hour = 18
host_time_minute = 1
host_time = datetime.time(host_time_hour - 3, host_time_minute)

# сколько человек
count_users = 30
