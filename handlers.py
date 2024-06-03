import config, copy, datetime, logging, json, admin, os, urllib, magic
from telebot import TeleBot, types
from DBManager import DBManager
from Model import Model
from models import *
from answers import *

paragraph_template = """<b>§{paragraph}</b>\n<b>Тема: </b><i>{theme}</i>\n{description}"""

def to_menu(bot: TeleBot, message: types.Message, user: Model, db_manager: DBManager, menu_message: str="Меню"):
    user.state = "menu"
    db_manager.save_data(user)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(menu_theory_button, menu_tests_button, row_width=2)
    markup.add(menu_info_button, menu_statistic_button, row_width=2)
    bot.send_message(user.telegram_id, menu_message, parse_mode="HTML", reply_markup=markup)
    return True

def to_registration(bot: TeleBot, message: types.Message, user: Model, db_manager: DBManager, description: str=""):
    user.state = "registration-name"
    if description:
        bot.send_message(user.telegram_id, description, parse_mode="HTML")
    bot.send_message(user.telegram_id, "Отправьте ваше имя", reply_markup=types.ReplyKeyboardRemove())
    db_manager.save_data(user)
    return True

def start(bot: TeleBot, message: types.Message, user: Model, db_manager: DBManager):
    return to_registration(bot, message, user, db_manager, description)

def registration_name(bot: TeleBot, message: types.Message, user: Model, db_manager: DBManager):
    user.full_name = message.text
    user.state = "registration-class"
    db_manager.save_data(user)
    bot.send_message(user.telegram_id, "Теперь отправьте класс", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add
                     (*[types.KeyboardButton(str(i)) for i in range(1, 12)], row_width=3))
    return True

def registration_class(bot: TeleBot, message: types.Message, user: Model, db_manager: DBManager):
    if not message.text.isdigit() or not(1 <= int(message.text) <= 11):
        return False
    user.grade = int(message.text)
    return to_menu(bot, message, user, db_manager)

def send_description(bot: TeleBot, user: Model, text: str, files: list[str], markup=None):
    message = bot.send_message(user.telegram_id, text, parse_mode="HTML", reply_markup=markup)
    m = magic.Magic(mime=True, uncompress=True)
    for filepath in files:
        filepath = f"./tmp/files/{filepath}"
        if not os.path.exists(filepath):
            logging.warning(f"{filepath} not found!")
            continue
        for key, func in {
            "image": bot.send_photo,
            "audio": bot.send_audio,
            "video": bot.send_video
        }.items():
            if key in m.from_file(filepath):
                func(user.telegram_id, open(filepath, "rb"), reply_to_message_id=message.id)
    return 

def to_tests(bot: TeleBot, message: types.Message, user: Model, db_manager: DBManager):
    tests = db_manager.find_data(TestModel)
    bot.reply_to(message, "<b>Доступные тесты:</b>", parse_mode="HTML")
    for test in tests:
        text = test.description
        if test.rowid in user.accepted_tests:
            text = "<b>Тест пройден✅</b>\n" + test.description
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Пройти тест✍️", callback_data=json.dumps({"c": "testing", "id": test.rowid})))
        send_description(bot, user, text, test.files, markup)
    return True

def to_theory(bot: TeleBot, message: types.Message, user: Model, db_manager: DBManager):
    theorys = db_manager.find_data(TheoryModel)
    bot.reply_to(message, "<b>Доступная теория:</b>", parse_mode="HTML")
    logging.info(theorys)
    for theory in theorys:
        confirm_theory = "<b>Теория пройдена✅</b>\n"
        message = f"{confirm_theory if theory.rowid in user.accepted_theory else ''}<b>{theory.name}</b>\n{theory.description}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Изучить теорию", callback_data=json.dumps({"c": "theory", "id": theory.rowid})))
        send_description(bot, user, message, theory.files, markup)
    return True

def menu(bot: TeleBot, message: types.Message, user: Model, db_manager: DBManager):
    if message.text == menu_statistic_button:
        bot.reply_to(message, f"""<b><u>Статистика:</u></b>
<b>Имя: </b><i>{user.full_name}</i>
<b>Класс: </b><i>{user.grade}</i>
<b>Пройдено тем: </b><i>{len(user.accepted_theory)}</i>
<b>Решено тестов: </b><i>{len(user.accepted_tests)}</i>
<b>Первое сообщение: </b><i>{user.first_message}</i>""", parse_mode="HTML")
    if message.text == menu_info_button:
        bot.reply_to(message, description, parse_mode="HTML")
    if message.text == menu_tests_button:
        return to_tests(bot, message, user, db_manager)
    if message.text == menu_theory_button:
        return to_theory(bot, message, user, db_manager)
    return False

