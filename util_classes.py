from enum import Enum


class GameStates(Enum):
    INIT = "0"
    ACTIVE = "1"


class PlayerStates(Enum):
    DEFAULT = "0"
    SELECT_RECIPIENT = "1"
    SELECT_MONEY_TRANSFER = "2"
    SELECT_MONEY_FROM_BANK = "3"
    SELECT_MONEY_TO_BANK = "4"
    CONFIRM_TRANSFER = "5"
    CONFIRM_FROM_BANK = "6"
    CONFIRM_TO_BANK = "7"


class PlayerStatuses(Enum):
    ACTIVE = "0"
    SPECTATOR = "1"


class Transaction:
    def __init__(self):
        self.recipient_login = None
        self.money = None

    def set_recipient_login(self, login):
        self.recipient_login = login

    def set_money(self, money):
        self.money = money


class Player:
    def __init__(self, user_id, chat_id, status, login, money, state):
        self.user_id = user_id
        self.chat_id = chat_id
        self.status = status
        self.login = login
        self.money = money
        self.state = state
        self.transactions = list()
