import asyncio
import logging
import traceback
import simplematrixbotlib as botlib
from nio import MatrixRoom, RoomMessageText
from bingo_game import BingoGame
from db_utils import get_rooms, get_admins, get_subscription
from app import app

# Настройки
homeserver = "https://matrix-client.matrix.org"
user_id = "@username:matrix.org"
password = "password"

# Время ожидания для обновления данных о ново добавленных комнатах и продленных подписках в секундах
UPDATE_DATABASE_TIMEOUT = 432000 # 2 часа

creds = botlib.Creds(
    homeserver=homeserver,
    username=user_id,
    password=password,
    session_stored_file="session.txt"
)

config = botlib.Config()
config.encryption_enabled = True
bot = botlib.Bot(creds, config)

# Хранилища данных
games = {}
current_rooms = {}
subscription = {}
admins = {}

@bot.listener.on_message_event
async def message_callback(room: MatrixRoom, message: RoomMessageText):
    room_id = room.room_id

    if room_id not in current_rooms:
        return

    if message.sender == bot.async_client.user_id:  # Игнорируем сообщения от бота
        return

    # Инициализация игры для комнаты
    if room_id not in games:
        room_alias = current_rooms[room_id]
        if room_id not in subscription:
            subscription[room_id] = get_subscription(room_alias or room_id)
        games[room_id] = BingoGame(room_id, admins.get(room_id, []), subscription[room_id], bot)

    game = games[room_id]
    game.subscription = subscription[room_id]

    try:
        await game.handle_message(message.sender, message.body)
    except Exception:
        logging.error(f"Ошибка обработки сообщения в комнате {room_id}:\n{traceback.format_exc()}")

async def get_rooms_and_subscription():
    global current_rooms

    try:
        with app.app_context():
            # current_rooms.clear()
            rooms_id = get_rooms()

            for room_id in rooms_id:
                room_alias = f"#{room_id}" if not room_id.startswith('!') else None
                room_id_resolved = room_id
                if room_alias:
                    try:
                        response = await bot.async_client.room_resolve_alias(room_alias)
                        room_id_resolved = response.room_id
                    except Exception:
                        logging.warning(f"Не удалось разрешить алиас {room_alias}")
                        logging.error(response.message)

                current_rooms[room_id_resolved] = room_alias

            # Обновляем подписки
            for room_id, room_alias in current_rooms.items():
                await update_subscription(room_id, room_alias)

    except Exception:
        logging.error(f"Ошибка проверки новых комнат:\n{traceback.format_exc()}")

async def update_subscription(room_id, room_alias):
    try:
        alias_key = room_alias[1:] if room_alias else room_id
        subscription[room_id] = get_subscription(alias_key)
        await bot.async_client.join(room_id)
        db_rec_admins = get_admins(alias_key)
        admins[room_id] = db_rec_admins
    except Exception:
        logging.error(f"Ошибка обновления подписки для комнаты {room_id}:\n{traceback.format_exc()}")

async def monitor_new_rooms():
    while True:
        try:
            await get_rooms_and_subscription()
        except Exception:
            logging.error(f"Ошибка при мониторинге новых комнат:\n{traceback.format_exc()}")
        await asyncio.sleep(UPDATE_DATABASE_TIMEOUT)


@bot.listener.on_startup
async def startup(room_alias):
    try:
        await get_rooms_and_subscription()
        asyncio.create_task(monitor_new_rooms())
        logging.info("Бот успешно запущен и готов к работе!")
    except Exception:
        logging.error(f"Ошибка при старте:\n{traceback.format_exc()}")

if __name__ == "__main__":
    try:
        with app.app_context():
            bot.run()
    except KeyboardInterrupt:
        logging.info("Бот остановлен")
