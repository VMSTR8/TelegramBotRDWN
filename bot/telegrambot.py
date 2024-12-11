from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from tortoise import Tortoise

from handlers.admin_handler import router as admin_router
from handlers.cancel_handler import router as cancel_router
from handlers.join_handler import router as join_router
from handlers.start_handler import router as start_router


class AiogramBot:
    """
    A class for creating and configuring a bot using the aiogram library and aiohttp for webhook handling.

    Attributes:
        token (str): The bot's token used to interact with the Telegram API.
        webhook_url (str): The base URL for the webhook.
        webhook_path (str): The path for handling the webhook.
        host (str): The host on which the application will run.
        port (int): The port on which the application will run.
        bot (Bot): An instance of the aiogram bot.
        dispatcher (Dispatcher): A dispatcher for handling incoming messages and events.
        app (web.Application): An aiohttp web application instance for webhook processing.

    Methods:
        __init__(token, webhook_url, webhook_path, host, port):
            Initializes the bot with a token, webhook settings, and application parameters.

        on_startup():
            Called on application startup. Sets up the webhook for the bot.

        on_shutdown():
            Called on application shutdown. Closes database connections and removes the webhook.

        setup_routes():
            Registers all routes and handlers for the bot.

        startup_register():
            Registers the startup function in the dispatcher to set up the webhook.

        shutdown_register():
            Registers the shutdown function in the dispatcher to properly close database connections.

        setup_webhook():
            Configures webhook handling using aiohttp and connects the dispatcher and bot to the web application.
    """

    def __init__(
            self,
            token: str,
            webhook_url: str,
            webhook_path: str,
            host: str,
            port: int
    ):
        """
        Initializes the bot instance.

        :param token: The token used to authenticate the bot with the Telegram API.
        :param webhook_url: The base URL of the webhook.
        :param webhook_path: The path where webhook requests will be received.
        :param host: The host where the application will be running.
        :param port: The port the application will listen on.
        """
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
        """
        Called on application startup.

        Sets up the webhook for the bot to receive incoming requests.
        """
        await self.bot.set_webhook(
            f'{self.webhook_url}{self.webhook_path}'
        )

    async def on_shutdown(self) -> None:
        """
        Called on application shutdown.

        Closes database connections and removes the bot's webhook.
        """
        await Tortoise.close_connections()
        await self.bot.delete_webhook()

    def setup_routes(self) -> None:
        """
        Registers all routes and handlers for the bot.
        """
        self.dispatcher.include_router(cancel_router)
        self.dispatcher.include_router(start_router)
        self.dispatcher.include_router(admin_router)
        self.dispatcher.include_router(join_router)

    def startup_register(self) -> None:
        """
        Registers the startup function in the dispatcher.

        Registers the `on_startup` method to be called on application startup.
        """
        self.dispatcher.startup.register(self.on_startup)

    def shutdown_register(self) -> None:
        """
        Registers the shutdown function in the dispatcher.

        Registers the `on_shutdown` method to be called on application shutdown.
        """
        self.dispatcher.shutdown.register(self.on_shutdown)

    def setup_webhook(self) -> None:
        """
        Configures webhook handling using aiohttp.

        Registers the dispatcher, bot, and web server to handle incoming requests at the specified webhook path.
        """
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=self.dispatcher,
            bot=self.bot,
        )
        webhook_requests_handler.register(self.app, path=self.webhook_path)
        setup_application(self.app, self.dispatcher, bot=self.bot)

    def run_webhook(self) -> None:
        """
        Starts the bot using webhook mode.

        This method sets up all necessary routes, registers the startup and shutdown functions,
        and configures the webhook to handle incoming requests. After the setup, it runs the aiohttp
        application on the specified host and port.

        :raises: Any exception raised during the aiohttp server operation will be propagated.
        """
        self.setup_routes()
        self.startup_register()
        self.shutdown_register()
        self.setup_webhook()
        web.run_app(self.app, host=self.host, port=self.port)

    async def run_polling(self) -> None:
        """
        Starts the bot using polling mode.

        This method sets up all necessary routes, registers the shutdown function, and then starts
        polling for incoming updates from the Telegram API. It will continuously check for new messages
        and other events, handling them with the registered handlers.

        This method is useful for environments where webhooks cannot be used (e.g., local development).

        :raises: Any exception raised during the polling operation will be propagated.
        """
        self.setup_routes()
        self.shutdown_register()
        await self.dispatcher.start_polling(self.bot)
