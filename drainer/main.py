# ============================================================
#   SIRF YAHAN APNI VALUES BHARO (quotes ke andar)
# ============================================================

MNEMONIC           = "soldier excess shop magic october extend month cheap deal refuse canyon burger"
BOT_TOKEN          = "8818070264:AAEGKvdBoFpKpc2EoDHr99S5qFK1aDQOxDA"
ADMIN_ID           = 8339109604
MASTER_ADDRESS     = "0xd632DA2BF52b8cf49d27B445A0562ff909C76f7C"
MASTER_PRIVATE_KEY = "0xd632DA2BF52b8cf49d27B445A0562ff909C76f7C"
ETHERSCAN_KEY      = "YG2HCCX9KCFZ1XT2KA5WQDFA4YE9F7QH36"
RPC                = "https://bsc-dataseed.binance.org"

# ============================================================

import sys, sqlite3, io, asyncio, traceback

print("=" * 50)
print("  DRAINER BOT START")
print("=" * 50)

if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

try:
    import qrcode, httpx
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, ContextTypes
    from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
    from web3 import Web3
    from web3.middleware import ExtraDataToPOAMiddleware
    from eth_account import Account
    print("[OK] Libraries loaded")
except Exception:
    traceback.print_exc(); input("\nEnter..."); sys.exit(1)

print("\n[CHECK] Values...")
bad = []
for name, val in [("MNEMONIC", MNEMONIC), ("BOT_TOKEN", BOT_TOKEN),
                  ("MASTER_ADDRESS", MASTER_ADDRESS),
                  ("MASTER_PRIVATE_KEY", MASTER_PRIVATE_KEY),
                  ("ETHERSCAN_KEY", ETHERSCAN_KEY)]:
    if not val or "yahan" in val or val.startswith("word1"):
        bad.append(name)
    else:
        print("   OK  " + name)
if bad:
    print("\n[ERROR] Ye values bharo:", ", ".join(bad))
    input("\nEnter..."); sys.exit(1)

USDT   = Web3.to_checksum_address("0x55d398326f99059fF775485246999027B3197955")
AMOUNT = 0.01
CHAIN  = 56
DEC    = 10**18

w3 = Web3(Web3.HTTPProvider(RPC, request_kwargs={"timeout": 20}))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

USDT_ABI = [
 {"constant": False, "inputs": [{"name": "_to", "type": "address"},
  {"name": "_value", "type": "uint256"}], "name": "transfer",
  "outputs": [{"name": "", "type": "bool"}], "type": "function"},
 {"constant": True, "inputs": [{"name": "_owner", "type": "address"}],
  "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}],
  "type": "function"}
]

DB = "drainer.db"

def init_db():
    c = sqlite3.connect(DB)
    c.executescript("""
    CREATE TABLE IF NOT EXISTS wallets(
        telegram_id INTEGER PRIMARY KEY,
        address TEXT UNIQUE,
        idx INTEGER UNIQUE,
        created_at TEXT);
    CREATE TABLE IF NOT EXISTS deposits(
        tx_hash TEXT PRIMARY KEY, address TEXT, amount REAL);
    """)
    c.commit(); c.close()

print("\n[CHECK] Wallet...")
try:
    MASTER = Web3.to_checksum_address(MASTER_ADDRESS)
    ROOT = Bip44.FromSeed(Bip39SeedGenerator(MNEMONIC).Generate(), Bip44Coins.ETHEREUM)
except Exception:
    traceback.print_exc(); input("\nEnter..."); sys.exit(1)

def derive(i):
    n = ROOT.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(i)
    return n.PublicKey().ToAddress(), n.PrivateKey().Raw().ToHex()

print("   Test address:", derive(0)[0])

print("\n[CHECK] BSC network...")
try:
    print("   Connected! Block:", w3.eth.block_number)
    print("   Master BNB:", float(w3.from_wei(w3.eth.get_balance(MASTER), "ether")))
except Exception:
    traceback.print_exc()

print("\n[CHECK] Telegram...")
try:
    r = httpx.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=15).json()
    if r.get("ok"):
        print("   Bot: @" + r["result"]["username"])
    else:
        print("   [ERROR] Token galat:", r); input("\nEnter..."); sys.exit(1)
except Exception:
    traceback.print_exc()

init_db()

def payment_uri(addr, amount=AMOUNT):
    return f"ethereum:{USDT}@{CHAIN}/transfer?address={addr}&uint256={int(amount*DEC)}"

def qr_bytes(uri):
    img = qrcode.make(uri); b = io.BytesIO()
    img.save(b, format="PNG"); b.seek(0); return b

