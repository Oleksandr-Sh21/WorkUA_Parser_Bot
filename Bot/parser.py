import asyncio
import re

import aiohttp
import aiosqlite
from bs4 import BeautifulSoup

from dbase import add_vacancy, get_saved_urls

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def fetch_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    print(f"Помилка: {response.status}")
                    return None
        except Exception as e:
            print(f"Помилка під час отримання HTML: {e}")
            return None


async def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    pjax_jobs_list = soup.find('div', id='pjax-jobs-list')

    link_vacancy = []

    if pjax_jobs_list:
        top_level_links = pjax_jobs_list.find_all('a', recursive=False)
        for link in top_level_links:
            if link.get('name'):
                link_vacancy.append(f"https://www.work.ua/jobs/{link.get('name')}/")

    return link_vacancy


async def fetch_href_html(link_vacancy):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = []
        for link in link_vacancy:
            tasks.append(fetch_html(link))  # Використовуємо fetch_html для обробки окремих сторінок

        return await asyncio.gather(*tasks)


def clean_text_advanced(text):
    if not text:
        return ''
    text = re.sub(r'[\u202f\u2009\xa0]', ' ', text)
    text = re.sub(r'\s+', ' ', text)  # Заміна множинних пробілів на один
    return text.strip()


async def get_href_vacancy(html_pages):
    vacancies = []
    for html in html_pages:
        if not html:
            continue

        soup = BeautifulSoup(html, 'html.parser')

        job_title = soup.find('h1', id='h1-name')
        job_title = job_title.text.strip() if job_title else 'Не знайдено'

        salary = soup.find('li', class_='text-indent').find('span', string=lambda x: 'грн' in x if x else False)
        salary = salary.text.strip() if salary else 'Не вказано'
        salary = re.sub(r'\u202f|\u2009', ' ', salary)

        company_id = soup.find("meta", property="og:url")
        url = company_id
        url = url['content'] if url else 'Не знайдено'
        company_id = company_id.get('content').strip('https://www.work.ua/jobs/')

        company_link = soup.find('a', class_="inline")
        if company_link:
            company_name_span = company_link.find('span', class_='strong-500')
            company_name = company_name_span.text.strip() if company_name_span else 'Не знайдено'
        else:
            company_name = 'Не знайдено'

        employment_info = soup.find('li', string=lambda x: 'Повна зайнятість' in x if x else False)
        employment_info = employment_info.text.strip() if employment_info else 'Не вказано'

        job_description = soup.find('div', id='job-description')
        job_description = job_description.get_text(separator="\n").strip() if job_description else 'Не знайдено'

        skills = soup.find_all('li', class_='label-skill')
        skills = [skill.text.strip() for skill in skills] if skills else []

        additional_requirements = soup.find('ul', string=lambda x: x and 'Ваші основними завданнями будуть' in x)
        additional_requirements = additional_requirements.get_text(separator="\n").strip() if additional_requirements else 'Не вказано'

        vacancies.append({
            "ID": company_id,
            "Назва вакансії": job_title,
            "Назва компанії": company_name,
            "Зарплата": salary,
            "Тип зайнятості та вимоги": employment_info,
            "Навички": skills,
            "Опис вакансії": job_description,
            "Додаткові умови": additional_requirements,
            "url": url
        })
    return vacancies


async def monitor_vacancies(bot):
    url = 'https://www.work.ua/jobs-remote/?advs=1'

    while True:
        saved_urls = await get_saved_urls()

        html = await fetch_html(url)
        if not html:
            await asyncio.sleep(60)
            continue

        link_vacancy = await parse_html(html)
        if not link_vacancy:
            await asyncio.sleep(60)
            continue

        new_links = [link for link in link_vacancy if link not in saved_urls]

        if not new_links:
            await asyncio.sleep(60)
            continue

        html_pages = await fetch_href_html(new_links)
        if not html_pages:
            await asyncio.sleep(60)
            continue

        new_vacancies = await get_href_vacancy(html_pages)

        await add_vacancy(new_vacancies)

        for vacancy in new_vacancies:
            # Видаляємо зайві переноси рядків
            description = vacancy['Опис вакансії']
            description = re.sub(r'\n+', ' ', description.strip())

            if len(description) > 1000:
                description = description[:1000] + "..."

            # Екранування спеціальних символів для Markdown
            def escape_markdown(text):
                return re.sub(r'([*_`\[\]()])', r'\\\1', text)

            response = (
                f"**Назва:** {escape_markdown(vacancy['Назва вакансії'])}\n"
                f"**Компанія:** {escape_markdown(vacancy['Назва компанії'])}\n"
                f"**Зарплата:** {escape_markdown(vacancy['Зарплата'])}\n"
                f"**Навички:** {escape_markdown(', '.join(vacancy['Навички']))}\n\n"
                f"**Про вакансію:** {escape_markdown(description)}\n"
            )

            # Додаємо кнопку "Детальніше"
            details_button = InlineKeyboardButton(text="Детальніше", url=vacancy['url'])
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[details_button]])

            # Відправляємо повідомлення
            try:
                await bot.send_message(
                    chat_id="-1002490820867",
                    text=response,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
            except Exception as e:
                print(f"Помилка під час відправлення повідомлення: {e}")

        await asyncio.sleep(60)
