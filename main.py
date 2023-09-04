from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import os
from telegram import Bot

API_TOKEN = '6657019188:AAFZqixuGXeUpFZ4vQR2S3vlww40oLrVuDs'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

admin_ids = ['6173245050', '6390512871',
             '1218800347']  # Add your admin IDs here
VERCEL_SERVERLESS_FUNCTION_URL = 

# Create the database files if they don't exist
conn = sqlite3.connect('books.db')
c = conn.cursor()
c.execute(
  '''CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, link TEXT NOT NULL)'''
)
conn.commit()
conn.close()

conn = sqlite3.connect('recentlybooks.db')
c = conn.cursor()
c.execute(
  '''CREATE TABLE IF NOT EXISTS recentlybooks (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)'''
)
conn.commit()
conn.close()

conn = sqlite3.connect('userscount.db')
c = conn.cursor()
c.execute(
  '''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL)'''
)
conn.commit()
conn.close()

# Keyboards
main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.row(KeyboardButton('📕Kitob qidirish'),
                  KeyboardButton('📚Oxirgi qidirilgan kitoblar'),
                  KeyboardButton('📖Barcha kitoblar'))

admin_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
admin_keyboard.row(KeyboardButton('Kitob qo\'shish'),
                   KeyboardButton('Kitobni o\'chirish'),
                   KeyboardButton('Statistik ma\'lumotlar'))

back_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
back_keyboard.row(KeyboardButton('Ortga'))


# States
class States:
  MAIN_MENU = 'main_menu'
  ADMIN_PANEL = 'admin_panel'
  ADD_BOOK_NAME = 'add_book_name'
  ADD_BOOK_LINK = 'add_book_link'
  SEARCH_BOOK = 'search_book'


states = {}


@dp.message_handler(commands=['start'])
async def start_cmd_handler(message: types.Message):
  states[message.from_user.id] = States.MAIN_MENU
  await message.answer(f'Assalomu alaykum {message.from_user.first_name}!',
                       reply_markup=main_keyboard)

  conn = sqlite3.connect('userscount.db')
  c = conn.cursor()
  c.execute('''SELECT * FROM users WHERE user_id=?''',
            (message.from_user.id, ))
  user = c.fetchone()

  if not user:
    c.execute('''INSERT INTO users(user_id) VALUES(?)''',
              (message.from_user.id, ))
    conn.commit()

  conn.close()


@dp.message_handler(commands=['admin'])
async def admin_cmd_handler(message: types.Message):
  if str(message.from_user.id) in admin_ids:
    states[message.from_user.id] = States.ADMIN_PANEL
    await message.answer('Admin paneliga xush kelibsiz!',
                         reply_markup=admin_keyboard)
  else:
    await message.answer('Siz admin emassiz!')


@dp.message_handler(lambda message: message.text == '📕Kitob qidirish')
async def search_book_handler(message: types.Message):
  states[message.from_user.id] = States.SEARCH_BOOK
  await message.answer('Kitob nomini yozing:', reply_markup=back_keyboard)


@dp.message_handler(
  lambda message: message.text == '📚Oxirgi qidirilgan kitoblar')
async def recently_books_handler(message: types.Message):
  conn = sqlite3.connect('recentlybooks.db')
  c = conn.cursor()
  c.execute('''SELECT * FROM recentlybooks ORDER BY id DESC LIMIT 10''')
  books = c.fetchall()
  conn.close()

  if not books:
    await message.answer('Oxirgi qidirilgan kitoblaringiz yo\'q!')
    return

  text = 'Oxirgi qidirilgan kitoblaringiz:\n\n'
  for book in books:
    text += f'📚 {book[1]}\n'

  await message.answer(text)


@dp.message_handler(lambda message: states.get(message.from_user.id) == States.
                    SEARCH_BOOK and message.text != 'Ortga')
async def search_book_name_handler(message: types.Message):
  conn = sqlite3.connect('books.db')
  c = conn.cursor()
  c.execute('''SELECT * FROM books WHERE name=?''', (message.text, ))
  book = c.fetchone()
  conn.close()

  if not book:
    await message.answer(f'{message.text} nomli kitob topilmadi!')
    return

  conn = sqlite3.connect('recentlybooks.db')
  c = conn.cursor()
  c.execute('''INSERT INTO recentlybooks(name) VALUES(?)''', (book[1], ))
  conn.commit()
  conn.close()

  await message.answer(
    f'{book[1]} nomli kitob topildi!\n\nYuklab olish uchun link: {book[2]}')


