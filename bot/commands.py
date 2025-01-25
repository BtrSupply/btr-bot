from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .helpers import get_schema, get_tokens, last, convert, pegcheck, create_keyboard_layout, format_price_message, round_sigfig

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  help_text = """
*Welcome, I'm BTR Markets Bot!*

Available commands:
/price <token> - Get mark prices for a token
/convert <token1> <token2> [amount] - Convert using mark prices
/pegcheck <token1> <token2> - Check if stables hold their peg
/liqinfo <token.origin> - Get details about a specific pool or CEX
/liqmap <token> - Token's on and off-chain liquidity (soon)
/oprange <token1> <token2> - Estimate a pair optimal CL range (soon)
/tokens - List available tokens
/help - Show this help message
"""

  # Sending the message with Markdown formatting
  await update.message.reply_text(help_text, parse_mode='Markdown')

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await start_handler(update, context)

async def price_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if context.args and len(context.args) == 1:
    token = context.args[0]
    try:
      price_data = await last(token)
      if not price_data:
        await update.message.reply_text(f"No price data found for {token}")
        return
      
      message = await format_price_message(token, price_data)
      await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
      await update.message.reply_text(f"Error retrieving price for {token}: {str(e)}")
    return

  # If no token specified, show token selection keyboard
  tokens = await get_tokens()
  keyboard = create_keyboard_layout(tokens, callback_prefix='price', max_cols=3)
  reply_markup = InlineKeyboardMarkup(keyboard)
  await update.message.reply_text('Select a token:', reply_markup=reply_markup)

async def convert_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  # Handle direct command with arguments
  if context.args and len(context.args) >= 2:
    try:
      conv_args = {
        'base': context.args[0],
        'quote': context.args[1],
        'amount': float(context.args[2]) if len(context.args) > 2 else None
      }
      
      # Validate tokens
      tokens = await get_tokens()
      if conv_args['base'] not in tokens or conv_args['quote'] not in tokens:
        await update.message.reply_text(
          f"Invalid tokens. Use /tokens to see available options.\n"
          f"Usage: /convert {conv_args['base']} {conv_args['quote']} [amount]"
        )
        return

      if conv_args['amount'] is None:
        # If no amount provided, store tokens and wait for amount
        context.user_data['convert'] = {
          'base': conv_args['base'],
          'quote': conv_args['quote'],
          'waiting_for_amount': True
        }
        await update.message.reply_text(
          f"Enter amount of {conv_args['base']} to convert to {conv_args['quote']}:"
        )
        return

      # If amount provided, do conversion directly
      result = await convert(conv_args['base'], conv_args['quote'], conv_args['amount'])
      
    except ValueError:
      await update.message.reply_text(
        "Invalid amount format. Usage: /convert TOKEN1 TOKEN2 [amount]\n"
        "Example: /convert USDT USDC 1000"
      )
      return
    except Exception as e:
      await update.message.reply_text(f"Error during conversion: {str(e)}")
      return

  # Handle amount input for previous token selection
  elif 'convert' in context.user_data and context.user_data['convert'].get('waiting_for_amount'):
    try:
      conv_args = context.user_data['convert']
      conv_args['amount'] = float(update.message.text)
      result = await convert(conv_args['base'], conv_args['quote'], conv_args['amount'])
      
    except ValueError:
      await update.message.reply_text("Please enter a valid number")
      return
    except Exception as e:
      await update.message.reply_text(f"Error during conversion: {str(e)}")
      return
    finally:
      context.user_data.clear()  # Reset conversion state

  # Initial convert command - show token selection
  else:
    context.user_data.clear()
    tokens = await get_tokens()
    keyboard = create_keyboard_layout(tokens, callback_prefix='convert_base', max_cols=3)
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Select base token:', reply_markup=reply_markup)
    return
  
  # Format and send conversion result
  message = f"""
*--------------------------------------------------------
💱 Conversion Result
--------------------------------------------------------*
{round_sigfig(conv_args['amount'])} {conv_args['base']} = {round_sigfig(result['quote_amount'])} {conv_args['quote']}
Rate: 1 {conv_args['base']} = {result['rate']} {conv_args['quote']}
--------------------------------------------------------
"""
  await update.message.reply_text(message, parse_mode='Markdown')

async def pegcheck_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  # Handle direct command with arguments
  if context.args and len(context.args) == 2:
    try:
      base_token = context.args[0].upper()
      quote_token = context.args[1].upper()
      
      # Validate tokens
      tokens = await get_tokens()
      if base_token not in tokens or quote_token not in tokens:
        await update.message.reply_text(
          f"Invalid tokens. Use /tokens to see available options.\n"
          f"Usage: /pegcheck {base_token} {quote_token}"
        )
        return

      peg_data = await pegcheck(f'{base_token}.idx', f'{quote_token}.idx')
      status = '✅ Pegged' if abs(peg_data['deviation']) <= peg_data['max_deviation'] else '⚠️ Deviating'
      message = f"""
*--------------------------------------------------------
🔗 Peg Check {base_token}-{quote_token}
--------------------------------------------------------
Status: {status}
Deviation: {peg_data['deviation']*100:.2f}%
Base Price: {peg_data['base_price']}
Quote Price: {peg_data['quote_price']}
--------------------------------------------------------*
"""
      await update.message.reply_text(message, parse_mode='Markdown')
      return
      
    except Exception as e:
      await update.message.reply_text(f"Error checking peg: {str(e)}")
      return

  # If no arguments, show token selection keyboard
  tokens = await get_tokens()
  keyboard = create_keyboard_layout(tokens, callback_prefix='pegcheck_base', max_cols=3)
  reply_markup = InlineKeyboardMarkup(keyboard)
  await update.message.reply_text('Select first token:', reply_markup=reply_markup)

async def liqmap_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  tokens = await get_tokens()
  keyboard = create_keyboard_layout(tokens, callback_prefix='liqmap', max_cols=3)
  reply_markup = InlineKeyboardMarkup(keyboard)
  await update.message.reply_text('Select a token:', reply_markup=reply_markup)

async def oprange_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  tokens = await get_tokens()
  keyboard = [[InlineKeyboardButton(token, callback_data=f'oprange_base_{token}') for token in tokens]]
  reply_markup = InlineKeyboardMarkup(keyboard)
  await update.message.reply_text('Select first token:', reply_markup=reply_markup)

async def tokens_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  tokens = await get_tokens()
  token_list = '\n'.join([f'• {token}' for token in tokens])
  await update.message.reply_text(f'Available tokens:\n{token_list}')

async def liqinfo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if not context.args or len(context.args) != 1:
    await update.message.reply_text(
      "Please provide a token and pool ID in the format: /liqinfo {token}.{origin}"
    )
    return
  try:
    token, origin = context.args[0].split('.', 1)
    
    schema = await get_schema()
    if token not in schema or origin not in schema[token]['fields']:
      await update.message.reply_text("Invalid token or liquidity origin not found")
      return

    info = schema[token]['fields'][origin]
    info_text = f"""
--------------------------------------------------------
*💧 Liquidity Info for {token}.{origin}*
--------------------------------------------------------
"""
    if 'target' in info:
      info_text += f"\n*Target*\n| `{info['target']}`"
    if 'tags' in info:
      info_text += f"\n\n*Tags*\n"
      for tag in info['tags']:
        info_text += f"| `{tag}` "
    await update.message.reply_text(info_text, parse_mode='Markdown')

  except Exception as e:
    await update.message.reply_text(f"Error retrieving pool information: {str(e)}")
