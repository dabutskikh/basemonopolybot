import telebot
import config

from telebot import types
from util_classes import *

bot = telebot.TeleBot(config.TOKEN)

game_state = None
players = list()
forward_money = config.DEFAULT_FORWARD_MONEY


def get_markup(player, player_state):
    global players
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if player_state == PlayerStates.DEFAULT.value:
        markup.add(
            types.KeyboardButton("Перевод игроку"),
            types.KeyboardButton("Баланс"),
            types.KeyboardButton("Получить из банка"),
            types.KeyboardButton("Заплатить банку"),
            types.KeyboardButton("Пройти поле ВПЕРЕД"),
            types.KeyboardButton("Auf Wiedersehen")
        )

    elif player_state == PlayerStates.SELECT_RECIPIENT.value:
        for other_player in players:
            if other_player != player and other_player.status != PlayerStatuses.SPECTATOR.value:
                markup.add(types.KeyboardButton(other_player.login))

    elif player_state == PlayerStates.CONFIRM_TRANSFER.value:
        markup.add(
            types.KeyboardButton("ОК"),
            types.KeyboardButton("Отмена")
        )

    elif player_state == PlayerStates.CONFIRM_FROM_BANK.value:
        markup.add(
            types.KeyboardButton("ОК"),
            types.KeyboardButton("Отмена")
        )

    elif player_state == PlayerStates.CONFIRM_TO_BANK.value:
        markup.add(
            types.KeyboardButton("ОК"),
            types.KeyboardButton("Отмена")
        )
    return markup


def get_player(user_id):
    global players
    for player in players:
        if player.user_id == user_id:
            return player


def get_player_from_login(login):
    global players
    for player in players:
        if player.login == login:
            return player


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
                     "Привет! Я Шнобик - монопольный ассистент. Очень приятно\n"
                     "Для инициализации игры пусть один из вас напишет мне /init",
                     reply_markup=types.ReplyKeyboardRemove())
    bot.send_sticker(message.chat.id,
                     "CAACAgIAAxkBAAM7X4Wtt67dPjApATnd8qht2PXBte8AAl4JAAJ5XOIJ1ceysiubHYwbBA")


