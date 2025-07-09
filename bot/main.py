import asyncio
import time

import matplotlib.pyplot as plt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from tolkien import tolkien
from backend.wisegolf import get_wisegolf_teetimes
from backend.handle_teetimes import get_teetimes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=
"""Tervetuloa käyttämään Ossin tiiaikabottia.

Toistaiseksi botti kattaa wisegolfin tampereen alueen tiiajat. Kokeile komennolla /teetimes."""
    )

async def teetimes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teetimes = get_wisegolf_teetimes(date_delta=2, players_looking_to_play=1)[0]  # TODO

    fig, ax = plt.subplots(figsize=(6,10))
    ax.axis('off')
    tbl = ax.table(cellText=teetimes.values, colLabels=teetimes.columns, loc='center', fontsize=130)
    plt.show()
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