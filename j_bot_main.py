import telebot, lyricsgenius, spotipy, YouTubeMusicAPI
from spotipy.oauth2 import SpotifyClientCredentials
from youtubepy import Video
import sqlite3
from yandex_music import Client
import vk_audio
from telebot import types


vk = vk_audio.VkAudio(login='+7(969) 969-5412', password='omopur97')  # ВК авторизация
client = Client()  # Клиент Яндекс.Музыки
bot = telebot.TeleBot('1763338570:AAH-6CSF7YSeBRu43b-rey2cHFwiYGeXC9I')  # API бота
genius = lyricsgenius.Genius('9bDm8DpQlsRIZ7TKG76or_AuR_Y0Fkx1g5tjL5tzmG0lgKaSTF6iOT8cjVpL65Qn')  # Api Genius
spotify = spotipy.Spotify(  # API Spotify
    auth_manager=SpotifyClientCredentials("614ac917f8fc4ac1b5d9ad1d4732b757", "805b79bb63d44b779e6052e0df2a5efa"))


# транслитерация
def transliterate(name):
    # Словарь с заменами
    dicktionary = {'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e', 'ж': 'zh',
                   'з': 'z', 'и': 'i', 'й': 'i', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
                   'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'c',
                   'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'i', 'ь': '', 'э': 'e', 'ю': 'u',
                   'я': 'ya', 'a': 'a', 'b': 'b', 'c': 'c', 'd': 'd', 'e': 'e', 'f': 'f', 'g': 'g', 'h': 'h',
                   'i': 'i', 'j': 'j', 'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n', 'o': 'o', 'p': 'p',
                   'q': 'q', 'r': 'r', 's': 's', 't': 't', 'u': 'u', 'v': 'v', 'w': 'w', 'x': 'x',
                   'y': 'y', 'z': 'z', ',': '', '?': '', ' ': ' ', '~': '', '!': '', '@': '', '#': '', 'Є': 'e', '—': '',
                   '$': '', '%': '', '^': '', '&': '', '*': '', '(': '', ')': '', '-': '', '=': '', '+': '',
                   ':': '', ';': '', '<': '', '>': '', '\'': '', '"': '', '\\': '', '/': '', '№': '',
                   '[': '', ']': '', '{': '', '}': '', 'ґ': '', 'ї': '', 'є': '', 'Ґ': 'g', 'Ї': 'i', }
    # Циклически заменяем все буквы в строке
    for key in dicktionary:
        name = name.replace(key, dicktionary[key])
    return name


# Функция, задающая песню
def setSong(message):
    global my_track  # название песни
    my_track = message.text.lower()
    init_keyboard(message)


# Инициализация клаиатуры с действиями
def init_keyboard(message):
    keyboard = telebot.types.InlineKeyboardMarkup()
    song_button = telebot.types.InlineKeyboardButton(text='Найти песню', callback_data='find_song')
    keyboard.add(song_button)
    video_button = telebot.types.InlineKeyboardButton(text='Найти клип', callback_data='find_video')
    keyboard.add(video_button)
    text_button = telebot.types.InlineKeyboardButton(text='Найти текст песни', callback_data='find_text')
    keyboard.add(text_button)
    bot.send_message(message.chat.id, text='Выбери действие', reply_markup=keyboard)


# Функция задающая автора
def setAuthor(message):
    global my_author  # автор песни
    my_author = message.text.lower()
    bot.send_message(message.chat.id, "Введи название композиции")
    bot.register_next_step_handler(message, setSong)


# Обработка команды /start
@bot.message_handler(commands=['start'])
def get_text_messages(message):
    global user_id
    user_id = message.from_user.id
    bot.send_message(message.chat.id, 'Добро пожаловать, {0.first_name}!\nЯ - {1.first_name},'
                                      ' бот созданный для помощи с музыкой.'.format(message.from_user, bot.get_me()), )
    bot.send_message(message.chat.id, "Введи автора композиции")
    bot.register_next_step_handler(message, setAuthor)


