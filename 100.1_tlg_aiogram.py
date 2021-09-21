from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
import config
import sqlite3

# -----------------------------------------------------------------------------------------------
# --------------------------------------------Настройки и переменные-----------------------------
# -----------------------------------------------------------------------------------------------



bot = Bot(token=config.token)
dp = Dispatcher(bot)



# -----------------------------------------------------------------------------------------------
# --------------------------------------------Начало работы бота---------------------------------
# -----------------------------------------------------------------------------------------------


@dp.message_handler(commands=['start'])
async def handle_start_help(message: types.Message):
    await message.reply("Привет!\nНапиши мне что-нибудь!")

@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply("Сдесь будут перечисленные возможности БОТа")


# -----------------------------------------------------------------------------------------------
# -----------------------------Создаем базу данных-----------------------------------------------
# ---------------------------- --------или-------------------------------------------------------
# --------------------------- --подключаемся к существующей--------------------------------------
# -----------------------------------------------------------------------------------------------

try:
    connection = sqlite3.connect('basa_img.db')
    create_table_query = '''CREATE TABLE MediaIds_developers (
                                    id INTEGER PRIMARY KEY,
                                    file_id TEXT NOT NULL,
                                    filename TEXT NOT NULL, 
                                    joining_date datetime);'''

    cursor = connection.cursor()
    cursor.execute(create_table_query)
    connection.commit()
    print("Таблица SQLite создана")





    query = "select sqlite_version();"
    cursor.execute(query)
    record = cursor.fetchall()
    print("Версия базы данных SQLite: ", record)
    cursor.close()

except sqlite3.Error as error:
    print("Ошибка при подключении к sqlite", error)
finally:
    if (connection):
        connection.close()
        print("Соединение с SQLite закрыто")



# -----------------------------------------------------------------------------------------------
# ------------------------------Обработчик поступающих сообщений --------------------------------
# -----------------------------------------------------------------------------------------------


@dp.message_handler()
async def echo_message(msg: types.Message):
    await bot.send_message(msg.from_user.id, msg.text+' Сообщение бота')



# -----------------------------------------------------------------------------------------------
# -----------------------------Обработчик поступающих изображений--------------------------------
# -----------------------------------------------------------------------------------------------







executor.start_polling(dp)