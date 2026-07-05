from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """States for user registration flow"""
    waiting_for_language = State()
    waiting_for_full_name = State()
    waiting_for_role = State()
    waiting_for_phone = State()
    confirmation = State()
