import asyncio
import logging
import time

from datetime import datetime, timedelta
from telegram import Update
from telegram.error import NetworkError
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from backend.wisegolf import get_wisegolf_teetimes
from backend.handle_teetimes import find_free_blocks, handle_teetime_dfs
from common.utils import weekdays, weekday_to_date_delta
from tolkien import tolkien


async def _send_message_with_retry(bot, retries=3, delay=2, **kwargs):
    for attempt in range(retries):
        try:
            await bot.send_message(**kwargs)
            return
        except NetworkError:
            if attempt == retries - 1:
                raise
            await asyncio.sleep(delay)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_message_with_retry(context.bot,
        chat_id=update.effective_chat.id,
        text=
"""Tervetuloa käyttämään Ossin tiiaikabottia.

Toistaiseksi botti kattaa wisegolfin Tampereen alueen tiiajat. Kokeile komennolla /tiiajat."""
    )

async def teetimes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info('Teetimes called with args: %s', context.args)
    if len(context.args) == 0:  # TODO More parameter handling
        await _send_message_with_retry(context.bot,
            chat_id=update.effective_chat.id,
            text='Käyttö: /tiiajat <pelaajat> [kenttä] [viikonpäivä], missä pelaajien määrä on vaadittu parametri.'
        )
        return
    players = int(context.args[0])
    if players < 1 or players > 4:
        await _send_message_with_retry(context.bot,
            chat_id=update.effective_chat.id,
            text='Usage: /tiiajat <pelaajat> [kenttä] [viikonpäivä], missä pelaajien määrä pitää olla 1-4.'
        )
        return

    course = None
    specific_date = None

    if len(context.args) >= 2:
        course = context.args[1]
        if course == 'all' or course == 'kaikki':
            course = None
    if len(context.args) >= 3:
        weekday = context.args[2]
        if weekday not in weekdays.keys():
            await _send_message_with_retry(context.bot,
                chat_id=update.effective_chat.id,
                text='Usage: /tiiajat <pelaajat> [kenttä] [viikonpäivä], missä viikonpäivä pitää olla ma, ti, ke, to, pe, la, tai su'
            )
            return
        specific_date = (datetime.today() + timedelta(weekday_to_date_delta(weekday))).date()

    dfs = await asyncio.to_thread(get_wisegolf_teetimes, players_looking_to_play=players, course=course, specific_date=specific_date)

    #df = handle_teetime_dfs(dfs)  # If getting separate teetimes, not blocks (concat dfs & sort)
    df = find_free_blocks(dfs)
    tee_options = df['block'].tolist()

    # Handle sending the poll / error messages
    if len(tee_options) == 0:
        await _send_message_with_retry(context.bot,
            chat_id=update.effective_chat.id,
            text='Ei vapaita tiiaikoja annetuilla valinnoilla.'
        )
        logging.info('Sent info for no free teetimes')
    elif len(tee_options) > 12:
        await _send_message_with_retry(context.bot,
            chat_id=update.effective_chat.id,
            text='Yli 12 vapaata tiiaikaa annetuilla valinnoilla, ei voitu luoda äänestystä.'
        )
        logging.info('Sent info for over 12 free teetimes')
    else:
        for attempt in range(3):  # Poll sending had connection issues, do a manual retry loop
            try:
                await context.bot.send_poll(chat_id=update.effective_chat.id, question='Äänestä aikaa', options=tee_options, is_anonymous=False, allows_multiple_answers=True)
                logging.info('Sent teetime poll %s', context.args)
                break
            except NetworkError:
                if attempt == 2:
                    raise
                await asyncio.sleep(2)

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    #logger = logging.getLogger(__name__)

    app = ApplicationBuilder().token(tolkien).connect_timeout(30).read_timeout(30).write_timeout(30).pool_timeout(30).build()

    app.add_handler(CommandHandler('aloita', start))
    app.add_handler(CommandHandler('tiiajat', teetimes))

    logging.info('app running...')

    app.run_polling(bootstrap_retries=5)  # Retry bot start up to 5 times

def test():
    players=2
    course='Tammer-golf 9r'
    specific_date=(datetime.today() + timedelta(weekday_to_date_delta('to'))).date()
    dfs = get_wisegolf_teetimes(players_looking_to_play=players, course=course, specific_date=specific_date)
    df = find_free_blocks(dfs)

    logging.info(df)

if __name__ == "__main__":
    main()
    #test()

