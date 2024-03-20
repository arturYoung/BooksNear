import asyncio
import logging

from aiogram import Bot
from aiogram import Dispatcher
from aiogram import F, Router, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.types import Message

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import json

from geopy.distance import geodesic as GD
from fuzzywuzzy import fuzz 
from fuzzywuzzy import process


# ЗАНОСИМ ТОКЕН БОТА В ПЕРЕМЕННУЮ
BOT_TOKEN = "6988933336:AAHU5G37BtpAMrCl5r34pCICedJh1CRjff8"

bot = Bot(token=BOT_TOKEN)

form_router = Router()

dp = Dispatcher()

dp.include_router(form_router)



class Buttons:
    registartion = "Зарегистрироваться"
    
class AdInfo(StatesGroup):
    isbn = State()
    book_real_name = State()
    geoposition = State() # State -> List[x, y]
    author = State()
    year = State()
    creator = State()
    
class SearchInfo(StatesGroup):
    book_real_name = State()
    author = State()
    
class Hello(StatesGroup):
    search_or_publish = State()



@form_router.message(CommandStart())
async def handle_command_start(message: types.message, state: FSMContext) -> None:
    
    await state.set_state(Hello.search_or_publish)
    await message.answer(
        text=f"Привет, {message.from_user.full_name}\nЭтот бот создан для того, чтобы найти книги рядом!",
        # ИНИЦИАЛИЗИРУЕМ КЛАВИАТУРУ
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Найти книгу рядом")
                ],
                [
                    KeyboardButton(text="Добавить свою книгу")
                ]
            ],
            resize_keyboard=True
        )
    )



@form_router.message(Hello.search_or_publish)
async def process_what_you_want(message: Message, state: FSMContext):
    if message.text == "Найти книгу рядом":
        await state.update_data(search_or_publish="search")
        await state.update_data(creator=message.from_user.username)
        await state.set_state(SearchInfo.author)
        
        return await message.answer(
            "Окей, напиши автора книги, которую ты хочешь найти",
            reply_markup=ReplyKeyboardRemove()
        )
        
    elif message.text == "Добавить свою книгу":
        await state.update_data(search_or_publish="publish")
        await state.set_state(AdInfo.author)
        return await message.answer(
            "Окей, напиши автора книги, которую ты хочешь отдать", 
            reply_markup=ReplyKeyboardRemove()
            
        )
    
    

@form_router.message(AdInfo.author)
async def process_create_author_want(message: Message, state: FSMContext):
    await state.update_data(author=message.text)
    await state.set_state(AdInfo.isbn)
    return await message.answer("Отлично, теперь отправь ISBN", reply_markup=ReplyKeyboardRemove())

@form_router.message(AdInfo.isbn)
async def process_create_author_want(message: Message, state: FSMContext):
    await state.update_data(isbn=message.text)
    await state.set_state(AdInfo.book_real_name)
    return await message.answer("Теперь отправь полное имя книги", reply_markup=ReplyKeyboardRemove())

@form_router.message(AdInfo.book_real_name)
async def process_create_author_want(message: Message, state: FSMContext):
    await state.update_data(book_real_name=message.text)
    await state.set_state(AdInfo.year)
    return await message.answer("Отправь дату выхода этой книги", reply_markup=ReplyKeyboardRemove())

@form_router.message(AdInfo.year)
async def process_create_author_want(message: Message, state: FSMContext):
    await state.update_data(year=int(message.text))
    await state.set_state(AdInfo.geoposition)
    return await message.answer("Теперь отправь свою геопозицию", reply_markup=ReplyKeyboardRemove())

@form_router.message(AdInfo.geoposition)
async def process_create_author_want(message: Message, state: FSMContext):
    if message.location != None:
        await state.update_data(geoposition=[
            message.location.longitude,
            message.location.latitude
        ])
        
    state_data = await state.get_data()
        
    with open("data.json", 'r') as file:
        data = json.load(file)
    
    with open("data.json", "w") as file:
        data['ads'].append(
            state_data
        )
        json.dump(data, file, indent=4)
        
    return await message.answer("Я разместил твое объявление в боте!", reply_markup=ReplyKeyboardRemove())



@form_router.message(SearchInfo.author)
async def process_what_author_want(message: Message, state: FSMContext):
    await state.update_data(author=message.text)
    await state.set_state(SearchInfo.book_real_name)
    return await message.answer("Отлично, как насчет реального имени книги?", reply_markup=ReplyKeyboardRemove())

@form_router.message(SearchInfo.book_real_name)
async def process_what_isbn_want(message: Message, state: FSMContext):
    await state.update_data(book_real_name=message.text)
    await message.answer("Отлично, сейчас найду точку", reply_markup=ReplyKeyboardRemove())
    
    state_data = await state.get_data()
    
    with open("data.json", 'r') as file:
        data = json.load(file)
        
    for ad in data['ads']:
        if fuzz.WRatio(f"{ad['author']} {ad['book_real_name']}", f"{state_data['author']} {state_data['book_real_name']}") > 60:
            await message.answer(f"""
Книга: {ad['book_real_name']}
Автор: {ad['author']}
Год печати: {ad['year']}
Место: https://www.google.com/maps/@{ad['geoposition'][1]},{ad['geoposition'][0]},14.27z?entry=ttu
                                 """ )


    
    

    
    
    


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == __name__:
    asyncio.run(main())
