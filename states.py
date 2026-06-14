from aiogram.fsm.state import State, StatesGroup


class UserState(StatesGroup):
    waiting_code = State()


class AddMovieState(StatesGroup):
    name = State()
    code = State()
    genres = State()
    movie_file = State()
    clip = State()
    description = State()


class AddAdminState(StatesGroup):
    waiting_id = State()


class RemoveAdminState(StatesGroup):
    waiting_id = State()


class AddChannelState(StatesGroup):
    waiting_channel = State()


class DeleteMovieState(StatesGroup):
    waiting_code = State()


class BroadcastState(StatesGroup):
    waiting_message = State()
    confirm = State()
