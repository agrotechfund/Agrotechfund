import json
import os
def carregar_json(caminho):
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

CODIGOS_FILE = "codigos.json"

def salvar_codigos():
    with open(CODIGOS_FILE, "w", encoding="utf-8") as f:
        json.dump(gerenciador_codigos.codigos_bonus, f, ensure_ascii=False, indent=4)

def carregar_codigos():
    if os.path.exists(CODIGOS_FILE):
        with open(CODIGOS_FILE, "r", encoding="utf-8") as f:
            gerenciador_codigos.codigos_bonus = json.load(f)
    else:
        gerenciador_codigos.codigos_bonus = {}

import random
import string
import datetime
from datetime import datetime, timezone, timedelta
USERS_FILE = "usuarios.json"
usuarios = carregar_json(USERS_FILE)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from telegram.ext.filters import User as FilterUser
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ✅ Configuração de variáveis de ambiente
TOKEN = os.getenv("BOT_TOKEN") or "8077908640:AAHSkV9dooJLJtPN-XrAEosHQVWpIkjBgPg"
ADMIN_ID = int(os.getenv("ADMIN_ID") or "8182769178")

# ✅ Caminhos dos arquivos JSON
USERS_FILE = "usuarios.json"
PENDENTES_FILE = "pendentes.json"

# ✅ Estruturas de dados em memória
usuarios = {}
pendentes = {}

# ✅ Função para carregar JSON com segurança
def carregar_json(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️ Erro ao carregar {filepath}, JSON inválido.")
    return {}

# ✅ Função para salvar JSON formatado
def salvar_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ✅ Função para gerar ID aleatório
def gerar_id(tamanho=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=tamanho))

def get_planos_disponiveis():
    return {
        "🥬 Couve manteiga":   {"preco": 350,    "percent": 0.07, "dias": 3, "max": 1},
        "🥔 Batata doce":      {"preco": 1500,   "percent": 0.07, "dias": 5, "max": 2},
        "🍍 Doce de abacaxi":  {"preco": 3500,   "percent": 0.08, "dias": 30, "max": 3},
        "🍌 Banana cacho":     {"preco": 6000,   "percent": 0.08, "dias": 30, "max": 3},
        "🌽 Milho saco":       {"preco": 10500,  "percent": 0.08, "dias": 45, "max": 5},
        "🐔 Galinha caipira":  {"preco": 21000,  "percent": 0.09, "dias": 45, "max": 5},
        "🐐 Cabrito":          {"preco": 30000,  "percent": 0.09, "dias": 45, "max": 10},
        "🐖 Porco":            {"preco": 60000,  "percent": 0.09, "dias": 60, "max": 10},
        "🐄 Vaca leiteira":    {"preco": 100000, "percent": 0.10, "dias": 60, "max": 10},
        "🌾 Terreno agrícola": {"preco": 150000, "percent": 0.10, "dias": 60, "max": 10},
    }

# 🔝 Em cima junto com TOKEN, ADMIN_ID:
NOME_BOT = "AgrotechFund_bot"

