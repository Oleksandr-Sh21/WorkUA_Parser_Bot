import asyncio
import logging

from aiogram import Bot, Dispatcher
from config import API_TOKEN
from apps.hendlers import router, cmd_start
from dbase import bd_start
from parser import monitor_vacancies

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


async def main():
    logging.basicConfig(level=logging.INFO)
    await bd_start()
    asyncio.create_task(monitor_vacancies(bot))
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот завершив роботу.")

