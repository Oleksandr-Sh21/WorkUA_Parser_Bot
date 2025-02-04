from aiogram import Router
from aiogram.filters.command import CommandStart, Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dbase import *

router = Router()


async def send_vacancies(message: Message):
    async with aiosqlite.connect('vacancies.db') as cursor:
        await cursor.execute("SELECT * FROM vacancies")
        vacancies = await cursor.fetchall()
        try:
            for vacancy in vacancies:
                description = vacancy['Опис вакансії']
                if len(description) > 1000:  # Максимальна довжина для опису
                    description = description[:1000] + '...'
                response = f"""
                           Назва: {vacancy['Назва вакансії']}
                           Компанія: {vacancy['Назва компанії']}
                           Зарплата: {vacancy['Зарплата']}
                           Навички: {', '.join(vacancy['Навички'])}
                           Про вакансію: {description}
                       """.strip()

                details_button = InlineKeyboardButton(text="Детальніше", url=vacancy['url'])
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[details_button]])
                await message.answer(response, reply_markup=keyboard)

        except Exception as e:
            print(f"Помилка: {e}")


@router.message(CommandStart())
async def cmd_start(message: Message):
    await bd_start()
    await send_vacancies(message)
    await message.answer(text='Привіт тут ви можене знайти віддалену роботу')
