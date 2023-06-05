from core import Stancil
from utilities import config_var
import asyncio
import asyncpg

bot = Stancil()


async def main():
    async with bot:
        pg_cred = {
            "database": config_var['postgres_name'],
            "host": config_var['postgres_host'],
            "user": config_var['postgres_user'],
            "port": config_var['postgres_port'],
            "password": config_var['postgres_pass']
        }
        bot.db = await asyncpg.create_pool(**pg_cred)
        with open("schema.sql", 'r') as schema:
            await bot.db.execute(schema.read())
        try:
            await bot.start(config_var['token'])
        finally:
            await bot.db.close()
            await bot.session.close()
            await bot.close()


asyncio.run(main())
