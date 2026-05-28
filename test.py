import asyncio
from database import init_database

async def main():
    result = await init_database.scrape_accounts_repo.get_scrape_accounts()
    for res in result:
        print(res.type)

asyncio.run(main())