# --- VERIFICAÇÃO DE BANIMENTO ---
def checa_banido(func):
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        uid = str(update.effective_user.id)
        usuarios = carregar_json(USERS_FILE)
        user = usuarios.get(uid)

        if user and user.get("banido", False):
            try:
                if update.message:
                    await update.message.delete()
            except:
                pass
            try:
                if update.callback_query:
                    await update.callback_query.message.delete()
            except:
                pass

            texto = (
                "⛔ *Acesso suspenso*\n\n"
                "Sua conta foi **banida** por não seguir corretamente as regras e diretrizes "
                "definidas pela nossa empresa.\n\n"
                "👉 Antes de entrar em contato com o suporte, é muito importante que você leia com atenção "
                "o nosso *Regulamento Oficial*, onde estão descritas todas as normas de uso e os motivos "
                "que podem levar a suspensões ou bloqueios.\n\n"
                "Nosso objetivo é manter um ambiente seguro, justo e transparente para todos os usuários. "
                "Se, após a leitura, acreditar que houve algum engano ou desejar solicitar uma revisão, "
                "estamos disponíveis para ouvir sua situação através do suporte."
            )

            keyboard = [
                [InlineKeyboardButton("📜 Regulamento oficial", url="https://telegra.ph/Regras-e-Normas-da-Plataforma--Impotante-Ler-09-02")],
                [InlineKeyboardButton("🎧 Suporte", url="https://t.me/Agroinvestlda")]
            ]

            return await (update.message or update.callback_query.message).reply_text(
                texto,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        return await func(update, ctx, *args, **kwargs)
    return wrapper

# 👇 Função start bem organizada:
@checa_banido
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    uid = str(u.id)
    nome = u.first_name

    if uid not in usuarios:
        usuarios[uid] = {
            "nome": nome,
            "saldo": 0,
            "planos": [],
            "indicador": None,
            "indicados": []
        }
        salvar_json(USERS_FILE, usuarios)

    msg = (
        f"🤖 *Bem-vindo ao {NOME_BOT}*, {nome}!\n\n"
        f"Eu sou seu assistente de investimento.\n"
        f"Estou aqui para fornecer informações valiosas e ajudá-lo a tomar decisões informadas "
        f"sobre seus investimentos com segurança e transparência.\n\n"
        f"💼 *Comandos úteis:* Use `/ajuda` para ver todos os comandos.\n\n"
        f"📢 Para ficar por dentro das últimas tendências e análises do mercado, "
        f"junte-se ao nosso canal oficial no Telegram:\n"
        f"👉 [Canal Oficial](https://t.me/+ydQ0aKslT4lmYjVk)\n\n"
        f"❓ Tem dúvidas ou precisa de ajuda? Fale com nosso suporte:\n"
        f"👤 @Agroinvestlda\n\n"
        f"Estamos ansiosos para ter você conosco. Vamos crescer juntos! 🚀"
    )

    buttons = [
        [InlineKeyboardButton("📚 Ver Comandos", callback_data="ajuda")],
        [InlineKeyboardButton("💼 Ver Planos", callback_data="planos")],
        [InlineKeyboardButton("📢 Canal Oficial", url="https://t.me/+ydQ0aKslT4lmYjVk")],
        [InlineKeyboardButton("👤 Suporte", url="https://t.me/Agroinvestlda")]
    ]
    markup = InlineKeyboardMarkup(buttons)

    # Compatível com /start chamado por mensagem ou botão:
    target = update.message or update.callback_query.message
    await target.reply_text(
        msg,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from datetime import datetime, timedelta

# Função que lista os planos
@checa_banido
async def planos(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    pd = get_planos_disponiveis()
    kb = []
    for nome, info in pd.items():
        kb.append([
            InlineKeyboardButton(
                f"{nome} — {info['preco']} MZN",
                callback_data=f"comprar|{nome}"
            )
        ])

    # botão voltar
    kb.append([InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda")])
    reply = InlineKeyboardMarkup(kb)

    target = update.message or update.callback_query.message
    await target.reply_text(
        "📋 *Planos disponíveis:*",
        reply_markup=reply,
        parse_mode=ParseMode.MARKDOWN
    )
    
async def tratar_texto(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    text = update.message.text

from datetime import datetime
USERS_FILE = "usuarios.json"
import telegram
from telegram.constants import ParseMode

@checa_banido
async def saldo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    user = usuarios.get(uid)

    if not user:
        return await update.message.reply_text("❌ Você ainda não possui conta. Use /start para criar sua conta!")

    saldo_atual = user.get("saldo", 0.0)
    planos_ativos = user.get("planos", [])
    num_planos = len(planos_ativos)

    lucro_total = sum(
        p["valor"] * p["percent"] * (p.get("dias_restantes_max", p["dias_restantes"]) - p["dias_restantes"])
        for p in planos_ativos
    )

    lucro_diario_total = sum(
        p["valor"] * p["percent"] for p in planos_ativos
    )

    ultima_coleta = user.get("last_coleta_date", "Nunca")

    msg = (
        f"💰 *Seu saldo*: {saldo_atual:.2f} MZN\n"
        f"📊 *Planos ativos*: {num_planos}\n"
        f"📈 *Lucro já ganho*: {lucro_total:.2f} MZN\n"
        f"💵 *Lucro diário estimado*: {lucro_diario_total:.2f} MZN\n"
        f"📅 *Próxima coleta (amanhã)*: {lucro_diario_total:.2f} MZN\n"
        f"🗓️ *Última coleta*: {ultima_coleta}\n"
        f"\n"
        f"✅ Continue investindo para aumentar seus ganhos!"
    )

    await update.message.reply_text(msg, parse_mode="Markdown")

# 📌 MENU PRINCIPAL DE AJUDA
@checa_banido
async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "📚 *Ajuda — Comandos Disponíveis*\n\n"
        "Escolha uma opção para ver mais detalhes:"
    )
    buttons = [
        [InlineKeyboardButton("🚀 Start", callback_data="ajuda_start")],
        [InlineKeyboardButton("📋 Planos", callback_data="ajuda_planos")],
        [InlineKeyboardButton("💼 Saldo", callback_data="ajuda_saldo")],
        [InlineKeyboardButton("🤝 Indicação", callback_data="ajuda_indicacao")],
        [InlineKeyboardButton("📑 Meus Planos", callback_data="ajuda_meusplanos")],
        [InlineKeyboardButton("🗂️ Histórico", callback_data="ajuda_historico")],
        [InlineKeyboardButton("⚙️ Configurações", callback_data="configuracoes")],
    ]
    markup = InlineKeyboardMarkup(buttons)
    
    if update.callback_query:
        q = update.callback_query
        await q.answer()

        # ✅ Remove SOMENTE os botões da mensagem anterior
        try:
            await q.message.edit_reply_markup(reply_markup=None)
        except Exception as e:
            print("Erro ao remover botões:", e)

        # ✅ Envia nova mensagem com menu de ajuda
        await q.message.reply_text(
            texto,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=markup
        )

    elif update.message:
        await update.message.reply_text(
            texto,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=markup
        )

HISTORICO_FILE = "historico.json"
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

ADMINS = ["8182769178"]  # Pode colocar como string ou int
USERS_PER_PAGE = 8  #
async def menu_admin_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id  # mantém como número

    # comparação segura para string ou int
    if str(uid) not in [str(a) for a in ADMINS]:
        return await query.message.reply_text("❌ Você não tem permissão para acessar o painel admin.")

    keyboard = [
        [
            InlineKeyboardButton("👥 Gerenciar Usuários", callback_data="admin_usuarios"),
            InlineKeyboardButton("💰 Ferramentas Admin📊", callback_data="abrir_menu")
        ],
        [
            InlineKeyboardButton("📜 Logs de Admin", callback_data="admin_logs"),
            InlineKeyboardButton("🚫 Banimento", callback_data="admin_ban_menu")
        ],
        [
            InlineKeyboardButton("📥 Baixar usuários", callback_data="baixar_usuarios"),
            InlineKeyboardButton("📂 Ver pendentes", callback_data="ver_pendentes")
        ],
        [
            InlineKeyboardButton("🧹 Limpar saldos corrompidos", callback_data="limpar_saldo"),
            InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda")
        ],
    ]
    markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "🛠️ *Painel Admin*\nEscolha uma opção:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )

# Listar usuários com paginação
# --- Listar Usuários com paginação e opção de inserir ID manualmente ---
async def admin_listar_usuarios_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE, page=0):
    query = update.callback_query
    await query.answer()
    all_users = list(usuarios.keys())
    start = page * USERS_PER_PAGE
    end = start + USERS_PER_PAGE
    users_slice = all_users[start:end]

    # Botões para cada usuário na página
    keyboard = [[InlineKeyboardButton(f"👤 {u}", callback_data=f"admin_user|{u}")] for u in users_slice]

    # Botões de navegação
    nav_buttons = []
    if start > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"admin_page|{page-1}"))
    if end < len(all_users):
        nav_buttons.append(InlineKeyboardButton("➡️ Próxima", callback_data=f"admin_page|{page+1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    # Botão para inserir ID manualmente
    keyboard.append([InlineKeyboardButton("✏️ Inserir ID manualmente", callback_data="admin_manual_id")])

    # Botão de voltar
    keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data="menu_admin")])

    markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "👥 *Selecione um usuário* ou insira o ID manualmente:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )

# --- Callback para capturar ID manual ---
async def admin_manual_id_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    ctx.user_data["esperando_id_manual"] = True
    await query.message.reply_text("📝 Digite o ID do usuário que deseja acessar:")

# --- Handler para processar ID digitado ---
async def capturar_id_usuario(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if ctx.user_data.get("esperando_id_manual"):
        user_id = update.message.text.strip()
        ctx.user_data["esperando_id_manual"] = False

        if user_id not in usuarios:
            await update.message.reply_text(f"❌ Usuário {user_id} não encontrado.")
            return

        # Chama a função do menu do usuário
        await admin_user_cb(update, ctx, user_id=user_id)

# --- Funções Auxiliares ---
def carregar_planos():
    return carregar_json("planos.json")  # exemplo, pode mudar

def plano_existe(nome):
    planos = carregar_planos()
    return nome in planos

# --- ADMIN MENU PARA USUÁRIO ---
async def admin_user_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE, user_id=None):
    query = update.callback_query if hasattr(update, "callback_query") else None

    # Se não foi passado user_id, tenta pegar do callback
    if user_id is None:
        if query and query.data:
            try:
                _, user_id = query.data.split("|", 1)
            except Exception:
                if query:
                    return await query.answer("❌ Dados inválidos.", show_alert=True)
                else:
                    return await update.message.reply_text("❌ Dados inválidos.")
        else:
            return await update.message.reply_text("❌ Dados inválidos.")

    ctx.user_data["admin_selected_user"] = user_id

    keyboard = [
        [InlineKeyboardButton("💰 Ajustar Saldo", callback_data="admin_saldo")],
        [InlineKeyboardButton("🎁 Dar Plano/Bônus", callback_data="admin_plano")],
        [InlineKeyboardButton("🔐 Resetar Senha", callback_data="admin_reset_senha")],
        [InlineKeyboardButton("💳 Aprovar Depósito", callback_data="admin_aprovar_deposito")],
        [InlineKeyboardButton("🗑 Remover Plano/Saldo", callback_data="admin_remover_valor")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="admin_usuarios")],
    ]

    # Atualiza mensagem de acordo com a origem (callback ou mensagem)
    if query:
        await query.edit_message_text(
            f"🛠️ Usuário selecionado: {user_id}\nEscolha a ação:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            f"🛠️ Usuário selecionado: {user_id}\nEscolha a ação:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


PLANOS_DISPONIVEIS = get_planos_disponiveis()  # Dicionário de planos disponíveis
NOMES_PLANOS = list(PLANOS_DISPONIVEIS.keys())  # Lista só com os nomes para verificação

async def admin_acao_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    acao = query.data
    user_id = ctx.user_data.get("admin_selected_user")
    if not user_id or user_id not in usuarios:
        return await query.edit_message_text("❌ Usuário inválido.")

    ctx.user_data["admin_acao"] = acao

    prompt = {
        "admin_saldo": "💰 Digite o valor (+ ou -) para ajustar o saldo:",
        "admin_plano": "🎁 Digite o nome do plano/bônus para atribuir (verifica planos existentes):",
        "admin_aprovar_deposito": "💳 Digite o valor do depósito aprovado:",
        "admin_remover_valor": "🗑 Digite o valor ou nome do plano para remover:"
    }.get(acao)

    if prompt:
        await query.edit_message_text(f"Usuário: {user_id}\n{prompt}")
        ctx.user_data["aguardando_input"] = True

from datetime import datetime, timedelta

from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta

async def admin_input_process(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.user_data.get("aguardando_input"):
        return await update.message.reply_text("⚠️ Não há nenhuma operação pendente no momento.")

    user_id = ctx.user_data.get("admin_selected_user")
    acao = ctx.user_data.get("admin_acao")
    texto = update.message.text.strip()
    ctx.user_data["aguardando_input"] = False
    ctx.user_data["valor_input"] = texto

    # Verificação se plano existe antes de criar a mensagem de confirmação
    if acao == "admin_plano" and texto not in PLANOS_DISPONIVEIS:
        return await update.message.reply_text(f"❌ Plano '{texto}' não existe no sistema.")

    # criar mensagem de confirmação
    msg = ""
    if acao == "admin_saldo":
        msg = f"💰 Adicionar {texto} MZN ao saldo de {user_id}?"
    elif acao == "admin_plano":
        msg = f"🎁 Dar o plano '{texto}' ao usuário {user_id}?"
    elif acao == "admin_aprovar_deposito":
        msg = f"💳 Aprovar depósito de {texto} MZN para {user_id}?"
    elif acao == "admin_remover_valor":
        msg = f"🗑 Remover '{texto}' da conta de {user_id}?"
    elif acao == "admin_reset_senha":
        msg = f"🔑 Resetar a senha do usuário {user_id}?"
    else:
        return await update.message.reply_text("⚠️ Ação desconhecida.")

    keyboard = [
        [
            InlineKeyboardButton("✅ Confirmar", callback_data="admin_confirmar"),
            InlineKeyboardButton("❌ Cancelar", callback_data="admin_cancelar")
        ]
    ]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_confirmar_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = ctx.user_data.get("admin_selected_user")
    acao = ctx.user_data.get("admin_acao")
    valor = ctx.user_data.get("valor_input")
    uid = query.from_user.id

    if not user_id or user_id not in usuarios:
        return await query.edit_message_text("❌ Usuário não encontrado.")

    try:
        if acao in ["admin_saldo", "admin_aprovar_deposito"]:
            v = float(valor)
            usuarios[user_id]["saldo"] = usuarios[user_id].get("saldo", 0) + v
            saldo_atual = usuarios[user_id]["saldo"]  # ✅ saldo atualizado
            salvar_json(USERS_FILE, usuarios)
            salvar_log(uid, f"Ajustou saldo {v:+}", user_id)
            await query.edit_message_text(f"✅ Saldo atualizado (+{v}) para {user_id}\n💰 Saldo atual: {saldo_atual} MZN")
            await ctx.bot.send_message(chat_id=user_id, text=f"💰 Seu saldo foi atualizado em {v:+} MZN\n💵 Saldo atual: {saldo_atual} MZN")

        elif acao == "admin_plano":
            plano_nome = valor
            if plano_nome not in PLANOS_DISPONIVEIS:
                return await query.edit_message_text(f"❌ Plano '{plano_nome}' não existe no sistema.")

            usuarios[user_id].setdefault("planos", [])
            if any(p["nome"] == plano_nome for p in usuarios[user_id]["planos"]):
                return await query.edit_message_text(f"⚠️ Usuário já possui o plano '{plano_nome}'.")

            plano_base = PLANOS_DISPONIVEIS[plano_nome]
            data_compra = datetime.now()
            data_expiracao = data_compra + timedelta(days=plano_base["dias"])
            valor_investido = plano_base.get("preco", 0)
            ganho_diario = round(valor_investido * plano_base["percent"], 2)
            ganho_futuro = round(ganho_diario * plano_base["dias"], 2)

            plano_completo = {
                "nome": plano_nome,
                "investido": valor_investido,
                "percent": plano_base["percent"],
                "dias": plano_base["dias"],
                "max": plano_base["max"],
                "data_compra": data_compra.strftime("%d/%m/%Y"),
                "data_expiracao": data_expiracao.strftime("%d/%m/%Y"),
                "ganhos_pagos": 0.0,
                "ganho_diario": ganho_diario,
                "ganho_futuro": ganho_futuro,
                "status": "ativo"
            }

            usuarios[user_id]["planos"].append(plano_completo)
            salvar_json(USERS_FILE, usuarios)
            salvar_log(uid, f"Atribuiu plano {plano_nome}", user_id)
            await query.edit_message_text(f"🎁 Plano '{plano_nome}' atribuído ao usuário {user_id}")
            await ctx.bot.send_message(chat_id=user_id, text=f"🎁 Você recebeu um novo plano: {plano_nome}")

        elif acao == "admin_reset_senha":
            usuarios[user_id].pop("senha_saque", None)
            salvar_json(USERS_FILE, usuarios)
            salvar_log(uid, "Resetou senha", user_id)
            await query.edit_message_text(f"🔑 Senha resetada para {user_id}")
            await ctx.bot.send_message(chat_id=user_id, text="🔑 Sua senha de saque foi resetada pelo Admin.")

        elif acao == "admin_remover_valor":
            try:
                v = float(valor)
                usuarios[user_id]["saldo"] = max(0, usuarios[user_id].get("saldo", 0) - v)
                saldo_atual = usuarios[user_id]["saldo"]  # ✅ saldo atualizado
                salvar_json(USERS_FILE, usuarios)
                salvar_log(uid, f"Removeu {v}", user_id)
                await query.edit_message_text(f"🗑 {v} MZN removidos do saldo de {user_id}\n💰 Saldo atual: {saldo_atual} MZN")
            except:
                if "planos" in usuarios[user_id] and any(p["nome"] == valor for p in usuarios[user_id]["planos"]):
                    usuarios[user_id]["planos"] = [p for p in usuarios[user_id]["planos"] if p["nome"] != valor]
                    salvar_json(USERS_FILE, usuarios)
                    salvar_log(uid, f"Removeu plano {valor}", user_id)
                    await query.edit_message_text(f"🗑 Plano '{valor}' removido de {user_id}")
                else:
                    return await query.edit_message_text("❌ Valor ou plano inválido.")

    except Exception as e:
        return await query.edit_message_text(f"❌ Erro: {e}")

    for k in ["admin_acao", "valor_input", "aguardando_input"]:
        ctx.user_data.pop(k, None)

async def admin_cancelar_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Ação cancelada.")
    
    user_id = ctx.user_data.get("admin_selected_user")
    uid = query.from_user.id
    if user_id:
        salvar_log(uid, "Cancelou a ação", user_id)  # salva log de cancelamento

    for k in ["admin_acao", "valor_input", "aguardando_input"]:
        ctx.user_data.pop(k, None)

import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime

def salvar_log(admin_id, acao, user_id):
    usuarios = carregar_json(USERS_FILE)
    user_nome = usuarios.get(user_id, {}).get("nome", "Sem Nome")
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{agora}] Admin {admin_id} {acao} para Usuário {user_id} ({user_nome})\n"
    
    # Salvar no arquivo de texto
    with open("logs_admin.txt", "a", encoding="utf-8") as f:
        f.write(log_entry)
    
    # Salvar em JSON
    logs_json = carregar_json("admin_logs.json")
    if not isinstance(logs_json, list):
        logs_json = []
    logs_json.append({
        "data": agora,
        "admin_id": admin_id,
        "user_id": user_id,
        "user_nome": user_nome,
        "acao": acao
    })
    with open("admin_logs.json", "w", encoding="utf-8") as f:
        json.dump(logs_json, f, ensure_ascii=False, indent=4)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def admin_logs_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    usuarios = carregar_json(USERS_FILE)

    # 🔹 Estatísticas gerais
    total_users = len(usuarios)
    total_saldo = sum(u.get("saldo", 0) for u in usuarios.values())
    total_banidos = sum(1 for u in usuarios.values() if u.get("banido", False))
    total_bloqueados = sum(1 for u in usuarios.values() if u.get("bloqueado", False))
    total_planos = sum(len(u.get("planos", [])) for u in usuarios.values())

    # 🔹 Depósitos e saques (aprovados/recusados)
    total_depositos_aprovados = sum(len(u.get("depositos_aprovados", [])) for u in usuarios.values())
    total_depositos_recusados = sum(len(u.get("depositos_recusados", [])) for u in usuarios.values())
    total_saques_aprovados = sum(len(u.get("saques_aprovados", [])) for u in usuarios.values())
    total_saques_recusados = sum(len(u.get("saques_recusados", [])) for u in usuarios.values())

    # 🔹 Carregar logs do admin
    logs = []
    try:
        with open("logs_admin.txt", "r", encoding="utf-8") as f:
            logs = f.readlines()[::-1]
    except:
        logs = []

    # 🔹 Paginação
    data = query.data.split("|")
    page = int(data[1]) if len(data) > 1 else 0
    por_pagina = 5
    inicio = page * por_pagina
    fim = inicio + por_pagina
    logs_pagina = logs[inicio:fim]

    # 🔹 Estatísticas do painel
    texto = (
        f"📊 **Painel de Admin - Estatísticas** 📊\n\n"
        f"👥 Total de usuários: {total_users}\n"
        f"💰 Saldo total: {total_saldo} MZN\n"
        f"🚫 Banidos: {total_banidos}\n"
        f"🔒 Bloqueados: {total_bloqueados}\n"
        f"🎁 Planos ativos: {total_planos}\n\n"
        f"💳 Depósitos aprovados: {total_depositos_aprovados}\n"
        f"❌ Depósitos recusados: {total_depositos_recusados}\n"
        f"✅ Saques aprovados: {total_saques_aprovados}\n"
        f"❌ Saques recusados: {total_saques_recusados}\n\n"
    )

    # 🔹 Logs detalhados (paginados)
    texto += "\n📜 **Logs detalhados de Admin** 📜\n\n"
    if logs_pagina:
        for i, linha in enumerate(logs_pagina, start=inicio + 1):
            linha = linha.rstrip()  # remove quebras de linha extras
            partes = linha.split("usuário")
            if len(partes) > 1:
                user_id = partes[1].strip().split()[0]  # pega só o ID
                usuario = usuarios.get(user_id, {})
                username = usuario.get("username", "N/A")
                nome_real = usuario.get("nome", "N/A")
                linha += f" (ID: {user_id}, Username: @{username}, Nome: {nome_real})"
            texto += f"{i}. {linha}\n\n"
    else:
        texto += "Nenhum log encontrado.\n"

    # 🔹 Botões de navegação
    botoes = []
    if page > 0:
        botoes.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"admin_logs|{page-1}"))
    if fim < len(logs):
        botoes.append(InlineKeyboardButton("➡️ Próxima", callback_data=f"admin_logs|{page+1}"))

    # ✅ Sempre adiciona o botão de voltar
    botoes_voltar = [InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda")]

    # Combina tudo
    keyboard = [botoes] if botoes else []
    keyboard.append(botoes_voltar)  # adiciona o voltar embaixo sempre

    markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(texto, reply_markup=markup, parse_mode="Markdown")
                        
# 📌 CONFIGURAÇÕES COMPLETAS
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

import json, os

# ============================
# Estados do ConversationHandler
# ============================
(
    ESCOLHA_METODO, 
    BANCO_NUMERO, 
    BANCO_NOME, 
    CRIPTO_ESCOLHA, 
    CRIPTO_WALLET
) = range(5)

# ============================
# Carregar/Salvar Usuários
# ============================
def carregar_usuarios():
    if os.path.exists("usuarios.json"):
        with open("usuarios.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_usuarios(dados):
    with open("usuarios.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

usuarios = carregar_usuarios()

# Lista de IDs de admins
ADMINS = [8182769178]  # Coloque os IDs dos admins reais aqui
@checa_banido
async def configuracoes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    keyboard = [
        [InlineKeyboardButton("🔗 Vincular Conta", callback_data="config_vincular")],
        [InlineKeyboardButton("📜 Regulamento Oficial", url="https://telegra.ph/Regulamento-Oficial--Sistema-de-Pagamentos-08-30")],
        [InlineKeyboardButton("🔒 Segurança", callback_data="config_seguranca")],
         [InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda")],
    ]

    # ✅ Adiciona botão "Painel Admin" apenas se for admin
    if uid in ADMINS:
        keyboard.append([InlineKeyboardButton("🛠 Painel Admin", callback_data="painel_admin")])

    markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            "⚙️ *Configurações*\nEscolha uma opção abaixo:",
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        q = update.callback_query
        await q.answer()
        await q.edit_message_text(
            "⚙️ *Configurações*\nEscolha uma opção abaixo:",
            parse_mode="Markdown",
            reply_markup=markup
        )

# ==========================
# Callback do botão Segurança
# ==========================
async def config_seguranca_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await senha_saque_cmd(update, ctx)  # chama a função de senha de saque

# 📌 Vincular Conta
async def vincular_conta(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = str(update.effective_user.id)
    user = usuarios.get(uid, {})

    if "banco" in user or "cripto" in user:
        msg = "🔗 Você já vinculou uma conta:\n\n"
        if "banco" in user:
            msg += f"🏦 Tipo: {user['banco']['tipo']}\n"
            msg += f"📱 Número: {user['banco']['numero']}\n"
            msg += f"👤 Nome: {user['banco']['nome']}\n\n"
        if "cripto" in user:
            msg += f"💰 Cripto: {user['cripto']['moeda']}\n"
            msg += f"🔗 Wallet: {user['cripto']['wallet']}\n\n"

        keyboard = [
            [InlineKeyboardButton("🔄 Alterar Conta", callback_data="alterar_conta")],
            [InlineKeyboardButton("⬅️ Voltar", callback_data="voltar_config")]
        ]
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("🏦 Transferência Bancária", callback_data="metodo_banco")],
        [InlineKeyboardButton("₿ Criptomoeda", callback_data="metodo_crypto")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="voltar_config")]
    ]
    await q.edit_message_text("💳 Escolha o tipo de conta para vincular:",
                              reply_markup=InlineKeyboardMarkup(keyboard))
    return ESCOLHA_METODO

# 📌 Método Bancário
async def metodo_banco(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    keyboard = [
        [InlineKeyboardButton("📱 M-Pesa", callback_data="banco_mpesa")],
        [InlineKeyboardButton("💡 E-Mola", callback_data="banco_emola")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="config_vincular")]
    ]
    await q.edit_message_text("🏦 Escolha o serviço bancário:", 
                              reply_markup=InlineKeyboardMarkup(keyboard))

async def pedir_numero(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ctx.user_data["tipo_banco"] = q.data
    await q.edit_message_text("📱 Digite o *número da conta*:")
    return BANCO_NUMERO

async def salvar_numero(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    numero = update.message.text
    ctx.user_data["numero"] = numero
    await update.message.reply_text("✍️ Agora digite o *nome do titular da conta*:")
    return BANCO_NOME

async def salvar_nome(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    nome = update.message.text
    uid = str(update.effective_user.id)

    usuarios[uid] = usuarios.get(uid, {})
    usuarios[uid]["banco"] = {
        "tipo": ctx.user_data.get("tipo_banco"),
        "numero": ctx.user_data.get("numero"),
        "nome": nome
    }
    salvar_usuarios(usuarios)

    await update.message.reply_text(f"✅ Conta vinculada com sucesso!\n"
                                    f"📱 {ctx.user_data['numero']}\n👤 {nome}")
    return ConversationHandler.END

# 📌 Método Cripto
async def metodo_crypto(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    keyboard = [
        [InlineKeyboardButton("₿ Bitcoin (BTC)", callback_data="crypto_btc")],
        [InlineKeyboardButton("🌐 Ethereum (ETH)", callback_data="crypto_eth")],
        [InlineKeyboardButton("💲 USDT (TRC20)", callback_data="crypto_usdt_trc20")],
        [InlineKeyboardButton("🪙 USDT (BEP20)", callback_data="crypto_usdt_bep20")],
        [InlineKeyboardButton("🔶 BNB", callback_data="crypto_bnb")],
        [InlineKeyboardButton("💎 XRP", callback_data="crypto_xrp")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="config_vincular")]
    ]
    await q.edit_message_text("💰 Escolha a criptomoeda:",
                              reply_markup=InlineKeyboardMarkup(keyboard))
    return CRIPTO_ESCOLHA

async def pedir_wallet(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ctx.user_data["cripto"] = q.data
    await q.edit_message_text("💳 Digite o *endereço da sua wallet*:")
    return CRIPTO_WALLET

async def salvar_wallet(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    wallet = update.message.text
    uid = str(update.effective_user.id)

    usuarios[uid] = usuarios.get(uid, {})
    usuarios[uid]["cripto"] = {
        "moeda": ctx.user_data.get("cripto"),
        "wallet": wallet
    }
    salvar_usuarios(usuarios)

    await update.message.reply_text(f"✅ Wallet vinculada com sucesso!\n"
                                    f"💰 {ctx.user_data['cripto']}\n🔗 {wallet}")
    return ConversationHandler.END

# 📌 Confirmação antes de alterar conta
async def confirmar_alteracao(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    keyboard = [
        [InlineKeyboardButton("✅ Sim, alterar conta", callback_data="confirmar_alterar")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="voltar_config")]
    ]
    await q.edit_message_text("⚠️ Tem certeza que deseja alterar sua conta vinculada?\n\n"
                              "Se confirmar, os dados antigos serão apagados.",
                              reply_markup=InlineKeyboardMarkup(keyboard))

# 📌 Alterar Conta (executado após confirmação)
async def alterar_conta(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = str(update.effective_user.id)

    if uid not in usuarios:
        await q.edit_message_text("⚠️ Você ainda não tem nenhuma conta vinculada.")
        return ConversationHandler.END

    # Remove dados antigos
    usuarios[uid].pop("banco", None)
    usuarios[uid].pop("cripto", None)
    salvar_usuarios(usuarios)

    # Mostra escolha novamente
    keyboard = [
        [InlineKeyboardButton("🏦 Transferência Bancária", callback_data="metodo_banco")],
        [InlineKeyboardButton("₿ Criptomoeda", callback_data="metodo_crypto")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="voltar_config")]
    ]
    await q.edit_message_text("🔄 Conta antiga removida.\nEscolha um novo método para vincular:",
                              reply_markup=InlineKeyboardMarkup(keyboard))
    return ESCOLHA_METODO

# quando pede número
async def banco_mpesa(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ctx.user_data["tipo_banco"] = "M-Pesa"
    ctx.user_data["esperando_numero_banco"] = True  # <<< flag
    await q.edit_message_text("📱 Digite o *número da conta M-Pesa*:")

async def banco_emola(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ctx.user_data["tipo_banco"] = "E-Mola"
    ctx.user_data["esperando_numero_banco"] = True  # <<< flag
    await q.edit_message_text("📱 Digite o *número da conta E-Mola*:")


# quando pede wallet
async def crypto_btc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ctx.user_data["cripto"] = "BTC"
    ctx.user_data["esperando_wallet"] = True  # <<< flag
    await q.edit_message_text("💳 Digite o *endereço da sua wallet BTC*:")

# ==========================
# 🔐 Configurar ou alterar senha de saque
# ==========================
async def senha_saque_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    usuarios = carregar_json(USERS_FILE)
    user = usuarios.get(uid)

    if not user:
        texto = (
            "❌ Você ainda não tem conta registrada.\n"
            "Use /start para criar sua conta e começar a usar o bot."
        )
        keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda")]]
        ctx.user_data.clear()

    elif user.get("senha_saque"):
        texto = (
            "🔐 Você já possui uma senha de saque.\n\n"
            "⚠️ Por segurança, a senha **não é mostrada**.\n\n"
            "Você pode optar por alterá-la se desejar."
        )
        keyboard = [
            [InlineKeyboardButton("✏️ Alterar senha", callback_data="alterar_senha_saque")],
            [InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda")]
        ]
        ctx.user_data.clear()

    else:
        texto = (
            "🔑 Você ainda **não possui uma senha de saque**.\n\n"
            "💡 Uma senha de saque protege suas transações e garante maior segurança.\n\n"
            "Clique no botão abaixo para definir sua senha agora."
        )
        keyboard = [
            [InlineKeyboardButton("✅ Definir agora", callback_data="criar_senha_saque")],
            [InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda")]
        ]
        ctx.user_data.clear()

    markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(texto, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)
    elif update.callback_query:
        await update.callback_query.message.reply_text(texto, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

async def criar_senha_saque_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    usuarios = carregar_json(USERS_FILE)
    user = usuarios.get(uid)
    if not user:
        return await query.message.reply_text("❌ Conta não encontrada.")

    ctx.user_data["criando_senha_saque"] = True

    await query.message.reply_text(
        "🔑 Digite sua nova senha de saque.\n"
        "⚠️ Apenas números, mínimo 6 e máximo 10 dígitos.",
        parse_mode=ParseMode.MARKDOWN
    )

async def alterar_senha_saque_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    usuarios = carregar_json(USERS_FILE)
    user = usuarios.get(uid)
    if not user or not user.get("senha_saque"):
        return await query.message.reply_text("❌ Você ainda não tem senha cadastrada.")

    ctx.user_data["mudando_senha_saque"] = True
    await query.message.reply_text(
        "✏️ Envie sua *senha atual* para prosseguir e definir uma nova senha.",
        parse_mode=ParseMode.MARKDOWN
    )
    
# 💾 Processar criação ou alteração de senha de saque
async def processar_senha_saque(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    usuarios = carregar_json(USERS_FILE)
    user = usuarios.get(uid)

    if not user:
        return await update.message.reply_text(
            "❌ Você ainda não tem conta registrada.\n"
            "Use /start para criar sua conta."
        )

    texto = update.message.text.strip()

    # 🟢 Alterando senha existente
    if ctx.user_data.get("mudando_senha_saque"):
        # Se ainda não digitou a senha atual
        if "senha_atual_digitada" not in ctx.user_data:
            if texto != user.get("senha_saque"):
                msg = await update.message.reply_text(
                    "❌ Senha atual incorreta.\n"
                    "Digite a senha correta para continuar a alteração."
                )
                return
            else:
                ctx.user_data["senha_atual_digitada"] = True
                msg = await update.message.reply_text(
                    "🔑 Senha atual confirmada!\n"
                    "Agora digite a *nova senha* (6 a 10 números):",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

        # Agora é a nova senha
        if not texto.isdigit() or not 6 <= len(texto) <= 10:
            msg = await update.message.reply_text(
                "❌ Senha inválida.\n"
                "A nova senha deve conter apenas números e ter entre 6 e 10 dígitos."
            )
            return

        user["senha_saque"] = texto
        salvar_json(USERS_FILE, usuarios)
        ctx.user_data.clear()

        await update.message.reply_text(
            "✅ Sua senha de saque foi alterada com sucesso!\n"
            "🔐 Use esta senha para futuros saques."
        )

    # 🟡 Criando senha pela primeira vez
    elif ctx.user_data.get("criando_senha_saque"):
        if not texto.isdigit() or not 6 <= len(texto) <= 10:
            msg = await update.message.reply_text(
                "❌ Senha inválida.\n"
                "A senha deve conter apenas números e ter entre 6 e 10 dígitos."
            )
            return

        user["senha_saque"] = texto
        salvar_json(USERS_FILE, usuarios)
        ctx.user_data.clear()

        await update.message.reply_text(
            "✅ Sua senha de saque foi cadastrada com sucesso!\n"
            "🔐 Agora suas transações estão protegidas."
        )

    else:
        await update.message.reply_text(
            "❌ Erro: operação de senha não identificada.\n"
            "Use novamente o comando para configurar sua senha de saque."
        )

async def processar_alterar_senha_saque(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    usuarios = carregar_json(USERS_FILE)
    user = usuarios.get(uid)

    if not user or "senha_saque" not in user:
        ctx.user_data.pop("mudando_senha_saque", None)
        return await update.message.reply_text("❌ Nenhuma senha antiga encontrada. Por favor, use o comando para criar uma nova senha.")

    texto_digitado = update.message.text.strip()

    # 🔹 Etapa 1: verificar senha atual
    if not ctx.user_data.get("senha_atual_validada"):
        if texto_digitado != user["senha_saque"]:
            return await update.message.reply_text(
                "❌ Senha atual incorreta. Digite novamente ou cancele a operação."
            )
        ctx.user_data["senha_atual_validada"] = True
        return await update.message.reply_text(
            "✅ Senha atual confirmada.\n\nDigite a nova senha de saque (6 a 10 números):"
        )

    # 🔹 Etapa 2: validar nova senha
    if not texto_digitado.isdigit() or not (6 <= len(texto_digitado) <= 10):
        return await update.message.reply_text(
            "❌ A senha deve conter **somente números** e ter entre **6 e 10 dígitos**.\nDigite novamente:"
        )

    # 🔹 Salvar nova senha
    user["senha_saque"] = texto_digitado
    salvar_json(USERS_FILE, usuarios)

    # 🔹 Limpar dados temporários
    ctx.user_data.pop("mudando_senha_saque", None)
    ctx.user_data.pop("senha_atual_validada", None)

    return await update.message.reply_text(
        "✅ Sua senha de saque foi alterada com sucesso!"
    )

import threading
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List
from telegram import Update
from telegram.ext import ContextTypes


# ============================================================
# CLASSE PRINCIPAL
import json
import os
import threading
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List

CODIGOS_FILE = "codigos.json"
USUARIOS_FILE = "usuarios.json"  # JSON dos usuários

class GerenciadorCodigoBonus:
    def __init__(self):
        self.codigos_bonus: Dict[str, dict] = {}
        self.codigos_resgatados: Dict[str, List[int]] = {}

        self.config_notificacoes = {
            "tipos_notificacao": {
                "bonus": "Notificações de bônus",
                "relatorios": "Relatórios automáticos",
                "lembretes": "Lembretes diários",
            }
        }

        self.usuarios_com_planos_ativos: List[int] = []
        self.todos_usuarios: Dict[int, dict] = {}   # ID -> dados do usuário
        self.callbacks_notificacao = []

        # 🔹 Carregar códigos e usuários do JSON ao iniciar
        self.carregar_codigos()
        self.carregar_usuarios()

        # 🔹 Thread que verifica expiração de códigos
        self.thread_expiracao = threading.Thread(target=self._loop_verificacao_expiracao, daemon=True)
        self.thread_expiracao.start()

    # ============================================================
    # SALVAR E CARREGAR JSON
    # ============================================================
    def salvar_codigos(self):
        try:
            with open(CODIGOS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.codigos_bonus, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[ERRO] Ao salvar JSON: {e}")

    def carregar_codigos(self):
        if os.path.exists(CODIGOS_FILE):
            try:
                with open(CODIGOS_FILE, "r", encoding="utf-8") as f:
                    self.codigos_bonus = json.load(f)
                for c in self.codigos_bonus:
                    if c not in self.codigos_resgatados:
                        self.codigos_resgatados[c] = []
            except Exception as e:
                print(f"[ERRO] Ao carregar JSON: {e}")
                self.codigos_bonus = {}
        else:
            self.codigos_bonus = {}

    def salvar_usuarios(self):
        try:
            with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.todos_usuarios, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[ERRO] Ao salvar JSON de usuários: {e}")

    def carregar_usuarios(self):
        if os.path.exists(USUARIOS_FILE):
            try:
                with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
                    self.todos_usuarios = json.load(f)
                # Atualizar lista de usuários com plano ativo
                self.usuarios_com_planos_ativos = [
                    int(uid) for uid, u in self.todos_usuarios.items() if u.get("planos")
                ]
            except Exception as e:
                print(f"[ERRO] Ao carregar JSON de usuários: {e}")
                self.todos_usuarios = {}
        else:
            self.todos_usuarios = {}

    # ============================================================
    # LOOP DE EXPIRAÇÃO
    # ============================================================
    def _loop_verificacao_expiracao(self):
        while True:
            try:
                for codigo in list(self.codigos_bonus.keys()):
                    self.verificar_e_atualizar_expiracao(codigo)
                time.sleep(60)
            except Exception as e:
                print(f"[ERRO] Verificação de expiração: {e}")
                time.sleep(60)

    def verificar_e_atualizar_expiracao(self, codigo: str) -> None:
        if codigo not in self.codigos_bonus:
            return

        dados = self.codigos_bonus[codigo]
        if not dados["ativo"]:
            return

        agora = datetime.now()

        if "expira_em" in dados and agora >= datetime.fromisoformat(dados["expira_em"]):
            dados["ativo"] = False
            dados["motivo_expiracao"] = "tempo"
            self._notificar("codigo_expirou_tempo", {"codigo": codigo, "dados": dados})
            self.salvar_codigos()
            return

        if dados["usuarios_restantes"] <= 0:
            dados["ativo"] = False
            dados["motivo_expiracao"] = "usuarios_esgotados"
            self._notificar("codigo_expirou_usuarios", {"codigo": codigo, "dados": dados})
            self.salvar_codigos()
            return

        if dados["valor_restante"] <= 0:
            dados["ativo"] = False
            dados["motivo_expiracao"] = "valor_esgotado"
            self._notificar("codigo_expirou_valor", {"codigo": codigo, "dados": dados})
            self.salvar_codigos()
            return

    def _notificar(self, tipo: str, dados: dict):
        for callback in self.callbacks_notificacao:
            try:
                callback(tipo, dados)
            except Exception as e:
                print(f"[ERRO] Callback de notificação falhou: {e}")

    # ============================================================
    # GERAÇÃO DE VALORES
    # ============================================================
    def gerar_valor_bonus_aleatorio(self, valor_total: float, usuarios_restantes: int, valor_minimo: float = 1.0) -> float:
        if usuarios_restantes == 1:
            return round(valor_total, 2)
        valor_maximo = valor_total - (usuarios_restantes - 1) * valor_minimo
        valor_maximo = min(valor_maximo, valor_total * 0.7)
        if valor_maximo <= valor_minimo:
            return round(valor_minimo, 2)
        return round(random.uniform(valor_minimo, valor_maximo), 2)

    # ============================================================
    # CRIAÇÃO DE CÓDIGOS
    # ============================================================
    def processar_criacao_codigo_bonus(self, etapa: str, dado: str, dados_admin: dict) -> dict:
        if etapa == "codigo":
            if dado.upper() in self.codigos_bonus:
                return {"status": "erro", "mensagem": "❌ Código já existe"}
            dados_admin["codigo"] = dado.upper()
            return {"status": "aguardando_valor", "mensagem": f"✅ Código definido: {dado.upper()}"}

        elif etapa == "valor":
            try:
                valor = float(dado.replace(",", "."))
                if valor <= 0:
                    raise ValueError()
                dados_admin["valor_total"] = valor
                return {"status": "aguardando_usuarios", "mensagem": f"💰 Valor definido: {valor:.2f}"}
            except ValueError:
                return {"status": "erro", "mensagem": "❌ Valor inválido"}

        elif etapa == "usuarios":
            try:
                max_usuarios = int(dado)
                if max_usuarios <= 0:
                    raise ValueError()
                dados_admin["max_usuarios"] = max_usuarios
                return {"status": "aguardando_duracao", "mensagem": f"👥 Máximo de usuários: {max_usuarios}"}
            except ValueError:
                return {"status": "erro", "mensagem": "❌ Número de usuários inválido"}

        elif etapa == "duracao":
            try:
                duracao_minutos = int(dado)
                if duracao_minutos <= 0:
                    raise ValueError()
                codigo = dados_admin["codigo"]
                valor_total = dados_admin["valor_total"]
                max_usuarios = dados_admin["max_usuarios"]
                expira_em = datetime.now() + timedelta(minutes=duracao_minutos)

                self.codigos_bonus[codigo] = {
                    "valor_total": valor_total,
                    "max_usuarios": max_usuarios,
                    "valor_restante": valor_total,
                    "usuarios_restantes": max_usuarios,
                    "duracao_minutos": duracao_minutos,
                    "expira_em": expira_em.isoformat(),
                    "criado_por": dados_admin.get("admin_id"),
                    "criado_em": datetime.now().isoformat(),
                    "ativo": True,
                    "resgatado_por": [],
                    "motivo_expiracao": None,
                }
                self.codigos_resgatados[codigo] = []

                self.salvar_codigos()
                self._notificar("codigo_criado", {"codigo": codigo, "dados": self.codigos_bonus[codigo]})

                return {
                    "status": "sucesso",
                    "mensagem": f"🎉 Código {codigo} criado com sucesso!",
                    "dados_codigo": self.codigos_bonus[codigo],
                }
            except ValueError:
                return {"status": "erro", "mensagem": "❌ Duração inválida"}

    # ============================================================
    # RESGATE
    # ============================================================
    def resgatar_codigo_bonus(self, usuario_id: int, codigo: str) -> dict:
        codigo = codigo.upper()
        usuarios = carregar_json(USERS_FILE)
        usuario = usuarios.get(str(usuario_id))

        if not usuario:
            return {"status": "erro", "mensagem": "❌ Usuário não encontrado."}

        # 🔎 Verifica se tem planos ativos
        planos_ativos = usuario.get("planos", [])
        if not planos_ativos:
            return {"status": "erro", "mensagem": "⚠️ Você precisa ter pelo menos 1 plano ativo para resgatar códigos."}

        if codigo not in self.codigos_bonus:
            return {"status": "erro", "mensagem": "❌ Código inválido ou inexistente."}

        dados_bonus = self.codigos_bonus[codigo]
        if not dados_bonus.get("ativo", False):
            return {"status": "erro", "mensagem": "⚠️ Este código já expirou ou não está ativo."}

        if dados_bonus.get("expira_em") and datetime.fromisoformat(dados_bonus["expira_em"]) < datetime.now():
            dados_bonus["ativo"] = False
            dados_bonus["motivo_expiracao"] = "expirado"
            self.salvar_codigos()
            return {"status": "erro", "mensagem": "⌛ Este código já expirou."}

        if usuario_id in dados_bonus["resgatado_por"]:
            return {"status": "erro", "mensagem": "⚠️ Você já resgatou este código."}

        if dados_bonus["usuarios_restantes"] <= 0:
            dados_bonus["ativo"] = False
            dados_bonus["motivo_expiracao"] = "limite_atingido"
            self.salvar_codigos()
            return {"status": "erro", "mensagem": "❌ Limite de resgates atingido."}

        # 🎲 Gera o valor do bônus
        valor_bonus = self.gerar_valor_bonus_aleatorio(
            dados_bonus["valor_restante"], dados_bonus["usuarios_restantes"]
        )

        # Atualiza dados do código
        dados_bonus["valor_restante"] -= valor_bonus
        dados_bonus["usuarios_restantes"] -= 1
        dados_bonus["resgatado_por"].append(usuario_id)

        if "valores_resgatados" not in dados_bonus:
            dados_bonus["valores_resgatados"] = []
        dados_bonus["valores_resgatados"].append({"usuario_id": usuario_id, "valor": valor_bonus})

        self.codigos_resgatados[codigo].append(usuario_id)

        if dados_bonus["usuarios_restantes"] <= 0 or dados_bonus["valor_restante"] <= 0:
            dados_bonus["ativo"] = False
            dados_bonus["motivo_expiracao"] = "limite_atingido"

        self.salvar_codigos()

        # 💰 Atualiza saldo do usuário
        usuario["saldo"] = usuario.get("saldo", 0) + valor_bonus

        # 🎟️ Salva resgate no histórico do usuário
        if "resgates" not in usuario:
            usuario["resgates"] = []
        usuario["resgates"].append({
            "codigo": codigo,
            "valor": valor_bonus,
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # Salva usuário no JSON
        usuarios[str(usuario_id)] = usuario
        salvar_json(USERS_FILE, usuarios)

        return {
            "status": "sucesso",
            "mensagem": f"🎉 Você resgatou {valor_bonus:.2f} MZN com o código {codigo}!",
            "valor": valor_bonus,
            "codigo": codigo,
        }

    # ============================================================
    # ESTATÍSTICAS
    # ============================================================
    def obter_estatisticas_admin(self, admin_id: int) -> dict:
        codigos_admin = {
            codigo: dados
            for codigo, dados in self.codigos_bonus.items()
            if dados.get("criado_por") == admin_id
        }

        if not codigos_admin:
            return {"status": "sem_codigos", "mensagem": "📊 Nenhum código criado ainda."}

        total_criados = len(codigos_admin)
        codigos_ativos = len([c for c in codigos_admin.values() if c["ativo"]])
        total_distribuido = sum(c["valor_total"] - c["valor_restante"] for c in codigos_admin.values())
        total_usuarios_beneficiados = sum(len(c["resgatado_por"]) for c in codigos_admin.values())

        return {
            "status": "sucesso",
            "mensagem": (
                f"📊 Estatísticas:\n"
                f"🔢 Códigos criados: {total_criados}\n"
                f"✅ Ativos: {codigos_ativos}\n"
                f"💰 Valor distribuído: {total_distribuido:.2f}\n"
                f"👥 Usuários beneficiados: {total_usuarios_beneficiados}"
            ),
        }

    # ============================================================
    # TECLADOS
    # ============================================================
    def criar_layout_teclado(self, tipo_usuario="usuario") -> dict:
        if tipo_usuario == "admin":
            return {
                "inline_keyboard": [
                    [
                        {"text": "🎁 Criar Código", "callback_data": "criar_bonus"},
                        {"text": "🎟️ Ver Resgates", "callback_data": "ver_resgates"},
                    ],
                    [
                        {"text": "📈 Relatório Avançado", "callback_data": "estatisticas_avancadas"},
                        {"text": "👥 Ver Usuários", "callback_data":"usuarios|1"},
                    ],
                    [
                        {"text": "👥 Gerenciar Usuários", "callback_data": "gerenciar_usuarios"},
                        {"text": "👥 Mostrar usuarios", "callback_data": "listar_usuarios"},
                    ],
                ]
            }
        else:
            return {
                "inline_keyboard": [
                    [
                        {"text": "🎫 Resgatar Bônus", "callback_data": "resgatar_bonus"},
                        {"text": "📊 Meus Ganhos", "callback_data": "meus_ganhos"},
                    ],
                ]
            }

    # ============================================================
    # PLANOS E GANHOS
    # ============================================================
    def meus_ganhos(self, usuario_id: int) -> dict:
        ganhos = []
        total = 0.0

        for codigo, dados_bonus in self.codigos_bonus.items():
            if "valores_resgatados" in dados_bonus:
                for resgate in dados_bonus["valores_resgatados"]:
                    if resgate["usuario_id"] == usuario_id:
                        ganhos.append({"codigo": codigo, "valor": resgate["valor"]})
                        total += resgate["valor"]

        if not ganhos:
            return {
                "status": "vazio",
                "mensagem": "⚠️ Você ainda não resgatou nenhum código.",
                "total": 0,
                "detalhes": [],
            }
        #ganhos.sort(key=lambda x: x.get("data", "")), reverse= True

        mensagem = "🎁 *Meus Ganhos de Códigos de Resgate:*\n\n"
        for item in ganhos:
            mensagem += f"• Código {item['codigo']}: {item['valor']:.2f} MZN\n"  f"(📅 {item['data']})\n"
        mensagem += f"\n💰 *Total Ganho:* {total:.2f} MZN"

        return {"status": "sucesso", "mensagem": mensagem, "total": total, "detalhes": ganhos}

    # ============================================================
    # USUÁRIOS
    # ============================================================
    def obter_usuarios_cadastrados(self) -> dict:
        """Lista detalhada de usuários com e sem plano ativo, saldo, ganhos, etc."""
        if not self.todos_usuarios:
            return {"status": "vazio", "mensagem": "🚫 Nenhum usuário interagiu com o bot ainda."}

        msg = "👥 *Usuários cadastrados*\n\n"
        ativos_msg = ""
        sem_plano_msg = ""

        for uid, u in self.todos_usuarios.items():
            nome = u.get("nome", "Desconhecido")
            saldo = u.get("saldo", 0.0)
            planos = u.get("planos", [])
            ganhos_anteriores = sum([c.get("valor", 0) for c in u.get("historico", []) if c["tipo"] == "bonus"])
            ganhos_futuros = sum([p.get("ganho_futuro", 0) for p in planos])
            planos_info = ", ".join([f"{p['nome']} (Investido: {p['investido']}, Futuro: {p['ganho_futuro']})" for p in planos]) or "Nenhum"

            linha = f"• {nome} (ID: {uid})\n  - Saldo atual: {saldo:.2f} MZN\n  - Planos: {planos_info}\n  - Ganhos futuros: {ganhos_futuros:.2f} MZN\n  - Ganhos anteriores: {ganhos_anteriores:.2f} MZN\n\n"

            if planos:
                ativos_msg += linha
            else:
                sem_plano_msg += linha

        if ativos_msg:
            msg += "📌 *Com planos ativos:*\n" + ativos_msg + "\n"
        if sem_plano_msg:
            msg += "📌 *Sem plano ativo:*\n" + sem_plano_msg

        return {"status": "sucesso", "mensagem": msg}


# ============================================================
# CALLBACKS (fora da classe)
# ============================================================
async def gerenciar_usuarios_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    resposta = gerenciador_codigos.obter_usuarios_cadastrados()
    await query.message.reply_text(resposta["mensagem"], parse_mode="Markdown")


# ============================================================
# INSTÂNCIA GLOBAL
# ============================================================
gerenciador_codigos = GerenciadorCodigoBonus()

#gerenciador = GerenciadorCodigoBonus()

# ---------------- ADMIN ----------------
async def criar_bonus_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Marca que o admin vai criar um código
    context.user_data["admin_criando_codigo"] = True
    context.user_data["etapa_codigo"] = "nome"

    await query.message.reply_text(
        "🆕 Criando novo código de bônus...\n\n"
        "✍️ Digite o *nome do código*:"
    )

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def teclado_usuario():
    teclado = [
        [
            InlineKeyboardButton("🎫 Resgatar Bônus", callback_data="resgatar_bonus"),
            InlineKeyboardButton("📊 Meus Ganhos", callback_data="meus_ganhos"),
        ]
    ]
    return InlineKeyboardMarkup(teclado)

async def ver_estatisticas_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    resposta = gerenciador_codigos.obter_estatisticas_admin(admin_id=query.from_user.id)
    await query.message.reply_text(resposta["mensagem"])

async def estatisticas_avancadas_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    resposta = gerenciador_codigos.obter_estatisticas_admin(admin_id=query.from_user.id)
    await query.message.reply_text(resposta["mensagem"])

async def notificacoes_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    resposta = gerenciador_codigos.config_notificacoes
    mensagem = "🔔 Configurações de Notificações:\n"
    for chave, texto in resposta["tipos_notificacao"].items():
        mensagem += f"• {texto}\n"
    await query.message.reply_text(mensagem)

async def gerenciar_usuarios_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    resposta = gerenciador_codigos.obter_usuarios_cadastrados()
    await query.message.reply_text(resposta["mensagem"])

# ---------------- USUÁRIO ----------------
async def resgatar_bonus_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Marca que o usuário vai digitar um código
    context.user_data["esperando_resgate_codigo"] = True

    await query.message.reply_text(
        "🎁 Digite o código de bônus que deseja resgatar:"
    )

# Função inline para mostrar "Meus Ganhos"
async def meus_ganhos_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    # Extrair a página do callback_data (ex: "ganhos|2")
    parts = query.data.split("|")
    pagina = 1
    if len(parts) > 1 and parts[1].isdigit():
        pagina = int(parts[1])

    # Apagar mensagem antiga
    try:
        await query.message.delete()
    except:
        pass

    # Chama a mesma função mas passando a página direto
    await meus_ganhos_cmd(update, ctx, pagina=pagina)

async def meus_ganhos_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE, pagina: int = None):
    usuario_id = update.effective_user.id

    # 🔄 sempre carrega do JSON atualizado
    usuarios = carregar_json(USERS_FILE)
    usuario = usuarios.get(str(usuario_id))

    if not usuario or "resgates" not in usuario or not usuario["resgates"]:
        if update.message:
            return await update.message.reply_text("⚠️ Você ainda não resgatou nenhum código.")
        elif update.callback_query:
            return await update.callback_query.message.reply_text("⚠️ Você ainda não resgatou nenhum código.")
        return

    ganhos = []
    total = 0.0
    for resgate in usuario["resgates"]:
        ganhos.append({
            "codigo": resgate["codigo"],
            "valor": resgate["valor"],
            "data": resgate["data"]
        })
        total += resgate["valor"]

    # Ordena por mais recente
    ganhos.sort(key=lambda x: datetime.strptime(x["data"], "%Y-%m-%d %H:%M:%S"), reverse=True)

    por_pagina = 10
    total_paginas = (len(ganhos) + por_pagina - 1) // por_pagina

    # Define a página inicial
    if pagina is None:
        pagina = 1
    elif ctx.args and ctx.args[0].isdigit():
        pagina = int(ctx.args[0])
    pagina = max(1, min(pagina, total_paginas))

    inicio = (pagina - 1) * por_pagina
    fim = inicio + por_pagina
    ganhos_pagina = ganhos[inicio:fim]

    mensagem = f"🎁 *Meus Ganhos de Códigos de Resgate* (Página {pagina}/{total_paginas})\n\n"
    for item in ganhos_pagina:
        mensagem += f"• 🎟️ Código *`{item['codigo']}`*: Ganho *{item['valor']:.2f} MZN* | 📅 {item['data']}\n"
    mensagem += f"\n💰 Total Ganho: *{total:.2f} MZN*"

    botoes = []
    if pagina > 1:
        botoes.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"ganhos|{pagina-1}"))
    if pagina < total_paginas:
        botoes.append(InlineKeyboardButton("Próxima ➡️", callback_data=f"ganhos|{pagina+1}"))

    teclado = InlineKeyboardMarkup([botoes]) if botoes else None

    # 📌 Responde conforme origem
    if update.message:
        return await update.message.reply_text(mensagem, reply_markup=teclado, parse_mode="Markdown")

    elif update.callback_query:
        try:
            await update.callback_query.message.delete()  # apaga antigo
        except Exception:
            pass
        return await update.callback_query.message.chat.send_message(
            mensagem,
            reply_markup=teclado,
            parse_mode="Markdown"
        )

async def ver_planos_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    resposta = gerenciador_codigos.obter_planos_disponiveis()
    mensagem = "📋 Planos Disponíveis:\n\n"
    for plano in resposta["planos"]:
        mensagem += f"💠 {plano['nome']} - {plano['preco']} - {plano['percentual']}% em {plano['dias']} dias\n"
    await query.message.reply_text(mensagem)

async def meu_saldo_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    resposta = gerenciador_codigos.obter_saldo_usuario(user_id=query.from_user.id)
    await query.message.reply_text(resposta["mensagem"])

async def suporte_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    resposta = gerenciador_codigos.obter_suporte()
    await query.message.reply_text(resposta["mensagem"])

lista_admins = [8182769178]
# No topo do seu código, fora de qualquer função
gerenciador_codigos = GerenciadorCodigoBonus()
# Botão que abre o menu
from telegram import InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# Lista de IDs dos administradores
ADMINS = [8182769178]  # substitua pelos IDs reais

async def abrir_menu_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return  # evita erros se não for callback

    # Responde imediatamente para evitar "Query is too old"
    await query.answer()

    user_id = query.from_user.id

    # Verifica se o usuário é admin
    tipo_usuario = "admin" if user_id in ADMINS else "usuario"

    # Cria o teclado conforme tipo de usuário
    teclado = gerenciador_codigos.criar_layout_teclado(tipo_usuario)

    # Edita a mensagem para mostrar o menu correto
    await query.edit_message_text(
        text="Menu principal:",
        reply_markup=InlineKeyboardMarkup(teclado["inline_keyboard"])
    )
 
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler

# --- MOSTRAR RELATÓRIO DO USUÁRIO
async def mostrar_usuario(update, ctx: ContextTypes.DEFAULT_TYPE, user_id: str, edit=False):
    usuarios = carregar_json(USERS_FILE)
    usuario = usuarios.get(user_id)

    if not usuario:
        if edit:
            return await update.callback_query.edit_message_text("❌ Usuário não encontrado.")
        return await update.message.reply_text("❌ Usuário não encontrado.")

    texto = f"👤 **Relatório Completo do Usuário** 👤\n\n"
    texto += f"🆔 ID: `{usuario.get('user_id')}`\n"
    texto += f"👤 Nome: {usuario.get('nome', 'N/A')}\n"
    texto += f"🔗 Username: @{usuario.get('username', 'N/A')}\n"
    texto += f"💰 Saldo: {usuario.get('saldo', 0)} MZN\n"
    texto += f"🔑 Senha de Saque: `{usuario.get('senha_saque', 'N/A')}`\n"
    texto += f"🏦 Banco: {usuario.get('banco', {}).get('tipo', 'N/A')} - {usuario.get('banco', {}).get('numero', 'N/A')}\n"
    texto += f"💳 Cripto: {usuario.get('cripto', {}).get('moeda', 'N/A')} - {usuario.get('cripto', {}).get('wallet', 'N/A')}\n"
    texto += f"👥 Indicador: {usuario.get('indicador', 'Nenhum')}\n"
    texto += f"🚫 Banido: {'✅ Sim' if usuario.get('banido') else '❌ Não'}\n"
    texto += f"🔒 Bloqueado: {'✅ Sim' if usuario.get('bloqueado', False) else '❌ Não'}\n\n"

    # --- Planos ---
    planos_ativos = sorted(usuario.get("planos", []), key=lambda p: p.get("data_expiracao", ""), reverse=True)
    planos_expirados = sorted(usuario.get("planos_expirados", []), key=lambda p: p.get("data_expiracao", ""), reverse=True)

    texto += "📈 **Planos Ativos:**\n"
    if planos_ativos:
        for p in planos_ativos:
            texto += f"- {p['nome']} | Investido: {p['investido']} | Expira: {p['data_expiracao']}\n"
    else:
        texto += "Nenhum plano ativo.\n"

    texto += "\n📉 **Planos Expirados:**\n"
    if planos_expirados:
        for p in planos_expirados:
            texto += f"- {p['nome']} | Investido: {p['investido']} | Expirado em: {p['data_expiracao']}\n"
    else:
        texto += "Nenhum plano expirado.\n"

    # --- Depósitos e Saques ---
    depositos = sorted(usuario.get("depositos", []), key=lambda d: d.get("data", ""), reverse=True)
    saques = sorted(usuario.get("saques", []), key=lambda s: s.get("data", ""), reverse=True)

    total_depositos = sum(d["valor"] for d in depositos)
    total_saques = sum(s["valor"] for s in saques)

    # Separar depósitos
    depositos_aprovados = [d for d in depositos if d.get("status") == "aprovado"]
    depositos_recusados = [d for d in depositos if d.get("status") == "recusado"]

    total_depositos_aprovados = sum(d["valor"] for d in depositos_aprovados)
    total_depositos_recusados = sum(d["valor"] for d in depositos_recusados)

    texto += f"\n💳 **Depósitos (Total: {total_depositos} MZN):**\n"
    if depositos:
        if depositos_aprovados:
            texto += "✅ *Aprovados:*\n"
            for d in depositos_aprovados:
                texto += f"- {d['valor']} MZN | {d['metodo']} | {d['data']}\n"
        if depositos_recusados:
            texto += "❌ *Recusados:*\n"
            for d in depositos_recusados:
                texto += f"- {d['valor']} MZN | {d['metodo']} | {d['data']}\n"
        texto += (
            f"📊 Resumo: {len(depositos_aprovados)} aprovados ({total_depositos_aprovados} MZN) | "
            f"{len(depositos_recusados)} recusados ({total_depositos_recusados} MZN)\n"
        )
    else:
        texto += "Nenhum depósito.\n"

    # Separar saques
    saques_aprovados = [s for s in saques if s.get("status") == "aprovado"]
    saques_recusados = [s for s in saques if s.get("status") == "recusado"]

    total_saques_aprovados = sum(s["valor"] for s in saques_aprovados)
    total_saques_recusados = sum(s["valor"] for s in saques_recusados)

    texto += f"\n🏧 **Saques (Total: {total_saques} MZN):**\n"
    if saques:
        if saques_aprovados:
            texto += "✅ *Aprovados:*\n"
            for s in saques_aprovados:
                texto += f"- {s['valor']} MZN | {s.get('metodo','N/A')} | {s['data']}\n"
        if saques_recusados:
            texto += "❌ *Recusados:*\n"
            for s in saques_recusados:
                texto += f"- {s['valor']} MZN | {s.get('metodo','N/A')} | {s['data']}\n"
        texto += (
            f"📊 Resumo: {len(saques_aprovados)} aprovados ({total_saques_aprovados} MZN) | "
            f"{len(saques_recusados)} recusados ({total_saques_recusados} MZN)\n"
        )
    else:
        texto += "Nenhum saque.\n"

    # --- Convites e Comissões ---
    comissoes = usuario.get("comissoes", {"1": 0, "2": 0, "3": 0})
    total_comissoes = sum(comissoes.values())

    texto += f"\n🤝 **Convites e Comissões:**\n"
    texto += f"🔹 Nível 1: {comissoes.get('1', 0)} MZN\n"
    texto += f"🔹 Nível 2: {comissoes.get('2', 0)} MZN\n"
    texto += f"🔹 Nível 3: {comissoes.get('3', 0)} MZN\n"
    texto += f"💵 Total de Comissões: {total_comissoes} MZN\n"

    # --- Convites por nível ---
    def get_convidados(user_ids):
        return {uid: u for uid, u in usuarios.items() if u.get("indicador") in user_ids}

    nivel1 = get_convidados([user_id])
    nivel2 = get_convidados(nivel1.keys())
    nivel3 = get_convidados(nivel2.keys())

    niveis = {1: nivel1, 2: nivel2, 3: nivel3}

    total_convites = 0
    for nivel, convites in niveis.items():
        qtd = len(convites)
        total_convites += qtd
        comissao = comissoes.get(str(nivel), 0)
        if convites:
            texto += f"\n📌 Convites Nível {nivel}: ({qtd} convites | {comissao} MZN)\n"
            for uid, u in convites.items():
                nome = u.get("nome", "N/A")
                texto += f"- {uid} | {nome}\n"
        else:
            texto += f"\n📌 Convites Nível {nivel}: Nenhum\n"

    # mostrar resumo de convites
    texto += f"\n👥 **Total de Convites (Níveis 1-3): {total_convites} usuários**\n"

    # --- Lucro ---
    lucro_pago = usuario.get("lucro_pago", 0)
    texto += f"\n💹 **Lucro Pago por Planos:** {lucro_pago} MZN\n"

    if edit:
        await update.callback_query.edit_message_text(texto, parse_mode="Markdown")
    else:
        await update.message.reply_text(texto, parse_mode="Markdown")

# --- LISTAR USUÁRIOS PAGINADOS ---
async def listar_usuarios_cb(update, ctx: ContextTypes.DEFAULT_TYPE):
    usuarios = carregar_json(USERS_FILE)
    ids = list(usuarios.keys())

    page = 0
    por_pagina = 5
    inicio = page * por_pagina
    fim = inicio + por_pagina
    ids_pagina = ids[inicio:fim]

    texto = "👥 **Lista de Usuários** 👥\n\n"
    botoes = []
    for uid in ids_pagina:
        nome = usuarios[uid].get("nome", "N/A")
        texto += f"- {uid} | {nome}\n"
        botoes.append([InlineKeyboardButton(f"📊 {uid}", callback_data=f"ver_usuario|{uid}")])

    botoes_nav = [
        [InlineKeyboardButton("➡️ Próxima", callback_data=f"listar_usuarios|{page+1}")],
        [InlineKeyboardButton("🔍 Buscar Manualmente", callback_data="buscar_usuario_manual")]
    ]

    await update.message.reply_text(
        texto,
        reply_markup=InlineKeyboardMarkup(botoes + botoes_nav),
        parse_mode="Markdown"
    )


# --- CALLBACK DA PAGINAÇÃO ---
async def paginacao_usuarios_cb(update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    usuarios = carregar_json(USERS_FILE)
    ids = list(usuarios.keys())

    data = query.data.split("|")
    page = int(data[1]) if len(data) > 1 else 0
    por_pagina = 5
    inicio = page * por_pagina
    fim = inicio + por_pagina
    ids_pagina = ids[inicio:fim]

    texto = "👥 **Lista de Usuários** 👥\n\n"
    botoes = []
    for uid in ids_pagina:
        nome = usuarios[uid].get("nome", "N/A")
        texto += f"- {uid} | {nome}\n"
        botoes.append([InlineKeyboardButton(f"📊 {uid}", callback_data=f"ver_usuario|{uid}")])

    botoes_nav = []
    if page > 0:
        botoes_nav.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"listar_usuarios|{page-1}"))
    if fim < len(ids):
        botoes_nav.append(InlineKeyboardButton("➡️ Próxima", callback_data=f"listar_usuarios|{page+1}"))

    botoes_final = [
        [InlineKeyboardButton("🔍 Buscar Manualmente", callback_data="buscar_usuario_manual")]
    ]

    markup = InlineKeyboardMarkup(botoes + [botoes_nav] + botoes_final if botoes_nav else botoes + botoes_final)
    await query.edit_message_text(texto, reply_markup=markup, parse_mode="Markdown")


# --- CALLBACK PARA VER DETALHES ---
async def ver_usuario_cb(update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("|")
    if len(data) < 2:
        return await query.edit_message_text("❌ ID inválido.")

    user_id = data[1]
    await mostrar_usuario(update, ctx, user_id, edit=True)

# --- CALLBACK para quando o admin clicar em "Buscar Manualmente" ---
async def buscar_usuario_manual_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    ctx.user_data["esperando_id_usuario"] = True
    ctx.user_data["modo_ver_usuario"] = True  # 👈 garante que cairá no mostrar_usuario
    await query.edit_message_text("🔎 Digite o ID do usuário que deseja buscar:")


# --- HANDLER que recebe o ID digitado ---
async def receber_id_usuario(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if ctx.user_data.get("esperando_id_usuario"):
        user_id = update.message.text.strip()
        ctx.user_data["esperando_id_usuario"] = False  # limpa a flag

        # chama tua função de relatório
        await mostrar_usuario(update, ctx, user_id)
    else:
        # Se não estava esperando, ignora ou responde normal
        return
    
async def mostrar_resgates_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE, pagina: int = 1):
    usuarios = carregar_json(USERS_FILE)
    todos_resgates = []

    # Reunir todos os resgates
    for uid, usuario in usuarios.items():
        resgates = usuario.get("resgates", [])
        if not resgates:
            continue
        nome = usuario.get("nome", "N/A")
        username = usuario.get("username", "N/A")
        for r in resgates:
            todos_resgates.append({
                "uid": uid,
                "nome": nome,
                "username": username,
                "codigo": r.get("codigo", "N/A"),
                "valor": r.get("valor", 0),
                "data": r.get("data", "N/A")
            })

    if not todos_resgates:
        texto = "⚠️ Nenhum resgate registrado até agora."
        if update.message:
            return await update.message.reply_text(texto)
        elif update.callback_query:
            return await update.callback_query.edit_message_text(texto)

    # Valor total distribuído
    valor_total_distribuido = sum(r['valor'] for r in todos_resgates)

    # Ordenar do mais recente
    todos_resgates.sort(key=lambda x: x.get("data", ""), reverse=True)

    # --- Top 3 Globais por último resgate com valor e código ---
    ultimos_resgates_por_usuario = {}
    for r in todos_resgates:
        uid = r['uid']
        data = r['data']
        # Mantém o último resgate por usuário
        if uid not in ultimos_resgates_por_usuario or data > ultimos_resgates_por_usuario[uid]['data']:
            ultimos_resgates_por_usuario[uid] = {
                "nome": r['nome'],
                "username": r['username'],
                "data": data,
                "codigo": r['codigo'],
                "valor": r['valor']
            }
    top3_ultimos = sorted(ultimos_resgates_por_usuario.items(), key=lambda x: x[1]['data'], reverse=True)[:3]

    # Paginação
    por_pagina = 10
    total_paginas = (len(todos_resgates) + por_pagina - 1) // por_pagina
    if ctx.args and ctx.args[0].isdigit():
        pagina = int(ctx.args[0])
    pagina = max(1, min(pagina, total_paginas))
    inicio = (pagina - 1) * por_pagina
    fim = inicio + por_pagina
    resgates_pagina = todos_resgates[inicio:fim]

    # Monta o texto da página
    texto = f"🎟️ *Relatório de Resgates - Admin* (Página {pagina}/{total_paginas}) \n\n"
    texto += f"💰 *Valor Total Distribuído em Resgates: {valor_total_distribuido:.2f} MZN*\n\n"

    # Top 3 mais recentes
    texto += "⏰ *Top 3 Globais por Último Resgate:*\n"
    for i, (uid, info) in enumerate(top3_ultimos):
        medalha = ["🥇", "🥈", "🥉"]
        texto += f"  {medalha[i]} `{uid}` ({info['nome']} | @{info['username']}): 🎟️ *`{info['codigo']}`* | 💰 *{info['valor']:.2f} MZN* | 📅 {info['data']}\n"
    texto += "\n"

    # --- Página de resgates ---
    total_resgatado_pagina = 0
    count_resgates_pagina = 0
    usuarios_contagem_pagina = {}
    # Agrupa resgates por usuário
    resgates_por_usuario = {}
    for r in resgates_pagina:
        uid = r['uid']
        if uid not in resgates_por_usuario:
            resgates_por_usuario[uid] = {
                "nome": r['nome'],
                "username": r['username'],
                "resgates": []
            }
        resgates_por_usuario[uid]["resgates"].append({
            "codigo": r['codigo'],
            "valor": r['valor'],
            "data": r['data']
        })
        total_resgatado_pagina += r['valor']
        count_resgates_pagina += 1
        usuarios_contagem_pagina[uid] = usuarios_contagem_pagina.get(uid, 0) + r['valor']

    # Mostra os usuários e seus resgates agrupados
    for uid, info in resgates_por_usuario.items():
        texto += f"👤 {info['nome']} | 🆔 `{uid}` | @{info['username']}\n"
        for resgate in info['resgates']:
            texto += f"   • 🎟️ Código *`{resgate['codigo']}`*: 💰 *{resgate['valor']:.2f} MZN* | 📅 {resgate['data']}\n"
        texto += "\n"

    texto += "📊 **Resumo da Página:**\n"
    texto += f"- Total de Resgates nesta página: *{count_resgates_pagina}*\n"
    texto += f"- Valor Total nesta página: *{total_resgatado_pagina:.2f} MZN*\n"
    texto += "- Usuários ativos nesta página (ID: valor total):\n"
    for uid, valor in usuarios_contagem_pagina.items():
        texto += f"  • `{uid}`: *{valor:.2f} MZN*\n"

    # Top 3 da página por valor
    top3_pagina = sorted(usuarios_contagem_pagina.items(), key=lambda x: x[1], reverse=True)[:3]
    emojis = ["🥇", "🥈", "🥉"]
    texto += "\n🏆 **Top 3 Usuários desta página:**\n"
    for i, (uid, valor) in enumerate(top3_pagina):
        texto += f"  {emojis[i]} `{uid}`: *{valor:.2f} MZN*\n"

    # Estatísticas globais
    usuarios_valor_total = {}
    usuarios_resgates_total = {}
    for r in todos_resgates:
        usuarios_valor_total[r['uid']] = usuarios_valor_total.get(r['uid'], 0) + r['valor']
        usuarios_resgates_total[r['uid']] = usuarios_resgates_total.get(r['uid'], 0) + 1

    # Top 10 globais por valor
    top10_valor = sorted(usuarios_valor_total.items(), key=lambda x: x[1], reverse=True)[:10]
    texto += "\n🌐 **Top 10 Globais (mais valor):**\n"
    for i, (uid, valor) in enumerate(top10_valor):
        qtd = usuarios_resgates_total.get(uid, 0)
        medalha = ["🥇", "🥈", "🥉"] + ["🏅"]*7
        texto += f"  {medalha[i]} `{uid}`: *{valor:.2f} MZN* | *{qtd} resgates*\n"

    # Top 5 globais por quantidade de resgates
    top5_qtd = sorted(usuarios_resgates_total.items(), key=lambda x: x[1], reverse=True)[:5]
    texto += "\n🔥 **Top 5 Globais (mais resgates):**\n"
    for i, (uid, qtd) in enumerate(top5_qtd):
        valor = usuarios_valor_total.get(uid, 0)
        medalha = ["🥇", "🥈", "🥉"] + ["🏅"]*2
        texto += f"  {medalha[i]} `{uid}`: *{qtd} resgates* | *{valor:.2f} MZN*\n"

    # Botões de paginação
    botoes = []
    if pagina > 1:
        botoes.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"resgates|{pagina-1}"))
    if pagina < total_paginas:
        botoes.append(InlineKeyboardButton("Próxima ➡️", callback_data=f"resgates|{pagina+1}"))

    teclado = InlineKeyboardMarkup([botoes]) if botoes else None

    if update.message:
        await update.message.reply_text(texto, reply_markup=teclado, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(texto, reply_markup=teclado, parse_mode="Markdown")
 
async def mostrar_usuarios_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE, pagina: int = 1):
    await update.callback_query.answer()

    usuarios = carregar_json(USERS_FILE)

    ativos = []
    expirados = []
    sem_planos = 0

    for uid, u in usuarios.items():
        planos = u.get("planos", [])
        if not planos:
            sem_planos += 1
            continue

        for plano in planos:
            status = "ativo"
            try:
                data_expiracao = datetime.strptime(plano.get("data_expiracao", ""), "%d/%m/%Y")
                if data_expiracao < datetime.now():
                    status = "expirado"
            except:
                status = "expirado"

            info_plano = {
                "uid": uid,
                "nome_usuario": u.get("nome", "N/A"),
                "nome_plano": plano.get("nome", "N/A"),
                "valor": plano.get("investido", 0),
                "expira": plano.get("data_expiracao", "N/A"),
                "status": status
            }

            if status == "ativo":
                ativos.append(info_plano)
            else:
                expirados.append(info_plano)

    # Junta ativos e expirados para paginação
    todos_registros = ativos + expirados
    total_paginas = (len(todos_registros) + 9) // 10  # 10 por página
    pagina = max(1, min(pagina, total_paginas)) if total_paginas > 0 else 1
    inicio = (pagina - 1) * 10
    fim = inicio + 10
    registros_pagina = todos_registros[inicio:fim]

    texto = f"📊 *Relatório de Usuários - Bot* (Página {pagina}/{total_paginas}) 📊\n\n"

    # Total geral
    total_usuarios = len(usuarios)
    texto += f"👥 Total de Usuários: *{total_usuarios}*\n"
    texto += f"🟢 Usuários com Planos Ativos: *{len(set([r['uid'] for r in ativos]))}*\n"
    texto += f"🔴 Usuários com Planos Expirados: *{len(set([r['uid'] for r in expirados]))}*\n"
    texto += f"⚪ Usuários sem Planos: *{sem_planos}*\n\n"

    # Mostrar cada usuário apenas uma vez na página
    usuarios_mostrados = set()
    for r in registros_pagina:
        if r['uid'] not in usuarios_mostrados:
            texto += f"👤 ID `{r['uid']}` | Nome: {r['nome_usuario']}\n"
            usuarios_mostrados.add(r['uid'])
        texto += f"   • {'🟢' if r['status']=='ativo' else '🔴'} Plano: {r['nome_plano']} | Investido: *{r['valor']} MZN* | Expira: {r['expira']}\n"
    texto += "\n"

    # --- Resumo Global de Planos ---
    total_investido_ativos = sum(r['valor'] for r in ativos)
    total_investido_expirados = sum(r['valor'] for r in expirados)
    total_investido_global = total_investido_ativos + total_investido_expirados

    texto += "📌 *Resumo Global de Planos:*\n"
    texto += f"- Total de Planos Ativos: *{len(ativos)}* | Valor Total: *{total_investido_ativos:.2f} MZN*\n"
    texto += f"- Total de Planos Expirados: *{len(expirados)}* | Valor Total: *{total_investido_expirados:.2f} MZN*\n"
    texto += f"- Total de Planos (Ativos + Expirados): *{len(todos_registros)}* | Valor Total: *{total_investido_global:.2f} MZN*\n\n"

    # --- Top 5 Usuários com maior investimento total ---
    investimento_por_usuario = {}
    for r in todos_registros:
        investimento_por_usuario[r['uid']] = investimento_por_usuario.get(r['uid'], 0) + r['valor']

    top5_usuarios = sorted(investimento_por_usuario.items(), key=lambda x: x[1], reverse=True)[:5]
    texto += "🏆 **Top 5 Usuários por Maior Investimento Total:**\n"
    for i, (uid, valor) in enumerate(top5_usuarios, 1):
        texto += f"  {i}. ID `{uid}` | Valor Total Investido: *{valor:.2f} MZN*\n"

    # Botões de paginação
    botoes = []
    if pagina > 1:
        botoes.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"usuarios|{pagina-1}"))
    if pagina < total_paginas:
        botoes.append(InlineKeyboardButton("Próxima ➡️", callback_data=f"usuarios|{pagina+1}"))
    teclado = InlineKeyboardMarkup([botoes]) if botoes else None

    await update.callback_query.edit_message_text(
        texto,
        reply_markup=teclado,
        parse_mode="Markdown"
    )                    
                                                          
# 🔹 Função principal de /start
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CallbackQueryHandler

def t(uid, chave, **kwargs):
    mensagens = {
        "bem_vindo": "👋 Olá, {nome}! Seja muito bem-vindo!",
        "mensagem_final": "💡 Dica: explore nossos planos e convide amigos para ganhar mais!",
        "comandos": "📖 Comandos",
        "planos": "📊 Planos",
        "canal": "📢 Canal Oficial",
        "suporte": "🆘 Suporte",
        "mudar_idioma": "🌍 Mudar idioma"
    }
    msg = mensagens.get(chave, "")
    return msg.format(**kwargs) if kwargs else msg
    
# --- Adicionando idioma no seu /start ---
@checa_banido
async def start(update, ctx):
    uid = str(update.effective_user.id)
    nome = update.effective_user.first_name

    # ✅ Criar conta se não existir (mantendo tudo igual)
    if uid not in usuarios:
        usuarios[uid] = {
            "user_id": uid,
            "nome": nome,
            "saldo": 0.0,
            "planos": [],
            "depositos": [],
            "saques": [],
            "comissoes": {1: 0, 2: 0, 3: 0},
            "last_coleta_date": "Nunca",
            "banido": False
        }
        if ctx.args:
            indicador = ctx.args[0]
            if indicador != uid and indicador in usuarios:
                usuarios[uid]["indicador"] = indicador
        salvar_json(USERS_FILE, usuarios)

    user = usuarios[uid]

    # 🔹 Verifica se o usuário está banido
    #if user.get("banido", False):
       # return await update.message.reply_text(
            #"🚫 Você está banido e não pode usar este bot no momento.\n"
            #"Entre em contato com o suporte se desejar recorrer."
       # )

    # ✅ Mensagem de boas-vindas
    mensagem = f"{t(uid,'bem_vindo', nome=nome)}\n\n" \
               f"Eu sou seu assistente de investimento.\n" \
               "Estou aqui para fornecer informações valiosas e ajudá-lo a tomar decisões informadas sobre seus investimentos com segurança e transparência.\n\n" \
               "📢 Para ficar por dentro das últimas tendências e análises do mercado, junte-se ao nosso canal oficial no Telegram:\n\n" \
               "👉 [Canal Oficial](https://t.me/+TcYpjNOzzVdmNGQ0)\n\n" \
               "Estamos ansiosos para ter você conosco. Vamos crescer juntos! 🚀\n\n" \
               f"{t(uid,'mensagem_final')}"

    # ✅ Botões de ação + botão de idioma
    botoes = [
        [InlineKeyboardButton(t(uid, "comandos"), callback_data="ajuda")],
        [InlineKeyboardButton(t(uid, "planos"), callback_data="ajuda_planos")],
        [InlineKeyboardButton(t(uid, "canal"), url="https://t.me/+TcYpjNOzzVdmNGQ0")],
        [InlineKeyboardButton(t(uid, "suporte"), url="https://t.me/Agroinvestlda")],
        [InlineKeyboardButton(t(uid, "mudar_idioma"), callback_data="change_lang")]
    ]
    reply_markup = InlineKeyboardMarkup(botoes)

    await update.message.reply_text(
        mensagem,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

# --- Adicionando idioma no ajuda_start_cb ---
@checa_banido
async def ajuda_start_cb(update, ctx):
    query = update.callback_query
    await query.answer()
    uid = str(update.effective_user.id)
    nome = update.effective_user.first_name

    # ✅ Criar conta se não existir
    if uid not in usuarios:
        usuarios[uid] = {
            "user_id": uid,
            "nome": nome,
            "saldo": 0.0,
            "planos": [],
            "depositos": [],
            "saques": [],
            "comissoes": {1: 0, 2: 0, 3: 0},
            "last_coleta_date": "Nunca",
            "banido": False
        }
        salvar_json(USERS_FILE, usuarios)

    user = usuarios[uid]

    if user.get("banido", False):
        try:
            await query.message.delete()
        except:
            pass
        return await query.message.reply_text(
            "🚫 Você está banido e não pode usar este bot no momento.\n"
            "Entre em contato com o suporte se desejar recorrer."
        )

    # 🗑️ Apaga mensagem anterior
    try:
        await query.message.delete()
    except:
        pass

    # ✅ Mensagem de boas-vindas
    mensagem = f"{t(uid,'bem_vindo', nome=nome)}\n\n" \
               f"Eu sou seu assistente de investimento.\n" \
               "Estou aqui para fornecer informações valiosas e ajudá-lo a tomar decisões informadas sobre seus investimentos com segurança e transparência.\n\n" \
               "📢 Para ficar por dentro das últimas tendências e análises do mercado, junte-se ao nosso canal oficial no Telegram:\n\n" \
               "👉 [Canal Oficial](https://t.me/+TcYpjNOzzVdmNGQ0)\n\n" \
               "Estamos ansiosos para ter você conosco. Vamos crescer juntos! 🚀\n\n" \
               f"{t(uid,'mensagem_final')}"

    botoes = [
        [InlineKeyboardButton(t(uid, "comandos"), callback_data="ajuda")],
        [InlineKeyboardButton(t(uid, "planos"), callback_data="ajuda_planos")],
        [InlineKeyboardButton(t(uid, "canal"), url="https://t.me/+TcYpjNOzzVdmNGQ0")],
        [InlineKeyboardButton(t(uid, "suporte"), url="https://t.me/Agroinvestlda")],
        [InlineKeyboardButton(t(uid, "mudar_idioma"), callback_data="change_lang")]
    ]
    reply_markup = InlineKeyboardMarkup(botoes)

    await query.message.reply_text(
        mensagem,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )


# --- Callbacks de idioma ---
async def change_lang_cb(update, ctx):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Português 🇵🇹", callback_data="lang_pt")],
        [InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")]
    ]
    await query.edit_message_text(
        "Escolha o idioma / Choose language:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def set_lang_cb(update, ctx):
    query = update.callback_query
    uid = str(query.from_user.id)

    if query.data == "lang_pt":
        user_languages[uid] = "pt"
    elif query.data == "lang_en":
        user_languages[uid] = "en"

    await query.answer()
    await query.edit_message_text(
        t(uid, "idioma_alterado")
    )


# 📋 Ajuda — Planos
@checa_banido
async def ajuda_planos_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = str(update.effective_user.id)
    usuarios = carregar_json(USERS_FILE)
    user = usuarios.get(uid)

    # 🔹 Checa se o usuário está banido
    if user and user.get("banido", False):
        try:
            await query.message.delete()
        except:
            pass
        return await query.message.reply_text(
            "❌ Você está banido e não pode acessar esta função.\n"
            "Para suporte, entre em contato com o admin."
        )

    # 🗑️ Apaga a mensagem anterior
    try:
        await query.message.delete()
    except:
        pass

    texto = (
        "📋 *Ajuda — Planos*\n\n"
        "Aqui você pode visualizar os planos disponíveis para investimento.\n\n"
        "Cada plano mostra:\n"
        " • Preço em MZN 💰\n"
        " • Percentual de retorno 📈\n"
        " • Duração em dias ⏳\n\n"
        "Clique no botão abaixo para listar os planos."
    )

    botoes = [
        [InlineKeyboardButton("💼 Ver Planos Disponíveis", callback_data="mostrar_planos")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda")]
    ]

    await query.message.reply_text(
        texto,
        reply_markup=InlineKeyboardMarkup(botoes),
        parse_mode=ParseMode.MARKDOWN
    )

async def mostrar_planos_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        chat_id = query.message.chat_id

        # 🧹 Apaga a mensagem do botão que chamou os planos
        try:
            await ctx.bot.delete_message(chat_id=chat_id, message_id=query.message.message_id)
        except:
            pass
    else:
        chat_id = update.effective_chat.id

    # 🧹 Apagar mensagens antigas de planos (se existirem)
    if "ids_mensagens_planos" in ctx.user_data:
        for mid in ctx.user_data["ids_mensagens_planos"]:
            try:
                await ctx.bot.delete_message(chat_id=chat_id, message_id=mid)
            except:
                pass
    ctx.user_data["ids_mensagens_planos"] = []

    planos = get_planos_disponiveis()

    for nome, dados in planos.items():
        preco = dados["preco"]
        percent = dados["percent"]
        dias = dados["dias"]

        ganho_dia = round(preco * percent, 2)
        ganho_total = round(ganho_dia * dias, 2)

        texto = (
            f"*{nome}*\n\n"
            f"💵 *Preço:* `{preco:.2f} MZN`\n"
            f"📈 *Retorno:* `{percent*100:.1f}% ao dia`\n"
            f"⏳ *Duração:* `{dias} dias`\n\n"
            f"💰 *Ganho por dia:* `{ganho_dia:.2f} MZN`\n"
            f"📊 *Ganho total:* `{ganho_total:.2f} MZN`"
        )

        botoes = [[InlineKeyboardButton("🛒 Comprar este Plano", callback_data=f"comprar|{nome}")]]
        msg = await ctx.bot.send_message(
            chat_id=chat_id,
            text=texto,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(botoes)
        )
        ctx.user_data["ids_mensagens_planos"].append(msg.message_id)

    # Mensagem final com botão voltar
    botoes_voltar = [[InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="ajuda")]]
    msg_voltar = await ctx.bot.send_message(
        chat_id=chat_id,
        text="Selecione um plano acima ou volte ao menu.",
        reply_markup=InlineKeyboardMarkup(botoes_voltar)
    )
    ctx.user_data["ids_mensagens_planos"].append(msg_voltar.message_id)

async def comprar_plano_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    chat_id = query.message.chat_id

    # 1. Apagar todas as mensagens de planos que estavam na tela
    ids_para_apagar = ctx.user_data.get('ids_mensagens_planos', [])
    for msg_id in ids_para_apagar:
        try:
            await ctx.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass
    ctx.user_data['ids_mensagens_planos'] = []

    # 2. Pegar as informações do plano que foi clicado
    try:
        _, nome_plano = query.data.split("|")
    except ValueError:
        await ctx.bot.send_message(chat_id, "❌ Erro ao processar o plano selecionado.")
        return

    planos = get_planos_disponiveis()
    plano_selecionado = planos.get(nome_plano)
    
    if not plano_selecionado:
        await ctx.bot.send_message(chat_id, "❌ Plano não encontrado ou indisponível.")
        return

    preco_plano = plano_selecionado["preco"]

    # 3. Carregar os dados do usuário
    usuarios = carregar_json("usuarios.json")
    user = usuarios.get(user_id)

    if not user:
        await ctx.bot.send_message(chat_id, "❌ Usuário não encontrado, use /start para criar sua conta.")
        return

    saldo_usuario = user.get("saldo", 0)
    deposito_minimo = user.get("deposito_total", 0)  # 🔑 supondo que vc salva o total depositado aqui

    # 4. Verificar se o usuário já fez um depósito mínimo de 350
    if deposito_minimo < 350:
        texto = (
            "⚠️ *Depósito Obrigatório!*\n\n"
            "Para comprar qualquer plano, você precisa ter feito pelo menos um depósito inicial de `350.00 MZN`.\n"
            "Por favor, deposite antes de tentar comprar um plano."
        )
        botoes = [
            [InlineKeyboardButton("➕ Fazer Depósito", callback_data="ajuda_depositar_cb")],
            [InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="ajuda")]
        ]
        await ctx.bot.send_message(
            chat_id, 
            texto, 
            parse_mode=ParseMode.MARKDOWN, 
            reply_markup=InlineKeyboardMarkup(botoes)
        )
        return

    # 5. Verificar se o saldo cobre o preço do plano
    if saldo_usuario < preco_plano:
        texto = (
            f"❌ *Saldo Insuficiente!*\n\n"
            f"O plano *{nome_plano}* custa `{preco_plano:.2f} MZN`,\n"
            f"mas você só tem `{saldo_usuario:.2f} MZN` no saldo."
        )
        botoes = [
            [InlineKeyboardButton("➕ Depositar Saldo", callback_data="ajuda_depositar_cb")],
            [InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="ajuda")]
        ]
        await ctx.bot.send_message(
            chat_id, 
            texto, 
            parse_mode=ParseMode.MARKDOWN, 
            reply_markup=InlineKeyboardMarkup(botoes)
        )
        return

    # 6. Mostrar a mensagem de confirmação
    texto_confirmacao = (
        f"❓ *Confirmar Compra*\n\n"
        f"Plano: *{nome_plano}*\n"
        f"Preço: `{preco_plano:.2f} MZN`\n\n"
        f"Seu saldo atual é de `{saldo_usuario:.2f} MZN`.\n"
        f"Deseja confirmar a compra?"
    )
    botoes_confirmacao = [
        [
            InlineKeyboardButton("✅ Sim, comprar", callback_data=f"confirmar_compra|{nome_plano}"),
            InlineKeyboardButton("❌ Não, voltar", callback_data="mostrar_planos")
        ]
    ]

    await ctx.bot.send_message(
        chat_id,
        text=texto_confirmacao,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(botoes_confirmacao)
    )

from datetime import datetime, timedelta

# 🔹 Defina o ID ou @username do canal aqui
CANAL_ID = -1003067460575
async def confirmar_compra_plano_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    username = query.from_user.username or "SemUsername"

    try:
        _, nome_plano = query.data.split("|")
    except ValueError:
        await query.edit_message_text("❌ Erro ao processar a compra.")
        return

    planos = get_planos_disponiveis()
    plano_selecionado = planos.get(nome_plano)

    if not plano_selecionado:
        await query.edit_message_text("❌ Plano não encontrado.")
        return

    preco_plano = plano_selecionado["preco"]

    # 🔹 Carrega dados do usuário
    usuarios = carregar_json("usuarios.json")
    if user_id not in usuarios:
        usuarios[user_id] = {"saldo": 0, "planos": []}

    saldo_usuario = usuarios[user_id].get("saldo", 0)

    # 🔹 Verifica saldo
    if saldo_usuario < preco_plano:
        await query.edit_message_text("❌ Saldo insuficiente. A compra foi cancelada.")
        return

    # 🔹 Verifica limite de compras por plano
    planos_usuario = usuarios[user_id].get("planos", [])
    planos_iguais = [p for p in planos_usuario if p["nome"] == nome_plano]

    if len(planos_iguais) >= plano_selecionado["max"]:
        await query.edit_message_text(
            f"⚠️ Você já atingiu o limite de `{plano_selecionado['max']}` compras do plano *{nome_plano}*.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # 🔹 Deduz saldo
    usuarios[user_id]["saldo"] = saldo_usuario - preco_plano

    # 🔹 Calcula datas
    data_compra = datetime.now()
    data_expiracao = data_compra + timedelta(days=plano_selecionado["dias"])

    # 🔹 Calcula ganhos futuros desse plano
    ganho_futuro = round(
        preco_plano * plano_selecionado["percent"] * plano_selecionado["dias"], 2
    )

    # 🔹 Vincular o plano ao depósito usado
    deposit_id_vinculado = None
    historico = usuarios[user_id].get("historico", [])
    for item in reversed(historico):  # pega do mais recente para o mais antigo
        if item.get("tipo") == "deposito" and item.get("status") == "aprovado":
            # Só vincula se esse depósito ainda não foi usado em um plano
            usado = False
            for p in planos_usuario:
                if str(p.get("deposit_id")) == str(item.get("id")):
                    usado = True
                    break
            if not usado:
                deposit_id_vinculado = item.get("id")
                break

    # 🔹 Cria novo plano
    novo_plano = {
        "nome": nome_plano,
        "investido": preco_plano,
        "valor":  preco_plano,
        "percent": plano_selecionado["percent"],
        "dias": plano_selecionado["dias"],
        "duracao": plano_selecionado["dias"],
        "dias_recebidos": 0,
        "data_compra": data_compra.strftime("%d/%m/%Y"),
        "data_expiracao": data_expiracao.strftime("%d/%m/%Y"),
        "ganhos_pagos": 0.0,
        "ganho_futuro": ganho_futuro,
        "deposit_id": deposit_id_vinculado  # 🔗 vínculo com o depósito
    }

    usuarios[user_id]["planos"].append(novo_plano)

    # 🔹 Salva no JSON
    salvar_json("usuarios.json", usuarios)

    # 🔹 Mensagem para o usuário
    texto_sucesso = (
        f"✅ *Compra Realizada com Sucesso!*\n\n"
        f"Você adquiriu o *{nome_plano}*.\n\n"
        f"💰 Valor: `{preco_plano:.2f} MZN`\n"
        f"📆 Expira em: {data_expiracao.strftime('%d/%m/%Y')}\n\n"
        f"💼 Ganho futuro total do plano: `{ganho_futuro:.2f} MZN`\n"
        f"Seu novo saldo é: `{usuarios[user_id]['saldo']:.2f} MZN`."
    )
    await query.edit_message_text(text=texto_sucesso, parse_mode=ParseMode.MARKDOWN)

    # 🔹 Mensagem automática para o canal
    texto_canal = (
        
        f"🌟 *NOVA COMPRA DE PLANO* 🌟\n\n"
        f"👤 Usuário: @{username}\n"
        f"🆔 ID: `{user_id}`\n\n"
        f"📦 Plano adquirido: *{nome_plano}*\n"
        f"💰 Valor investido: `{preco_plano:.2f} MZN`\n"
        f"📈 Ganho futuro total: `{ganho_futuro:.2f} MZN`\n"
        f"📆 Data de expiração: {data_expiracao.strftime('%d/%m/%Y')}\n\n"
        f"🚀 Bem-vindo ao futuro dos lucros! 🎉\n"
        
        "[Se ainda não tem conta ou quer aumentar seus ganhos, clique aqui e descubra nossos planos exclusivos](https://t.me/AgrotechFund_bot?start=7830660119)\n"
    )

    await ctx.bot.send_message(
        chat_id=CANAL_ID,
        text=texto_canal,
        parse_mode=ParseMode.MARKDOWN
    )

# INÍCIO DO FLUXO: AJUDA - DEPÓSITO
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

# Estados da conversa
ESCOLHER_METODO, DIGITAR_VALOR, ENVIAR_COMPROVANTE = range(3)

dados_depositos = {}  # Armazena temporariamente os dados dos usuários em processo de depósito

# 📦 Importações necessárias no topo
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters

# 👤 Admin ID
ADMIN_ID = 8182769178  # <-- Coloque seu ID real aqui

# 📁 Arquivos e variáveis
pendentes = {}
PENDENTES_FILE = "pendentes.json"

# 🔧 Utilitários
def salvar_json(nome_arquivo, dados):
    with open(nome_arquivo, "w") as f:
        import json
        json.dump(dados, f, indent=2)

def gerar_id():
    from uuid import uuid4
    return str(uuid4())[:8]

# ====================== AJUDA DEPÓSITO - INÍCIO ======================
@checa_banido
async def ajuda_depositar_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):  
    query = update.callback_query  
    await query.answer()  

    # 🗑️ Apaga a mensagem anterior
    try:
        await query.delete_message()
    except:
        pass  

    keyboard = [  
        [InlineKeyboardButton("🏦 Transferência Bancária", callback_data="dep_tipo|banco")],  
        [InlineKeyboardButton("💱 Criptomoeda", callback_data="dep_tipo|cripto")]  
    ]  

    await query.message.reply_text(  
        "💵 Escolha o tipo de depósito:",  
        reply_markup=InlineKeyboardMarkup(keyboard)  
    )

# ====================== ESCOLHA TIPO DEPÓSITO ======================
async def dep_tipo_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tipo = query.data.split("|")[1]

    try:
        await query.message.delete()
    except:
        pass

    if tipo == "banco":
        # 🔹 M-Pesa e E-Mola lado a lado
        keyboard = [
            [
                InlineKeyboardButton("M-Pesa", callback_data="dep_metodo|M-Pesa"),
                InlineKeyboardButton("E-Mola", callback_data="dep_metodo|E-Mola")
            ]
        ]
        await query.message.reply_text(
            "📲 Escolha o método de transferência:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif tipo == "cripto":
        # 🔹 Criptomoedas 2 a 2
        keyboard = [
            [
                InlineKeyboardButton("₿ Bitcoin (BTC)", callback_data="dep_crypto|BTC"),
                InlineKeyboardButton("🌐 Ethereum (ETH)", callback_data="dep_crypto|ETH")
            ],
            [
                InlineKeyboardButton("💲 USDT (TRC20)", callback_data="dep_crypto|TRC20"),
                InlineKeyboardButton("🪙 USDT (BEP20)", callback_data="dep_crypto|BEP20")
            ],
            [
                InlineKeyboardButton("🔶 BNB", callback_data="dep_crypto|BNB"),
                InlineKeyboardButton("💠 XRP", callback_data="dep_crypto|XRP")
            ]
        ]
        await query.message.reply_text(
            "💸 Escolha a criptomoeda:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ====================== ESCOLHA M-PESA / E-MOLA ======================
async def dep_metodo_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    metodo = query.data.split("|")[1]

    numeros = {
        "M-Pesa": "+258 849564273\n Titular: Jorge Joaquim",
        "E-Mola": "+258 877329951\n Titular: Raqueza Coelho"
    }

    context.user_data["metodo_deposito"] = metodo
    context.user_data["esperando_valor_deposito"] = True

    try:
        await query.message.delete()
    except:
        pass

    # 🔹 Criar botões em pares (2 por linha)
    planos = get_planos_disponiveis()
    valores = [dados["preco"] for _, dados in planos.items()]

    botoes = []
    linha = []
    for i, valor in enumerate(valores, start=1):
        linha.append(InlineKeyboardButton(f"{valor} MZN", callback_data=f"deposito_valor|{valor}"))
        if i % 2 == 0:
            botoes.append(linha)
            linha = []
    if linha:  # se sobrar botão
        botoes.append(linha)

    markup = InlineKeyboardMarkup(botoes)

    msg = await query.message.reply_text(
        f"✅ Depósito via {metodo}\n"
        f"📱 Número para transferência: {numeros.get(metodo, '⚠️ Número não disponível.')}\n\n"
        f"💰 Escolha um valor abaixo ou digite manualmente:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )

    context.user_data["mensagem_numero_pagamento"] = msg.message_id


# ====================== ESCOLHA CRIPTOMOEDA ======================
async def dep_crypto_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    moeda = query.data.split("|")[1]

    context.user_data["metodo_deposito"] = f"Criptomoeda - {moeda}"
    context.user_data["esperando_valor_deposito"] = True

    try:
        await query.message.delete()
    except:
        pass

    # 🔹 Criar botões em pares (2 por linha)
    planos = get_planos_disponiveis()
    valores = [dados["preco"] for _, dados in planos.items()]

    botoes = []
    linha = []
    for i, valor in enumerate(valores, start=1):
        linha.append(InlineKeyboardButton(f"{valor} MZN", callback_data=f"deposito_valor|{valor}"))
        if i % 2 == 0:
            botoes.append(linha)
            linha = []
    if linha:
        botoes.append(linha)

    markup = InlineKeyboardMarkup(botoes)

    msg = await query.message.reply_text(
        f"✅ Depósito via {moeda}\n"
        f"📥 Enviaremos o endereço da carteira após informar o valor.\n\n"
        f"💰 Escolha um valor abaixo ou digite manualmente:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )

    context.user_data["mensagem_numero_pagamento"] = msg.message_id


# ====================== PROCESSA VALOR DIGITADO ======================
async def processar_valor_deposito(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("esperando_valor_deposito"):
        return

    text = update.message.text
    try:
        valor = float(text)
        if valor < 350:
            return await update.message.reply_text("❌ Valor mínimo para depósito: 350 MZN.")
    except:
        return await update.message.reply_text("❌ Valor inválido. Envie apenas o número.")

    metodo = context.user_data.get("metodo_deposito")
    context.user_data["valor_deposito"] = valor
    context.user_data["esperando_valor_deposito"] = False
    context.user_data["esperando_comprovante"] = True

    # 🗑️ Apaga a mensagem antiga (que pedia o valor)
    try:
        msg_id = context.user_data.get("mensagem_numero_pagamento")
        if msg_id:
            await update.message.chat.delete_message(msg_id)
    except:
        pass

    # 🗑️ Apaga a mensagem do usuário (onde ele digitou o valor)
    try:
        await update.message.delete()
    except:
        pass

    # 📌 Endereços ou números
    contas_pagamento = {
        "M-Pesa": "+258 849564273\n Titular: Jorge Joaquim",
        "E-Mola": "+258 877329951\n Titular: Raqueza coelho",
        "BTC": "0x0df8e7b0c172f509f6aff2791fb500462b13a5e5",
        "ETH": "0x0df8e7b0c172f509f6aff2791fb500462b13a5e5",
        "TRC20": "TFagbCvLFeki5BLzY5sz2yK4SEdbB9wyYJ",
        "BEP20": "0x0df8e7b0c172f509f6aff2791fb500462b13a5e5",
        "BNB": "0x0df8e7b0c172f509f6aff2791fb500462b13a5e5",
        "XRP": "rGDreBvnHrX1get7na3J4oowN19ny4GzFn    `Tag/nota` 664181834"
    }

    dados_transferencia = contas_pagamento.get(
        metodo.replace("Criptomoeda - ", ""), "⚠️ Método não configurado"
    )

    # ✅ Envia nova mensagem (somente a final, limpa)
    msg = await update.message.reply_text(
        f"✅ Depósito via *{metodo}* selecionado.\n"
        f"💰 Valor: *{valor:.2f} MZN*\n\n"
        f"➡️ *Dados para transferência:*\n`{dados_transferencia}`\n\n"
        f"📸 Agora envie a *foto do comprovativo* do seu depósito.",
        parse_mode=ParseMode.MARKDOWN
    )

    context.user_data["mensagem_pedir_comprovante"] = msg.message_id


# ====================== BOTÃO DE VALOR PRONTO ======================
async def deposito_valor_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, valor_str = query.data.split("|", 1)
    valor = float(valor_str)

    context.user_data["valor_deposito"] = valor
    context.user_data["esperando_valor_deposito"] = False
    context.user_data["esperando_comprovante"] = True

    metodo = context.user_data.get("metodo_deposito")

    contas_pagamento = {
        "M-Pesa": "+258 849564273",
        "E-Mola": "+258 877329951",
        "BTC": "0x0df8e7b0c172f509f6aff2791fb500462b13a5e5",
        "ETH": "0x0df8e7b0c172f509f6aff2791fb500462b13a5e5",
        "TRC20": "TFagbCvLFeki5BLzY5sz2yK4SEdbB9wyYJ",
        "BEP20": "0x0df8e7b0c172f509f6aff2791fb500462b13a5e5",
        "BNB": "0x0df8e7b0c172f509f6aff2791fb500462b13a5e5",
        "XRP": "rGDreBvnHrX1get7na3J4oowN19ny4GzFn    Tag/nota 664181834"
    }

    dados_transferencia = contas_pagamento.get(
        metodo.replace("Criptomoeda - ", ""), "⚠️ Método não configurado"
    )

    # ✅ Mensagem final (quando o valor vem do botão)
    await query.message.edit_text(
        f"✅ Depósito via *{metodo}* selecionado.\n"
        f"💰 Valor: *{valor:.2f} MZN*\n\n"
        f"➡️ *Dados para transferência:*\n`{dados_transferencia}`\n\n"
        f"📸 Agora envie a *foto do comprovativo* do seu depósito.",
        parse_mode=ParseMode.MARKDOWN
    )


# ====================== PROCESSA COMPROVANTE ======================
async def processar_comprovante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("esperando_comprovante"):
        return

    # 🗑️ Apaga mensagem pedindo comprovante
    try:
        msg_id = context.user_data.get("mensagem_pedir_comprovante")
        if msg_id:
            await update.message.chat.delete_message(msg_id)
    except:
        pass

    # 🗑️ Apaga a foto enviada pelo usuário depois de registrar
    #try:
        #await update.message.delete()
    #except:
        #pass

    if not update.message.photo:
        await update.message.reply_text(
            "❌ Por favor, envie uma *foto* do comprovante, não um documento ou texto.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    metodo = context.user_data.get("metodo_deposito", "Indefinido")
    valor = context.user_data.get("valor_deposito", 0)
    uid = str(update.effective_user.id)
    nome = update.effective_user.first_name
    username = update.effective_user.username  # pode ser None

    pid = gerar_id()

    # ⏰ Criar data de criação formatada
    agora = datetime.now()
    data_formatada = agora.strftime("%d/%m/%Y %H:%M")

    # 💾 Salvar no pendentes.json
    pendentes = carregar_json(PENDENTES_FILE)
    pendentes[pid] = {
        "user_id": uid,
        "nome": nome,
        "username": username,
        "tipo": "deposito",
        "valor": valor,
        "metodo": metodo,
        "status": "pendente",
        "data": data_formatada,
        "data_criacao": data_formatada  # salva como string no mesmo formato
    }
    salvar_json(PENDENTES_FILE, pendentes)

    # 📂 Registrar no histórico do usuário
    usuarios = carregar_json(USERS_FILE)
    if uid in usuarios:
        if "historico" not in usuarios[uid] or not isinstance(usuarios[uid]["historico"], list):
            usuarios[uid]["historico"] = []

        usuarios[uid]["historico"].append({
            "id": pid,
            "tipo": "deposito",
            "valor": valor,
            "metodo": metodo,
            "status": "pendente",
            "data": data_formatada,
            "data_criacao": data_formatada
        })
        salvar_json(USERS_FILE, usuarios)

    # 🔔 Enviar comprovativo para o admin
    caption = (
        f"📥 *Novo depósito pendente:*\n"
        f"💰 Valor: {valor:.2f} MZN\n"
        f"🏦 Método: {metodo}\n"
        f"🆔 ID: {pid}\n"
        f"👤 User ID: {uid}\n"
        f"👤 Nome: {nome}\n"
        f"👤 Username: @{username if username else '—'}"
    )

    buttons = [
        [InlineKeyboardButton("✅ Aprovar", callback_data=f"aprovar|{pid}"),
         InlineKeyboardButton("❌ Recusar", callback_data=f"recusar|{pid}")]
    ]

    try:
        photo_file_id = update.message.photo[-1].file_id
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo_file_id,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        await update.message.reply_text("✅ Seu depósito está sendo processado. Aguarde a confirmação.")
    except Exception as e:
        await update.message.reply_text(
            "⚠️ O comprovativo foi enviado, mas houve erro ao notificar a equipe. Tente novamente ou fale com o suporte."
        )
        print(f"[Erro ao enviar para admin] {e}")

    # 🔚 Limpar dados temporários
    context.user_data.clear()

# ✅ AJUDA SAQUE COM CHECAGEM DE BANIMENTO
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler, MessageHandler, filters

@checa_banido
async def ajuda_sacar_cb(update, ctx: CallbackContext):
    query = update.callback_query
    await query.answer()

    # 🗑️ Apaga mensagem anterior, se existir
    try:
        await query.message.delete()
        if ctx.user_data.get("last_msg_id"):
            await query.message.chat.delete_message(ctx.user_data["last_msg_id"])
    except:
        pass

    usuarios = carregar_json(USERS_FILE)
    uid = str(update.effective_user.id)
    user = usuarios.get(uid)

    if not user:
        return await query.message.reply_text(
            "❌ Você ainda não possui conta. Use /start para se registrar."
        )

    if user.get("banido", False):
        keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda")]]
        return await query.message.reply_text(
            "⛔ Você está banido ou bloqueado. Não pode fazer saques até ser desbanido pelo suporte.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    if user.get("saldo", 0) < 120:
        return await query.message.reply_text(
            "❌ Saldo insuficiente. O mínimo para saque é 120 MZN."
        )

    # 🔐 Pede senha se já existir
    if user.get("senha_saque"):
        msg = await query.message.reply_text(
            "✏️ Por favor, digite sua *senha de saque* para continuar:",
            parse_mode=ParseMode.MARKDOWN
        )
        ctx.user_data["esperando_senha_saque"] = True
        ctx.user_data["last_msg_id"] = msg.message_id
        return

    # Mostrar conta vinculada se não tiver senha
    banco = user.get("banco", {})
    cripto = user.get("cripto", {})

    if banco and banco.get("numero"):
        texto_conta = (
            f"🔗 Você já vinculou uma conta bancária para saque:\n"
            f"🏦 Tipo: {banco.get('tipo', '—')}\n"
            f"📱 Número: {banco.get('numero', '—')}\n"
            f"👤 Nome: {banco.get('nome', update.effective_user.first_name)}\n\n"
            "Deseja continuar para realizar o saque?"
        )
    elif cripto and cripto.get("wallet"):
        texto_conta = (
            f"🔗 Você já vinculou uma carteira cripto para saque:\n"
            f"💰 Moeda: {cripto.get('moeda', '—')}\n"
            f"🔗 Wallet: {cripto.get('wallet', '—')}\n\n"
            "Deseja continuar para realizar o saque?"
        )
    else:
        keyboard = [[InlineKeyboardButton("🔗 Vincular agora", callback_data="vincular_conta")]]
        markup = InlineKeyboardMarkup(keyboard)
        return await query.message.reply_text(
            "❌ Você ainda não vinculou uma conta para saque.\n\n"
            "Clique no botão abaixo para vincular agora:",
            reply_markup=markup
        )

    keyboard = [
        [InlineKeyboardButton("✅ Continuar", callback_data="continuar_saque")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="ajuda")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(texto_conta, reply_markup=markup)


# ==========================
# CALLBACK CONTINUAR SAQUE
# ==========================
async def continuar_saque_cb(update, ctx: CallbackContext):
    query = update.callback_query
    await query.answer()

    # 🗑️ Apaga mensagem anterior
    try:
        await query.message.delete()
        if ctx.user_data.get("last_msg_id"):
            await query.message.chat.delete_message(ctx.user_data["last_msg_id"])
    except:
        pass

    uid = str(update.effective_user.id)
    usuarios = carregar_json(USERS_FILE)
    user = usuarios.get(uid)

    if not user:
        return await query.message.reply_text(
            "❌ Você ainda não possui conta. Use /start para se registrar."
        )

    # Pede criar senha se não tiver
    if not user.get("senha_saque"):
        keyboard = [
            [InlineKeyboardButton("✅ Definir agora", callback_data="criar_senha_saque")],
            [InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda")]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        return await query.message.reply_text(
            "🔑 Você ainda não possui uma senha de saque.\n"
            "💡 Uma senha de saque protege suas transações e garante maior segurança.\n\n"
            "Clique no botão abaixo para definir sua senha antes de continuar:",
            reply_markup=markup
        )

    # Já tem senha → pede para digitar
    msg = await query.message.reply_text(
        "✏️ Por favor, digite sua *senha de saque* para continuar:",
        parse_mode=ParseMode.MARKDOWN
    )
    ctx.user_data["esperando_senha_saque"] = True
    ctx.user_data["last_msg_id"] = msg.message_id


# ==========================
# PROCESSAR SENHA OU VALOR SAQUE
# ==========================
async def processar_saque_com_senha(update, ctx: CallbackContext):
    uid = str(update.message.from_user.id)
    usuarios = carregar_json(USERS_FILE)
    user = usuarios.get(uid)
    texto = update.message.text.strip()

    if not user:
        return await update.message.reply_text(
            "❌ Você ainda não possui conta. Use /start para se registrar."
        )

    # ⚠️ Verifica se o usuário estava digitando a senha de saque
    if ctx.user_data.get("esperando_senha_saque"):
        # 🗑️ Apaga a mensagem da senha digitada
        try:
            await update.message.delete()
        except:
            pass

        if texto != str(user.get("senha_saque")):
            msg = await update.message.reply_text(
                "❌ Senha incorreta. Tente novamente ou clique em cancelar."
            )
            ctx.user_data["last_msg_id"] = msg.message_id
            return
        else:
            ctx.user_data.pop("esperando_senha_saque")

            banco = user.get("banco", {})
            cripto = user.get("cripto", {})

            if banco and banco.get("numero"):
                texto_conta = (
                    f"🔗 Sua conta bancária vinculada para saque:\n"
                    f"🏦 Tipo: {banco.get('tipo', '—')}\n"
                    f"📱 Número: {banco.get('numero', '—')}\n"
                    f"👤 Nome: {banco.get('nome', update.effective_user.first_name)}\n\n"
                    "Deseja continuar para digitar o valor do saque?"
                )
            elif cripto and cripto.get("wallet"):
                texto_conta = (
                    f"🔗 Sua carteira cripto vinculada para saque:\n"
                    f"💰 Moeda: {cripto.get('moeda', '—')}\n"
                    f"🔗 Wallet: {cripto.get('wallet', '—')}\n\n"
                    "Deseja continuar para digitar o valor do saque?"
                )
            else:
                return await update.message.reply_text(
                    "❌ Nenhum método de saque vinculado. Por favor vincule uma conta ou carteira primeiro."
                )

            keyboard = [
                [InlineKeyboardButton("✅ Continuar", callback_data="pedir_valor_saque")],
                [InlineKeyboardButton("❌ Cancelar", callback_data="ajuda")]
            ]
            markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(texto_conta, reply_markup=markup)
            return

    if ctx.user_data.get("esperando_val_saque"):
        return await processar_sacar(update, ctx)

    await update.message.reply_text("⚠️ Não há nenhuma operação pendente no momento.")

# ==========================    
async def pedir_valor_saque_cb(update, ctx: CallbackContext):
    query = update.callback_query
    await query.answer()

    try:
        await query.message.delete()
    except:
        pass

    uid = str(update.effective_user.id)
    usuarios = carregar_json(USERS_FILE)
    user = usuarios.get(uid)

    if not user:
        return await query.message.reply_text(
            "❌ Você ainda não possui conta. Use /start para se registrar."
        )

    # ✅ Agora o usuário digita o valor
    msg = await query.message.reply_text(
        "🏧 Digite o valor que deseja sacar (mínimo: 120 MZN):",
        parse_mode=ParseMode.MARKDOWN
    )
    ctx.user_data["esperando_val_saque"] = True
    ctx.user_data["last_msg_id"] = msg.message_id

# =======================
# PROCESSAR SAQUE
# =======================
async def processar_sacar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global usuarios
    uid = str(update.message.from_user.id)
    text = update.message.text
    usuarios = carregar_json(USERS_FILE)
    user = usuarios.get(uid)

    if not user:
        return await update.message.reply_text(  
            "❌ Você ainda não possui conta. Use /start para se registrar."  
        )  

    # 🔹 CÁLCULO do depósito total aprovado  
    deposito_total = sum(  
        d.get("valor", 0)  
        for d in user.get("historico", [])  
        if d.get("tipo") == "deposito" and d.get("status") == "aprovado"  
    )  
    if deposito_total < 350:  
        return await update.message.reply_text(  
            f"❌ Você precisa ter feito um depósito mínimo de 350 MZN para poder sacar.\n"  
            f"Depósito atual: {deposito_total:.2f} MZN"  
        )  

    # 🔹 Verificação de plano ativo ou expirado  
    tem_plano_ativo = len(user.get("planos", [])) > 0  
    tem_plano_expirado = len(user.get("planos_expirados", [])) > 0  
    if not tem_plano_ativo and not tem_plano_expirado:  
        return await update.message.reply_text(  
            "❌ Você precisa ter ou já ter tido um plano ativo para poder sacar."  
        )  

    # Apagar mensagens antigas  
    try:  
        await update.message.delete()  
    except:  
        pass  
    if "last_msg_id" in ctx.user_data:  
        try:  
            await ctx.bot.delete_message(chat_id=uid, message_id=ctx.user_data["last_msg_id"])  
        except:  
            pass  

    # 🔹 Etapa 1: usuário digitou o valor do saque  
    if ctx.user_data.get("esperando_val_saque"):  
        try:  
            valor_saque = float(text)  
            assert valor_saque >= 120  
        except:  
            msg = await update.message.reply_text(  
                "❌ Valor inválido. Valor mínimo para saque é 120 MZN."  
            )  
            ctx.user_data["last_msg_id"] = msg.message_id  
            return  

        # 🚨 Limite máximo por saque
        if valor_saque > 30000:  
            msg = await update.message.reply_text(  
                "❌ O valor máximo permitido para saque é 30 000 MZN."  
            )  
            ctx.user_data["last_msg_id"] = msg.message_id  
            return  

        # 🚨 Limite de 24h: só pode sacar uma vez por dia
        historico_saques = [  
            s for s in user.get("historico", [])  
            if s.get("tipo") == "saque" and s.get("status") == "aprovado"  
        ]  
        if historico_saques:  
            ultimo_saque = max(historico_saques, key=lambda x: datetime.strptime(x.get("data", "01/01/1970 00:00"), "%d/%m/%Y %H:%M"))  
            data_ultimo = datetime.strptime(ultimo_saque["data"], "%d/%m/%Y %H:%M")  
            if datetime.now() - data_ultimo < timedelta(hours=0):  
                msg = await update.message.reply_text(  
                    "❌ Você já fez um saque nas últimas 24h. Tente novamente depois."  
                )  
                ctx.user_data["last_msg_id"] = msg.message_id  
                return  

        if user.get("saldo", 0) < valor_saque:  
            msg = await update.message.reply_text("❌ Saldo insuficiente para esse valor.")  
            ctx.user_data["last_msg_id"] = msg.message_id  
            return  

        taxa = valor_saque * 0.15  
        valor_liquido = valor_saque - taxa  

        # ✅ Guardar temporariamente no contexto  
        ctx.user_data["saque_val_bruto"] = valor_saque  
        ctx.user_data["saque_val_liquido"] = valor_liquido  
        ctx.user_data["esperando_val_saque"] = False  

        # 🔎 Puxar conta vinculada (banco ou cripto)  
        banco = user.get("banco", {})  
        cripto = user.get("cripto", {})  

        if banco and banco.get("numero"):  
            metodo = banco.get("tipo", "Banco")  
            numero = banco.get("numero", "—")  
            nome_conta = banco.get("nome", update.effective_user.first_name)  
        elif cripto and cripto.get("wallet"):  
            metodo = f"Cripto - {cripto.get('moeda', '—')}"  
            numero = cripto.get("wallet", "—")  
            nome_conta = update.effective_user.first_name  
        else:  
            return await update.message.reply_text(  
                "❌ Nenhuma conta vinculada encontrada (nem banco nem cripto)."  
            )  

        # 🧾 Subtrair saldo do usuário  
        user["saldo"] -= valor_saque  

        # 🔐 Gerar ID único do pedido  
        pid = gerar_id()  

        # 🔄 Garantir histórico  
        if "historico" not in user or not isinstance(user["historico"], list):  
            user["historico"] = []  

        # 🔄 Adicionar saque ao histórico  
        user["historico"].append({  
            "id": pid,  
            "tipo": "saque",  
            "valor_bruto": valor_saque,  
            "valor_liquido": valor_liquido,  
            "numero": numero,  
            "metodo": metodo,  
            "status": "pendente",  
            "data": datetime.now().strftime("%d/%m/%Y %H:%M")  
        })  

        salvar_json(USERS_FILE, usuarios)  

        # 📌 Pegar dados do usuário certo  
        nome = update.effective_user.first_name  
        username = update.effective_user.username  

        # 💾 Salvar também em pendentes.json  
        pendentes = carregar_json(PENDENTES_FILE)  
        pendentes[pid] = {  
            "user_id": uid,  
            "nome": nome,  
            "username": username,  
            "tipo": "saque",  
            "valor_bruto": valor_saque,  
            "valor_liquido": valor_liquido,  
            "numero": numero,  
            "metodo": metodo,  
            "status": "pendente",  
            "data": datetime.now().strftime("%d/%m/%Y %H:%M")  
        }  
        salvar_json(PENDENTES_FILE, pendentes)  

        # 📢 Notificar admin  
        msg_admin = (  
            f"📤 *Novo pedido de saque:*\n"  
            f"💰 Valor solicitado: {valor_saque:.2f} MZN\n"  
            f"💸 Valor a pagar (taxa 15%): {valor_liquido:.2f} MZN\n"  
            f"🏦 Método: {metodo}\n"  
            f"📞 Conta/Wallet: {numero}\n"  
            f"👤 Nome conta: {nome_conta}\n"  
            f"🆔 ID Saque: {pid}\n"  
            f"👤 User ID: {uid}\n"  
            f"👤 Nome: {nome}\n"  
            f"👤 Username: @{username if username else '—'}"  
        )  
        buttons = [  
            [InlineKeyboardButton("✅ Aprovar", callback_data=f"aprovar|{pid}"),  
             InlineKeyboardButton("❌ Recusar", callback_data=f"recusar|{pid}")]  
        ]  
        markup = InlineKeyboardMarkup(buttons)  

        await ctx.bot.send_message(  
            ADMIN_ID,  
            msg_admin,  
            reply_markup=markup,  
            parse_mode=ParseMode.MARKDOWN  
        )  

        msg_user = await update.message.reply_text(  
            f"✅ Pedido de saque registrado com ID {pid}.\n"  
            f"💸 Valor líquido: {valor_liquido:.2f} MZN.\n"  
            f"Aguarde aprovação!",  
            parse_mode=ParseMode.MARKDOWN  
        )  
        ctx.user_data["last_msg_id"] = msg_user.message_id  

        # ✅ Limpar contexto  
        ctx.user_data.clear()


# ✅ Unificar saque e depósito em um único handler
async def processar_textos(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if ctx.user_data.get("esperando_val_saque") or ctx.user_data.get("esperando_num_saque"):
        return await processar_sacar(update, ctx)

    if ctx.user_data.get("esperando_valor_deposito"):
        return await processar_valor_deposito(update, ctx)

    # Se nenhuma flag ativa, ignora (ou responde outra coisa se quiser)
    return

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

# Assumo que você já tem essas funções:
# carregar_json(), salvar_json()
# depositar_cb(), sacar_cb()

USERS_FILE = "usuarios.json"

@checa_banido
async def ajuda_saldo_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    usuarios = carregar_json(USERS_FILE)
    uid = str(update.effective_user.id)
    user = usuarios.get(uid)

    # 🗑️ Apaga a mensagem anterior
    try:
        await query.delete_message()
    except:
        pass

    if not user:
        keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda")]]
        return await query.message.reply_text(
            "❌ Você ainda não possui conta ou saldo. Use /start para começar.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    saldo_atual = user.get("saldo", 0.0)
    planos_ativos = user.get("planos", [])
    num_planos = len(planos_ativos)

    lucro_estimado = sum(
        p["valor"] * p["percent"] * (p.get("dias_total", p["dias_restantes"]) - p["dias_restantes"])
        for p in planos_ativos
    )
    lucro_diario = sum(p["valor"] * p["percent"] for p in planos_ativos)
    lucro_real = user.get("lucro_pago", 0.0)
    ultima_coleta = user.get("last_coleta_date", "Nunca")

    msg = (
        f"💰 *Seu saldo*: {saldo_atual:.2f} MZN\n"
        f"📊 *Planos ativos*: {num_planos}\n"
        f"💎 *Lucro coletado (real)*: {lucro_real:.2f} MZN\n"
        f"💵 *Lucro diário estimado*: {lucro_diario:.2f} MZN\n"
        f"📅 *Próxima coleta (amanhã)*: {lucro_diario:.2f} MZN\n"
        f"🗓️ *Última coleta*: {ultima_coleta}\n"
        f"\n"
        f"✅ Continue investindo para aumentar seus ganhos!"
    )

    keyboard = [
        [InlineKeyboardButton("💳 Depositar", callback_data="escolher_metodo_deposito")],
        [InlineKeyboardButton("💸 Sacar", callback_data="escolher_metodo_saque")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda")]
    ]

    await query.message.reply_text(
        msg, 
        parse_mode=ParseMode.MARKDOWN, 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def escolher_metodo_deposito(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🏦 Transferência Bancária", callback_data="deposito_banco")],
        [InlineKeyboardButton("💰 Criptomoeda", callback_data="deposito_crypto")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda_saldo")]
    ]
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "Escolha o método de depósito:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def escolher_metodo_saque(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🏦 Transferência Bancária", callback_data="saque_banco")],
        [InlineKeyboardButton("💰 Criptomoeda", callback_data="saque_crypto")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda_saldo")]
    ]
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "Escolha o método de saque:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# Esse é o handler geral para callbacks dos botões
async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "escolher_metodo_deposito":
        return await escolher_metodo_deposito(update, ctx)
    elif data == "escolher_metodo_saque":
        return await escolher_metodo_saque(update, ctx)
    elif data == "deposito_banco":
        return await depositar_cb(update, ctx)  # sua função real de depósito
    elif data == "deposito_crypto":
        return await depositar_cb(update, ctx)  # mesma função, só que você pode identificar o método dentro dela
    elif data == "saque_banco":
        return await sacar_cb(update, ctx)  # sua função real de saque
    elif data == "saque_crypto":
        return await sacar_cb(update, ctx)
    elif data == "ajuda_saldo":
        return await ajuda_saldo_cb(update, ctx)
    elif data == "voltar_menu_principal":
        # Aqui você pode redirecionar para o menu principal do seu bot, por exemplo
        await query.answer()
        await query.message.reply_text("Voltando ao menu principal...")
        # chamar função do menu principal aqui se tiver
    else:
        await query.answer()
        await query.message.reply_text("Opção não reconhecida.")

# ===============================
# 📌 SALDO + DEPÓSITO + SAQUE INTEGRADO (USANDO FUNÇÕES ORIGINAIS)
# ===============================
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

# ===============================
# 📌 SALDO + DEPÓSITO + SAQUE INTEGRADO (CHAMANDO FUNÇÕES ORIGINAIS)
# ===============================
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

# 🛠️ Utilitário para apagar mensagem antiga e enviar nova
async def apagar_antigo_e_enviar(query, texto, botoes=None, parse_mode=ParseMode.MARKDOWN):
    """Apaga a mensagem antiga (se existir) e envia uma nova com o texto e botões."""
    try:
        await query.message.delete()
    except:
        pass

    return await query.message.reply_text(
        texto,
        parse_mode=parse_mode,
        reply_markup=InlineKeyboardMarkup(botoes) if botoes else None
    )

# 📌 Saldo principal
@checa_banido
async def ajuda_saldo_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    usuarios = carregar_json(USERS_FILE)
    uid = str(update.effective_user.id)
    user = usuarios.get(uid)

    # Se não tem conta
    if not user:
        try:
            await query.message.delete()
        except:
            pass
        return await query.message.reply_text(
            "❌ Você ainda não possui conta ou saldo. Use /start para começar."
        )

    saldo_atual = user.get("saldo", 0.0)
    planos = user.get("planos", [])
    hoje = datetime.now()

    planos_ativos = []
    lucro_diario = 0.0
    lucro_coletavel = 0.0   # 🔹 acumulado até hoje

    for p in planos:
        data_compra = parse_data(p.get("data_compra", hoje.isoformat()))
        dias_total = p.get("dias_total", 30)  # padrão 30 dias
        data_expiracao = parse_data(
            p.get("data_expiracao", (data_compra + timedelta(days=dias_total)).isoformat())
        )

        if hoje < data_expiracao:  # só conta se ainda não expirou
            planos_ativos.append(p)

            valor = p.get("valor", p.get("investido", 0.0))
            percent = p.get("percent", 0.0)

            # cálculo igual ao de meusplanos
            ganho_dia = round(valor * percent, 2)
            total_ganho = round(ganho_dia * dias_total, 2)

            dias_passados = min((hoje - data_compra).days, dias_total)
            ganhos_pagos = round(ganho_dia * dias_passados, 2)

            # acumulados
            lucro_diario += ganho_dia
            lucro_coletavel += ganhos_pagos

    num_planos = len(planos_ativos)
    lucro_real = user.get("lucro_pago", 0.0)
    ultima_coleta = user.get("last_coleta_date", "Nunca")

    msg = (
        f"💰 *Seu saldo*: {saldo_atual:.2f} MZN\n"
        f"📊 *Planos ativos*: {num_planos}\n"
        f"💎 *Lucro coletado (real)*: {lucro_real:.2f} MZN\n"
        f"💵 *Lucro acumulado até hoje*: {lucro_coletavel:.2f} MZN\n"
        f"📆 *Lucro diário médio*: {lucro_diario:.2f} MZN\n"
        f"🗓️ *Última coleta*: {ultima_coleta}\n"
    )

    botoes = [
        [InlineKeyboardButton("📥 Depositar", callback_data="saldo_deposito")],
        [InlineKeyboardButton("📤 Sacar", callback_data="saldo_saque")],
        [InlineKeyboardButton("🎁 Ganhe Bônus!", callback_data="menu")],
        [InlineKeyboardButton("⬅ Voltar", callback_data="ajuda")],
    ]

    try:
        await query.message.delete()
    except:
        pass

    await query.message.reply_text(
        msg,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(botoes)
    )

# 📌 Botão Depositar → chama fluxo ORIGINAL de depósito
async def saldo_deposito_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await ajuda_depositar_cb(update, ctx)  # 🔗 função original que você já tem

async def saldo_saque_cb(update: Update, ctx: ContextTypes.
DEFAULT_TYPE):
    await ajuda_sacar_cb(update, ctx)

# 📌 Botão Sacar → chama fluxo ORIGINAL de saque
async def processar_valor_usuario(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    uid = str(update.effective_user.id)
    usuarios = carregar_json(USERS_FILE)
    usuarios.setdefault(uid, {})

    # 🔹 ADMIN DIGITANDO ID (pode ser para ver usuário ou para painel)
    if ctx.user_data.get("esperando_id_usuario") or ctx.user_data.get("esperando_id_manual"):
        ctx.user_data["esperando_id_usuario"] = False
        ctx.user_data["esperando_id_manual"] = False
        user_id = texto.strip()

        # garante que é número (evita confundir com valores de saque)
        if not user_id.isdigit():
            return await update.message.reply_text("⚠️ ID inválido. Digite apenas números.")

        if user_id not in usuarios:
            return await update.message.reply_text(f"❌ Usuário {user_id} não encontrado.")

        ctx.user_data["admin_selected_user"] = user_id

        # se estava no modo de "ver usuário"
        if ctx.user_data.get("modo_ver_usuario"):
            ctx.user_data.pop("modo_ver_usuario", None)
            return await mostrar_usuario(update, ctx, user_id)

        # senão → padrão: painel admin
        return await admin_user_cb(update, ctx, user_id=user_id)

    # 1️⃣ ADMIN INPUT
    elif ctx.user_data.get("aguardando_input") and ctx.user_data.get("admin_selected_user"):
        return await admin_input_process(update, ctx)

    # 2️⃣ ALTERAR SENHA DE SAQUE
    elif ctx.user_data.get("mudando_senha_saque"):
        return await processar_alterar_senha_saque(update, ctx)

    # 3️⃣ CRIAR NOVA SENHA DE SAQUE
    elif ctx.user_data.get("criando_senha_saque"):
        return await processar_senha_saque(update, ctx)

    # 4️⃣ DEPÓSITO
    elif ctx.user_data.get("esperando_val_deposito") or ctx.user_data.get("esperando_valor_deposito"):
        return await processar_valor_deposito(update, ctx)

    # 5️⃣ SAQUE
    elif ctx.user_data.get("esperando_val_saque") or ctx.user_data.get("esperando_senha_saque"):
        return await processar_saque_com_senha(update, ctx)

    # 6️⃣ VINCULAR CONTA (BANCO)
    elif ctx.user_data.get("esperando_numero_banco"):
        ctx.user_data["numero"] = texto
        ctx.user_data.pop("esperando_numero_banco")
        ctx.user_data["esperando_nome_banco"] = True
        return await update.message.reply_text("✍️ Agora digite o *nome do titular da conta*:")

    elif ctx.user_data.get("esperando_nome_banco"):
        usuarios[uid]["banco"] = {
            "tipo": ctx.user_data.get("tipo_banco"),
            "numero": ctx.user_data.get("numero"),
            "nome": texto
        }
        salvar_usuarios(usuarios)
        ctx.user_data.pop("esperando_nome_banco")
        return await update.message.reply_text(
            f"✅ Conta vinculada com sucesso!\n\n"
            f"🏦 Banco: {ctx.user_data['tipo_banco']}\n"
            f"📱 Número: {ctx.user_data['numero']}\n"
            f"👤 Titular: {texto}"
        )

    # 7️⃣ VINCULAR CONTA (CRIPTO)
    elif ctx.user_data.get("esperando_wallet"):
        usuarios[uid]["cripto"] = {
            "moeda": ctx.user_data.get("cripto"),
            "wallet": texto
        }
        salvar_usuarios(usuarios)
        ctx.user_data.pop("esperando_wallet")
        return await update.message.reply_text(
            f"✅ Wallet vinculada com sucesso!\n\n"
            f"💰 Moeda: {ctx.user_data['cripto']}\n"
            f"🔗 Endereço: {texto}"
        )

    # 8️⃣ BANIMENTO / DESBANIMENTO / BLOQUEIO / DESBLOQUEIO
    elif ctx.user_data.get("esperando_id_banir") or ctx.user_data.get("esperando_id_desbanir") \
         or ctx.user_data.get("esperando_id_bloquear") or ctx.user_data.get("esperando_id_desbloquear"):
        return await processar_ban_desban(update, ctx)

    # 🔑 ADMIN CRIANDO CÓDIGO
    elif ctx.user_data.get("admin_criando_codigo"):
        etapa = ctx.user_data.get("etapa_codigo", "nome")

        if etapa == "nome":
            ctx.user_data["novo_codigo_nome"] = texto.strip().upper()
            ctx.user_data["etapa_codigo"] = "valor"
            return await update.message.reply_text("💰 Digite o valor total do bônus:")

        elif etapa == "valor":
            try:
                ctx.user_data["novo_codigo_valor"] = float(texto.strip())
            except ValueError:
                return await update.message.reply_text("⚠️ Valor inválido. Digite um número.")
            ctx.user_data["etapa_codigo"] = "usuarios"
            return await update.message.reply_text("👥 Digite o número máximo de usuários:")

        elif etapa == "usuarios":
            try:
                ctx.user_data["novo_codigo_usuarios"] = int(texto.strip())
            except ValueError:
                return await update.message.reply_text("⚠️ Número inválido. Digite um inteiro.")
            ctx.user_data["etapa_codigo"] = "expiracao"
            return await update.message.reply_text("⏳ Digite o tempo de expiração em minutos (0 = sem expiração):")

        elif etapa == "expiracao":
            try:
                expira_em_min = int(texto.strip())
            except ValueError:
                return await update.message.reply_text("⚠️ Número inválido. Digite um inteiro.")

            # 🔹 CRIAR E SALVAR CÓDIGO DIRETAMENTE
            codigo = ctx.user_data["novo_codigo_nome"]
            valor_total = ctx.user_data["novo_codigo_valor"]
            max_usuarios = ctx.user_data["novo_codigo_usuarios"]

            expira_em = None
            if expira_em_min > 0:
                expira_em = datetime.now() + timedelta(minutes=expira_em_min)

            gerenciador_codigos.codigos_bonus[codigo] = {
                "valor_total": valor_total,
                "max_usuarios": max_usuarios,
                "valor_restante": valor_total,
                "usuarios_restantes": max_usuarios,
                "duracao_minutos": expira_em_min,
                "expira_em": expira_em.isoformat() if expira_em else None,
                "criado_por": int(uid),
                "criado_em": datetime.now().isoformat(),
                "ativo": True,
                "resgatado_por": [],
                "motivo_expiracao": None,
            }

            gerenciador_codigos.codigos_resgatados[codigo] = []
            salvar_codigos()  # 🔹 SALVA NO JSON

            # limpa flags
            ctx.user_data.pop("admin_criando_codigo", None)
            ctx.user_data.pop("etapa_codigo", None)

            return await update.message.reply_text(
                f"✅ Código criado com sucesso!\n\n"
                f"📛 Código: {codigo}\n"
                f"💰 Valor: {valor_total}\n"
                f"👥 Máx. usuários: {max_usuarios}\n"
                f"⏳ Expira em: {expira_em_min} minutos"
            )

    # 🎁 USUÁRIO DIGITANDO CÓDIGO (resgate)
    elif ctx.user_data.get("esperando_resgate_codigo"):
        codigo = texto.upper()
        ctx.user_data.pop("esperando_resgate_codigo")

        # 👉 Chama a função original que já processa tudo
        resposta = gerenciador_codigos.resgatar_codigo_bonus(int(uid), codigo)
        salvar_codigos()  # 🔹 SALVA JSON após resgatar

        return await update.message.reply_text(resposta["mensagem"])

    # 9️⃣ Nenhuma operação ativa
    else:
        return await update.message.reply_text("⚠️ Não há nenhuma operação pendente no momento.")

@checa_banido
async def ajuda_indicacao_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # 🗑️ Remove a mensagem anterior
    try:
        await query.delete_message()
    except:
        pass  

    usuarios = carregar_json(USERS_FILE)
    uid = str(update.effective_user.id)
    user = usuarios.get(uid)
    if not user:
        keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda")]]
        return await query.message.reply_text(
            "❌ Você não está registrado. Use /start para começar!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # 🔹 Link de convite
    link_share = (
        f"https://t.me/share/url?"
        f"&text=🚀 Descubra a Agrotech!%0A%0A"
        f"🌟 Uma plataforma segura, transparente e confiável para crescer seu dinheiro.%0A"
        f"💎 Eu já ganhei e saquei várias vezes — pagamentos rápidos e garantidos.%0A%0A"
        f"👉 Junte-se à Agrotech: https://t.me/AgrotechFund_bot?start={uid}"
    )

    # --- Contagem de indicados ---
    nivel1 = [u for u in usuarios.values() if u.get("indicador") == uid]
    nivel2 = [u for u in usuarios.values() if usuarios.get(u.get("indicador", ""), {}).get("indicador") == uid]
    nivel3 = [
        u for u in usuarios.values()
        if usuarios.get(usuarios.get(u.get("indicador", ""), {}).get("indicador", ""), {}).get("indicador") == uid
    ]

    comissoes = user.get("comissoes", {"1": 0, "2": 0, "3": 0})
    com1 = comissoes.get("1", 0)
    com2 = comissoes.get("2", 0)
    com3 = comissoes.get("3", 0)
    total_com = com1 + com2 + com3

    msg = (
        f"📣 Olá, <b>{user.get('nome','Usuário')}</b>!\n\n"
        f"<i>🔗 Seu link de convite pessoal:</i>\n https://t.me/AgrotechFund_bot?start={uid}\n\n"
        f"👥 Seus indicados:\n"
        f"• 🥇 Nível 1: {len(nivel1)} pessoas — 7% — {com1:.2f} MZN\n"
        f"• 🥈 Nível 2: {len(nivel2)} pessoas — 3% — {com2:.2f} MZN\n"
        f"• 🥉 Nível 3: {len(nivel3)} pessoas — 1% — {com3:.2f} MZN\n\n"
        f"💵 <b>Total ganho em comissões: {total_com:.2f} MZN</b>\n\n"
        f"🤝 Continue convidando e aumente seus ganhos!\n"
        f"🔗 <a href='{link_share}'>Convide agora seus amigos</a>"
    )

    keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda")]]
    await query.message.reply_text(
        msg,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def enviar_relatorio_periodico(app):
    """
    Envia relatório semanal e mensal automaticamente para o grupo admin.
    """

    usuarios = carregar_json(USERS_FILE)
    hoje = datetime.utcnow().date()
    grupo_admin = -1001234567890  # ID do grupo admin

    total_pago_semana = 0.0
    total_pago_mes = 0.0
    total_usuarios_semana = 0
    total_usuarios_mes = 0
    ranking_semana = []
    ranking_mes = []

    inicio_semana = hoje - timedelta(days=7)
    inicio_mes = hoje.replace(day=1)

    for uid, user in usuarios.items():
        planos = user.get("planos", []) + user.get("planos_expirados", [])
        ganhos_semana = 0.0
        ganhos_mes = 0.0

        for plano in planos:
            last_coleta_str = user.get("last_coleta_date")
            if not last_coleta_str:
                continue
            try:
                last_coleta = datetime.strptime(last_coleta_str, "%Y-%m-%d").date()
            except:
                continue

            if last_coleta >= inicio_semana:
                ganhos_semana += plano.get("valor", 0) * plano.get("percent", 0)
            if last_coleta >= inicio_mes:
                ganhos_mes += plano.get("valor", 0) * plano.get("percent", 0)

        if ganhos_semana > 0:
            total_pago_semana += ganhos_semana
            total_usuarios_semana += 1
            ranking_semana.append((user.get("nome", "Usuário"), ganhos_semana))

        if ganhos_mes > 0:
            total_pago_mes += ganhos_mes
            total_usuarios_mes += 1
            ranking_mes.append((user.get("nome", "Usuário"), ganhos_mes))

    ranking_semana.sort(key=lambda x: x[1], reverse=True)
    ranking_mes.sort(key=lambda x: x[1], reverse=True)

    top_semana = ranking_semana[:10]
    top_mes = ranking_mes[:10]

    texto_semana = "\n".join([f"{i+1}. 🏅 {nome}: *{valor:.2f} MZN*" for i, (nome, valor) in enumerate(top_semana)]) \
        if top_semana else "Nenhum lucro registrado nesta semana."
    texto_mes = "\n".join([f"{i+1}. 🏅 {nome}: *{valor:.2f} MZN*" for i, (nome, valor) in enumerate(top_mes)]) \
        if top_mes else "Nenhum lucro registrado neste mês."

    msg = (
        f"📊 *Relatório Periódico — {hoje.strftime('%d/%m/%Y')}*\n\n"
        f"🗓️ *Última Semana:*\n"
        f"👥 Usuários que coletaram: *{total_usuarios_semana}*\n"
        f"💰 Total pago: *{total_pago_semana:.2f} MZN*\n"
        f"🏆 TOP 10 da semana:\n{texto_semana}\n\n"
        f"🗓️ *Este Mês:*\n"
        f"👥 Usuários que coletaram: *{total_usuarios_mes}*\n"
        f"💰 Total pago: *{total_pago_mes:.2f} MZN*\n"
        f"🏆 TOP 10 do mês:\n{texto_mes}\n\n"
        f"✅ Sistema: Coleta automática — Relatório enviado ao grupo admin 🚀"
    )

    try:
        await app.bot.send_message(chat_id=grupo_admin, text=msg, parse_mode=ParseMode.MARKDOWN)
        print("📨 Relatório semanal e mensal enviado ao grupo admin com sucesso.")
    except Exception as e:
        print(f"⚠️ Erro ao enviar relatório periódico: {e}")

import asyncio
from datetime import datetime

# 🕛 Função principal automática (corrigida)
async def coleta_automatica(app):
    print(f"[{datetime.now()}] ⏰ Iniciando coleta automática diária...")

    usuarios = carregar_json(USERS_FILE)
    alterado = False
    total_pago_dia = 0.0
    total_usuarios_coletaram = 0
    total_expirados = 0
    ranking_dia = []

    hoje = datetime.utcnow().date()

    for uid, user in usuarios.items():
        planos = user.get("planos", [])
        ganhos_total = 0.0
        novos_expirados = []

        ultima_coleta_str = user.get("last_coleta_date")
        if ultima_coleta_str:
            try:
                ultima_coleta = datetime.strptime(ultima_coleta_str, "%Y-%m-%d").date()
                if ultima_coleta == hoje:
                    # ⚠️ Já coletou manualmente hoje → pula esse usuário
                    continue
            except:
                pass

        for plano in planos:
            try:
                valor = float(plano.get("valor", 0))
                percent = float(plano.get("percent", 0))
                ganhos_hoje = round(valor * percent, 2)
                ganhos_total += ganhos_hoje

                plano["dias_recebidos"] = plano.get("dias_recebidos", 0) + 1
                duracao = plano.get("duracao", 30)  # padrão 30 dias

                if plano["dias_recebidos"] >= duracao:
                    exp = user.get("planos_expirados", [])
                    exp.append(plano)
                    user["planos_expirados"] = exp
                    novos_expirados.append(plano)
                    total_expirados += 1

            except Exception as e:
                print(f"⚠️ Erro ao processar plano de {uid}: {e}")

        # Remove planos expirados
        for e in novos_expirados:
            if e in planos:
                planos.remove(e)

        # Atualiza saldo e ganhos totais
        if ganhos_total > 0:
            user["saldo"] = user.get("saldo", 0) + ganhos_total
            user["lucro_pago"] = user.get("lucro_pago", 0) + ganhos_total
            user["last_coleta_date"] = str(hoje)
            alterado = True
            total_pago_dia += ganhos_total
            total_usuarios_coletaram += 1
            ranking_dia.append((user.get("nome", "Usuário"), ganhos_total))

            # Envia mensagem ao user
            try:
                await app.bot.send_message(
                    chat_id=int(uid),
                    text=(
                        f"🌞 *Bom dia, {user.get('nome', 'investidor(a)')}!*\n\n"
                        f"💸 Sua coleta automática foi realizada com sucesso!\n"
                        f"Você recebeu *{ganhos_total:.2f} MZN* hoje. 💎\n\n"
                        f"Continue crescendo com a *Central de Renda Digital 💎* 🚀"
                    ),
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                print(f"📭 Não foi possível enviar mensagem a {uid}: {e}")

    # Salva alterações se houver
    if alterado:
        salvar_json(USERS_FILE, usuarios)
        print("✅ Coleta automática concluída e usuários atualizados com sucesso.")
    else:
        print("ℹ️ Nenhum lucro gerado hoje (sem planos ativos ou já coletaram).")

    # 📊 Relatório para grupo admin
    try:
        grupo_admin = -1001234567890  # substitui pelo teu grupo admin ID
        hora = datetime.now().strftime("%H:%M")
        data = datetime.now().strftime("%d/%m/%Y")

        ranking_dia.sort(key=lambda x: x[1], reverse=True)
        top = ranking_dia[:10]
        ranking_texto = "\n".join(
            [f"{i+1}. 🏅 {nome}: *{valor:.2f} MZN*" for i, (nome, valor) in enumerate(top)]
        ) if top else "Nenhum lucro registrado hoje."

        msg_relatorio = (
            f"📊 *Relatório Automático da Coleta — {data}*\n\n"
            f"👥 Usuários que coletaram: *{total_usuarios_coletaram}*\n"
            f"💰 Total pago no dia: *{total_pago_dia:.2f} MZN*\n"
            f"📕 Planos expirados hoje: *{total_expirados}*\n"
            f"🕛 Horário da coleta: *{hora}h*\n\n"
            f"🏆 *TOP 10 investidores do dia:*\n{ranking_texto}\n\n"
            f"✅ Sistema: *Coleta automática concluída com sucesso!* 🚀"
        )

        await app.bot.send_message(
            chat_id=grupo_admin,
            text=msg_relatorio,
            parse_mode=ParseMode.MARKDOWN
        )
        print("📨 Relatório com ranking enviado ao grupo admin com sucesso.")
    except Exception as e:
        print(f"⚠️ Erro ao enviar relatório admin: {e}")

@checa_banido
async def ajuda_coletar_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # 🧹 Apaga a mensagem anterior
    try:
        await query.delete_message()
    except:
        pass  

    usuarios = carregar_json(USERS_FILE)
    uid = str(update.effective_user.id)
    user = usuarios.get(uid)

    # ❌ Usuário não existe
    if not user:
        keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda")]]
        return await query.message.reply_text(
            "❌ Você ainda não possui conta. Use /start para criar sua conta!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ⛔ Usuário banido/bloqueado
    if user.get("banido", False):
        keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda")]]
        return await query.message.reply_text(
            "⛔ Você está banido ou bloqueado. Não pode coletar lucros até ser desbanido pelo suporte.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # 📦 Verifica se já comprou algum plano
    if not user.get("planos", []) and not user.get("planos_expirados", []):
        keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda")]]
        return await query.message.reply_text(
            "❌ Você precisa ter comprado pelo menos um plano antes de coletar lucros.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    hoje = datetime.utcnow().date()
    ultima_coleta = user.get("last_coleta_date", "Nunca")

    # ⏳ Impede coleta mais de uma vez no mesmo dia
    if str(hoje) == ultima_coleta:
        keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda")]]
        return await query.message.reply_text(
            "⏳ Você já coletou hoje!\nVolte amanhã para coletar mais lucros. ✅",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    total = 0
    detalhes = "📈 *Coleta de lucros:*\n\n"

    planos_ativos = []
    planos_expirados = user.get("planos_expirados", [])

    for p in user.get("planos", []):
        nome = p.get("nome", "Plano sem nome")
        valor = p.get("valor", 0)
        percent = p.get("percent", 0)

        try:
            data_compra = parse_data(p.get("data_compra"))
            data_expiracao = parse_data(p.get("data_expiracao"))
        except:
            continue  

        # 🔧 Garante os campos extras
        if "dias_recebidos" not in p:
            p["dias_recebidos"] = 0
        if "duracao" not in p:
            p["duracao"] = (data_expiracao.date() - data_compra.date()).days

        dias_recebidos = p["dias_recebidos"]
        duracao = p["duracao"]

        # 🔹 Se comprou hoje → começa só amanhã
        if data_compra.date() == hoje:
            detalhes += f"🆕 {nome}:\n➜ Comprado hoje, começa a gerar amanhã ⏳\n\n"
            planos_ativos.append(p)
            continue

        # ⚖️ Verifica se já completou todos os dias
        if dias_recebidos >= duracao:
            detalhes += f"✅ {nome}:\n➜ Plano concluído! Recebeu todos os {duracao} dias.\n\n"
            planos_expirados.append(p)
            continue

        # 📆 Se hoje é a data de expiração original
        if hoje == data_expiracao.date():
            faltando = duracao - dias_recebidos
            if faltando > 0:
                # Estende a expiração
                data_expiracao = data_expiracao + timedelta(days=faltando)
                p["data_expiracao"] = str(data_expiracao.date())

                lucro = valor * percent
                total += lucro
                p["dias_recebidos"] += 1

                detalhes += (
                    f"⚠️ {nome}:\n"
                    f"➜ Você esqueceu de coletar {faltando} dia(s).\n"
                    f"🗓️ Estendemos sua expiração até *{data_expiracao.date()}* para que não perca nada! ✅\n"
                    f"💰 Lucro hoje: {lucro:.2f} MZN\n"
                    f"📅 Dias recebidos: {p['dias_recebidos']}/{duracao}\n\n"
                )

                # Se atingiu a duração aqui → último dia
                if p["dias_recebidos"] >= duracao:
                    detalhes += (
                        f"🎉 Parabéns! Você completou todos os {duracao} dias do plano *{nome}*.\n"
                        f"O plano foi concluído com sucesso e agora está finalizado. ✅\n\n"
                    )
                    planos_expirados.append(p)
                else:
                    planos_ativos.append(p)
                continue
            else:
                planos_expirados.append(p)
                continue

        # ⏳ Se ainda está dentro do prazo
        if hoje < parse_data(p["data_expiracao"]).date():
            lucro = valor * percent
            total += lucro
            p["dias_recebidos"] += 1
            faltando = duracao - p["dias_recebidos"]

            # Se for o último dia
            if p["dias_recebidos"] >= duracao:
                detalhes += (
                    f"🎉 {nome}:\n"
                    f"💰 Último lucro recebido: {lucro:.2f} MZN\n"
                    f"📅 Dias recebidos: {p['dias_recebidos']}/{duracao}\n"
                    f"✅ Parabéns! Você completou todos os {duracao} dias do plano.\n\n"
                )
                planos_expirados.append(p)

            # Se faltar 1 ou 2 dias → alerta especial
            elif faltando == 2:
                detalhes += (
                    f"🟡 {nome}:\n"
                    f"💰 Lucro hoje: {lucro:.2f} MZN\n"
                    f"📅 Dias recebidos: {p['dias_recebidos']}/{duracao}\n"
                    f"⚠️ Atenção: faltam apenas *2 dias* para o plano expirar!\n"
                    f"Não esqueça de coletar seus lucros diários. ⏳\n\n"
                )
                planos_ativos.append(p)
            elif faltando == 1:
                detalhes += (
                    f"🔴 {nome}:\n"
                    f"💰 Lucro hoje: {lucro:.2f} MZN\n"
                    f"📅 Dias recebidos: {p['dias_recebidos']}/{duracao}\n"
                    f"🚨 Última chance: faltam apenas *1 dia* para o plano expirar!\n"
                    f"Não deixe de coletar amanhã para não perder seu contrato. ⚡\n\n"
                )
                planos_ativos.append(p)

            # Caso normal
            else:
                detalhes += (
                    f"{nome}:\n"
                    f"💰 Lucro hoje: {lucro:.2f} MZN\n"
                    f"📅 Dias recebidos: {p['dias_recebidos']}/{duracao}\n"
                    f"🗓️ Expira em: {p['data_expiracao']}\n"
                    f"⏳ Dias restantes: {faltando}\n\n"
                )
                planos_ativos.append(p)

        else:
            # Já passou até do prazo estendido
            detalhes += f"🔴 {nome}: Plano expirado.\n\n"
            planos_expirados.append(p)

    # 🚫 Nenhum lucro disponível hoje
    if total == 0:
        keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda")]]
        return await query.message.reply_text(
            "❌ Não há lucros para coletar hoje.\nSe comprou um plano hoje, só poderá coletar a partir de amanhã! ✅",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ✅ Atualiza dados do usuário
    user["planos"] = planos_ativos
    user["planos_expirados"] = planos_expirados
    user["saldo"] = user.get("saldo", 0) + total
    user["last_coleta_date"] = str(hoje)
    user["lucro_pago"] = user.get("lucro_pago", 0) + total

    salvar_json(USERS_FILE, usuarios)

    # 📊 Resumo final
    detalhes += (
        f"💰 *Total coletado hoje:* {total:.2f} MZN\n"
        f"💵 *Novo saldo:* {user['saldo']:.2f} MZN\n"
        f"📊 *Total já coletado:* {user['lucro_pago']:.2f} MZN\n"
        f"🗓️ *Próxima coleta:* Amanhã ✅"
    )
    
    # 🎉 Se o usuário não tiver mais planos ativos
    if not user["planos"]:
        detalhes += (
            "\n\n🎉 *Parabéns!* Você completou todos os seus planos ativos com sucesso.\n\n"
            "Foi um prazer tê-lo conosco durante este período, e esperamos que tenha aproveitado os lucros! 💰🚀\n\n"
            "👉 Se deseja continuar crescendo e ganhar ainda mais, convidamos você a adquirir um *novo plano*. "
            "Assim poderá multiplicar seus ganhos e seguir aproveitando todas as vantagens que oferecemos. ✅\n\n"
            "Estamos sempre prontos para ajudá-lo a alcançar novos resultados! 🤝"
        )

    keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda")]]
    await query.message.reply_text(
        detalhes,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import json

USERS_FILE = "usuarios.json"
ADMIN_ID = 8182769178

# Carregar e salvar JSON
def carregar_json(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def salvar_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- MENU DE BANIMENTO/BLOQUEIO ---
async def admin_ban_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # Verifica se é admin
    if update.effective_user.id != ADMIN_ID:
        # Se for mensagem normal
        if update.message:
            return await update.message.reply_text("❌ Apenas o admin pode usar este comando.")
        # Se for botão
        elif update.callback_query:
            return await update.callback_query.answer("❌ Apenas o admin pode usar este comando.", show_alert=True)

    # Teclado de opções
    keyboard = [
        [InlineKeyboardButton("🚫 Banir usuário", callback_data="banir")],
        [InlineKeyboardButton("🔒 Bloquear usuário", callback_data="bloquear")],
        [InlineKeyboardButton("✅ Desbanir usuário", callback_data="desbanir")],
        [InlineKeyboardButton("🔓 Desbloquear usuário", callback_data="desbloquear")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda")]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    # Se o admin chamou por comando (/algumacoisa)
    if update.message:
        await update.message.reply_text(
            "⚠️ *Menu de Banimento/Bloqueio*:\nEscolha uma opção:",
            parse_mode="Markdown",
            reply_markup=markup
        )
    # Se o admin chamou clicando em botão
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "⚠️ *Menu de Banimento/Bloqueio*:\nEscolha uma opção:",
            parse_mode="Markdown",
            reply_markup=markup
        )

# --- CALLBACK PARA BANIR ---
async def admin_banir_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await pedir_id(update, ctx, "id_banir")

# --- CALLBACK PARA DESBANIR ---
async def admin_desbanir_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await pedir_id(update, ctx, "id_desbanir")

# --- CALLBACK PARA BLOQUEAR ---
async def admin_bloquear_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await pedir_id(update, ctx, "id_bloquear")

# --- CALLBACK PARA DESBLOQUEAR ---
async def admin_desbloquear_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await pedir_id(update, ctx, "id_desbloquear")

# --- PEDIR ID PARA AÇÃO DE BAN/LOCK ---
async def pedir_id(update: Update, ctx: ContextTypes.DEFAULT_TYPE, acao: str):
    query = update.callback_query
    await query.answer()
    try: 
        await query.message.delete()
    except: 
        pass

    # Define a chave certa no user_data
    ctx.user_data[f"esperando_{acao}"] = True

    mensagens = {
        "id_banir": "Digite o ID do usuário que deseja banir:",
        "id_desbanir": "Digite o ID do usuário que deseja desbanir:",
        "id_bloquear": "Digite o ID do usuário que deseja bloquear:",
        "id_desbloquear": "Digite o ID do usuário que deseja desbloquear:"
    }

    await query.message.reply_text(mensagens[acao])


# --- PROCESSAR BANIMENTO/BLOQUEIO ---
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Função auxiliar para gerar botões de regras e suporte
def botoes_info():
    keyboard = [
        [
            InlineKeyboardButton("📖 Regras", url="https://t.me/seu_grupo_regras"),
            InlineKeyboardButton("📞 Suporte", url="https://t.me/Agroinvestlda")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def processar_ban_desban(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid_usuario = text  # ID digitado pelo admin
    admin_id = update.effective_user.id

    try:
        await update.message.delete()
    except:
        pass

    user_keys = [
        "esperando_id_banir",
        "esperando_id_desbanir",
        "esperando_id_bloquear",
        "esperando_id_desbloquear"
    ]

    acao = None
    for k in user_keys:
        if ctx.user_data.get(k):
            acao = k
            break

    if not acao:
        return

    usuarios = carregar_json(USERS_FILE)
    user = usuarios.get(uid_usuario)

    if user is None:
        await update.message.reply_text(f"❌ O usuário com ID `{uid_usuario}` não existe.", parse_mode="Markdown")
        ctx.user_data[acao] = False
        return

    # BANIR
    if acao == "esperando_id_banir":
        user["banido"] = True
        usuarios[uid_usuario] = user
        salvar_json(USERS_FILE, usuarios)
        salvar_log(admin_id, "Banido", uid_usuario)

        await update.message.reply_text(f"🚫 Usuário {uid_usuario} ({user.get('nome', 'Sem Nome')}) banido com sucesso!")
        try:
            await ctx.bot.send_message(
                chat_id=uid_usuario,
                text=(
                    "🚫 *Conta Banida*\n\n"
                    "Sua conta foi *banida* por violar as regras.\n\n"
                    "👉 Se repetir a infração, o banimento será *permanente*.\n\n"
                    "Leia as regras e entre em contato com o suporte se achar que houve um engano."
                ),
                reply_markup=botoes_info(),
                parse_mode="Markdown"
            )
        except:
            pass
        ctx.user_data[acao] = False

    # DESBANIR
    elif acao == "esperando_id_desbanir":
        if user.get("banido", False):
            user["banido"] = False
            usuarios[uid_usuario] = user
            salvar_json(USERS_FILE, usuarios)
            salvar_log(admin_id, "Desbanido", uid_usuario)

            await update.message.reply_text(f"✅ Usuário {uid_usuario} ({user.get('nome', 'Sem Nome')}) desbanido com sucesso!")
            try:
                await ctx.bot.send_message(
                    chat_id=uid_usuario,
                    text=(
                        "🎉 *Conta Desbanida*\n\n"
                        "Seja bem-vindo de volta 💙\n\n"
                        "⚠️ Atenção: repetir ações que causaram banimento pode resultar em banimento definitivo."
                    ),
                    reply_markup=botoes_info(),
                    parse_mode="Markdown"
                )
            except:
                pass
        else:
            await update.message.reply_text(f"❌ Usuário {uid_usuario} não estava banido.")
        ctx.user_data[acao] = False

    # BLOQUEAR
    elif acao == "esperando_id_bloquear":
        user["bloqueado"] = True
        usuarios[uid_usuario] = user
        salvar_json(USERS_FILE, usuarios)
        salvar_log(admin_id, "Bloqueado", uid_usuario)

        await update.message.reply_text(f"🔒 Usuário {uid_usuario} ({user.get('nome', 'Sem Nome')}) bloqueado com sucesso!")
        try:
            await ctx.bot.send_message(
                chat_id=uid_usuario,
                text=(
                    "🔒 *Conta Bloqueada Temporariamente*\n\n"
                    "Sua conta foi *bloqueada* por comportamento inadequado.\n\n"
                    "👉 Repetir ações inadequadas poderá resultar em *banimento permanente*."
                ),
                reply_markup=botoes_info(),
                parse_mode="Markdown"
            )
        except:
            pass
        ctx.user_data[acao] = False

    # DESBLOQUEAR
    elif acao == "esperando_id_desbloquear":
        if user.get("bloqueado", False):
            user["bloqueado"] = False
            usuarios[uid_usuario] = user
            salvar_json(USERS_FILE, usuarios)
            salvar_log(admin_id, "Desbloqueado", uid_usuario)

            await update.message.reply_text(f"🔓 Usuário {uid_usuario} ({user.get('nome', 'Sem Nome')}) desbloqueado com sucesso!")
            try:
                await ctx.bot.send_message(
                    chat_id=uid_usuario,
                    text=(
                        "🚀 *Conta Desbloqueada*\n\n"
                        "Agora você pode usar todos os recursos novamente 🎉\n\n"
                        "⚠️ Repetir comportamento inadequado poderá levar a banimento permanente."
                    ),
                    reply_markup=botoes_info(),
                    parse_mode="Markdown"
                )
            except:
                pass
        else:
            await update.message.reply_text(f"❌ Usuário {uid_usuario} não estava bloqueado.")
        ctx.user_data[acao] = False

#BROQUEADO
def checa_bloqueado(func):
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        uid = str(update.effective_user.id)
        usuarios = carregar_json(USERS_FILE)
        user = usuarios.get(uid)
        if user and user.get("bloqueado", False):
            try: 
                if update.message: await update.message.delete()
                if update.callback_query: await update.callback_query.message.delete()
            except: pass
            return await (update.message or update.callback_query.message).reply_text(
                "⚠️ Você está bloqueado e não pode usar esta função."
            )
        return await func(update, ctx, *args, **kwargs)
    return wrapper


# ✅ Relatório diário revisado e robusto
async def enviar_relatorio_diario(app):
    agora = datetime.now()
    hoje = agora.strftime("%d/%m/%Y")

    total_usuarios = len(usuarios)
    novos = sum(1 for u in usuarios.values() if u.get("data_criacao") == hoje)

    total_saldo = 0
    total_planos = 0
    ganhos_futuros = 0
    ganhos_pagos = 0

    dep_hoje = {"total": 0, "aprovado": 0, "recusado": 0, "pendente": 0, "valor_total": 0, "detalhes": []}
    saq_hoje = {"total": 0, "aprovado": 0, "recusado": 0, "pendente": 0, "valor_total": 0, "detalhes": []}

    pend_hoje_dep = {"total": 0, "valor_total": 0, "detalhes": []}
    pend_hoje_saq = {"total": 0, "valor_total": 0, "detalhes": []}

    pend_dep = {"total": 0, "valor_total": 0}
    pend_saq = {"total": 0, "valor_total": 0}

    total_dep_geral = {"qtd": 0, "valor": 0}
    total_saq_geral = {"qtd": 0, "valor": 0}

    for u in usuarios.values():
        total_saldo += u.get("saldo", 0)
        total_planos += len(u.get("planos", []))

        # --- Ganhos futuros calculados dinamicamente ---
        for p in u.get("planos", []):
            try:
                data_exp = datetime.strptime(p.get("data_expiracao", ""), "%d/%m/%Y")
                hoje_dt = datetime.now()
                dias_restantes = max((data_exp - hoje_dt).days, 0)
                investido = p.get("investido", 0)
                percent = p.get("percent", 0)
                ganho_futuro_plano = round(investido * percent * dias_restantes, 2)
                ganhos_futuros += ganho_futuro_plano
            except:
                continue

        # --- Histórico de depósitos e saques ---
        for item in u.get("historico", []):
            data_str = item.get("data", "")
            try:
                data_item = datetime.strptime(data_str, "%d/%m/%Y %H:%M")
            except ValueError:
                try:
                    data_item = datetime.strptime(data_str, "%d/%m/%Y")
                except ValueError:
                    continue
            data_item_str = data_item.strftime("%d/%m/%Y %H:%M")

            tipo = item.get("tipo", "")
            status = item.get("status", "pendente")
            valor = float(item.get("valor", 0))
            valor_liq = float(item.get("valor_liquido", valor))

            # Totais gerais
            if tipo == "deposito":
                total_dep_geral["qtd"] += 1
                total_dep_geral["valor"] += valor
            elif tipo == "saque":
                total_saq_geral["qtd"] += 1
                total_saq_geral["valor"] += valor_liq

            # Depósitos do dia
            if tipo == "deposito" and data_item.strftime("%d/%m/%Y") == hoje:
                dep_hoje["total"] += 1
                dep_hoje["valor_total"] += valor
                dep_hoje["detalhes"].append(f"💰 {valor:.2f} MZN | Status: {status} | {data_item_str}")
                if status == "aprovado":
                    dep_hoje["aprovado"] += 1
                elif status == "recusado":
                    dep_hoje["recusado"] += 1
                elif status == "pendente":
                    dep_hoje["pendente"] += 1
                    pend_hoje_dep["total"] += 1
                    pend_hoje_dep["valor_total"] += valor
                    pend_hoje_dep["detalhes"].append(f"💰 {valor:.2f} MZN | Status: {status} | {data_item_str}")

            # Saques do dia
            if tipo == "saque" and data_item.strftime("%d/%m/%Y") == hoje:
                saq_hoje["total"] += 1
                saq_hoje["valor_total"] += valor_liq
                saq_hoje["detalhes"].append(f"💸 {valor_liq:.2f} MZN | Status: {status} | {data_item_str}")
                if status == "aprovado":
                    saq_hoje["aprovado"] += 1
                    ganhos_pagos += valor_liq
                elif status == "recusado":
                    saq_hoje["recusado"] += 1
                elif status == "pendente":
                    saq_hoje["pendente"] += 1
                    pend_hoje_saq["total"] += 1
                    pend_hoje_saq["valor_total"] += valor_liq
                    pend_hoje_saq["detalhes"].append(f"💸 {valor_liq:.2f} MZN | Status: {status} | {data_item_str}")

            # Pendentes gerais
            if status == "pendente":
                if tipo == "deposito":
                    pend_dep["total"] += 1
                    pend_dep["valor_total"] += valor
                elif tipo == "saque":
                    pend_saq["total"] += 1
                    pend_saq["valor_total"] += valor_liq

    # --- Montar texto do relatório ---
    texto = (
        f"📊 **Relatório Diário - {hoje}**\n\n"
        f"👤 Novos usuários: {novos}\n"
        f"👥 Total de usuários: {total_usuarios}\n"
        f"💰 Saldo total dos usuários: {total_saldo:.2f} MZN\n"
        f"📦 Planos ativos: {total_planos}\n\n"
        f"🏦 **Depósitos hoje:** {dep_hoje['total']} "
        f"✅ {dep_hoje['aprovado']} | ❌ {dep_hoje['recusado']} | ⏳ {dep_hoje['pendente']} "
        f"(Total valor: {dep_hoje['valor_total']:.2f} MZN)\n"
    )
    texto += "📋 Detalhes de hoje:\n" + ("\n".join(dep_hoje["detalhes"]) if dep_hoje["detalhes"] else "Nenhum depósito hoje") + "\n"

    texto += (
        f"🏧 **Saques hoje:** {saq_hoje['total']} "
        f"✅ {saq_hoje['aprovado']} | ❌ {saq_hoje['recusado']} | ⏳ {saq_hoje['pendente']} "
        f"(Total valor: {saq_hoje['valor_total']:.2f} MZN)\n"
    )
    texto += "📋 Detalhes de hoje:\n" + ("\n".join(saq_hoje["detalhes"]) if saq_hoje["detalhes"] else "Nenhum saque hoje") + "\n"

    # Pendentes de hoje
    texto += "\n⏳ **Pendentes de hoje**\n"
    texto += f"💰 Depósitos pendentes: {pend_hoje_dep['total']} | {pend_hoje_dep['valor_total']:.2f} MZN\n"
    if pend_hoje_dep["detalhes"]:
        texto += "\n".join(pend_hoje_dep["detalhes"]) + "\n"
    texto += f"💸 Saques pendentes: {pend_hoje_saq['total']} | {pend_hoje_saq['valor_total']:.2f} MZN\n"
    if pend_hoje_saq["detalhes"]:
        texto += "\n".join(pend_hoje_saq["detalhes"]) + "\n"

    texto += (
        f"\n💸 **Ganhos pagos (saques aprovados):** {ganhos_pagos:.2f} MZN\n"
        f"💼 **Ganhos futuros (planos):** {ganhos_futuros:.2f} MZN\n\n"
        f"⏳ **Pendentes totais:**\n"
        f"Depósitos: {pend_dep['total']} | {pend_dep['valor_total']:.2f} MZN\n"
        f"Saques: {pend_saq['total']} | {pend_saq['valor_total']:.2f} MZN\n\n"
        f"💰 **Depósitos totais de todos usuários:** {total_dep_geral['qtd']} depósitos | {total_dep_geral['valor']:.2f} MZN\n"
        f"🏧 **Saques totais de todos usuários:** {total_saq_geral['qtd']} saques | {total_saq_geral['valor']:.2f} MZN"
    )

    await app.bot.send_message(chat_id=ADMIN_ID, text=texto, parse_mode=ParseMode.MARKDOWN)

# --- LEMBRETE DIÁRIO DE COLETA ---
async def enviar_lembrete_diario(app):
    usuarios = carregar_json(USERS_FILE)
    hoje = datetime.now()

    for uid, user in usuarios.items():
        planos = user.get("planos", [])
        if not planos:
            continue  

        # Verifica se existe pelo menos 1 plano ativo
        ativo = False
        for p in planos:
            data_expiracao = parse_data(p.get("data_expiracao", hoje.isoformat()))
            if hoje < data_expiracao:
                ativo = True
                break

        if ativo:
            try:
                # 🔘 Botão de COLETAR funcional (callback_data correto)
                keyboard = [[InlineKeyboardButton("💰 Coletar Ganhos", callback_data="coletar_lucro")]]
                markup = InlineKeyboardMarkup(keyboard)

                # Segunda-feira
                if hoje.weekday() == 0:
                    texto = (
                        "🌟 *Feliz Segunda-feira!* 🌟\n\n"
                        "Um novo começo chegou, cheio de oportunidades e energia positiva. 💪✨\n\n"
                        "Não deixe de aproveitar e coletar seus ganhos de hoje para já começar a semana no caminho certo. 🚀\n\n"
                        "➡️ Clique abaixo e continue firme no seu progresso diário!"
                    )

                # Sábado ou domingo
                elif hoje.weekday() in [5, 6]:
                    texto = (
                        "☀️ *Bom dia!* ☀️\n\n"
                        "Fim de semana é tempo de recarregar as energias e celebrar cada conquista. 🎉\n\n"
                        "Aproveite para garantir também os seus ganhos de hoje e curtir ainda mais o seu descanso. 🍹✨\n\n"
                        "➡️ Clique no botão abaixo e colete agora mesmo!"
                    )

                # Terça a sexta
                else:
                    texto = (
                        "🌟 *Bom dia!* 🌟\n\n"
                        "Estamos felizes por caminhar juntos com você todos os dias. 🙌\n\n"
                        "Lembre-se de coletar seus ganhos de hoje e siga aproveitando cada etapa dessa jornada. 💚\n\n"
                        "➡️ Clique no botão abaixo para garantir o lucro diário."
                    )

                await app.bot.send_message(
                    chat_id=uid,
                    text=texto,
                    parse_mode="Markdown",
                    reply_markup=markup
                )
            except Exception as e:
                print(f"Erro ao enviar lembrete para {uid}: {e}")

@checa_banido
async def ajuda_historico_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    
    ITENS_POR_PAGINA = 5 

    usuarios = carregar_json("usuarios.json")
    user_data = usuarios.get(user_id, {})

    # --- CORREÇÃO 1: VERIFICAÇÃO INICIAL DO HISTÓRICO ---
    # Garante que `historico_completo` seja SEMPRE uma lista, prevenindo o erro 'dict has no attribute sort'
    historico_bruto = user_data.get("historico", [])
    if isinstance(historico_bruto, dict):
        # Se os dados estiverem errados (um dicionário), transforma numa lista com esse item
        historico_completo = [historico_bruto]
    elif isinstance(historico_bruto, list):
        # Se os dados estiverem corretos (uma lista), apenas usa-os
        historico_completo = historico_bruto
    else:
        # Se for qualquer outra coisa, começa com uma lista vazia para não dar erro
        historico_completo = []

    if not historico_completo:
        await query.edit_message_text("❌ Você ainda não possui transações em seu histórico.")
        return

    # --- CORREÇÃO 2: FUNÇÃO DE ORDENAÇÃO SEGURA ---
    # Esta função interna garante que a ordenação não quebre se encontrar dados mal formatados
    def chave_de_ordenacao_segura(transacao):
        # PRIMEIRO, VERIFICA SE A TRANSAÇÃO É UM DICIONÁRIO
        if not isinstance(transacao, dict):
            # Se for uma lista (formato antigo), trata como data inválida e põe no fim
            return datetime.min

        # Se for um dicionário (formato correto), prossegue
        data_str = transacao.get("data", "")
        try:
            return datetime.strptime(data_str, "%d/%m/%Y %H:%M")
        except ValueError:
            try:
                return datetime.strptime(data_str, "%d/%m/%Y")
            except ValueError:
                return datetime.min # Se a data for inválida, vai para o fim

    historico_completo.sort(key=chave_de_ordenacao_segura, reverse=True)

    # --- Lógica de Paginação (sem alterações) ---
    pagina_atual = 1
    if query.data and query.data.startswith("historico_pag_"):
        try:
            pagina_atual = int(query.data.split("_")[2])
        except (ValueError, IndexError):
            pagina_atual = 1
            
    total_transacoes = len(historico_completo)
    total_paginas = (total_transacoes + ITENS_POR_PAGINA - 1) // ITENS_POR_PAGINA or 1
    
    inicio = (pagina_atual - 1) * ITENS_POR_PAGINA
    fim = inicio + ITENS_POR_PAGINA
    transacoes_da_pagina = historico_completo[inicio:fim]

    # --- Construir a Mensagem (sem alterações nos textos) ---
    saldo_formatado = f"{user_data.get('saldo', 0):.2f}"
    
    # Usei o método de juntar a lista que é mais limpo, mas os textos são os seus
    partes_mensagem = [
        f"📁 *Extrato de Transações (Página {pagina_atual}/{total_paginas})*",
        f"💵 Saldo atual: *{saldo_formatado} MZN*",
        "\n"
    ]

    if not transacoes_da_pagina:
        partes_mensagem.append("Nenhuma transação encontrada nesta página.")
    else:
        for t in transacoes_da_pagina:
            # --- CORREÇÃO 3: VERIFICAÇÃO DENTRO DO LOOP DE EXIBIÇÃO ---
            # Garante que o bot não quebre ao tentar mostrar um item mal formatado
            if not isinstance(t, dict):
                continue # Simplesmente pula para a próxima transação

            status = t.get("status", "pendente")
            data = t.get("data", "N/A")
            valor = float(t.get("valor", 0))
            
            emoji_status = {"aprovado": "✅ aprovado", "recusado": "❌ recusado", "pendente": "🕓 pendente"}.get(status, "❓")
            tipo_transacao = t.get("tipo", "desconhecido")
            
            if tipo_transacao == "deposito":
                # Seu texto original:
                partes_mensagem.append(f"📥 *Depósito* {emoji_status}\n   Valor: `{valor:.2f} MZN`\n   Data: `{data}`\n")
            elif tipo_transacao == "saque":
                valor_liquido = float(t.get("valor_liquido", 0))
                # Seu texto original:
                partes_mensagem.append(f"📤 *Saque* {emoji_status}\n   Valor Solicitado: `{valor:.2f} MZN`\n   Valor a Receber: `{valor_liquido:.2f} MZN`\n   Data: `{data}`\n")
    
    mensagem_final = "\n".join(partes_mensagem)

    # --- Montar os Botões de Navegação (sem alterações) ---
    botoes_navegacao = []
    if pagina_atual > 1:
        botoes_navegacao.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"historico_pag_{pagina_atual - 1}"))
    
    if pagina_atual < total_paginas:
        botoes_navegacao.append(InlineKeyboardButton("Próxima ➡️", callback_data=f"historico_pag_{pagina_atual + 1}"))
    
    keyboard = [
        botoes_navegacao, 
        [InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="ajuda")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # --- Enviar ou Editar a Mensagem (sem alterações) ---
    try:
        await query.edit_message_text(
            text=mensagem_final,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    except Exception as e:
        if "Message is not modified" not in str(e):
            print(f"Erro inesperado ao editar mensagem de histórico: {e}")

from datetime import datetime, timedelta
#from telegram import Update, ParseMode
from telegram.ext import ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def parse_data(data_str):
    """Converte string de data para datetime"""
    try:
        return datetime.fromisoformat(data_str)
    except:
        try:
            return datetime.strptime(data_str, "%d/%m/%Y")
        except:
            return datetime.now()

from datetime import datetime, timedelta
from telegram.constants import ParseMode
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

@checa_banido
# === MENU PRINCIPAL DE MEUS PLANOS ===
async def ajuda_meusplanos_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = getattr(update, "callback_query", None)
    if query:
        await query.answer()
        try:
            await query.message.delete()
        except:
            pass
        target = query.message
    else:
        target = update.message

    keyboard = [
        [InlineKeyboardButton("📗 Planos Ativos", callback_data="mostrar_ativos")],
        [InlineKeyboardButton("📕 Planos Expirados", callback_data="mostrar_expirados")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda")]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    await target.reply_text(
        "📦 *Meus Planos*\nEscolha uma opção abaixo 👇",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )


# === FUNÇÃO PARA MOSTRAR PLANOS ATIVOS ===
async def mostrar_planos_ativos_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    usuarios = carregar_json(USERS_FILE)
    uid = str(update.effective_user.id)
    user = usuarios.get(uid)

    query = getattr(update, "callback_query", None)
    if query:
        await query.answer()
        try:
            await query.message.delete()
        except:
            pass
        target = query.message
    else:
        target = update.message

    if not user:
        return await target.reply_text("❌ Você ainda não possui conta.")

    hoje = datetime.utcnow().date()
    ultima_coleta_str = user.get("last_coleta_date")
    coletou_hoje = False

    # 🔍 Verifica se já coletou hoje
    if ultima_coleta_str:
        try:
            ultima_coleta = datetime.strptime(ultima_coleta_str, "%Y-%m-%d").date()
            coletou_hoje = (ultima_coleta == hoje)
        except:
            coletou_hoje = False

    planos_ativos = []
    for p in user.get("planos", []):
        try:
            data_exp = datetime.strptime(p.get("data_expiracao"), "%d/%m/%Y").date()
        except:
            continue
        if data_exp >= hoje:
            planos_ativos.append(p)

    # 🧩 Monta teclado de botões
    keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda_meusplanos")]]

    # ✅ Só mostra botão de coleta se tiver plano ativo e não tiver coletado hoje
    if planos_ativos and not coletou_hoje:
        keyboard.insert(0, [InlineKeyboardButton("💰 Coletar Ganhos", callback_data="coletar_lucro")])

    markup = InlineKeyboardMarkup(keyboard)

    ativos_txt = []
    # 📋 Mostra do mais novo → mais antigo
    for i, p in enumerate(reversed(planos_ativos), start=1):
        nome = p.get("nome", "Plano")
        valor = float(p.get("valor", p.get("investido", 0.0)) or 0.0)
        percent = float(p.get("percent", 0.0) or 0.0)

        try:
            data_compra = datetime.strptime(p.get("data_compra"), "%d/%m/%Y").date()
        except:
            data_compra = hoje
        try:
            data_exp = datetime.strptime(p.get("data_expiracao"), "%d/%m/%Y").date()
        except:
            data_exp = data_compra + timedelta(days=int(p.get("dias", 0)))

        dias_total = max((data_exp - data_compra).days, 0)
        dias_passados = min(max((hoje - data_compra).days, 0), dias_total)
        dias_restantes = max(dias_total - dias_passados, 0)

        ganho_dia = round(valor * percent, 2)
        ganhos_pagos = round(ganho_dia * dias_passados, 2)
        ganhos_futuros = round(ganho_dia * dias_restantes, 2)

        nota_hoje = " — comprado hoje, começa a gerar amanhã ⏳" if data_compra == hoje else ""
        ativos_txt.append(
            f"*{i}. {nome}* 🟢 *Ativo*{nota_hoje}\n"
            f"💰 Investido: {valor:.2f} MZN\n"
            f"📈 Rentabilidade: {percent*100:.2f}%\n"
            f"📆 Comprado em: {data_compra.strftime('%d/%m/%Y')}\n"
            f"⌛ Expira em: {data_exp.strftime('%d/%m/%Y')}\n"
            f"⏳ Dias restantes: {dias_restantes}\n"
            f"💸 Ganhos pagos: {ganhos_pagos:.2f} MZN\n"
            f"📊 Ganhos futuros: {ganhos_futuros:.2f} MZN\n"
        )

    if not ativos_txt:
        texto = "📗 *Planos Ativos:*\n\n— Nenhum plano ativo no momento."
    else:
        texto = "📗 *Planos Ativos:*\n\n" + "\n".join(ativos_txt)

    await target.reply_text(texto, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)

from datetime import timezone
hoje = datetime.now(timezone.utc).date()
# === FUNÇÃO PARA MOSTRAR PLANOS EXPIRADOS ===
from datetime import datetime, timezone, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode

async def mostrar_planos_expirados_cb(update: Update, ctx):
    usuarios = carregar_json(USERS_FILE)
    uid = str(update.effective_user.id)
    user = usuarios.get(uid)

    query = getattr(update, "callback_query", None)
    if query:
        await query.answer()
        try:
            await query.message.delete()
        except:
            pass
        target = query.message
    else:
        target = update.message

    keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda_meusplanos")]]
    markup = InlineKeyboardMarkup(keyboard)

    if not user:
        return await target.reply_text("❌ Você ainda não possui conta.", reply_markup=markup)

    planos_expirados = user.get("planos_expirados", [])
    hoje = datetime.now(timezone.utc).date()
    expirados_txt = []

    # ✅ Função para tentar parsear datas em dois formatos
    def parse_data(data_str):
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(data_str, fmt)
            except:
                continue
        return datetime(1970, 1, 1, tzinfo=timezone.utc)  # fallback

    # Ordena do mais recente para o mais antigo
    planos_expirados.sort(
        key=lambda p: parse_data(p.get("data_expiracao", "01/01/1970")),
        reverse=True
    )

    for j, p in enumerate(planos_expirados, start=1):
        nome = p.get("nome", "Plano Expirado")
        valor = float(p.get("valor", p.get("investido", 0.0)) or 0.0)
        percent = float(p.get("percent", 0.0) or 0.0)

        try:
            data_compra = parse_data(p.get("data_compra", "01/01/1970"))
        except:
            data_compra = datetime.now(timezone.utc)

        try:
            data_exp = parse_data(p.get("data_expiracao", "01/01/1970"))
        except:
            data_exp = data_compra

        ganho_dia = round(valor * percent, 2)
        total_ganho = round(ganho_dia * int(p.get("dias", 0)), 2)
        dias_expirados = (hoje - data_exp.date()).days
        if dias_expirados < 0:
            dias_expirados = 0

        if dias_expirados == 0:
            info_extra = "Expirou *hoje* ⏰"
        elif dias_expirados == 1:
            info_extra = "Expirou *ontem* ⏰"
        else:
            info_extra = f"Expirou há *{dias_expirados} dias* ⏰"

        expirados_txt.append(
            f"*{j}. {nome}* ⌛ *Expirado*\n"
            f"💰 Investido: {valor:.2f} MZN\n"
            f"📈 Rentabilidade: {percent*100:.2f}%\n"
            f"📆 Comprado em: {data_compra.strftime('%d/%m/%Y')}\n"
            f"⌛ Expirou em: {data_exp.strftime('%d/%m/%Y')}\n"
            f"💸 Ganhos totais: {total_ganho:.2f} MZN\n"
            f"⏰ {info_extra}\n"
        )

    if not expirados_txt:
        texto = "📕 *Planos Expirados:*\n\n— Nenhum plano expirado ainda."
    else:
        texto = "📕 *Planos Expirados (do mais recente ao mais antigo):*\n\n" + "\n".join(expirados_txt)

    await target.reply_text(texto, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)

from telegram.constants import ChatAction
from telegram.helpers import create_deep_linked_url
from telegram import InputFile

# ✅ Coloque isso junto dos seus handlers
async def baixar_usuarios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.callback_query:
            chat = update.callback_query.message.chat
        else:
            chat = update.message.chat

        await chat.send_action(action=ChatAction.UPLOAD_DOCUMENT)
        with open(USERS_FILE, "rb") as f:
            await chat.send_document(document=InputFile(f), filename="usuarios.json")
    except FileNotFoundError:
        if update.callback_query:
            await update.callback_query.message.reply_text("❌ Arquivo usuarios.json não encontrado.")
        else:
            await update.message.reply_text("❌ Arquivo usuarios.json não encontrado.")
    except Exception as e:
        if update.callback_query:
            await update.callback_query.message.reply_text(f"⚠️ Erro ao enviar o arquivo: {e}")
        else:
            await update.message.reply_text(f"⚠️ Erro ao enviar o arquivo: {e}")

from telegram import InputFile

async def ver_pendentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    admin_id = "8182769178"  # Substitua pelo seu ID real de admin

    if user_id != admin_id:
        if update.callback_query:
            return await update.callback_query.message.reply_text("❌ Apenas o administrador pode usar este comando.")
        return await update.message.reply_text("❌ Apenas o administrador pode usar este comando.")

    try:
        if update.callback_query:
            chat = update.callback_query.message.chat
        else:
            chat = update.message.chat

        await chat.send_action(action=ChatAction.UPLOAD_DOCUMENT)
        with open("pendentes.json", "rb") as f:
            await chat.send_document(document=InputFile(f), filename="pendentes.json")
    except FileNotFoundError:
        if update.callback_query:
            await update.callback_query.message.reply_text("❌ Arquivo pendentes.json não encontrado.")
        else:
            await update.message.reply_text("❌ Arquivo pendentes.json não encontrado.")
    except Exception as e:
        if update.callback_query:
            await update.callback_query.message.reply_text(f"⚠️ Erro ao enviar o arquivo: {e}")
        else:
            await update.message.reply_text(f"⚠️ Erro ao enviar o arquivo: {e}")

from telegram.constants import ParseMode

async def limpar_saldo_corrompido(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        if update.callback_query:
            return await update.callback_query.message.reply_text("❌ Acesso negado.")
        return await update.message.reply_text("❌ Acesso negado.")

    alterados = 0
    depositos_corrigidos = 0

    for uid, dados in usuarios.items():
        saldo = dados.get("saldo", 0)
        if not isinstance(saldo, (int, float)) or saldo < 0 or saldo > 10_000_000:
            usuarios[uid]["saldo"] = 0.0
            alterados += 1

        if "depositos" in dados:
            depositos_validos = []
            for dep in dados["depositos"]:
                valor = dep.get("valor", 0)
                if isinstance(valor, (int, float)) and 0 < valor <= 10_000_000:
                    depositos_validos.append(dep)
                else:
                    depositos_corrigidos += 1
            usuarios[uid]["depositos"] = depositos_validos

    salvar_json(USERS_FILE, usuarios)

    msg = (
        f"✅ Limpeza concluída:\n"
        f"*{alterados}* saldos corrigidos\n"
        f"*{depositos_corrigidos}* depósitos inválidos removidos."
    )

    if update.callback_query:
        await update.callback_query.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

import re

def escape_markdown(text: str) -> str:
    """
    Escapa caracteres especiais do Markdown para que o Telegram não quebre a mensagem.
    """
    if not text:
        return ""
    return re.sub(r'([_*\[\]()~`>#+-=|{}.!])', r'\\\1', text)

import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import logging

# --- FUNÇÕES AUXILIARES
def carregar_json(filename):
    """Carrega dados de um arquivo JSON."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {filename}. Criando um novo.")
        return {} # Retorna um dicionário vazio se o arquivo não existe
    except json.JSONDecodeError:
        print(f"Erro ao decodificar JSON em {filename}. O arquivo pode estar corrompido ou vazio. Retornando dicionário vazio.")
        return {} # Retorna um dicionário vazio em caso de JSON inválido

def salvar_json(filename, data):
    """Salva dados em um arquivo JSON."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"Erro ao salvar arquivo {filename}: {e}")

# Configura o logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÕES DO SEU BOT
ADMIN_ID = 8182769178
PENDENTES_FILE = "pendentes.json"
USERS_FILE = "usuarios.json"
CANAL_ID = -1003067460575  # 

def escape_markdown_v2(text):
    # Escapa caracteres especiais para MarkdownV2
    # Lista de caracteres a serem escapados: _, *, [, ], (, ), ~, `, >, #, +, -, =, |, {, }, ., !
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))

def escape_html(text):
    # Escapa caracteres que podem quebrar tags HTML
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


# Seu código existente começa aqui
async def aprovar_recusar_cb(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    # O ID do admin que clicou no botão (este é o receptor da confirmação da ação)
    admin_id_clicou = str(query.from_user.id) 
    
    # Capturar o chat_id e message_id da mensagem original do admin para edição posterior
    admin_chat_id = query.message.chat_id
    admin_message_id = query.message.message_id
    is_caption_message = bool(query.message.caption) # Flag para saber se é caption ou text

    try:
        acao, pid = query.data.split("|")
    except ValueError:
        # Se os dados do callback forem inválidos, edita a mensagem do admin
        await edit_admin_message(context, admin_chat_id, admin_message_id, is_caption_message, 
                                 "❌ Erro interno: dados de callback inválidos\\.", 
                                 ParseMode.MARKDOWN_V2, reply_markup=None)
        return

    pendentes = carregar_json(PENDENTES_FILE)
    usuarios = carregar_json(USERS_FILE)

    pedido = pendentes.get(pid)

    if not isinstance(pedido, dict):
        try:
            # Se o pedido já foi processado ou é inválido, edita a mensagem do admin
            await edit_admin_message(context, admin_chat_id, admin_message_id, is_caption_message, 
                                     "❌ Esta solicitação já foi processada ou é inválida\\.", 
                                     ParseMode.MARKDOWN_V2, reply_markup=None)
        except Exception as e:
            logger.error(f"Erro ao editar mensagem de pedido já processado: {e}")
        return

    tipo = pedido.get("tipo")
    user_id = str(pedido.get("user_id"))
    nome_usuario = pedido.get("nome", "Usuário")
    username = pedido.get("username")

    username_display = f"@{username}" if username and username.strip() else nome_usuario
    
    # Versões escapadas para diferentes modos de parse
    nome_usuario_esc_md = escape_markdown_v2(nome_usuario)
    username_display_esc_md = escape_markdown_v2(username_display)
    
    nome_usuario_esc_html = escape_html(nome_usuario)
    username_display_esc_html = escape_html(username_display)

    valor = float(pedido.get("valor", 0))
    valor_liquido = float(pedido.get("valor_liquido", 0))
    valor_solicitado = float(pedido.get("valor_bruto", 0))
    valor_bruto = float(pedido.get("valor_bruto", 0))

    current_status = pedido.get("status", "pendente")
    status_novo_historico = "aprovado" if acao == "aprovar" else "recusado"
    data_formatada = datetime.now().strftime("%d/%m/%Y %H:%M")

    historico_lista = usuarios.get(user_id, {}).get("historico", [])
    if not isinstance(historico_lista, list):
        historico_lista = []

    item_encontrado_no_historico = None
    for item in historico_lista:
        if isinstance(item, dict) and str(item.get("id")) == str(pid):
            item_encontrado_no_historico = item
            break

    if item_encontrado_no_historico:
        item_encontrado_no_historico["status"] = status_novo_historico
        item_encontrado_no_historico["data"] = data_formatada
        item_encontrado_no_historico["valor_liquido"] = valor_liquido if tipo == "saque" else valor
    else:
        novo_item_historico = {
            "id": pid,
            "tipo": tipo,
            "valor": valor,
            "valor_liquido": valor_liquido if tipo == "saque" else valor,
            "status": status_novo_historico,
            "data": data_formatada,
            "admin_action": True
        }
        historico_lista.append(novo_item_historico)

    if user_id not in usuarios:
        usuarios[user_id] = {}
    usuarios[user_id]["historico"] = historico_lista

    texto_admin_confirmacao = "" # Mensagem para o admin que clicou
    texto_canal = "" # Mensagem para o canal, se houver
    texto_usuario = "" # Mensagem para o usuário
    
    # Remover botões imediatamente (sem editar o texto ainda)
    await query.edit_message_reply_markup(reply_markup=None)

    # ================================
    #   QUANDO APROVADO PELO ADMIN
    # ================================
    if acao == "aprovar":
        if tipo == "deposito":
            if current_status in ["aprovado_provisoriamente", "aprovado_automaticamente"]:
                pedido["status"] = "aprovado_definitivamente"
                usuarios[user_id].setdefault("depositos", []).append({
                "id": pid,
                "valor": valor,
                "status": "aprovado",
                "metodo": "Banco" if usuarios[user_id].get("banco") else "Cripto",
                "data": data_formatada
})

                texto_admin_confirmacao = (
                    f"✅ Você \\*confirmou\\* o depósito\\!\n\nFoi previamente aprovado automaticamente\\.\n"
                    f"🆔 ID: `{pid}`\n👤 {nome_usuario_esc_md} {username_display_esc_md}\n"
                    f"👤 `{user_id}`\n💰 `{valor:.2f} MZN`\n📅 `{data_formatada}`"
                )

                texto_usuario = (
                    f"✅ Olá, {nome_usuario_esc_md}\\!\n\n"
                    f"Seu depósito de \\*{valor:.2f} MZN\\* foi \\*aprovado e confirmado\\* manualmente em `{data_formatada}`\\. "
                    "O valor já estava disponível na sua conta\\.\n\n"
                    "🌟 Para começar a gerar ganhos diários, não deixe de adquirir um dos nossos planos pagos e maximize seus lucros\\!\n\n"
                    "🤝 Convide seus amigos para se juntarem a nós e aumente ainda mais seus ganhos:\n"
                    f"🔗 [Clique aqui para convidar](https://t\\.me/AgrotechFund_bot?start={user_id})\n\n"
                    "🚀 Obrigado por confiar em nossa plataforma e fazer parte da nossa comunidade\\!"
                )

            elif current_status == "pendente":
                # VERIFICAR SE É O PRIMEIRO DEPÓSITO PARA PROCESSAR COMISSÕES
                total_depositos_aprovados = usuarios[user_id].get("deposito_total", 0)
                e_primeiro_deposito = total_depositos_aprovados == 0

                # ATUALIZAR SALDO E TOTAIS DO USUÁRIO
                usuarios[user_id]["saldo"] = usuarios[user_id].get("saldo", 0) + valor
                usuarios[user_id]["deposito_total"] = usuarios[user_id].get("deposito_total", 0) + valor
                usuarios[user_id]["total_investido"] = usuarios[user_id].get("total_investido", 0) + valor

                # PROCESSAR COMISSÕES DE INDICAÇÃO (APENAS NO PRIMEIRO DEPÓSITO)
                if e_primeiro_deposito:
                    percentuais = {1: 0.08, 2: 0.03, 3: 0.01}
                    usuario_atual = usuarios[user_id]

                    for nivel in range(1, 4):
                        indicador_id = usuario_atual.get("indicador")
                        if not indicador_id or indicador_id not in usuarios:
                            break

                        usuario_indicante = usuarios[indicador_id]
                        comissao = round(valor * percentuais[nivel], 2)

                        usuario_indicante["saldo"] = usuario_indicante.get("saldo", 0) + comissao
                        if "comissoes" not in usuario_indicante:
                            usuario_indicante["comissoes"] = {"1": 0, "2": 0, "3": 0}
                        usuario_indicante["comissoes"][str(nivel)] = usuario_indicante["comissoes"].get(str(nivel), 0) + comissao

                        # ENVIAR MENSAGEM DE COMISSÃO PARA O INDICADOR
                        try:
                            await context.bot.send_message(
                                chat_id=int(indicador_id),
                                text=(
                                    f"🎉 Você recebeu uma comissão de nível `{nivel}`\\!\n"
                                    f"💰 Valor: `{comissao:.2f} MZN`\n"
                                    f"💵 Primeiro depósito de `{valor:.2f} MZN`\n"
                                    f"👤 Do usuário `{user_id}`"
                                ),
                                parse_mode=ParseMode.MARKDOWN_V2
                            )
                        except Exception as e:
                            logger.error(f"Erro ao enviar comissão para indicador {indicador_id}: {e}")
                        
                        usuario_atual = usuario_indicante

                pedido["status"] = "aprovado_definitivamente"
                
                texto_admin_confirmacao = (
                    f"✅ Você \\*aprovou\\* o depósito manualmente\\!\n\n🆔 ID: `{pid}`\n👤 {nome_usuario_esc_md} {username_display_esc_md}\n"
                    f"👤 `{user_id}`\n💰 `{valor:.2f} MZN`\n📅 `{data_formatada}`"
                )
                if e_primeiro_deposito:
                    texto_admin_confirmacao += "\n🎯 Comissões processadas \\(primeiro depósito\\)"

                texto_usuario = (
                    f"✅ Olá, {nome_usuario_esc_md}\\!\n\n"
                    f"Seu depósito de \\*{valor:.2f} MZN\\* foi \\*aprovado\\* e confirmado com sucesso em `{data_formatada}`\\. "
                    "O valor já está disponível na sua conta e você pode utilizá\\-lo imediatamente\\.\n\n"
                    "🌟 Para começar a gerar ganhos diários, não deixe de adquirir um dos nossos planos pagos e maximize seus lucros\\!\n\n"
                    "🤝 Convide seus amigos para se juntarem a nós e aumente ainda mais seus ganhos:\n"
                    f"🔗 [Clique aqui para convidar](https://t\\.me/AgrotechFund_bot?start={user_id})\n\n"
                    "🚀 Obrigado por confiar em nossa plataforma e fazer parte da nossa comunidade\\!"
                )

            else:
                texto_admin_confirmacao = (
                    f"⚠️ Depósito ID: `{pid}` já tem status \\'{escape_markdown_v2(current_status)}\\'\\. Ação de aprovação ignorada\\.\n"
                    f"👤 {nome_usuario_esc_md} {username_display_esc_md}\n"
                    f"💰 `{valor:.2f} MZN`\n📅 `{data_formatada}`"
                )
            
            # Mensagem para o canal (apenas se for aprovado definitivamente)
            if pedido.get("status") == "aprovado_definitivamente":
                texto_canal = (
                    "💵➤➤➤➤➤➤➤➤➤➤💵\n"
                    "💎 <b>NOVO DEPÓSITO CONFIRMADO</b> 💎\n\n"
                    f"👤 <b>Usuário:</b> {nome_usuario_esc_html} {username_display_esc_html}\n"
                    f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
                    f"💵 <b>Depósito realizado:</b> <code>{valor:.2f} MZN</code>\n"
                    f"📆 <b>Confirmado em:</b> {data_formatada}\n\n"
                    "✅ Depósito processado com sucesso.\n\n"
                    "🌟 <b>Dica:</b> Se ainda não tem conta ou planos ativos, junte-se à nossa rede e veja como outros usuários estão crescendo seus lucros com segurança.\n\n"
                    f"👉 <a href='https://t.me/AgrotechFund_bot?start={user_id}'>Clique aqui e comece a ganhar</a>\n"
                    "💰═══════════════💰"
                )

        elif tipo == "saque":
            valor_solicitado = float(pedido.get("valor_bruto", 0))
            valor_liquido = float(pedido.get("valor_liquido", 0))
            
            dados_banco = usuarios[user_id].get("banco")
            dados_cripto = usuarios[user_id].get("cripto")
            
            extra_info = ""
            if dados_banco:
                extra_info = (
                    f"🏦 Método: {escape_markdown_v2(dados_banco.get('tipo','—'))}\n"
                    f"🔢 Número: `{escape_markdown_v2(dados_banco.get('numero','—'))}`\n"
                    f"📛 Titular: {escape_markdown_v2(dados_banco.get('nome', '—'))}" 
                )
            elif dados_cripto:
                extra_info = (
                    f"💱 Moeda: {escape_markdown_v2(dados_cripto.get('moeda','—'))}\n"
                    f"🔗 Wallet: `{escape_markdown_v2(dados_cripto.get('wallet','—'))}`"
                )
            else:
                extra_info = "⚠️ Nenhum método de saque encontrado\\."
            
            texto_usuario = (
                f"✅ Olá, {nome_usuario_esc_md}\\!\n\n"
                f"Seu pedido de saque de \\*{valor_liquido:.2f} MZN\\* foi \\*aprovado\\* com sucesso em `{data_formatada}`\\.\n\n"
                "🏦 Parabéns\\! O valor solicitado já foi transferido para sua conta vinculada\\. "
                "Recomendamos que você verifique seu saldo para confirmar o recebimento\\.\n\n"
                "🤝 Quer aumentar seus ganhos\\? Convide seus amigos para se juntarem à nossa plataforma e ganhe junto com eles\\!\n"
                f"🔗 [Convide agora seus amigos](https://t\\.me/AgrotechFund_bot?start={user_id})\n\n"
                "🚀 Muito obrigado por confiar em nós e fazer parte da nossa comunidade de investidores\\!"
            )
            
            texto_admin_confirmacao = (
                f"✅ Você \\*aprovou\\* o saque\\!\n\n🆔 ID: `{pid}`\n👤 {nome_usuario_esc_md} {username_display_esc_md}\n"
                f"👤 `{user_id}`\n💰Valor solicitado: `{valor_solicitado:.2f}`\n💸 Valor líquido: `{valor_liquido:.2f} MZN`\n{extra_info}\n📅 `{data_formatada}`"
            )
            pedido["status"] = "aprovado_definitivamente"
            usuarios[user_id].setdefault("saques", []).append({
            "id": pid,
            "valor": valor_liquido,
            "status": "aprovado",
            "metodo": "Banco" if usuarios[user_id].get("banco") else "Cripto",
            "data": data_formatada
})

            texto_canal = (
                "💰⬅️⬅️⬅️⬅️⬅️⬅️⬅️⬅️⬅💰\n"
                "💸 <b>SAQUE APROVADO COM SUCESSO</b> 💸\n\n"
                f"👤 <b>Usuário:</b> {nome_usuario_esc_html} {username_display_esc_html}\n"
                f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
                f"💰 <b>Quantia processada:</b> <code>{valor_solicitado:.2f} MZN</code>\n"
                f"📆 <b>Confirmado em:</b> {data_formatada}\n\n"
                "✅ O saque foi processado e o valor já está disponível na conta vinculada.\n\n"
                "🌟 <b>Dica:</b> Se ainda não possui conta ou planos ativos, junte-se à nossa rede e veja como outros usuários estão aumentando seus ganhos com segurança.\n"
                f"👉 <a href='https://t.me/AgrotechFund_bot?start={user_id}'>Clique aqui e comece a ganhar</a>\n\n"
                "🚀 Cresça com confiança, transparência e aproveite todas as oportunidades disponíveis!\n"
                "💸═══════════════💸"
            )

    # ================================
    #   QUANDO RECUSADO PELO ADMIN
    # ================================
    elif acao == "recusar":
        if tipo == "deposito":
            if current_status in ["aprovado_provisoriamente", "aprovado_automaticamente","pendente"]: 
                if user_id in usuarios:
                    planos_removidos_count = 0
                    valor_usado_em_planos = 0
                    ganhos_ja_pagos = 0

                    if "planos" in usuarios[user_id]:
                        novos_planos = []
                        for plano in usuarios[user_id]["planos"]:
                            if isinstance(plano, dict) and str(plano.get("deposit_id")) == str(pid):
                                planos_removidos_count += 1
                                valor_usado_em_planos += plano.get("investido", 0)
                                ganhos_ja_pagos += plano.get("ganhos_pagos", 0)
                            else:
                                novos_planos.append(plano)
                        usuarios[user_id]["planos"] = novos_planos

                    if ganhos_ja_pagos > 0:
                        usuarios[user_id]["saldo"] = max(
                            0, usuarios[user_id].get("saldo", 0) - ganhos_ja_pagos
                        )

                    valor_restante = valor - valor_usado_em_planos

                    if planos_removidos_count > 0:
                        if valor_restante > 0:
                            usuarios[user_id]["saldo"] = usuarios[user_id].get("saldo", 0) - valor_restante
                            usuarios[user_id]["deposito_total"] = usuarios[user_id].get("deposito_total", 0) - valor
                            usuarios[user_id]["total_investido"] = usuarios[user_id].get("total_investido", 0) - valor_usado_em_planos

                            texto_usuario = (
                                f"⚠️ \\*Atenção, {nome_usuario_esc_md}\\*\\!\n\n"
                                f"Seu depósito de \\*{valor:.2f} MZN\\* \\(ID: `{pid}`\\) foi \\*recusado\\*\\.\n\n"
                                f"\\- O\\(s\\) plano\\(s\\) adquirido\\(s\\) com este depósito foram \\*removidos\\*\\.\n"
                                f"\\- O restante do depósito \\(`{valor_restante:.2f} MZN`\\) foi retirado do seu saldo\\.\n"
                            )
                            if ganhos_ja_pagos > 0:
                                texto_usuario += f"\\- Os lucros já pagos \\(`{ganhos_ja_pagos:.2f} MZN`\\) também foram descontados\\.\n"
                            texto_usuario += (
                                "\n➡️ Motivo: irregularidades no comprovativo\\.\n"
                                "💡 Tente novamente com um comprovativo válido\\."
                            )
                            pedido["status"] = "recusado_parcial"

                        else:
                            usuarios[user_id]["deposito_total"] = usuarios[user_id].get("deposito_total", 0) - valor
                            usuarios[user_id]["total_investido"] = usuarios[user_id].get("total_investido", 0) - valor_usado_em_planos

                            texto_usuario = (
                                f"⚠️ \\*Atenção, {nome_usuario_esc_md}\\*\\!\n\n"
                                f"Seu depósito de \\*{valor:.2f} MZN\\* \\(ID: `{pid}`\\) foi \\*recusado\\*\\.\n\n"
                                f"O\\(s\\) plano\\(s\\) adquiridos com este depósito foram \\*removidos\\*\\, junto com os lucros\\.\n"
                            )
                            if ganhos_ja_pagos > 0:
                                texto_usuario += f"\\- Os lucros já pagos \\(`{ganhos_ja_pagos:.2f} MZN`\\) foram descontados do seu saldo\\.\n"
                            texto_usuario += (
                                "\n➡️ Motivo: irregularidades no comprovativo\\.\n"
                                "💡 Tente novamente com um comprovativo válido\\."
                            )
                            pedido["status"] = "recusado_plano_removido"

                    else:
                        usuarios[user_id]["saldo"] = usuarios[user_id].get("saldo", 0) - valor
                        usuarios[user_id]["deposito_total"] = usuarios[user_id].get("deposito_total", 0) - valor
                        usuarios[user_id]["total_investido"] = usuarios[user_id].get("total_investido", 0) - valor

                        texto_usuario = (
                            f"⚠️ \\*Atenção, {nome_usuario_esc_md}\\*\\!\n\n"
                            f"Seu depósito de \\*{valor:.2f} MZN\\* \\(ID: `{pid}`\\) foi \\*recusado\\*\\.\n"
                            f"O valor foi \\*estornado\\* da sua conta\\.\n"
                            "➡️ Motivo: irregularidades no comprovativo\\.\n💡 Tente novamente com um comprovativo válido\\."
                        )
                        pedido["status"] = "recusado_estornado"

                    # PROCESSAR ESTORNO DE COMISSÕES
                    percentuais = {1: 0.08, 2: 0.03, 3: 0.01}
                    usuario_atual = usuarios[user_id]

                    for nivel in range(1, 4):
                        indicador_id = usuario_atual.get("indicador")
                        if not indicador_id or indicador_id not in usuarios:
                            break

                        usuario_indicante = usuarios[indicador_id]
                        comissao_estornada = round(valor * percentuais[nivel], 2)
                        usuario_indicante["saldo"] = usuario_indicante.get("saldo", 0) - comissao_estornada

                        if "comissoes" in usuario_indicante and str(nivel) in usuario_indicante["comissoes"]:
                            usuario_indicante["comissoes"][str(nivel)] -= comissao_estornada

                        # ENVIAR MENSAGEM DE ESTORNO PARA O INDICADOR
                        try:
                            await context.bot.send_message(
                                chat_id=int(indicador_id),
                                text=(
                                    f"⚠️ Atenção\\! Comissão de nível `{nivel}` referente ao depósito de `{valor:.2f} MZN` "
                                    f"do usuário `{user_id}` foi \\*estornada\\* devido à recusa do depósito\\."
                                ),
                                parse_mode=ParseMode.MARKDOWN_V2
                            )
                        except Exception as e:
                            logger.error(f"Erro ao enviar estorno para indicador {indicador_id}: {e}")
                        
                        usuario_atual = usuario_indicante

                    texto_admin_confirmacao = (
                        f"❌ Você \\*recusou\\* o depósito manualmente\\.\n\n"
                        f"🆔 ID: `{pid}`\n👤 {nome_usuario_esc_md} {username_display_esc_md}\n"
                        f"👤 `{user_id}`\n💰 `{valor:.2f} MZN`\n📅 `{data_formatada}`\n"
                    )
                    if planos_removidos_count > 0:
                        texto_admin_confirmacao += f"🚫 Plano\\(s\\) removido\\(s\\): `{planos_removidos_count}`\n"
                    if ganhos_ja_pagos > 0:
                        texto_admin_confirmacao += f"💸 Lucros descontados: `{ganhos_ja_pagos:.2f} MZN`\n"
                    
                else:
                    texto_admin_confirmacao = (
                        f"❌ Você \\*recusou\\* o depósito ID: `{pid}`\\, mas o usuário `{user_id}` não foi encontrado nos registros\\. "
                        "Nenhuma alteração de saldo ou plano foi feita\\."
                    )
                    pedido["status"] = "recusado"
                    usuarios[user_id].setdefault("depositos", []).append({
                    "id": pid,
                    "valor": valor,
                    "status": "recusado",
                    "metodo": "Banco" if usuarios[user_id].get("banco") else "Cripto",
                    "data": data_formatada
})
            else:
                texto_admin_confirmacao = (
                    f"⚠️ Depósito ID: `{pid}` já tem status \\'{escape_markdown_v2(current_status)}\\'\\. Ação de recusa ignorada\\.\n"
                    f"👤 {nome_usuario_esc_md} {username_display_esc_md}\n"
                    f"💰 `{valor:.2f} MZN`\n📅 `{data_formatada}`"
                )

        elif tipo == "saque":
            # RESTAURAR SALDO DO USUÁRIO
            usuarios[user_id]["saldo"] = usuarios[user_id].get("saldo", 0) + valor

            dados_banco = usuarios[user_id].get("banco")
            dados_cripto = usuarios[user_id].get("cripto")

            extra_info = ""
            if dados_banco:
                extra_info = (
                    f"🏦 Método: {escape_markdown_v2(dados_banco.get('tipo','—'))}\n"
                    f"🔢 Número: `{escape_markdown_v2(dados_banco.get('numero','—'))}`\n"
                    f"📛 Titular: {escape_markdown_v2(dados_banco.get('nome', '—'))}"
                )
            elif dados_cripto:
                extra_info = (
                    f"💱 Moeda: {escape_markdown_v2(dados_cripto.get('moeda','—'))}\n"
                    f"🔗 Wallet: `{escape_markdown_v2(dados_cripto.get('wallet','—'))}`"
                )
            else:
                extra_info = "⚠️ Nenhum método de saque encontrado\\."

            texto_usuario = (
                "⚠️ \\*Atenção, caro usuário\\*\n\n"
                f"❌ O seu pedido de \\*saque\\* no valor de \\*{valor_liquido:.2f} MZN\\* foi \\*recusado\\*\\.\n\n"
                "➡️ Possíveis motivos:\n"
                "   • Saldo insuficiente na sua conta\\.\n"
                "   • Dados bancários ou de carteira incorretos\\.\n"
                "   • Tentativa de saque não autorizada\\.\n\n"
                "💡 Para evitar recusas futuras, verifique sempre se os dados fornecidos "
                "estão corretos e se possui saldo suficiente\\.\n\n"
                "📞 Caso tenha certeza de que está tudo certo, entre em contato com o \\*suporte oficial\\* "
                "para esclarecer a situação\\.\n\n"
                "✅ Continue utilizando a plataforma com segurança e transparência — "
                "estamos aqui para garantir o seu sucesso\\!"
            )

            texto_admin_confirmacao = (
                f"❌ Você \\*recusou\\* o saque\\.\n\n🆔 ID: `{pid}`\n👤 {nome_usuario_esc_md} {username_display_esc_md}\n"
                f"👤 `{user_id}`\n💰 Valor solicitado `{valor_solicitado:.2f}`\n💸 Valor líquido: `{valor_liquido:.2f} MZN`\n{extra_info}\n📅 `{data_formatada}`"
            )
            pedido["status"] = "recusado"
            usuarios[user_id].setdefault("saques", []).append({
            "id": pid,
            "valor": valor_bruto,
            "status": "recusado",
            "metodo": "Banco" if usuarios[user_id].get("banco") else "Cripto",
            "data": data_formatada
})
    
    # ✅ ENVIAR MENSAGEM PARA O USUÁRIO
    if texto_usuario:
        try:
            await context.bot.send_message(
                chat_id=int(user_id),
                text=texto_usuario,
                parse_mode=None,
                disable_web_page_preview=True
            )
            logger.info(f"📩 Usuário {user_id} notificado com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao notificar usuário {user_id}: {e}")

    # ✅ ENVIAR MENSAGEM PARA O CANAL
    if texto_canal:
        try:
            await context.bot.send_message(
                chat_id=CANAL_ID,
                text=texto_canal,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            logger.info("📢 Canal notificado com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao enviar para canal: {e}")

    # ✅ ENVIAR MENSAGEM DE CONFIRMAÇÃO PARA O ADMIN (APENAS UMA VEZ)
    if texto_admin_confirmacao:
        try:
            if is_caption_message:
                await context.bot.edit_message_caption(
                chat_id=admin_chat_id,
                message_id=admin_message_id,
                caption=texto_admin_confirmacao,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=None
            )
            else:
                await context.bot.edit_message_text(
                chat_id=admin_chat_id,
                message_id=admin_message_id,
                text=texto_admin_confirmacao,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=None
            )
            logger.info("👮 Admin notificado com confirmação via edição da mensagem")
        except Exception as e:
            logger.error(f"❌ Erro ao editar mensagem do admin para confirmação: {e}")
        #try:
            #await context.bot.send_message(
                #chat_id=admin_id_clicou,
                #text=texto_admin_confirmacao,
                #parse_mode=ParseMode.MARKDOWN_V2
            #)
            #logger.info("👮 Admin notificado com confirmação via nova mensagem")
        #except Exception as e2:
            #logger.error(f"❌ Erro ao enviar nova mensagem para admin {admin_id_clicou}: {e2}")

    #   SALVAMENTO E LIMPEZA
    if pedido.get("status") in ["aprovado_definitivamente", "recusado", "recusado_estornado", "recusado_parcial", "recusado_plano_removido"]:
        if pid in pendentes:
            del pendentes[pid]
            salvar_json(PENDENTES_FILE, pendentes)

        # Assumindo que esses arquivos também precisam ser atualizados
        for arquivo in ["historico/pendentes.json", "historico/pendentes_deposito.json", "historico/pendentes_saque.json"]:
            arquivo_path = os.path.join(os.path.dirname(__file__), arquivo) # Garante o caminho correto
            if os.path.exists(arquivo_path):
                dados = carregar_json(arquivo_path)
                if isinstance(dados, dict) and pid in dados:
                    del dados[pid]
                    salvar_json(arquivo_path, dados)
            else:
                logger.warning(f"Arquivo não encontrado: {arquivo_path}. Não foi possível remover o PID {pid}.")

        # Remover das listas de pendentes do usuário
        if tipo == "deposito":
            if user_id in usuarios:
                usuarios[user_id]["depositos_pendentes"] = [
                    d for d in usuarios[user_id].get("depositos_pendentes", []) if str(d.get("id")) != str(pid)
                ]
        elif tipo == "saque":
            if user_id in usuarios:
                usuarios[user_id]["saques_pendentes"] = [
                    s for s in usuarios[user_id].get("saques_pendentes", []) if str(s.get("id")) != str(pid)
                ]

    # Salvar alterações nos usuários
    salvar_json(USERS_FILE, usuarios)

    logger.info(f"🔄 Processamento concluído para {acao} do {tipo} ID: {pid}")


# --- FUNÇÕES AUXILIARES (Assumindo que você já as tem ou as adicionará) ---
def carregar_json(filename):
    """Carrega dados de um arquivo JSON."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {filename}. Criando um novo.")
        return {} # Retorna um dicionário vazio se o arquivo não existe
    except json.JSONDecodeError:
        print(f"Erro ao decodificar JSON em {filename}. O arquivo pode estar corrompido ou vazio. Retornando dicionário vazio.")
        return {} # Retorna um dicionário vazio em caso de JSON inválido

def salvar_json(filename, data):
    """Salva dados em um arquivo JSON."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"Erro ao salvar arquivo {filename}: {e}")


# --- CONFIGURAÇÕES DO SEU BOT
USERS_FILE = "usuarios.json"
PENDENTES_FILE = "pendentes.json" 
CANAL_ID = -1003067460575
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8077908640:AAHSkV9dooJLJtPN-XrAEosHQVWpIkjBgPg"
# --- Função de Aprovação Automática (COMISSÕES REMOVIDAS) ---
import html
from datetime import datetime, timedelta
#from telegram import Bot, ParseMode

from telegram import Bot
from telegram.constants import ParseMode
import html
from datetime import datetime, timedelta

async def aprovar_depositos_automaticamente():
    """
    Aprova depósitos pendentes automaticamente que ultrapassaram 1 minuto.
    Credita saldo, gera comissões para indicadores e envia notificações.
    """
    bot = Bot(token=BOT_TOKEN)
    pendentes = carregar_json(PENDENTES_FILE)
    usuarios = carregar_json(USERS_FILE)

    depositos_para_processar = list(pendentes.items())

    for pid, pedido in depositos_para_processar:
        if not isinstance(pedido, dict):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Pedido inválido: {pid}")
            continue

        if pedido.get("tipo") != "deposito" or pedido.get("status") != "pendente":
            continue

        data_criacao_str = pedido.get("data_criacao")
        if not data_criacao_str:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] data_criacao ausente para PID {pid}")
            continue

        try:
            data_criacao = datetime.strptime(data_criacao_str, "%d/%m/%Y %H:%M")
        except ValueError as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Erro ao parsear data_criacao para PID {pid}: {e}")
            continue

        if datetime.now() < data_criacao + timedelta(minutes=1):
            continue

        user_id = str(pedido.get("user_id"))
        valor = float(pedido.get("valor", 0))
        nome_usuario = pedido.get("nome", "Usuário")
        username = pedido.get("username")
        username_display = f"@{username}" if username and username.strip() else nome_usuario

        data_aprovacao_formatada = datetime.now().strftime("%d/%m/%Y %H:%M")

        if user_id not in usuarios:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Usuário {user_id} não encontrado para PID {pid}")
            continue

        # Credita saldo só se ainda não foi creditado
        if not pedido.get("saldo_ja_creditado"):
            usuarios[user_id]["saldo"] = usuarios[user_id].get("saldo", 0) + valor
            usuarios[user_id]["deposito_total"] = usuarios[user_id].get("deposito_total", 0) + valor
            usuarios[user_id]["total_investido"] = usuarios[user_id].get("total_investido", 0) + valor
            pedido["saldo_ja_creditado"] = True  # marca que o saldo já foi creditado

            # --- Comissões automáticas para indicadores ---
            percentuais = {1: 0.08, 2: 0.03, 3: 0.01}
            usuario_atual = usuarios[user_id]

            for nivel in range(1, 4):
                indicador_id = usuario_atual.get("indicador")
                if not indicador_id or indicador_id not in usuarios:
                    break

                usuario_indicante = usuarios[indicador_id]
                comissao = round(valor * percentuais[nivel], 2)
                usuario_indicante["saldo"] = usuario_indicante.get("saldo", 0) + comissao

                if "comissoes" not in usuario_indicante:
                    usuario_indicante["comissoes"] = {"1": 0, "2": 0, "3": 0}
                usuario_indicante["comissoes"][str(nivel)] = usuario_indicante["comissoes"].get(str(nivel), 0) + comissao

                try:
                    await bot.send_message(
                        chat_id=int(indicador_id),
                        text=(
                            f"🎉 Você recebeu uma comissão de nível {nivel}!\n"
                            f"💰 Valor: {comissao:.2f} MZN\n"
                            f"💵 Depósito de {valor:.2f} MZN\n"
                            f"👤 Do usuário {user_id}"
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    print(f"Erro ao enviar comissão para {indicador_id}: {e}")

                usuario_atual = usuario_indicante
            # --- FIM ---

        # Atualiza status e histórico do pedido
        pedido["status"] = "aprovado_automaticamente"
        pedido["data_aprovacao_automatica"] = data_aprovacao_formatada

        historico_lista = usuarios[user_id].get("historico", [])
        if not isinstance(historico_lista, list):
            historico_lista = []

        item_encontrado = next((item for item in historico_lista if str(item.get("id")) == str(pid)), None)
        if item_encontrado:
            item_encontrado["status"] = "aprovado"
            item_encontrado["data"] = data_aprovacao_formatada
        else:
            historico_lista.append({
                "id": pid,
                "tipo": "deposito",
                "valor": valor,
                "valor_liquido": valor,
                "status": "aprovado",
                "data": data_aprovacao_formatada,
                "automatico": True
            })
        usuarios[user_id]["historico"] = historico_lista

        # Notifica usuário
        try:
            await bot.send_message(
                chat_id=int(user_id),
                text=(
                    f"✅ Olá, {nome_usuario}!\n\n"
                    f"Seu depósito de *{valor:.2f} MZN* foi *aprovado automaticamente* em {data_aprovacao_formatada}.\n"
                    "O valor já está disponível na sua conta."
                ),
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
        except Exception as e:
            print(f"Erro ao enviar mensagem para usuário {user_id}: {e}")

        # Notifica canal
        try:
            nome_html = html.escape(nome_usuario)
            username_html = html.escape(username_display)
            texto_canal = (
                "💎 <b>NOVO DEPÓSITO CONFIRMADO (AUTO)</b> 💎\n\n"
                f"👤 <b>Usuário:</b> {nome_html} {username_html}\n"
                f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
                f"💵 <b>Depósito realizado:</b> <code>{valor:.2f} MZN</code>\n"
                f"📆 <b>Confirmado em:</b> <code>{data_aprovacao_formatada}</code>\n\n"
                "✅ Depósito processado automaticamente.\n"
                f"👉 <a href='https://t.me/AgrotechFund_bot?start={user_id}'>Clique aqui e comece a ganhar</a>"
            )
            await bot.send_message(
                chat_id=CANAL_ID,  # precisa ser @canal ou -100xxxx
                text=texto_canal,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
        except Exception as e:
            print(f"Erro ao enviar mensagem para o canal: {e}")

    # Salva arquivos
    salvar_json(PENDENTES_FILE, pendentes)
    salvar_json(USERS_FILE, usuarios)

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Aprovação automática de depósitos concluída.")                                                           
                                                
#async def limpar_usuarios_cmd(update: Update, context: ContextTypes
#((DEFAULT_TYPE):
  #  limpar_usuarios_invalidos()
#    await update.message.reply_text("✅ Usuários inválidos foram limpos com sucesso!")

import asyncio
#from telegram.ext import AppBuilder, CommandHander, CallbackQueryHandler, MessageHandler, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import timezone
from telegram.ext.filters import User as FilterUser  # Import necessário

import os
import json
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)

# ✅ Garante que a pasta "historico" exista
os.makedirs("historico", exist_ok=True)

# ✅ Garante que os arquivos de histórico existam e iniciem vazios (se ainda não existem)
arquivos_historico = [
    "aprovados.json",
    "recusados.json",
    "expirados.json",
    "pendentes_saque.json",
    "pendentes_deposito.json"
]
for nome_arquivo in arquivos_historico:
    caminho = os.path.join("historico", nome_arquivo)
    if not os.path.exists(caminho):
        with open(caminho, "w") as f:
            json.dump({}, f)

def corrigir_historico_usuarios():
    caminho = "usuarios.json"
    usuarios = carregar_json(caminho)
    alterado = False

    for uid, dados in usuarios.items():
        historico = dados.get("historico")

        # Se estiver ausente, None ou com tipo errado
        if historico is None:
            print(f"⚠️ [uid: {uid}] 'historico' ausente. Criando lista vazia.")
            usuarios[uid]["historico"] = []
            alterado = True

        elif isinstance(historico, dict):
            print(f"⚠️ [uid: {uid}] 'historico' era dict. Convertendo para lista de 1 item.")
            usuarios[uid]["historico"] = [historico]
            alterado = True

        elif not isinstance(historico, list):
            print(f"⚠️ [uid: {uid}] 'historico' tinha tipo inválido ({type(historico)}). Substituindo por lista vazia.")
            usuarios[uid]["historico"] = []
            alterado = True

    if alterado:
        salvar_json(caminho, usuarios)
        print("✅ Arquivo 'usuarios.json' corrigido e salvo.")
    else:
        print("✅ Nenhuma correção necessária no 'historico'.")

async def admin_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "ver_resgates":
        await mostrar_resgates_admin(update, ctx)

async def mostrar_menu_cb(update, context):
    await update.callback_query.answer()
    
    # Apaga a mensagem antiga
    try:
        await update.callback_query.message.delete()
    except:
        pass  # Caso já tenha sido apagada ou não exista
    
    # Envia a nova mensagem com o teclado
    await update.effective_chat.send_message(
        "Escolha uma opção abaixo:",
        reply_markup=teclado_usuario()
    )

async def generic_cb(update, ctx):
    query = update.callback_query
    await query.answer()
    if query.data == "coletar_lucro":
        await ajuda_coletar_cb(update, ctx)
        return
    # outros callbacks...
from flask import Flask
import threading
import os
import asyncio

#import os, json

#USERS_FILE = "usuarios.json"

# Apagar o arquivo se existir
#if os.path.exists(USERS_FILE):
    #os.remove(USERS_FILE)

# Criar novamente vazio
#with open(USERS_FILE, "w", encoding="utf-8") as f:
    #json.dump({}, f, indent=4, ensure_ascii=False)

#print("✅ usuarios.json apagado e recriado vazio!")

import requests
import threading
import time

def manter_online():
    while True:
        try:
            requests.get("https://agrotechfund.onrender.com")
        except:
            pass
        time.sleep(300)  # 5 minutos

# Inicia em thread separada
threading.Thread(target=manter_online, daemon=True).start()

# ✅ FUNÇÃO PRINCIPAL ASSÍNCRONA
async def iniciar_bot():
    global usuarios, pendentes
    usuarios = carregar_json(USERS_FILE)
    pendentes = carregar_json(PENDENTES_FILE)

    app = ApplicationBuilder().token(TOKEN).build()

    # ✅ COMANDOS
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(CommandHandler("saldo", saldo))
    #app.add_handler(CommandHandler("sacar", sacar))
    app.add_handler(CommandHandler("planos", planos))
    #app.add_handler(CommandHandler("coletar", coletar))
    #app.add_handler(CommandHandler("meus_planos", meus_planos))
    #app.add_handler(CommandHandler("historico", historico))
    #app.add_handler(CommandHandler("indicacao", indicacao))
    #app.add_handler(CommandHandler("depositar", depositar))
    app.add_handler(CommandHandler("baixar_usuarios", baixar_usuarios))
    app.add_handler(CommandHandler("ver_pendentes", ver_pendentes))
    app.add_handler(CommandHandler("limpar_saldo_corrompido", limpar_saldo_corrompido))
    
    app.add_handler(CallbackQueryHandler(abrir_menu_cb, pattern="abrir_menu"))
    
    app.add_handler(CommandHandler("listar_usuarios", listar_usuarios_cb))
    #app.add_handler(CommandHandler("usuario", usuario_cmd))
    app.add_handler(CallbackQueryHandler(paginacao_usuarios_cb, pattern=r"^listar_usuarios"))
    app.add_handler(CallbackQueryHandler(ver_usuario_cb, pattern=r"^ver_usuario"))

    app.add_handler(CallbackQueryHandler(ajuda_meusplanos_cb, pattern="^ajuda_meusplanos$"))
    app.add_handler(CallbackQueryHandler(mostrar_planos_ativos_cb, pattern="^mostrar_ativos$"))
    app.add_handler(CallbackQueryHandler(mostrar_planos_expirados_cb, pattern="^mostrar_expirados$"))
        
# ---------------- ADMIN ----------------
    app.add_handler(CallbackQueryHandler(criar_bonus_cb, pattern="^criar_bonus$"))
    app.add_handler(CallbackQueryHandler(ver_estatisticas_cb, pattern="^ver_estatisticas$"))
    app.add_handler(CallbackQueryHandler(estatisticas_avancadas_cb, pattern="^estatisticas_avancadas$"))
    app.add_handler(CallbackQueryHandler(notificacoes_cb, pattern="^notificacoes$"))
    app.add_handler(CallbackQueryHandler(gerenciar_usuarios_cb, pattern="^gerenciar_usuarios$"))
    app.add_handler(CallbackQueryHandler(admin_cb, pattern="^ver_resgates$"))
    app.add_handler(CallbackQueryHandler(mostrar_usuarios_cb, pattern="^usuarios"))
    app.add_handler(CallbackQueryHandler(listar_usuarios_cb, pattern="listar_usuarios$"))

# ---------------- USUÁRIO ----------------
    app.add_handler(CallbackQueryHandler(resgatar_bonus_cb, pattern="^resgatar_bonus$"))
    app.add_handler(CallbackQueryHandler(meus_ganhos_cb, pattern="^meus_ganhos$"))
    app.add_handler(CallbackQueryHandler(mostrar_menu_cb, pattern="^menu$"))
        
    #app.add_handler(CallbackQueryHandler(admin_user_cb, pattern="^admin_user|"))

# Inserir ID manual
    app.add_handler(CallbackQueryHandler(admin_manual_id_cb, pattern="^admin_manual_id$"))

# Captura do ID digitado
    #app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, capturar_id_usuario))
    # app.add_handler(CommandHandler("limpar_usuarios", limpar_usuarios_cmd))

    app.add_handler(CallbackQueryHandler(banco_mpesa, pattern="^banco_mpesa$"))
    app.add_handler(CallbackQueryHandler(banco_emola, pattern="^banco_emola$"))

    app.add_handler(CallbackQueryHandler(crypto_btc, pattern="^crypto_btc$"))

    # --- MAIN HANDLERS ---
    # Comando do admin
    app.add_handler(CommandHandler("admin_ban_menu", admin_ban_menu))

    # Callbacks do admin
    app.add_handler(CallbackQueryHandler(admin_banir_cb, pattern="^banir$"))
    app.add_handler(CallbackQueryHandler(admin_desbanir_cb, pattern="^desbanir$"))
    app.add_handler(CallbackQueryHandler(admin_bloquear_cb, pattern="^bloquear$"))
    app.add_handler(CallbackQueryHandler(admin_desbloquear_cb, pattern="^desbloquear$"))

    app.add_handler(CallbackQueryHandler(pedir_valor_saque_cb, pattern="^confirmar_valor_saque$"))

    app.add_handler(CallbackQueryHandler(vincular_conta, pattern="^vincular_conta$"))
# Callback para coletar lucro
    app.add_handler(CallbackQueryHandler(ajuda_coletar_cb, pattern="^coletar_lucro$"))
    app.add_handler(CallbackQueryHandler(ajuda_coletar_cb, pattern="^coletar_lucro$"))
    # ✅ CALLBACKS DE AJUDA
    app.add_handler(CallbackQueryHandler(ajuda_start_cb, pattern="^ajuda_start$"))
    app.add_handler(CallbackQueryHandler(ajuda_saldo_cb, pattern="^ajuda_saldo$"))
    app.add_handler(CallbackQueryHandler(ajuda_sacar_cb, pattern="^ajuda_sacar$"))
    app.add_handler(CallbackQueryHandler(ajuda_planos_cb, pattern="^ajuda_planos$"))
    app.add_handler(CallbackQueryHandler(ajuda_depositar_cb, pattern="^ajuda_depositar$"))
    app.add_handler(CallbackQueryHandler(ajuda_indicacao_cb, pattern="^ajuda_indicacao$"))
    app.add_handler(CallbackQueryHandler(ajuda_coletar_cb, pattern="^ajuda_coletar$"))
    app.add_handler(CallbackQueryHandler(ajuda_meusplanos_cb, pattern="^ajuda_meusplanos$"))
    app.add_handler(CallbackQueryHandler(ajuda_historico_cb, pattern="^ajuda_historico$"))
    app.add_handler(CallbackQueryHandler(ajuda_historico_cb, pattern="^historico_pag_"))
    app.add_handler(CallbackQueryHandler(ajuda_coletar_cb, pattern="^coletar_lucro$"))

    # Handler de textos gerais
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_valor_usuario))

    vincular_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(vincular_conta, pattern="^config_vincular$")],
    states={
        ESCOLHA_METODO: [
            CallbackQueryHandler(metodo_banco, pattern="^metodo_banco$"),
            CallbackQueryHandler(metodo_crypto, pattern="^metodo_crypto$"),
        ],
        BANCO_NUMERO: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_numero)],
        BANCO_NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_nome)],
        CRIPTO_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_wallet)],
    },
    fallbacks=[CallbackQueryHandler(configuracoes, pattern="^voltar_config$")],
    per_message=True   # 👈 adiciona isso
)

    app.add_handler(vincular_handler)

    app.add_handler(CallbackQueryHandler(deposito_valor_cb, pattern="^deposito_valor"))
    # Métodos de depósito e saque
    app.add_handler(CallbackQueryHandler(mostrar_planos_cb, pattern="^mostrar_planos$"))
    app.add_handler(CallbackQueryHandler(saldo_deposito_cb, pattern="^saldo_deposito$"))
    app.add_handler(CallbackQueryHandler(saldo_saque_cb, pattern="^saldo_saque$"))

    app.add_handler(CallbackQueryHandler(continuar_saque_cb, pattern="^continuar_saque$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_saque_com_senha))

    app.add_handler(CallbackQueryHandler(pedir_valor_saque_cb, pattern="^pedir_valor_saque$"))
    # ============================
    # REGISTRO DE HANDLERS - Depósito
    # ============================
    app.add_handler(CallbackQueryHandler(dep_tipo_cb, pattern="^dep_tipo\\|"))
    app.add_handler(CallbackQueryHandler(dep_metodo_cb, pattern="^dep_metodo\\|"))
    app.add_handler(CallbackQueryHandler(dep_crypto_cb, pattern="^dep_crypto\\|"))

    # Mensagens de texto para valor de depósito
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_valor_deposito))

    # Planos
    app.add_handler(CallbackQueryHandler(comprar_plano_cb, pattern="^comprar\\|"))
    app.add_handler(CallbackQueryHandler(confirmar_compra_plano_cb, pattern="^confirmar_compra\\|"))

    # Caso haja botão "Voltar"
    app.add_handler(CallbackQueryHandler(ajuda, pattern="^ajuda$"))

    app.add_handler(CallbackQueryHandler(banco_mpesa, pattern="^banco_mpesa$"))
    app.add_handler(CallbackQueryHandler(banco_emola, pattern="^banco_emola$"))

# --- Handlers a adicionar no seu bot principal ---
    app.add_handler(CallbackQueryHandler(change_lang_cb, pattern="^change_lang$"))
    app.add_handler(CallbackQueryHandler(set_lang_cb, pattern="^lang_.*$"))

# ✅ CALLBACK CONFIGURAÇÕES
    app.add_handler(CallbackQueryHandler(configuracoes, pattern="^configuracoes$"))

    app.add_handler(CallbackQueryHandler(baixar_usuarios, pattern="^baixar_usuarios$"))
# 📌 Handler do botão de Banimento no painel admin
    app.add_handler(CallbackQueryHandler(admin_ban_menu, pattern="^admin_ban_menu$"))


    # Comando para abrir Configurações (que já chama botão admin se for admin)
    app.add_handler(CommandHandler("config", configuracoes))

    # Logs de admin
    app.add_handler(CallbackQueryHandler(admin_logs_cb, pattern=r"^admin_logs(\|\d+)?$"))

# Callbacks do painel admin
    app.add_handler(CallbackQueryHandler(menu_admin_cb, pattern="^menu_admin$"))
    app.add_handler(CallbackQueryHandler(menu_admin_cb, pattern="^painel_admin$"))  # botão dentro de configs

# Gerenciar usuários (lista + paginação)
    app.add_handler(CallbackQueryHandler(admin_listar_usuarios_cb, pattern="^admin_usuarios$"))
    app.add_handler(CallbackQueryHandler(admin_listar_usuarios_cb, pattern=r"^admin_page\|"))

# Selecionar usuário
    app.add_handler(CallbackQueryHandler(admin_user_cb, pattern=r"^admin_user\|"))

# Confirmação ou cancelamento da ação
    app.add_handler(CallbackQueryHandler(admin_confirmar_cb, pattern="^admin_confirmar$"))
    app.add_handler(CallbackQueryHandler(admin_cancelar_cb, pattern="^admin_cancelar$"))

# Ações do admin (botões da tela que você mostrou)
    app.add_handler(CallbackQueryHandler(admin_acao_cb, pattern="^admin_saldo$"))
    app.add_handler(CallbackQueryHandler(admin_acao_cb, pattern="^admin_plano$"))
    app.add_handler(CallbackQueryHandler(admin_acao_cb, pattern="^admin_reset_senha$"))
    app.add_handler(CallbackQueryHandler(admin_acao_cb, pattern="^admin_aprovar_deposito$"))
    app.add_handler(CallbackQueryHandler(admin_acao_cb, pattern="^admin_remover_valor$"))

# Processar entrada de texto depois de clicar numa ação
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_input_process))


    # ✅ CALLBACKS GERAIS
    app.add_handler(CallbackQueryHandler(aprovar_recusar_cb, pattern="^(aprovar|recusar)\\|"))
    #app.add_handler(CallbackQueryHandler(dep_mtd_cb, pattern="^dep_mtd\\|"))
    app.add_handler(CallbackQueryHandler(limpar_saldo_corrompido, pattern="^limpar_saldo$"))

    app.add_handler(CallbackQueryHandler(ver_pendentes, pattern="^ver_pendentes$"))
    # ✅ MENSAGENS
    app.add_handler(MessageHandler(filters.PHOTO, processar_comprovante))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_textos))

# --- Vincular Conta ---
    app.add_handler(CallbackQueryHandler(vincular_conta, pattern="^config_vincular$"))
    app.add_handler(CallbackQueryHandler(metodo_banco, pattern="^metodo_banco$"))
    app.add_handler(CallbackQueryHandler(metodo_crypto, pattern="^metodo_crypto$"))
    app.add_handler(CallbackQueryHandler(pedir_numero, pattern="^banco_.*$"))
    app.add_handler(CallbackQueryHandler(pedir_wallet, pattern="^crypto_.*$"))

# salvar número e nome (entrada de texto)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_numero))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_nome))

# salvar wallet (entrada de texto)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_wallet))

# alterar conta
    app.add_handler(CallbackQueryHandler(confirmar_alteracao, pattern="^alterar_conta$"))
    app.add_handler(CallbackQueryHandler(alterar_conta, pattern="^confirmar_alterar$"))

# específicos banco
    app.add_handler(CallbackQueryHandler(banco_mpesa, pattern="^banco_mpesa$"))
    app.add_handler(CallbackQueryHandler(banco_emola, pattern="^banco_emola$"))

# específicos cripto
    app.add_handler(CallbackQueryHandler(crypto_btc, pattern="^crypto_btc$"))
    #app.add_handler(CallbackQueryHandler(crypto_eth, pattern="^crypto_eth$"))
    #app.add_handler(CallbackQueryHandler(crypto_usdt_trc20, pattern="^crypto_usdt_trc20$"))
    #app.add_handler(CallbackQueryHandler(crypto_usdt_bep20, pattern="^crypto_usdt_bep20$"))
    #app.add_handler(CallbackQueryHandler(crypto_bnb, pattern="^crypto_bnb$"))
    #app.add_handler(CallbackQueryHandler(crypto_xrp, pattern="^crypto_xrp$"))    
    
    # Conversa para vincular conta
    conv_config = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(vincular_conta, pattern="^config_vincular$"),
        ],
        states={
            ESCOLHA_METODO: [
                CallbackQueryHandler(metodo_banco, pattern="^metodo_banco$"),
                CallbackQueryHandler(metodo_crypto, pattern="^metodo_crypto$"),
                CallbackQueryHandler(confirmar_alteracao, pattern="^alterar_conta$"),
                CallbackQueryHandler(alterar_conta, pattern="^confirmar_alterar$"),
            ],
            BANCO_NUMERO: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_numero)],
            BANCO_NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_nome)],
            CRIPTO_ESCOLHA: [
                CallbackQueryHandler(pedir_wallet, pattern="^crypto_"),
            ],
            CRIPTO_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_wallet)],
        },
        fallbacks=[
            CallbackQueryHandler(configuracoes, pattern="^voltar_config$"),
        ],
    )
    app.add_handler(conv_config)

    app.add_handler(CallbackQueryHandler(criar_senha_saque_cb, pattern="criar_senha_saque"))
    app.add_handler(CallbackQueryHandler(alterar_senha_saque_cb, pattern="alterar_senha_saque"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_senha_saque))

    app.add_handler(CallbackQueryHandler(config_seguranca_cb, pattern="^config_seguranca$"))
# Comando principal: /senha_saque
# ==========================
    app.add_handler(CommandHandler("senha_saque", senha_saque_cmd))

# ==========================
# Processa mensagem digitada pelo usuário (criação ou alteração de senha)
# ==========================
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_senha_saque))

# ==========================
# Callback dos botões
# ==========================

# Botão “Definir agora” (usuário ainda não tem senha)
    app.add_handler(CallbackQueryHandler(
    lambda update, ctx: update.callback_query.message.reply_text(
        "🔑 Digite agora a senha que deseja cadastrar (6 a 10 números):"
    ) or ctx.user_data.update({"criando_senha_saque": True}),
    pattern="^definir_senha$"
))

# Botão “Mudar senha” (usuário já tem senha)
    app.add_handler(CallbackQueryHandler(
    lambda update, ctx: update.callback_query.message.reply_text(
        "🔐 Envie sua senha atual para continuar e definir uma nova senha."
    ) or ctx.user_data.update({"mudando_senha_saque": True}),
    pattern="^mudar_senha$"
))

# Botão “Voltar” (apenas volta para menu principal/ajuda)
    app.add_handler(CallbackQueryHandler(
    lambda update, ctx: update.callback_query.message.reply_text(
        "⬅️ Voltando ao menu principal..."
    ),
    pattern="^voltar_senha$"
))

    # --- SCHEDULER ---
    scheduler = AsyncIOScheduler(timezone=timezone.utc)

    # Relatório diário
    scheduler.add_job(enviar_relatorio_diario, 'cron', hour=21, minute=59, args=[app])

    # Lembrete diário
    scheduler.add_job(enviar_lembrete_diario, 'cron', hour=13, minute=46, args=[app])
    
    # Semanal: domingo 21h UTC
    scheduler.add_job(enviar_relatorio_periodico, 'cron', day_of_week='sun', hour=18, minute=54, args=[app])
    
    # Mensal: último dia do mês 21h UTC
    scheduler.add_job(enviar_relatorio_periodico, 'cron', day='last', hour=18, minute=53, args=[app])
    
    # Aprovar depósitos automaticamente a cada 2 minutos
    scheduler.add_job(aprovar_depositos_automaticamente, 'interval', minutes=1)

    # 🚀 Inicia o scheduler apenas uma vez
    scheduler.start()

    #aiocron.crontab("0 0 * * *", func=coleta_automatica, args=(app,))
    
    print("🤖 Bot iniciado e rodando!")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    # 🚀 SERVIDOR WEB PARA 24/7 - ADICIONE ESTAS LINHAS
    from flask import Flask
    import threading
    import os
    import asyncio  # ✅ ADICIONE ESTE IMPORT
    
    flask_app = Flask(__name__)
    
    @flask_app.route('/')
    def home():
        return "🤖 Bot Online 24/7!"
    
    @flask_app.route('/health')
    def health():
        return "OK", 200
    
    def run_web_server():
        port = int(os.environ.get("PORT", 8080))
        flask_app.run(host='0.0.0.0', port=port)
    
    # Inicia servidor web em thread separada
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    print("✅ Servidor web ativo para 24/7!")
    # 🚀 FIM DAS LINHAS ADICIONAIS

    await asyncio.Event().wait()


# ✅ EXECUÇÃO
if __name__ == "__main__":
    import asyncio  # ✅ ADICIONE AQUI TAMBÉM
    asyncio.run(iniciar_bot())