def init_user(message: types.Message, db_manager: DBManager):
    users = db_manager.find_data(UserModel, condition="telegram_id=?", condition_data=[message.from_user.id])
    if users == []:
        user = copy.deepcopy(UserModel)
        user.telegram_id = message.from_user.id
        user.full_name = message.from_user.full_name
        user.user_name = message.from_user.username
        user.state = "start"
        user.first_message = datetime.datetime.now()
        db_manager.save_data(user)
    else:
        user = users[0]
    return user

def init_user_and_log(message, db_manager: DBManager):
    user = init_user(message, db_manager)
    if isinstance(message, types.CallbackQuery):
        logging.info("Data "+ message.data)
        message = message.message
    logging.info("Type: Message; Id: {user_id}; Name: {user_name}; Username: @{username}; State: {state}; Text: {text}; ContentType: {content_type}".format(
        user_id=message.from_user.id,
        user_name=message.from_user.full_name,
        username=message.from_user.username,
        state=user.state,
        text=message.text,
        content_type=message.content_type
    ))
    return user

task_template = "<b>Вопрос {id}</b>\n<b>{name}</b>\n{description}"
answer_template = "<b>{name}</b>\n{description}"
def testing_cb(bot: TeleBot, callback: types.CallbackQuery, user: Model, db_manager: DBManager):
    user.state = "test"
    data = json.loads(callback.data)
    tests = db_manager.find_data(TestModel, condition="rowid=?", condition_data=[data["id"]])
    if not tests:
        return 
    test = tests[0]
    user.current_test = {
        "id": test.rowid,
        "task": 0,
        "answers": [],
    }
    db_manager.save_data(user)
    task = test.tasks[0]
    markup = types.InlineKeyboardMarkup()
    for i, answer in enumerate(task["answers"]):
        message = answer_template.format(
            name=answer["name"],
            description=answer["description"]
        )
        send_description(bot, user, message, answer["files"], types.ReplyKeyboardMarkup(resize_keyboard=True).add(
            types.KeyboardButton(end_test_button),
        ))
        markup.add(types.InlineKeyboardButton(answer["name"], 
            callback_data=json.dumps({"c":"task-ans", "id":test.rowid,"task":0,"ans":i, "delete":0})))
    message = task_template.format(
        id=1,
        name=task["name"],
        description=task["description"]
    )
    send_description(bot, user, message, task["files"], markup)

def task_ans(bot: TeleBot, callback: types.CallbackQuery, user: Model, db_manager: DBManager):
    if user.state != "test":
        return
    data = json.loads(callback.data)
    tests = db_manager.find_data(TestModel, condition="rowid=?", condition_data=[data["id"]])
    if not tests:
        return 
    test = tests[0]
    if user.current_test.get("id") != test.rowid \
        or user.current_test.get("task") != data["task"]:
        return
    user.current_test["answers"].append(data["ans"])
    bot.edit_message_text(callback.message.text + f"\n\n<b>Ответ: </b>{test.tasks[data['task']]['name']}",
        user.telegram_id, callback.message.id, parse_mode="HTML", reply_markup='')
    if user.current_test["task"]+1 == len(test.tasks):
        s = 0
        for i, ans in enumerate(user.current_test["answers"]):
            task = test.tasks[i]
            right_answer = str(task["right_answer"])
            if str(ans+1) == str(right_answer) \
                or right_answer.upper() == task["answers"][ans]["name"].upper():
                s += 1
        result = s/len(test.tasks)*100
        bot.send_message(user.telegram_id, f"<b>Результат: </b><i>{result}% (необходимо набрать 70% для прохождения)</i>", parse_mode="HTML")
        if result >= 70:
            bot.send_message(user.telegram_id, f"Тест пройден✅")
            if test.rowid not in user.accepted_tests:
                user.accepted_tests.append(test.rowid)
        else:
            bot.send_message(user.telegram_id, f"Тест не пройден❌")
        user.current_test = {}
        to_menu(bot, callback, user, db_manager)
        return
    user.current_test["task"] += 1
    db_manager.save_data(user)
    task = test.tasks[user.current_test["task"]]
    markup = types.InlineKeyboardMarkup()
    for i, answer in enumerate(task["answers"]):
        message = answer_template.format(
            name=answer["name"],
            description=answer["description"]
        )
        send_description(bot, user, message, answer["files"], types.ReplyKeyboardMarkup(resize_keyboard=True).add(
            types.KeyboardButton(end_test_button),
        ))
        markup.add(types.InlineKeyboardButton(answer["name"], 
            callback_data=json.dumps({"c":"task-ans", "id":test.rowid,"task":user.current_test["task"],"ans":i, "delete":0})))
    message = task_template.format(
        id=user.current_test["task"]+1,
        name=task["name"],
        description=task["description"]
    )
    send_description(bot, user, message, task["files"], markup)
    

