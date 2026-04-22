# Saved pdf making and sending
import matplotlib.pyplot as plt

def make_pdf():
    fig, ax = plt.subplots(figsize=(6,10))
    ax.axis('off')
    tbl = ax.table(cellText=dfs[0].values, colLabels=dfs[0].columns, loc='center', fontsize=130)
    # plt.show()
    plt.savefig('output.pdf', bbox_inches='tight')
    # await context.bot.send_message(chat_id=update.effective_chat.id, text=str(teetimes))
    with open('output.pdf', 'rb') as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f, filename='output.pdf')