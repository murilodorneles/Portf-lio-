import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bot")

TOKEN = os.getenv("BOT_TOKEN", "")

# isso aqui o cliente edita direto, é o cardapio dele
CARDAPIO = {
    "lanches": [
        {"id": "x1", "nome": "X-Burger", "preco": 18.90},
        {"id": "x2", "nome": "X-Bacon", "preco": 22.90},
        {"id": "x3", "nome": "X-Tudo", "preco": 28.90},
    ],
    "bebidas": [
        {"id": "b1", "nome": "Coca lata", "preco": 6.00},
        {"id": "b2", "nome": "Suco 500ml", "preco": 9.00},
    ],
}

# carrinho em memoria: {user_id: {item_id: qtd}}
carrinhos = {}


def pega_item(item_id):
    for lista in CARDAPIO.values():
        for item in lista:
            if item["id"] == item_id:
                return item
    return None


def teclado_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Ver cardapio", callback_data="menu")],
        [InlineKeyboardButton("Carrinho", callback_data="cart")],
        [InlineKeyboardButton("Fechar pedido", callback_data="checkout")],
    ])


def teclado_categorias():
    botoes = [
        [InlineKeyboardButton(cat.capitalize(), callback_data=f"cat:{cat}")]
        for cat in CARDAPIO
    ]
    botoes.append([InlineKeyboardButton("Voltar", callback_data="home")])
    return InlineKeyboardMarkup(botoes)


def teclado_itens(cat):
    botoes = []
    for item in CARDAPIO.get(cat, []):
        texto = f"{item['nome']} - R$ {item['preco']:.2f}"
        botoes.append([InlineKeyboardButton(texto, callback_data=f"add:{item['id']}")])
    botoes.append([InlineKeyboardButton("Voltar", callback_data="menu")])
    return InlineKeyboardMarkup(botoes)


async def cmd_start(update, ctx):
    nome = update.effective_user.first_name or "cliente"
    await update.message.reply_text(
        f"Ola, {nome}. Bem-vindo. Escolhe ai:",
        reply_markup=teclado_menu(),
    )


async def cmd_botao(update, ctx):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "home":
        await q.edit_message_text("Menu:", reply_markup=teclado_menu())

    elif q.data == "menu":
        await q.edit_message_text("Categoria:", reply_markup=teclado_categorias())

    elif q.data.startswith("cat:"):
        cat = q.data.split(":", 1)[1]
        await q.edit_message_text(f"{cat.capitalize()}:", reply_markup=teclado_itens(cat))

    elif q.data.startswith("add:"):
        item = pega_item(q.data.split(":", 1)[1])
        if not item:
            return
        c = carrinhos.setdefault(uid, {})
        c[item["id"]] = c.get(item["id"], 0) + 1
        await q.answer(f"+1 {item['nome']}")

    elif q.data == "cart":
        c = carrinhos.get(uid, {})
        if not c:
            await q.edit_message_text("Carrinho vazio.", reply_markup=teclado_menu())
            return
        linhas, total = [], 0.0
        for item_id, qtd in c.items():
            item = pega_item(item_id)
            if not item:
                continue
            sub = item["preco"] * qtd
            total += sub
            linhas.append(f"{qtd}x {item['nome']} = R$ {sub:.2f}")
        texto = "Carrinho:\n" + "\n".join(linhas) + f"\n\nTotal: R$ {total:.2f}"
        await q.edit_message_text(texto, reply_markup=teclado_menu())

    elif q.data == "checkout":
        c = carrinhos.get(uid, {})
        if not c:
            await q.edit_message_text("Nada pra fechar.", reply_markup=teclado_menu())
            return
        total = sum(pega_item(i)["preco"] * q for i, q in c.items() if pega_item(i))
        await q.edit_message_text(
            f"Pedido fechado. Total: R$ {total:.2f}\n\nManda o endereco aqui."
        )
        ctx.user_data["esperando_endereco"] = True


async def cmd_texto(update, ctx):
    if ctx.user_data.get("esperando_endereco"):
        ctx.user_data["esperando_endereco"] = False
        carrinhos.pop(update.effective_user.id, None)
        await update.message.reply_text(
            f"Anotado:\n{update.message.text}\n\nJa vamos preparar."
        )
        return
    await update.message.reply_text("Manda /start pra ver o menu.")


def main():
    if not TOKEN:
        print("Falta BOT_TOKEN no ambiente.")
        return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(cmd_botao))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, cmd_texto))
    print("Rodando...")
    app.run_polling()


if __name__ == "__main__":
    main()