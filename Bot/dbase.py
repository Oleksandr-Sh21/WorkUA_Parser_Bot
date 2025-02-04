import aiosqlite


async def bd_start():
    async with aiosqlite.connect('vacancies.db') as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS vacancies (
            ID TEXT PRIMARY KEY,
            job_title TEXT NOT NULL,
            company_name TEXT,
            salary TEXT,
            employment_info TEXT,
            skills TEXT,
            job_description TEXT,
            additional_requirements TEXT,
            url TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        await conn.commit()

        await conn.execute("""
        DELETE FROM vacancies
        WHERE ID NOT IN (
            SELECT ID FROM vacancies
            ORDER BY added_at DESC
            LIMIT 1000
        )
        """)
        await conn.commit()


async def add_vacancy(vacancies):
    async with aiosqlite.connect('vacancies.db') as conn:
        for vacancy in vacancies:
            await conn.execute("""
                INSERT OR IGNORE INTO vacancies (ID, job_title, company_name, salary, employment_info, skills, job_description, additional_requirements, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                vacancy["ID"],
                vacancy["Назва вакансії"],
                vacancy["Назва компанії"],
                vacancy["Зарплата"],
                vacancy["Тип зайнятості та вимоги"],
                ', '.join(vacancy["Навички"]),
                vacancy["Опис вакансії"],
                vacancy["Додаткові умови"],
                vacancy["url"]
            ))

        await conn.execute("""
        DELETE FROM vacancies
        WHERE ID NOT IN (
            SELECT ID FROM vacancies
            ORDER BY added_at DESC
            LIMIT 1000
        )
        """)
        await conn.commit()


async def get_saved_urls():
    async with aiosqlite.connect('vacancies.db') as conn:
        async with conn.execute("SELECT url FROM vacancies") as cursor:
            return {row[0] for row in await cursor.fetchall()}