from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from handlers.start_handler import router as start_router
from handlers.admin_handler import router as admin_router
from handlers.join_handler import router as join_router

from tortoise import Tortoise


class AiogramBot:
    def __init__(
            self,
            token: str,
            webhook_url: str,
            webhook_path: str,
            host: str,
            port: int
    ):
        self.token = token
        self.webhook_url = webhook_url
        self.webhook_path = webhook_path
        self.host = host
        self.port = port

        self.bot = Bot(
            token=self.token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )

        self.dispatcher = Dispatcher()

        self.app = web.Application()

    async def on_startup(self) -> None:
        await self.bot.set_webhook(
            f'{self.webhook_url}{self.webhook_path}'
        )

    async def on_shutdown(self) -> None:
        await Tortoise.close_connections()
        await self.bot.delete_webhook()

    def setup_routes(self) -> None:
        self.dispatcher.include_router(start_router)
        self.dispatcher.include_router(admin_router)
        self.dispatcher.include_router(join_router)

    def startup_register(self):
        self.dispatcher.startup.register(self.on_startup)

    def shutdown_register(self):
        self.dispatcher.shutdown.register(self.on_shutdown)

    def setup_webhook(self) -> None:
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=self.dispatcher,
            bot=self.bot,
        )
        webhook_requests_handler.register(self.app, path=self.webhook_path)
        setup_application(self.app, self.dispatcher, bot=self.bot)

    def run_webhook(self) -> None:
        """
        Основной метод запуска бота. Использовать на продакшене.
        Запускает бота через настроенный webhook.
        :return: None
        """
        self.setup_routes()
        self.startup_register()
        self.shutdown_register()
        self.setup_webhook()
        web.run_app(self.app, host=self.host, port=self.port)

    async def run_polling(self) -> None:
        """
        Запуск бота через long polling. Метод исключительно для
        тестирования. В отличие от запуска через webhook требует
        асинхронный запуск.

        Пример:
            asyncio.run(AiogramBot().run_polling())
        :return: None
        """
        self.setup_routes()
        self.shutdown_register()
        await self.dispatcher.start_polling(self.bot)
