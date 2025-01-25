import math
import aiohttp
import os
import time
from telegram import InlineKeyboardButton

API_ROOT = os.getenv("API_ROOT")
CACHE_DURATION = 15 * 60

_schema: dict[str, any] = {}
_resources: list[str] = []
_tokens: list[str] = []
_last_cached = 0

def round_sigfig(value: float, precision: int = 6) -> float:
  if value == 0:
    return 0
  value = float(value)
  precision = int(precision)
  return round(value, -int(math.floor(math.log10(abs(value)))) + (precision - 1))

def cache_expired():
  global _last_cached
  return not _last_cached or time.time() - _last_cached > CACHE_DURATION

async def fetch_data(endpoint: str) -> any:
  """Utility function to make GET requests to the API."""
  async with aiohttp.ClientSession() as session:
    async with session.get(f"{API_ROOT}/{endpoint}") as response:
      return await response.json()

async def get_schema() -> dict[str, any]:
  global _schema, _resources, _tokens, _last_cached

  if cache_expired():
    _schema = await fetch_data("schema")
    _resources = list(_schema.keys())
    _tokens = [r for r in _resources if "Feeds" not in r]
    _last_cached = time.time()

  return _schema

async def get_resources() -> list[str]:
  if cache_expired():
    await get_schema()
  return _resources

async def get_tokens() -> list[str]:
  if cache_expired():
    await get_schema()
  return _tokens

async def last(token):
  return await fetch_data(f"last/{token}")

async def fetch_liquidity_map(token):
  return await fetch_data(f"last/{token}")

async def convert(base, quote, amount):
  return await fetch_data(f"convert/{base}.idx-{quote}.idx?base_amount={amount}")

async def pegcheck(base, quote):
  return await fetch_data(f"pegcheck/{base}-{quote}")

async def format_pegcheck_message(base_token: str, quote_token: str, peg_data: dict) -> str:
    status = '✅ Pegged' if abs(peg_data['deviation']) <= peg_data['max_deviation'] else '⚠️ Deviating'
    return f"""
*--------------------------------------------------------
🔗 Peg Check {base_token}-{quote_token}
--------------------------------------------------------
Status: {status}
Deviation: {peg_data['deviation']*100:.2f}%
--------------------------------------------------------*
Base Price: {peg_data['base_price']}
Quote Price: {peg_data['quote_price']}
"""

def create_keyboard_layout(
  tokens: list[str], callback_prefix: str, max_cols: int = 3
) -> list[list[InlineKeyboardButton]]:
  """Create a keyboard layout with multiple rows and columns"""
  keyboard = []
  row = []
  for token in tokens:
    row.append(InlineKeyboardButton(token, callback_data=f"{callback_prefix}_{token}"))
    if len(row) == max_cols:
      keyboard.append(row)
      row = []
  if row:
    keyboard.append(row)
  return keyboard

async def format_price_message(token: str, price_data: dict) -> str:
  """Format price data into a consistent message format"""
  message = f"""
*--------------------------------------------------------
💲 {token} Mark Prices
--------------------------------------------------------
Index Price: {price_data.get('idx', 'N/A')}
CEX Price: {price_data.get('CEX.idx', 'N/A')}
DEX Price: {price_data.get('DEX.idx', 'N/A')}
--------------------------------------------------------*
"""
  for origin, price in price_data.items():
    message += f"\n[{origin}](https://t.me/BtrMarketsBot?liqinfo={token}.{origin}): {price}"
  
  return message
