import asyncio
import random
import time
import traceback
from datetime import datetime


class BingoGame:
    def __init__(self, room_id, admins, subscription, bot):
        self.bot = bot
        self.room_id = room_id
        self.participants = {}
        self.participants_info = None
        self.generated_numbers_log = []
        self.game_control = False
        self.game_active = False
        self.player_warnings = {}
        self.muted_players = {}
        self.pending_verification = None
        self.participants_task = None
        self.bingo_task = None
        self.admins = admins
        self.subscription = subscription


    async def send_message(self, message):
        try:
            await self.bot.api.send_text_message(self.room_id, message)
            print(f"Сообщение отправлено в комнату {self.room_id}: {message}")
        except Exception:
            print(f"Ошибка при отправке сообщения: {traceback.format_exc()}")


    async def generate_bingo_numbers(self):
        try:
            while self.game_active:
                new_numbers = random.sample(range(1, 101), 5)
                new_numbers_string = " | ".join(map(str, new_numbers))
                self.generated_numbers_log.append(new_numbers_string)

                combined_message = "\n".join(self.generated_numbers_log)
                await self.send_message(f"🎱 Новые числа: \n{combined_message}")
                await asyncio.sleep(10)
        finally:
            self.bingo_task = None


    async def collect_participants(self):
        try:
            while len(self.participants) < 50 and self.game_control and not self.game_active:
                await self.send_message(
                    f"🎲 Ждём участников! Напишите 5 чисел от 1 до 100. Осталось мест: {50 - len(self.participants)}"
                )
                await asyncio.sleep(10)
            if self.game_control and not self.game_active:
                await self.start_game()
        finally:
            self.participants_task = None


    async def start_game(self):
        if self.game_active:
            return
        self.game_active = True
        participants_info = "\n".join([f"{user}: {numbers}" for user, numbers in self.participants.items()])
        await self.send_message(f"🎮 Игра начинается!\nУчастники:\n{participants_info}")

        if self.bingo_task is None:
            self.bingo_task = asyncio.create_task(self.generate_bingo_numbers())


    async def end_game(self):
        self.game_control = False
        self.game_active = False
        self.participants.clear()
        self.generated_numbers_log.clear()

        if self.bingo_task:
            self.bingo_task.cancel()
            self.bingo_task = None

        if self.participants_task:
            self.participants_task.cancel()
            self.participants_task = None

        await self.send_message("⏲️ Игра завершена. Спасибо за участие!")


    async def handle_message(self, sender, message):
        print(self.admins)
        if self.subscription < datetime.now():
            mes = "Cрок действия подписки окончен, пожалуйста, продлите подписку"
            await self.send_message(mes)
            return


        if sender in self.muted_players:
            return  # Игнорируем сообщения от пользователей в муте

        if sender in self.admins:
            print(self.admins)
            await self.handle_admin_commands(sender, message)
            return

        if not self.game_control:
            return

        if "бинго" in message.lower() and self.game_active:
            await self.check_bingo(sender)
        elif not self.game_active and self.game_control and sender not in self.participants:
            await self.register_participant(sender, message)


    async def handle_admin_commands(self, sender, message):
        try:
            if message.lower() == "on":
                self.game_control = True
                await self.send_message("🟢 Игра запущена!")
                if self.participants_task is None:
                    self.participants_task = asyncio.create_task(self.collect_participants())

            elif message.lower() == "off":
                await self.end_game()

            elif message.lower() == "start" and self.game_control:
                await self.start_game()

            elif message.lower() == "выполнено" and self.pending_verification:
                await self.send_message(f"🎉 Победа подтверждена! Поздравляем {self.pending_verification}!")
                self.pending_verification = None
                await self.end_game()

            elif message.lower() == "не выполнено" and self.pending_verification:
                await self.send_message("⚠️ Победа отклонена. Игра продолжается!")
                self.pending_verification = None
                self.game_active = True
                if self.bingo_task is None:
                    self.bingo_task = asyncio.create_task(self.generate_bingo_numbers())
        except:
            print(traceback.format_exc())


    async def register_participant(self, sender, message):
        numbers = [int(num) for num in message.split() if num.isdigit() and 0 <= int(num) <= 100]
        if len(numbers) >= 5:
            self.participants[sender] = numbers[:5]
            await self.send_message(f"✅ {sender} присоединился с числами: {numbers[:5]}")

            self.participants_info = "\n".join([f"{user}: {nums}" for user, nums in self.participants.items()])
            await self.send_message(f"📋 Текущий список участников:\n{self.participants_info}")


    async def check_bingo(self, sender):
        user_numbers = self.participants.get(sender, [])
        all_generated_numbers = {num for line in self.generated_numbers_log for num in map(int, line.split(" | "))}

        if all(num in all_generated_numbers for num in user_numbers):
            await self.send_message(f"🎉 {sender} выиграл! Ожидаем подтверждения.")
            self.pending_verification = sender
            self.game_active = False
        else:
            await self.handle_incorrect_bingo(sender)


    async def handle_incorrect_bingo(self, sender):
        self.player_warnings[sender] = self.player_warnings.get(sender, 0) + 1
        if self.player_warnings[sender] < 3:
            await self.send_message(f"⚠️ {sender}, это неправильно! Предупреждение {self.player_warnings[sender]} из 3.")
        else:
            await self.send_message(f"🔇 {sender}, вы получили мут на 5 минут.")
            self.muted_players[sender] = time.time() + 300
            self.player_warnings[sender] = 0
            await asyncio.create_task(self.mute_user(sender, 300))


    async def mute_user(self, user_id, mute_duration):
        try:
            original_power_level = 0
            power_levels_response = await self.bot.async_client.room_get_state_event(self.room_id, "m.room.power_levels")
            power_levels = power_levels_response.content
            original_power_level = power_levels.get("users", {}).get(user_id, 0)
            power_levels["users"][user_id] = -1
            await self.bot.async_client.room_put_state(self.room_id, "m.room.power_levels", content=power_levels)

            await self.send_message(f"🔇 {user_id} приглушен на {mute_duration // 60} минут.")
            await asyncio.sleep(mute_duration)

            power_levels["users"][user_id] = original_power_level
            await self.bot.async_client.room_put_state(self.room_id, "m.room.power_levels", content=power_levels)
            self.muted_players.pop(user_id, None)

            await self.send_message(f"🔔 {user_id} теперь может снова писать сообщения.")
        except Exception:
            print(f"Ошибка мьюта {user_id}: {traceback.format_exc()}")
