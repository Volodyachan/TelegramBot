from aiogram import Bot, executor, types
from aiogram.dispatcher import Dispatcher
from aiogram.types.bot_command import BotCommand
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from random import choice
import os
from dotenv import load_dotenv

load_dotenv('./token.env')

TOKEN = os.getenv('TOKEN')

compliments = ['Ты прекрасен(на)', "У тебя будет хороший день", "У тебя всё получится", "Ты справишься",
               "Ты красивый(ая)", "У тебя крутой лук", "Ты класно выглядишь", "У тебя красивые глаза",
               "Ты супер", "У тебя яркая улыбка", "Ты просто космос"]

storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)

data = dict()


class FSMCommands(StatesGroup):
    admin = State()
    ch_st1 = State()
    ch_st2 = State()


async def checker_for_admin(ch: int, user_to_check: int):
    for name in (await bot.get_chat_administrators(chat_id=ch)):
        if name["user"]["id"] == user_to_check:
            return True
    return False


async def checker_for_owner(ch: int, user_to_check: int):
    name = await bot.get_chat_member(ch, user_to_check)
    if name["status"] == "creator":
        return True
    return False


@dp.message_handler(commands="start")
async def command_start(message: types.Message):
    data[message.chat.id] = data.get(message.chat.id, dict())
    await bot.set_my_commands(
        [
            BotCommand('start', 'запустить бота'),
            BotCommand('add_new_admin', 'Добавить администратора'),
            BotCommand('change_status', 'Поменять статус пользователя'),
            BotCommand('get_random_compliment', 'Получить рандомный комплимент'),
            BotCommand('darts', 'Сыграть в дартс'),
            BotCommand('ping_all', 'Отметить всех'),
            BotCommand('delete_bot', 'Удалить бота из чата')
        ])
    await message.answer("Бот сделан Гиро Владимиром в рамках курса ИПР")

@dp.message_handler(content_types=types.ContentType.NEW_CHAT_MEMBERS)
async def some_handler(message: types.Message):
    data[message.chat.id] = data.get(message.chat.id, dict())
    data[message.chat.id][message.from_user.username] = message.from_user.id


@dp.message_handler(commands="add_new_admin")
async def add_new_admin(message: types.Message):
    data[message.chat.id] = data.get(message.chat.id, dict())
    if await checker_for_admin(message.chat.id, message.from_user.id):
        await FSMCommands.admin.set()
        await message.answer("Укажите имя пользователя")
    else:
        await message.answer("Вы не являетесь администратором")


@dp.message_handler(state=FSMCommands.admin)
async def pull_admin(message: types.Message, state: FSMContext):
    res = message.text
    if message.text[0] == '@':
        res = message.text[1:len(message.text)]
    if res in data[message.chat.id].keys():
        res = data[message.chat.id][res]
    else:
        res = "no"

    if res == "no":
        await message.answer("В чате нет пользователя с таким именем")
        await state.finish()
    else:
        if await checker_for_admin(message.chat.id, res):
            await message.answer("Пользователь уже является администратором")
            await state.finish()
        else:
            await bot.promote_chat_member(chat_id=message.chat.id,
                                          user_id=res,
                                          can_manage_chat=True,
                                          can_change_info=True,
                                          can_delete_messages=True,
                                          can_promote_members=True,
                                          can_pin_messages=True,
                                          can_edit_messages=True,
                                          can_post_messages=True,
                                          can_invite_users=True)
            await message.answer("Новый администратор добавлен")
            await state.finish()


@dp.message_handler(commands="ping_all")
async def ping_all(message: types.Message):
    data[message.chat.id] = data.get(message.chat.id, dict())
    if await checker_for_admin(message.chat.id, message.from_user.id):
        cnt = 0
        ping_names: str = ""
        for user_name in data[message.chat.id].keys():
            if cnt % 5 == 4:
                await message.answer(ping_names)
                ping_names = ""
            ping_names += ('@' + user_name + ' ')
            cnt += 1
        if len(ping_names) != 0:
            await message.answer(ping_names)
    else:
        await message.answer("Вы не являетесь администратором")


@dp.message_handler(commands="change_status")
async def change_stat(message: types.Message):
    data[message.chat.id] = data.get(message.chat.id, dict())
    if await checker_for_admin(message.chat.id, message.from_user.id):
        await FSMCommands.ch_st1.set()
        await message.answer("Укажите имя пользователя")
    else:
        await message.answer("Вы не являетесь администратором")


@dp.message_handler(state=FSMCommands.ch_st1)
async def change_stat1(message: types.Message, state: FSMContext):
    res = message.text
    if message.text[0] == '@':
        res = message.text[1:len(message.text)]
    if res in data[message.chat.id].keys():
        res = data[message.chat.id][res]
    else:
        res = "no"

    if res == "no":
        await message.answer("В чате нет пользователя с таким именем")
        await state.finish()
    else:
        if await checker_for_owner(message.chat.id, res):
            await message.answer(f"{res}")
            await message.answer("Пользователь является владельцем")
            await state.finish()
            return
        await message.answer("Введите желаемый статус")
        await FSMCommands.ch_st2.set()
        async with state.proxy() as d:
            d['username'] = res


@dp.message_handler(state=FSMCommands.ch_st2)
async def change_stat2(message: types.Message, state: FSMContext):
    if len(message.text) > 16:
        await message.answer("Количество символов привышено, статус не изменён")
        await state.finish()
    else:
        async with state.proxy() as d:
            if not await checker_for_admin(message.chat.id, d['username']):
                await bot.promote_chat_member(chat_id=message.chat.id,
                                              user_id=d['username'])
            await bot.set_chat_administrator_custom_title(chat_id=message.chat.id,
                                                          user_id=d['username'],
                                                          custom_title=message.text)
        await message.answer("Статус изменён")
        await state.finish()


@dp.message_handler(commands='get_random_compliment')
async def compliment(message: types.Message):
    await message.answer(choice(compliments))


@dp.message_handler(commands='darts')
async def darts(message: types.Message):
    await bot.send_dice(chat_id=message.chat.id,
                        emoji="🎯",
                        protect_content=True)
    await message.answer(message.from_user.username)


@dp.message_handler(commands="delete_bot")
async def leave_chat(message: types.Message):
    if await checker_for_admin(message.chat.id, message.from_user.id):
        await message.answer("Бот удалён(")
        await bot.leave_chat(chat_id=message.chat.id)
    else:
        await message.answer("Вы не являетесь администратором")

@dp.message_handler()
async def collect_all_messages(message: types.Message):
    if message.from_user.id != bot.id:
        data[message.chat.id] = data.get(message.chat.id, dict())
        data[message.chat.id][message.from_user.username] = message.from_user.id

executor.start_polling(dp, skip_updates=True)