@bot.message_handler(commands=['init'])
def create(message):
    global game_state
    if game_state is not None:
        bot.send_message(message.chat.id,
                         "Игра уже создана")
        return
    game_state = GameStates.INIT.value
    bot.send_message(message.chat.id,
                     "Каждый должен ввести свой логин\n"
                     "Последний игрок должен написать мне /begin",
                     reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(commands=['begin'])
def begin(message):
    global game_state
    global players
    if game_state is None:
        bot.send_message(message.chat.id,
                         "Игра еще не создана",
                         reply_markup=types.ReplyKeyboardRemove())
        return
    if game_state == GameStates.ACTIVE.value:
        bot.send_message(message.chat.id,
                         "Игра уже началась")
        return
    game_state = GameStates.ACTIVE.value
    for player in players:
        bot.send_message(player.chat_id, "Игра началась",
                         reply_markup=get_markup(player, player.state))
        
        bot.send_sticker(player.chat_id,
                         "CAACAgIAAxkBAAMeX4WfV3Mah6QgVQFBpTaEXpXdOZcAAl8JAAJ5XOIJkICNeZlHYvobBA")


@bot.message_handler(func=lambda message: game_state == GameStates.INIT.value)
def join_to_game(message):
    global players
    for player in players:
        if player.chat_id == message.chat.id:
            bot.send_message(message.chat.id,
                             "Вы уже зарегистрированы")
            return
        if player.login == message.text:
            bot.send_message(message.chat.id,
                             "Этот логин уже занят. Попробуйте еще раз",
                             reply_markup=types.ReplyKeyboardRemove())
            return
    user_id = message.from_user.id
    chat_id = message.chat.id
    status = PlayerStatuses.ACTIVE.value
    login = message.text
    money = config.DEFAULT_START_MONEY
    state = PlayerStates.DEFAULT.value
    players.append(Player(user_id, chat_id, status, login, money, state))
    for player in players:
        bot.send_message(player.chat_id,
                         "Игрок " + login + " вошел в игру",
                         reply_markup=types.ReplyKeyboardRemove())
    bot.send_sticker(message.chat.id,
                         "CAACAgIAAxkBAANBX4WuHq8CZqbHQWp21QABtMPqRbfsAAJNCQACeVziCfzk6s8SBAFXGwQ")


@bot.message_handler(func=lambda message: game_state == GameStates.ACTIVE.value)
def parse_command(message):
    global players
    user_id = message.from_user.id
    player = get_player(user_id)
    command = message.text
    if player is None:
        bot.send_message(message.chat.id,
                         "Вы не зарегистрированы в текущей игре")
        return
    if player.status == PlayerStatuses.SPECTATOR.value:
        bot.send_message(message.chat.id,
                         "Вы наблюдате за игрой, так как банкрот")
        return
    if player.state == PlayerStates.DEFAULT.value:
        if command == "Перевод игроку":
            player.transactions.append(Transaction())
            player.state = PlayerStates.SELECT_RECIPIENT.value
            bot.send_message(message.chat.id,
                             "Для перевода выберете игрока",
                             reply_markup=get_markup(player, player.state))

        elif command == "Баланс":
            bot.send_message(message.chat.id,
                             "Ваш баланс " + str(player.money),
                             reply_markup=get_markup(player, player.state))

        elif command == "Получить из банка":
            player.state = PlayerStates.SELECT_MONEY_FROM_BANK.value
            bot.send_message(message.chat.id,
                             "Получить деньги из банка. Введите сумму",
                             reply_markup=types.ReplyKeyboardRemove())

        elif command == "Заплатить банку":
            player.state = PlayerStates.SELECT_MONEY_TO_BANK.value
            bot.send_message(message.chat.id,
                             "Заплатить деньги банку. Введите сумму",
                             reply_markup=types.ReplyKeyboardRemove())

        elif command == "Пройти поле ВПЕРЕД":
            player.money += forward_money
            bot.send_message(message.chat.id,
                             "Вы прошли поле ВПЕРЕД и получили " + str(forward_money) +
                             ". Ваш баланс " + str(player.money),
                             reply_markup=get_markup(player, player.state))
            bot.send_sticker(message.chat.id,
                             "CAACAgIAAxkBAAMgX4WfkO_v5WYUqetKLlanpibhC7oAAkkJAAJ5XOIJPogmK7FTfnkbBA")
            for other_player in players:
                if other_player != player:
                    bot.send_message(other_player.chat_id,
                                     "Игрок " + player.login + " прошел ВПЕРЕД и получил " + str(forward_money))

        elif command == "Auf Wiedersehen":
            if player.money != 0:
                bot.send_message(message.chat.id,
                                 "Вы пока еще не банкрот",
                                 reply_markup=get_markup(player, player.state))
                bot.send_sticker(message.chat.id,
                                 "CAACAgIAAxkBAAM4X4WhMDLrT3t0YY-Z7LzA-i6_fm4AAk4JAAJ5XOIJPyHcqwyiZs8bBA")
            else:
                player.status = PlayerStatuses.SPECTATOR.value
                bot.send_message(message.chat.id,
                                 "Вы объявлены банкротом. Попутного вiтра тобi в сраку",
                                 reply_markup=types.ReplyKeyboardRemove())
                bot.send_sticker(message.chat.id,
                                 "CAACAgIAAxkBAANJX4Wwdg1ejSOM9lqhCUiqjGTnisMAAkUJAAJ5XOIJkMTp3vTnv0kbBA")
                for other_player in players:
                    if other_player != player:
                        bot.send_message(other_player.chat_id,
                                         "Игрок " + player.login + " обанкротился")
                        bot.send_sticker(other_player.chat_id,
                                         "CAACAgIAAxkBAAM_X4Wt65dURmmY-7bMxlVKkm-BaIQAAlUJAAJ5XOIJr1qauV5Gf3EbBA")

    elif player.state == PlayerStates.SELECT_RECIPIENT.value:
        transaction = player.transactions[-1]
        if get_player_from_login(command) is None:
            bot.send_message(message.chat.id,
                             "Игрока с данным логином не существует")
            return
        transaction.set_recipient_login(command)
        player.state = PlayerStates.SELECT_MONEY_TRANSFER.value
        bot.send_message(message.chat.id,
                         "Перевод игроку " + command + ". Введите сумму",
                         reply_markup=types.ReplyKeyboardRemove())

    elif player.state == PlayerStates.SELECT_MONEY_TRANSFER.value:
        transaction = player.transactions[-1]
        try:
            money = int(command)
            if money < 0:
                raise ValueError
        except ValueError:
            bot.send_message(message.chat.id,
                             "Некорректный ввод. Попробуйте еще раз")
        else:
            if money > player.money:
                bot.send_message(message.chat.id,
                                 "У вас недостаточно денег. Введите другую сумму")
                return
            transaction.set_money(money)
            player.state = PlayerStates.CONFIRM_TRANSFER.value
            bot.send_message(message.chat.id, "Подтвердите", reply_markup=get_markup(player, player.state))

    elif player.state == PlayerStates.CONFIRM_TRANSFER.value:
        transaction = player.transactions[-1]
        player.state = PlayerStates.DEFAULT.value
        if command == "ОК":
            player.money -= transaction.money
            get_player_from_login(transaction.recipient_login).money += transaction.money
            bot.send_message(message.chat.id,
                             "Перевод игроку " + transaction.recipient_login +
                             " выполнен. Ваш баланс " + str(player.money),
                             reply_markup=get_markup(player, player.state))
            bot.send_sticker(message.chat.id,
                             "CAACAgIAAxkBAAMWX4WeGWKG-oUmopRCcpAosBv0IMUAAksJAAJ5XOIJyaZkWYxb6HgbBA")
            bot.send_message(get_player_from_login(transaction.recipient_login).chat_id,
                             "Игрок " + player.login + " перевел вам " + str(transaction.money) + ". Ваш баланс " +
                             str(get_player_from_login(transaction.recipient_login).money))
            bot.send_sticker(get_player_from_login(transaction.recipient_login).chat_id,
                             "CAACAgIAAxkBAAMcX4WeoTNSAxCO3SR4aC01voqdpoYAAkoJAAJ5XOIJbIauOPX8g6gbBA")

        else:
            player.transactions.remove(transaction)
            bot.send_message(message.chat.id,
                             "Перевод отменен",
                             reply_markup=get_markup(player, player.state))

    elif player.state == PlayerStates.SELECT_MONEY_FROM_BANK.value:
        try:
            money = int(command)
            if money < 0:
                raise ValueError
        except ValueError:
            bot.send_message(message.chat.id, "Некорректный ввод. Попробуйте еще раз")
        else:
            player.transactions.append(Transaction())
            transaction = player.transactions[-1]
            transaction.set_money(money)
            player.state = PlayerStates.CONFIRM_FROM_BANK.value
            bot.send_message(message.chat.id,
                             "Подтвердите",
                             reply_markup=get_markup(player, player.state))

    elif player.state == PlayerStates.CONFIRM_FROM_BANK.value:
        transaction = player.transactions[-1]
        player.state = PlayerStates.DEFAULT.value
        if command == "ОК":
            player.money += transaction.money
            bot.send_message(message.chat.id,
                             "Вы получили из банка " + str(transaction.money) + ". Ваш баланс " + str(player.money),
                             reply_markup=get_markup(player, player.state))
            bot.send_sticker(message.chat.id,
                             "CAACAgIAAxkBAAMPX4WdgEeCfZnHhozQrx-7UpHgmOAAAlIJAAJ5XOIJqcszPXH0_W0bBA")
            for other_player in players:
                if other_player != player:
                    bot.send_message(other_player.chat_id,
                                     "Игрок " + player.login + " получил из банка " + str(transaction.money))
        else:
            player.transactions.remove(transaction)
            bot.send_message(message.chat.id,
                             "Отмена операции",
                             reply_markup=get_markup(player, player.state))

    elif player.state == PlayerStates.SELECT_MONEY_TO_BANK.value:
        try:
            money = int(command)
            if money < 0:
                raise ValueError
        except ValueError:
            bot.send_message(message.chat.id,
                             "Некорректный ввод. Попробуйте еще раз")
        else:
            if money > player.money:
                bot.send_message(message.chat.id,
                                 "У вас недостаточно денег. Введите другую сумму")
                return
            player.transactions.append(Transaction())
            transaction = player.transactions[-1]
            transaction.set_money(money)
            player.state = PlayerStates.CONFIRM_TO_BANK.value
            bot.send_message(message.chat.id,
                             "Подтвердите",
                             reply_markup=get_markup(player, player.state))

    elif player.state == PlayerStates.CONFIRM_TO_BANK.value:
        transaction = player.transactions[-1]
        player.state = PlayerStates.DEFAULT.value
        if command == "ОК":
            player.money -= transaction.money
            bot.send_message(message.chat.id,
                             "Вы заплатили банку " + str(transaction.money) + ". Ваш баланс " + str(player.money),
                             reply_markup=get_markup(player, player.state))
            bot.send_sticker(message.chat.id,
                             "CAACAgIAAxkBAAMNX4WdCq-tUDMJQ_Uwt0CB752IEzAAAlsJAAJ5XOIJ5z5sFYhK9R8bBA")
            for other_player in players:
                if other_player != player:
                    bot.send_message(other_player.chat_id,
                                     "Игрок " + player.login + " заплатил банку " + str(transaction.money))
        else:
            player.transactions.remove(transaction)
            bot.send_message(message.chat.id,
                             "Отмена операции",
                             reply_markup=get_markup(player, player.state))


bot.polling(none_stop=True)
