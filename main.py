from aiopg.sa import create_engine
from bot import PeshoBot
import asyncio
import os


BOT_PREFIXES = ('!',)
TOKEN = os.environ.get('ACCESS_TOKEN')
DATABASE_NAME = os.environ.get('DATABASE_NAME')
DATABASE_USER = os.environ.get('DATABASE_USER')
DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD')
DATABASE_HOST = os.environ.get('DATABASE_HOST')
DATABASE_PORT = os.environ.get('DATABASE_PORT')
dsn = f'dbname={DATABASE_NAME} user={DATABASE_USER} password={DATABASE_PASSWORD} host={DATABASE_HOST}'

async def run():
    async with create_engine(dsn=dsn) as engine:
        async with engine.acquire() as conn:
            bot = PeshoBot(BOT_PREFIXES, conn)
            await bot.start(TOKEN)

loop = asyncio.get_event_loop()
loop.run_until_complete(run())

