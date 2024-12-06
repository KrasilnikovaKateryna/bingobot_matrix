import traceback


async def send_message(bot, room_id, message):
    try:
        await bot.api.send_text_message(room_id, message)
        print(f"Сообщение отправлено в комнату {room_id}: {message}")
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {traceback.format_exc()}")


def send_message_no_async(bot, room_id, message):
    try:
        bot.api.send_text_message(room_id, message)
        print(f"Сообщение отправлено в комнату {room_id}: {message}")
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {traceback.format_exc()}")