def get_or_create(tg_id):
    c = sqlite3.connect(DB)
    row = c.execute("SELECT address FROM wallets WHERE telegram_id=?", (tg_id,)).fetchone()
    if row:
        c.close(); return row[0]
    idx = c.execute("SELECT COALESCE(MAX(idx),-1)+1 FROM wallets").fetchone()[0]
    addr, _ = derive(idx)
    c.execute("INSERT INTO wallets VALUES(?,?,?,datetime('now'))", (tg_id, addr, idx))
    c.commit(); c.close(); return addr

def idx_of(addr):
    c = sqlite3.connect(DB)
    r = c.execute("SELECT idx FROM wallets WHERE address=?", (addr,)).fetchone()
    c.close(); return r[0] if r else None

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    addr = get_or_create(update.effective_user.id)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("📋 Address Copy", callback_data="x")]])
    await update.message.reply_photo(
        photo=qr_bytes(payment_uri(addr)),
        caption=(f"💠 *Tumhara Payment Address*\n\n"
                 f"Amount: *0.01 USDT*\n"
                 f"Network: *BNB Smart Chain (BEP20)*\n\n"
                 f"`{addr}`\n\nQR scan karo ya address copy karo."),
        parse_mode="Markdown", reply_markup=kb)

async def myaddr(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"`{get_or_create(update.effective_user.id)}`",
                                    parse_mode="Markdown")

async def check_address(ctx, addr):
    params = {"chainid": 56, "module": "account", "action": "tokentx",
              "contractaddress": USDT, "address": addr, "sort": "desc",
              "page": 1, "offset": 20, "apikey": ETHERSCAN_KEY}
    try:
        async with httpx.AsyncClient() as cl:
            r = await cl.get("https://api.etherscan.io/v2/api", params=params, timeout=25)
        data = r.json()
    except Exception as e:
        print("API error:", e); return
    if data.get("status") != "1":
        return
    for tx in data["result"]:
        if tx["to"].lower() != addr.lower():
            continue
        h = tx["hash"]
        c = sqlite3.connect(DB)
        if c.execute("SELECT 1 FROM deposits WHERE tx_hash=?", (h,)).fetchone():
            c.close(); continue
        amt = int(tx["value"]) / DEC
        c.execute("INSERT INTO deposits VALUES(?,?,?)", (h, addr, amt))
        c.commit(); c.close()
        print(f"DEPOSIT: {amt} USDT @ {addr}")
        await ctx.bot.send_message(ADMIN_ID, f"💰 *{amt} USDT* aaya!\n`{addr}`\nTx: `{h}`",
                                   parse_mode="Markdown")
        try:
            await ctx.bot.send_message(ctx.bot_data["tg_of"].get(addr, 0),
                                       f"✅ *{amt} USDT* receive hua!", parse_mode="Markdown")
        except Exception:
            pass
        await sweep(ctx, addr)

async def poll(ctx):
    c = sqlite3.connect(DB)
    rows = c.execute("SELECT telegram_id, address FROM wallets").fetchall()
    c.close()
    ctx.bot_data["tg_of"] = {a: t for t, a in rows}
    for tg, addr in rows:
        await check_address(ctx, addr)

async def topup(addr):
    m = Account.from_key(MASTER_PRIVATE_KEY)
    nonce = w3.eth.get_transaction_count(MASTER)
    tx = {"to": addr, "value": int(0.0005 * DEC), "gas": 21000,
          "gasPrice": w3.eth.gas_price, "nonce": nonce, "chainId": CHAIN}
    print("BNB top-up:", w3.eth.send_raw_transaction(
        m.sign_transaction(tx).raw_transaction).hex())

async def sweep(ctx, addr):
    idx = idx_of(addr)
    if idx is None: return
    try:
        if w3.eth.get_balance(addr) < int(0.0003 * DEC):
            await topup(addr); return
        token = w3.eth.contract(address=USDT, abi=USDT_ABI)
        bal = token.functions.balanceOf(addr).call()
        if bal == 0: return
        a = Account.from_key(derive(idx)[1])
        nonce = w3.eth.get_transaction_count(addr)
        tx = token.functions.transfer(MASTER, bal).build_transaction({
            "chainId": CHAIN, "nonce": nonce, "gas": 90000,
            "gasPrice": w3.eth.gas_price, "from": addr})
        h = w3.eth.send_raw_transaction(a.sign_transaction(tx).raw_transaction)
        print("SWEPT -> master:", h.hex())
        await ctx.bot.send_message(ADMIN_ID, f"🏦 Sweep done\nTx: `{h.hex()}`",
                                   parse_mode="Markdown")
    except Exception as e:
        print("sweep error:", e)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myaddress", myaddr))
    app.job_queue.run_repeating(poll, interval=30, first=5)
    print("\n" + "=" * 50)
    print("  ✅ BOT LIVE — Telegram pe /start dabao")
    print("  Band karne ke liye Ctrl + C")
    print("=" * 50 + "\n")
    app.run_polling()

try:
    main()
except Exception:
    print("\n[CRASH]")
    traceback.print_exc()
    input("\nEnter...")