from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from dotenv import load_dotenv

def main():
  load_dotenv()

  # Import commands and callbacks after loading env
  import os
  from bot.commands import (
    start_handler, help_handler, price_handler, convert_handler, pegcheck_handler,
    liqinfo_handler, liqmap_handler, oprange_handler, tokens_handler
  )
  from bot.callbacks import handle_callback_query

  # Initialize application with builder pattern
  application = Application.builder().token(os.getenv('TG_BOT_TOKEN')).build()

  # Register commands
  commands = {
    'start': start_handler,
    'help': help_handler,
    'price': price_handler,
    'convert': convert_handler,
    'pegcheck': pegcheck_handler,
    'liqinfo': liqinfo_handler,
    'liqmap': liqmap_handler,
    'oprange': oprange_handler,
    'tokens': tokens_handler
  }

  for command, handler in commands.items():
    application.add_handler(CommandHandler(command, handler))
  
  # Register callback handler
  application.add_handler(CallbackQueryHandler(handle_callback_query))

  # Add message handler for convert amount
  application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, convert_handler))

  # Start the bot
  application.run_polling()

if __name__ == '__main__':
  print("""
  ██████╗ ████████╗██████╗ 
  ██╔══██╗╚══██╔══╝██╔══██╗
  ██████╔╝   ██║   ██████╔╝
  ██╔══██╗   ██║   ██╔══██╗
  ██████╔╝   ██║   ██║  ██║
  ╚═════╝    ╚═╝   ╚═╝  ╚═╝
  Markets Telegram Bot v1.0
  """)

  main()
