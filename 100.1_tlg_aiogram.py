from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.utils import executor
import config
import sqlite3
import cv2
import dlib
import io
import nmslib
import time


# -----------------------------------------------------------------------------------------------
# --------------------------------------------Настройки и переменные-----------------------------
# -----------------------------------------------------------------------------------------------



bot = Bot(token=config.token)
dp = Dispatcher(bot)

sp = dlib.shape_predictor('./models/shape_predictor_68_face_landmarks.dat')
facerec = dlib.face_recognition_model_v1('./models/dlib_face_recognition_resnet_model_v1.dat')
detector = dlib.get_frontal_face_detector()




# -----------------------------------------------------------------------------------------------
# ---------------------------------------Допалнительные функции----------------------------------
# -----------------------------------------------------------------------------------------------


def change_class(img):
    # Переводим из одного класса в другой
    # из 'numpy.ndarray' в class '_io.BufferedReader'
    # Чтобы потом сразу отправить фотку в бот
    _, img_encode = cv2.imencode('.jpg', img)
    str_encode = img_encode.tobytes()  # tostring()  Convert array to binary type
    f4 = io.BytesIO(str_encode)  # Convert to _io.BytesIO type
    return io.BufferedReader(f4)  # Convert to _io.BufferedReader type


def face_recog(img_path):
    face_descriptor =[]
    if img_path != '':
        img = cv2.imread(img_path)
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector(img_gray)
        for k,d in enumerate(faces):
            cv2.rectangle(img, (d.left(), d.top()), (d.right(), d.bottom()), (0, 255, 0), 2)
            shape = sp(img, d)
            face_descriptor.append(facerec.compute_face_descriptor(img, shape))
        return change_class(img), face_descriptor
    else:
        print('нет Переменной с путем файла')


def get_hnsw(path_bin,t, face_descriptor):
    all_ids_dists = {}  # все индексы в словарь

    for i in range(t):
        i +=1
        # print('Параметр i:', str(i))
        start_time_f = time.time()

        path_bin_file = path_bin + str(i) + '.bin'
        # print('Путь:',path_bin_file)
        index_hnsw = nmslib.init(method='hnsw', space='l2', data_type=nmslib.DataType.DENSE_VECTOR)
        index_hnsw.loadIndex(path_bin_file)
        query_time_params = {'efSearch': 400}
        index_hnsw.setQueryTimeParams(query_time_params)
        ids, dists = index_hnsw.knnQuery(face_descriptor, k=9)  # запрос ближайших соседей точки данных

        for n in range(9):
            all_ids_dists[ids[n]] = dists[n], str(i)

        end_time_f = time.time()
        print(str(i)," findface_nmslib поиск лица в базе ---- %s seconds ----" % (end_time_f - start_time_f))

    TheBest_9 = {}
    for n in range(9):
        min_key = min(all_ids_dists, key=lambda k: all_ids_dists[k])
        min_value = all_ids_dists.pop(min_key)
        TheBest_9[min_key] = min_value
    return TheBest_9



def findface_nmslib(face_descriptor):

    TheBest_9 = get_hnsw('./db/WhatsApp_', 1, face_descriptor)
    answer = []
    a = []
    b = []
    c = []
    for k, v in TheBest_9.items():
        # print(' Проверка словаря полученного. Ключ:',k, v, '    Значения:', v[0], v[1])
        cursor_WA = connection_WA.cursor()
        sql = "select id, phone from associations where id = " + str(k)
        cursor_WA.execute(sql)
        data_assoc = cursor_WA.fetchone()
        a = data_assoc[0]	#  порядковый номер картинки
        b = data_assoc[1]	#  телефон
        c = b+'.jpg'	#  имя картинки

        a = str(100-round(v[0]*100))+'%'              # дистанция совпадения с лицом в %
        x = a, b, c
        answer.append(x)
    cursor_WA.close()
    return answer

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

connection_WA = sqlite3.connect('./db/WhatsApp_ass.db')


# try:
#     connection = sqlite3.connect('basa_img.db')
#     create_table_query = '''CREATE TABLE MediaIds_developers (
#                                     id INTEGER PRIMARY KEY,
#                                     file_id TEXT NOT NULL,
#                                     filename TEXT NOT NULL,
#                                     joining_date datetime);'''
#
#     cursor = connection.cursor()
#     cursor.execute(create_table_query)
#     connection.commit()
#     print("Таблица SQLite создана")
#
#     query = "select sqlite_version();"
#     cursor.execute(query)
#     record = cursor.fetchall()
#     print("Версия базы данных SQLite: ", record)
#     cursor.close()
#
# except sqlite3.Error as error:
#     print("Ошибка при подключении к sqlite", error)
# finally:
#     if (connection):
#         connection.close()
#         print("Соединение с SQLite закрыто")




# -----------------------------------------------------------------------------------------------
# -----------------------------Обработчик поступающих изображений--------------------------------
# -----------------------------------------------------------------------------------------------


# Первый вариант
@dp.message_handler(Text(equals="Соц.сети"))
async def find_face_vk(message: types.Message):
    await message.reply("VK!", reply_markup=types.ReplyKeyboardRemove())

# Второй вариант
@dp.message_handler(lambda message: message.text == "БДО")
async def find_face_bdo(message: types.Message):
    await message.reply("Отдельная база!", reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler(lambda message: message.text == "Whatsapp")
async def find_face_whatsapp(message: types.Message):
    await message.reply("WhatsApp!", reply_markup=types.ReplyKeyboardRemove())


# Типы содержимого тоже можно указывать по-разному.
@dp.message_handler(content_types=["photo"])
async def download_photo(msg: types.Message):
    await msg.photo[-1].download()
    document_id = msg.photo[-1].file_id
    file_info = await bot.get_file(document_id)
    # print(f'file_id: {file_info.file_id}')
    # print(f'file_path: {file_info.file_path}')
    # print(f'file_size: {file_info.file_size}')
    # print(f'file_unique_id: {file_info.file_unique_id}')
    img, fac_rec = face_recog(file_info.file_path)

    # photo = open('photos/file_41.jpg', 'rb')
    # print(type(photo), ' and ', type(img))

    await bot.send_photo(msg.from_user.id, photo=img, caption=f'Лиц обнаружено {str(len(fac_rec))}')
    for n in fac_rec:
        face_rezult = findface_nmslib(n)
        for d in face_rezult:
            mess = d[1]+' - '+d[0]+'\n'
            try:
                await bot.send_photo(msg.from_user.id, photo=open(f'./images/WhatsApp/{d[2]}', 'rb'), caption=mess)
            except:
                await bot.send_message(msg.from_user.id, mess)






# -----------------------------------------------------------------------------------------------
# ------------------------------Обработчик поступающих сообщений --------------------------------
# -----------------------------------------------------------------------------------------------


@dp.message_handler()
async def echo_message(msg: types.Message):
    await bot.send_message(msg.from_user.id, 'Извините, но команду:' + msg.text+' бот не знает.')






executor.start_polling(dp)
