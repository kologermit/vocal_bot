import models, config, handlers, logger, logging
from DBManager import DBManager
from telebot import TeleBot

def main():
    logger.setup()
    logging.info("Start Vocal Teacher Bot")
    db_manager = DBManager(config.DB_FILENAME)
    db_manager.init_tables(models.all_models)
    bot = TeleBot(config.TOKEN)
    logging.info(bot.get_me())
    handlers.init(bot, db_manager)
    handlers.loop(bot)

if __name__ == "__main__":
    main()