import config, magic
from telebot import TeleBot
bot = TeleBot(config.TOKEN)
user_id = 847721936
m = magic.Magic(mime=True, uncompress=True)

files = ["file.jpg", "audio.m4a", "audio.mp4"]
for filepath in files:
    filepath = f"./tmp/files/{filepath}"
    for key, func in {
        "image": bot.send_photo,
        "audio": bot.send_audio,
        "video": bot.send_video
    }.items():
        if key in m.from_file(filepath):
            func(user_id, open(filepath, "rb"))

