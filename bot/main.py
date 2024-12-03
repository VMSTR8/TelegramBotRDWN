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
    bot = AiogramBot(
        token=str(BOT_TOKEN),
        webhook_url=str(BASE_WEBHOOK_URL),
        webhook_path=str(WEBHOOK_PATH),
        host=str(WEB_SERVER_HOST),
        port=int(WEB_SERVER_PORT),
    )

    run(init())

    # POLLING ЗАПУСКАЕТСЯ ТОЛЬКО ДЛЯ ТЕСТИРОВАНИЯ
    run(bot.run_polling())
    # bot.run_webhook()


if __name__ == '__main__':
    main()
