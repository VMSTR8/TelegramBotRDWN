## О проекте
TelegramBotRDWN создается для перевода менеджерских задач с человека на чат-бот. Основной функционал, 
это анкетирование пользователей, которые желают вступить в команду; проведение опросов по предстоящим 
мероприятиям команды среди участников; а так же мелкие ежедневные задачи, в духе следить за своевременным 
прохождением опросов, создавать чаты в беседе-форуме на платформе Telegram, чистить удаленных из базы 
пользователей и все в таком духе.

Проект находится в стадии активной разработки.
## Стэк
* [python 3.13](https://www.python.org/)
* [aiogram 3.15](https://docs.aiogram.dev/en/v3.15.0/)
* [tortoise orm 0.22.1](https://tortoise.github.io/)

В качестве базы данных используется SQLite. В проекте нет "сложных" задач, связанных с базой данных, не 
требуется полнотекстовой поиск, поэтому было принято решение не использовать Postgres, а довольствоваться 
простенькой SQLite.
## Запуск и развертывание
Так как чат-бот сейчас находится в стадии активной разработки, то пока что предусмотрена возможность запустить 
бота через polling. После релиза версии 1.0 чат-бот будет работать через webhook (в качестве веб-сервера выбран 
nginx)

Для тестирования имеющегося функционала вам потребуется скачать репозиторий себе локально и перейти в папку 
bot/settings, после чего создать .env файл (переменные виртуального окружения):

```bash
git clone https://github.com/VMSTR8/TelegramBotRDWN
cd bot/settings
touch .env
```
Через vim наполняете файл по примеру ниже:
```bash
vim .env
```
Что записать в файл
```
DATABASE_URL=sqlite://database/botdatabase.sqlite3

BOT_TOKEN=токен вашего бота
ADMINS=1234567890 # пишите тут просто цифры своего tgid, можно через запятую, если их несколько

WEB_SERVER_HOST=127.0.0.1
WEB_SERVER_PORT=8080
WEBHOOK_PATH=/webhook
BASE_WEBHOOK_URL=тут пока что можно написать какой угодно url, без настроеннго nginx'а это просто заглушка
```
:qw чтобы сохранить все, что понаписали и выйти из vim.

Дальше делаем миграции базы данных.
Возвращаетесь в папку bot и прописываете следующие команды
```bash
cd .. # просто вернет вас в папку bot, ну или cd bot, если .env руками создавали
aerich init -t database.config.TORTOISE_ORM
aerich init-db
```
База данных инициализирована, можно ковырять бота.

**ВАЖНО!!!** В файле main.py закомментируйте строку с запуском бота через webhook, а строку с polling наоборот 
раскомментируйте.
```python
# POLLING MODE IS ONLY FOR TESTING
# Uncomment the line below to run the bot in polling mode for local testing
run(bot.run_polling())

# Start the bot in webhook mode
# bot.run_webhook()
```
Запуск бота:
```bash
python3 main.py
```

После релиза распишу и другие способы запуска (деплой через Docker, локальный билд через compose).