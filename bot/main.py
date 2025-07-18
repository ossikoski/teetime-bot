import asyncio
import time

import matplotlib.pyplot as plt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from backend.handle_teetimes import get_teetimes
from backend.wisegolf import get_wisegolf_teetimes
from common.utils import weekdays, weekday_to_date_delta
from tolkien import tolkien


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=
"""Tervetuloa käyttämään Ossin tiiaikabottia.

Toistaiseksi botti kattaa wisegolfin tampereen alueen tiiajat. Kokeile komennolla /teetimes."""
    )

async def teetimes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:  # TODO More parameter handling
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Usage: /teetimes <players> [course] [weekday], where number of players is required.'
        )
        return
    players = int(context.args[0])
    if players < 1 or players > 4:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Usage: /teetimes <players> [course] [weekday], where number of players must be 1 to 4.'
        )
        return
    if len(context.args) >= 1:
        course = context.args[1]
        if course == 'all' or course == 'kaikki':
            course = None
    if len(context.args) == 2:
        weekday = context.args[2]
        if weekday not in weekdays.keys():
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Usage: /teetimes <players> [course] [weekday], where weekday is one of ma, ti, ke, to, pe, la, su.'
            )
            return
        date_delta = weekday_to_date_delta(weekday_abbr=weekday)

    dfs = get_wisegolf_teetimes(date_delta=date_delta, players_looking_to_play=players)
    

    fig, ax = plt.subplots(figsize=(6,10))
    ax.axis('off')
    tbl = ax.table(cellText=teetimes.values, colLabels=teetimes.columns, loc='center', fontsize=130)
    # plt.show()
    plt.savefig('output.pdf', bbox_inches='tight')
    # await context.bot.send_message(chat_id=update.effective_chat.id, text=str(teetimes))
    with open('output.pdf', 'rb') as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f, filename='output.pdf')


def main():
    app = ApplicationBuilder().token(tolkien).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('teetimes', teetimes))

    app.run_polling()


if __name__ == "__main__":
    main()