def test(bot: TeleBot, message: types.Message, user: Model, db_manager: DBManager):
    if message.text != end_test_button:
        return False
    user.current_test = {}
    return to_menu(bot, message, user, db_manager)

def get_theory_by_callback(bot: TeleBot, callback: types.CallbackQuery, db_manager: DBManager, user: Model):
    data = json.loads(callback.data)
    theorys = db_manager.find_data(TheoryModel, condition="rowid=?", condition_data=[data["id"]])
    if not theorys:
        bot.send_message(user.telegram_id, "Теория не найдена!")
        return False, None, None
    theory = theorys[0]
    return True, theory, data

def theory_cb(bot: TeleBot, callback: types.CallbackQuery, user: Model, db_manager: DBManager):
    res, theory, _ = get_theory_by_callback(bot, callback, db_manager, user)
    if not res:
        return
    paragraph = theory.paragraphs[0]
    markup = types.InlineKeyboardMarkup()
    if len(theory.paragraphs) >= 1:
        markup.add(
            types.InlineKeyboardButton("❌", callback_data="None"),
            types.InlineKeyboardButton("▶️", 
                callback_data=json.dumps({"c": "theory-next", "id": theory.rowid, "paragraph": 0, "delete": False})),
                row_width=2)
    send_description(
        bot, 
        user, 
        paragraph_template.format(paragraph=1, theme=paragraph["name"], description=paragraph["description"]), 
        paragraph["files"], 
        markup)
    
def theory_next_cb(bot: TeleBot, callback: types.CallbackQuery, user: Model, db_manager: DBManager):
    res, theory, data = get_theory_by_callback(bot, callback, db_manager, user)
    if not res:
        return
    print(theory)
    current_paragraph = theory.paragraphs[data["paragraph"]]
    current_paragraph["id"] = data["paragraph"]
    next_paragraph = theory.paragraphs[data["paragraph"]+1]
    next_paragraph["id"] = data["paragraph"]+1
    buttons = []
    buttons.append(
        types.InlineKeyboardButton("◀️", 
            callback_data=json.dumps({"c": "theory-back", "id": theory.rowid, 
                "paragraph": next_paragraph["id"], "delete": False})))
    if len(theory.paragraphs) != next_paragraph["id"]+1:
        buttons.append(types.InlineKeyboardButton("▶️", 
        callback_data=json.dumps({"c": "theory-next", 
            "id": theory.rowid, "paragraph": next_paragraph["id"], "delete": False})))
    else:
        buttons.append(types.InlineKeyboardButton("❌", callback_data="None"))
        if theory.rowid not in user.accepted_theory:
            user.accepted_theory.append(theory.rowid)
            db_manager.save_data(user)
    markup = types.InlineKeyboardMarkup().add(*buttons, row_width=2)
    message = paragraph_template.format(
        paragraph=next_paragraph["id"]+1, 
        theme=next_paragraph["name"], 
        description=next_paragraph["description"])
    send_description(bot, user, message, next_paragraph["files"], markup)

