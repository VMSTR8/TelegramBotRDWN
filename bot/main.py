from asyncio import run

from database.init import init
from telegrambot import AiogramBot
from settings.settings import (
    BOT_TOKEN,
    WEBHOOK_PATH,
    WEB_SERVER_PORT,
    WEB_SERVER_HOST,
    BASE_WEBHOOK_URL
)


def main() -> None:
    """
    Main entry point of the bot application.

    This function initializes the `AiogramBot` instance with the necessary configuration parameters
    such as the bot token, webhook URL, webhook path, server host, and port. It also initializes the
    database by running the `init` function before starting the bot.

    The bot is configured to run in webhook mode (not polling), which listens for updates via
    webhooks sent to the specified URL. For testing purposes, you can uncomment the polling line
    to run the bot in polling mode instead.

    Steps:
        1. Initialize the bot with necessary configuration.
        2. Initialize the database connection.
        3. Run the bot with webhook or polling mode.

    :raises: Any exception raised during the initialization or the running of the bot will be propagated.
    """
    bot = AiogramBot(
        token=str(BOT_TOKEN),
        webhook_url=str(BASE_WEBHOOK_URL),
        webhook_path=str(WEBHOOK_PATH),
        host=str(WEB_SERVER_HOST),
        port=int(WEB_SERVER_PORT),
    )

    # Initialize the database connection
    run(init())

    # POLLING MODE IS ONLY FOR TESTING
    # Uncomment the line below to run the bot in polling mode for local testing
    # run(bot.run_polling())

    # Start the bot in webhook mode
    bot.run_webhook()


if __name__ == '__main__':
    main()