@bot.message_handler(commands=['developers'])
def developers_info(message):
    bot.send_message(message.chat.id, "Разработчики:\nАнтон Короткин @WindInMyHead\nАнтон Макотра @macktosha\nНикита Клейменов @gloomy_tenzor\nПо всем вопросам и предложениям обращаться и не стесняться!")


 #Поиск ссылки на Spotify
def url_spotify(searchQuery):
    songs = spotify.search(q=searchQuery, limit=1)
    print(' ')
    return songs['tracks']['items'][0]['external_urls']['spotify']


# Поиск обложки на Spotify
def image_spotify(searchQuery):
    image = spotify.search(q=searchQuery, limit=1)
    return image['tracks']['items'][0]


# Поиск ссылки на Яндекс Музыке
def url_yandex(searchQuery):
    search_result = client.search(searchQuery)
    result = "https://music.yandex.ru/album/" + str(search_result.tracks.results[0].albums[0].id) +\
             "/track/" + str(search_result.tracks.results[0].id)
    return result


# Поиск ссылки на ВК
def url_vk(searchQuery):
    search_result = vk.search(searchQuery)
    result = "https://vk.com/music/album/" + str(search_result.Audios[00].Album.owner_id) + "_" + \
             str(search_result.Audios[00].Album.id) + "_" + \
            str(search_result.Audios[00].Album.access_hash)
    return result


# Поиск ссылки на YouTube Music
def url_youtube(searchQuery):
    result = YouTubeMusicAPI.getsonginfo(searchQuery)
    return result['track_url']


# Поиск ссылки на Apple Music
def url_apple(searchQuery):
    return searchQuery


# КНОПКА ПОИСК ПЕСНИ
@bot.callback_query_handler(func=lambda call: call.data.startswith('find_song'))
def url_keyboard(call):
    searchQuery = my_track + ' ' + my_author  # Запрос в совмещенном виде
    searchQuery = transliterate(searchQuery)
    markup = types.InlineKeyboardMarkup(row_width=2)
    item1 = types.InlineKeyboardButton(text='Spotify', url=url_spotify(searchQuery))
    item2 = types.InlineKeyboardButton(text='Яндекс.Музыка', url=url_yandex(searchQuery))
    item3 = types.InlineKeyboardButton(text='Вконтакте', url=url_vk(searchQuery))
    item4 = types.InlineKeyboardButton(text='YouTube Music', url=url_youtube(searchQuery))
    item5 = types.InlineKeyboardButton(text='Apple Music', url='https://www.google.com')
    markup.add(item1, item2, item3, item4, item5)
    image = image_spotify(searchQuery)
    bot.send_photo(call.message.chat.id, image['album']['images'][0]['url'],
                   caption=f"Исполнитель: {image['artists'][0]['name']}\n"
                           f"Трек: {image['name']} \n"
                           f"Альбом: {image['album']['name']} \n"
                           f"Дата релиза: {image['album']['release_date']} ", reply_markup=markup)
    init_keyboard(call.message)


# КНОПКА ПОИСК ВИДЕО
@bot.callback_query_handler(func=lambda call: call.data.startswith('find_video'))
def button_video(call):
    bot.send_message(call.message.chat.id, "Идет поиск клипа " + my_author + "-" + my_track)
    search_res = my_author + ' ' + my_track
    search_res = transliterate(search_res)
    clip_search = Video(search_res)
    result = clip_search.search()
    bot.send_message(call.message.chat.id, result)
    init_keyboard(call.message)


# КНОПКА ПОИСК ТЕСКТА
@bot.callback_query_handler(func=lambda call: call.data.startswith('find_text'))
def button_text(call):
    bot.send_message(call.message.chat.id, "Идет поиск текста " + my_author + "-" + my_track)
    artist = genius.search_artist(my_author, 0)
    song = artist.song(my_track)
    parts = [song.lyrics[i:i + 4096]
             for i in range(0, len(song.lyrics), 4096)]
    for part in parts:  # если строка длиннее 4096
        bot.send_message(call.message.chat.id, part)
    init_keyboard(call.message)


bot.polling()