def theory_back_cb(bot: TeleBot, callback: types.CallbackQuery, user: Model, db_manager: DBManager):
    res, theory, data = get_theory_by_callback(bot, callback, db_manager, user)
    if not res:
        return
    current_paragraph = theory.paragraphs[data["paragraph"]]
    current_paragraph["id"] = data["paragraph"]
    prev_paragraph = theory.paragraphs[data["paragraph"]-1]
    prev_paragraph["id"] = data["paragraph"]-1
    buttons = []
    if prev_paragraph["id"]:
        buttons.append(
        types.InlineKeyboardButton("◀️", 
            callback_data=json.dumps({"c": "theory-back", "id": theory.rowid, 
                "paragraph": prev_paragraph["id"], "delete": False})))
    else:
        buttons.append(types.InlineKeyboardButton("❌", callback_data="None"))
    buttons.append(types.InlineKeyboardButton("▶️", 
        callback_data=json.dumps({"c": "theory-next", 
            "id": theory.rowid, "paragraph": prev_paragraph["id"], "delete": False})))
    markup = types.InlineKeyboardMarkup().add(*buttons, row_width=2)
    message = paragraph_template.format(
        paragraph=prev_paragraph["id"]+1, 
        theme=prev_paragraph["name"], 
        description=prev_paragraph["description"])
    send_description(bot, user, message, prev_paragraph["files"], markup)

def init(bot: TeleBot, db_manager: DBManager):
    @bot.message_handler(commands=['menu'])
    def _(message: types.Message):
        user = init_user_and_log(message, db_manager)
        to_menu(bot, message, user, db_manager)

    @bot.message_handler(commands=['admin'])
    def _(message: types.Message):
        if message.from_user.id not in config.ADMINS:
            return
        bot.reply_to(message, "Панель администратора:", reply_markup=admin.admin_markup)

    @bot.callback_query_handler(lambda x: True)
    def _(callback: types.CallbackQuery):
        bot.answer_callback_query(callback.id)
        user = init_user_and_log(callback, db_manager)
        try:
            data = json.loads(callback.data)
        except json.JSONDecodeError:
            return
        except Exception as err:
            logging.exception(err)
        if not isinstance(data, dict) or data.get("c") is None:
            return
        callbacks = {
            "update-tests": admin.update_tests_cb,
            "get-tests": admin.get_tests_cb,
            "update-theory": admin.update_theory_cb,
            "get-theory": admin.get_theory_cb,
            "update-file": admin.update_file_cb,
            "get-users-table": admin.get_users_table,
            "testing": testing_cb,
            "task-ans": task_ans,
            "theory": theory_cb,
            "theory-next": theory_next_cb,
            "theory-back": theory_back_cb,
        }
        if callbacks.get(data["c"]) is None:
            return
        if data.get("delete", True):
            bot.delete_message(user.telegram_id, callback.message.id)
        callbacks.get(data["c"])(bot, callback, user, db_manager)

    @bot.message_handler(content_types='document')
    def _(message: types.Message):
        user = init_user_and_log(message, db_manager)
        if user.telegram_id not in config.ADMINS:
            return
        os.makedirs("tmp/files", exist_ok=True)
        states = {
            "update_tests": admin.update_tests,
            "update_theory": admin.update_theory,
            "update_file": admin.update_file,
        }
        if user.state not in states:
            bot.reply_to(message, f"state:{user.state} не найден для отправленнго файла")
            return
        filename = message.document.file_name
        try:
            filepath = bot.get_file(message.document.file_id).file_path
            urllib.request.urlretrieve(f'https://api.telegram.org/file/bot{config.TOKEN}/{filepath}', f"tmp/files/{filename}")
            filepath = f"tmp/files/{filename}"
        except Exception as err:
            logging.exception(err)
            bot.reply_to(message, "Ошибка скачивания файла")
            return
        bot.reply_to(message, "Файл успешно скачан")

        try:
            states[user.state](bot, filepath, message, user, db_manager)
        except Exception as err:
            logging.exception(err)
            bot.reply_to(message, "Проишла ошибка обработки файла")

    @bot.message_handler()
    def _(message: types.Message):
        user = init_user_and_log(message, db_manager)
        states = {
            "start": start,
            "registration-name": registration_name,
            "registration-class": registration_class,
            "menu": menu,
            "test": test,
        }
        if states.get(user.state):
            try:
                if not states[user.state](bot, message, user, db_manager):
                    bot.reply_to(message, "Я вас не понял!")
                    return
                return
            except Exception as err:
                logging.exception(err)
                bot.reply_to(message, "Произошла ошибка!")
                return
        bot.reply_to(message, f"state:{user.state} не найден!")

def loop(bot: TeleBot):
    for admin in config.ADMINS:
        try:
            bot.send_message(admin, "Start Vocal Teacher Bot")
        except:
            pass
    bot.infinity_polling()