@dp.message_handler(lambda message: message.text == 'Kitob qo\'shish' and
                    states.get(message.from_user.id) == States.ADMIN_PANEL)
async def add_book_handler(message: types.Message):
  states[message.from_user.id] = States.ADD_BOOK_NAME
  await message.answer('Yangi kitob nomini yuboring:',
                       reply_markup=back_keyboard)


@dp.message_handler(
  lambda message: states.get(message.from_user.id) == States.ADD_BOOK_NAME)
async def add_book_name_handler(message: types.Message):
  states[message.from_user.id] = States.ADD_BOOK_LINK
  states[f'{message.from_user.id}_book_name'] = message.text
  await message.answer('Kitobni yuklab olish uchun link yuboring:')


@dp.message_handler(
  lambda message: states.get(message.from_user.id) == States.ADD_BOOK_LINK)
async def add_book_link_handler(message: types.Message):
  conn = sqlite3.connect('books.db')
  c = conn.cursor()
  c.execute('''INSERT INTO books(name, link) VALUES(?, ?)''',
            (states[f'{message.from_user.id}_book_name'], message.text))
  conn.commit()
  conn.close()

  states[message.from_user.id] = States.ADMIN_PANEL
  await message.answer(
    f'{states[f"{message.from_user.id}_book_name"]} nomli kitob muvaffaqiyatli qo\'shildi!',
    reply_markup=admin_keyboard)


@dp.message_handler(lambda message: message.text == 'Ortga')
async def back_handler(message: types.Message):
  if states.get(message.from_user.id) == States.MAIN_MENU:
    return

  if states.get(message.from_user.id) == States.ADMIN_PANEL:
    states[message.from_user.id] = States.MAIN_MENU
    await message.answer('Bosh menuga qaytdingiz!', reply_markup=main_keyboard)
    return

  if states.get(
      message.from_user.id) in [States.ADD_BOOK_NAME, States.ADD_BOOK_LINK]:
    states[message.from_user.id] = States.ADMIN_PANEL
    await message.answer('Admin paneliga qaytdingiz!',
                         reply_markup=admin_keyboard)
    return

  if states.get(message.from_user.id) == States.SEARCH_BOOK:
    states[message.from_user.id] = States.MAIN_MENU
    await message.answer('Bosh menuga qaytdingiz!', reply_markup=main_keyboard)
    return


@dp.message_handler(lambda message: message.text == '📖Barcha kitoblar')
async def all_books_handler(message: types.Message):
  conn = sqlite3.connect('books.db')
  c = conn.cursor()
  c.execute('''SELECT * FROM books''')
  books = c.fetchall()
  conn.close()

  if not books:
    await message.answer('Kitoblar yo\'q!')
    return

  text = 'Barcha kitoblar:\n\n'
  for book in books:
    text += f'📚 {book[1]}\n'

  await bot.send_message(chat_id=message.chat.id,
                         text=f'```\n{text}\n```',
                         parse_mode='MarkdownV2')


@dp.message_handler(lambda message: message.text == 'Statistik ma\'lumotlar'
                    and str(message.from_user.id) in admin_ids)
async def statistics_handler(message: types.Message):
  conn = sqlite3.connect('userscount.db')
  c = conn.cursor()
  c.execute('''SELECT COUNT(*) FROM users''')
  count = c.fetchone()[0]
  conn.close()

  await message.answer(f'Botdagi foydalanuvchilar soni: {count}')


if __name__ == '__main__':

  PORT = int(os.environ.get('PORT', 5000))

  updater.start_webhook(listen="0.0.0.0", port=PORT, url_path="6657019188:AAFZqixuGXeUpFZ4vQR2S3vlww40oLrVuDs")
updater.bot.setWebhook("VERCEL_SERVERLESS_FUNCTION_URL" + "6657019188:AAFZqixuGXeUpFZ4vQR2S3vlww40oLrVuDs")
updater.idle()