import asyncio
import time

from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from backend.wisegolf import get_wisegolf_teetimes
from backend.handle_teetimes import find_free_blocks, handle_teetime_dfs
from common.utils import weekdays, weekday_to_date_delta
from tolkien import tolkien


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=
"""Tervetuloa käyttämään Ossin tiiaikabottia.

Toistaiseksi botti kattaa wisegolfin Tampereen alueen tiiajat. Kokeile komennolla /tiiajat."""
    )

async def teetimes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('Teetimes called with args:', context.args)
    if len(context.args) == 0:  # TODO More parameter handling
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Käyttö: /tiiajat <pelaajat> [kenttä] [viikonpäivä], missä pelaajien määrä on vaadittu parametri.'
        )
        return
    players = int(context.args[0])
    if players < 1 or players > 4:
        await context.bot.send_message(
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
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Usage: /tiiajat <pelaajat> [kenttä] [viikonpäivä], missä viikonpäivä pitää olla ma, ti, ke, to, pe, la, tai su'
            )
            return
        specific_date = (datetime.today() + timedelta(weekday_to_date_delta(weekday))).date()

    dfs = await asyncio.to_thread(get_wisegolf_teetimes, players_looking_to_play=players, course=course, specific_date=specific_date)

    df = handle_teetime_dfs(dfs)

    await context.bot.send_poll(chat_id=update.effective_chat.id, question='Äänestä aikaa', options=['Testi1', 'Testi2'], is_anonymous=False, allows_multiple_answers=True)

    print('Sent teetime poll', context.args)

def main():
    app = ApplicationBuilder().token(tolkien).build()

    app.add_handler(CommandHandler('aloita', start))
    app.add_handler(CommandHandler('tiiajat', teetimes))

    print('app running...')

    app.run_polling()


if __name__ == "__main__":
    main()
