import math
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .helpers import (
    last, fetch_liquidity_map, convert, 
    pegcheck,
    get_tokens, format_price_message, 
    create_keyboard_layout,
    format_pegcheck_message 
)

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()

  data = query.data.split('_')
  action = data[0]

  if action == 'price':
    token = data[1]
    price_data = await last(token)
    message = await format_price_message(token, price_data)
    await query.edit_message_text(text=message, parse_mode='Markdown')

  elif action == 'convert':
    if data[1] == 'base':
      base_token = data[2]
      tokens = await get_tokens()
      quote_tokens = [t for t in tokens if t != base_token]
      keyboard = create_keyboard_layout(quote_tokens, callback_prefix=f'convert_quote_{base_token}', max_cols=3)
      reply_markup = InlineKeyboardMarkup(keyboard)
      await query.edit_message_text('Select quote token:', reply_markup=reply_markup)
    
    elif data[1] == 'quote':
      base_token, quote_token = data[2], data[3]
      context.user_data['convert'] = {
        'base': base_token,
        'quote': quote_token,
        'waiting_for_amount': True
      }
      await query.edit_message_text(
        f'Enter amount of {base_token} to convert to {quote_token}:'
      )

  elif action == 'pegcheck':
    if data[1] == 'base':
      base_token = data[2]
      tokens = await get_tokens()
      quote_tokens = [t for t in tokens if t != base_token]
      keyboard = create_keyboard_layout(quote_tokens, callback_prefix=f'pegcheck_check_{base_token}', max_cols=3)
      reply_markup = InlineKeyboardMarkup(keyboard)
      await query.edit_message_text('Select second token:', reply_markup=reply_markup)

    elif data[1] == 'check':
      base_token, quote_token = data[2], data[3]
      peg_data = await pegcheck(f'{base_token}.idx', f'{quote_token}.idx')
      message = await format_pegcheck_message(base_token, quote_token, peg_data)
      await query.edit_message_text(text=message, parse_mode='Markdown')

  elif action == 'liqmap':
    token = data[1]
    liq_map = await fetch_liquidity_map(token)
    liq_map_str = '\n'.join([f'{key}: {value}' for key, value in liq_map.items()])
    await query.edit_message_text(text=f'Liquidity Map for {token}:\n{liq_map_str}')
