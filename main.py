import asyncpg
import disnake
import locale
import logging
import os
from decouple import config
from utils.constants import *
import utils.classes as classes

logger = logging.getLogger('errors')
logger.setLevel(logging.ERROR)
handler = logging.FileHandler(
    filename='errors.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Indiquer la localité, ici la France
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
os.environ['TZ'] = 'Europe/Paris'

intents = disnake.Intents.all()

bot = classes.EvaBot(intents=intents)
bot.i18n.load("locale/")

# Initialisation de la connexion à la base de données Interne
bot.pool: asyncpg.Pool = bot.loop.run_until_complete(asyncpg.create_pool(
    host=config("HOST_DB"),
    user=config("USER_DB"),
    password=config("PASSWD_DB"),
    database=config("DB")))

bot.load_extensions("cogs")
bot.run(config("TOKEN"))
