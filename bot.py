import os
import telebot
import folium
from geopy.geocoders import Nominatim
from github import Github

# Скрипт сам заберет ключи из настроек сервера
TG_TOKEN = os.environ.get("TG_TOKEN")
GH_TOKEN = os.environ.get("GH_TOKEN")
GH_REPO = os.environ.get("GH_REPO")
MY_TELEGRAM_ID = int(os.environ.get("MY_ID"))

bot = telebot.TeleBot(TG_TOKEN)
geolocator = Nominatim(user_agent="my_travel_bot_2026")

# Список для хранения точек маршрута
travel_points = []

def update_map():
    if not travel_points:
        return
    
    # Центрируем карту на последнем добавленном городе
    last_lat, last_lon, _ = travel_points[-1]
    mymap = folium.Map(location=[last_lat, last_lon], zoom_start=6)
    
    # Расставляем маркеры городов
    for lat, lon, desc in travel_points:
        folium.Marker([lat, lon], popup=desc, icon=folium.Icon(color="blue", icon="info-sign")).add_to(mymap)
    
    # Рисуем линию маршрута между городами
    if len(travel_points) > 1:
        coords = [[p, p] for p in travel_points]
        folium.PolyLine(coords, color="red", weight=3, opacity=0.8).add_to(mymap)
        
    map_html = mymap._repr_html_()
    
    # Отправляем обновленную карту на GitHub Pages
    g = Github(GH_TOKEN)
    repo = g.get_repo(GH_REPO)
    try:
        contents = repo.get_contents("index.html")
        repo.update_file(contents.path, "auto-update", map_html, contents.sha)
    except Exception:
        repo.create_file("index.html", "init-map", map_html)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Отправляй мне точки в формате:\nГород, Описание\n\nПример:\nСочи, Отель Волна, с 5 по 10 июля")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.from_user.id != MY_TELEGRAM_ID:
        return  # Игнорируем сообщения от чужих людей

    try:
        parts = message.text.split(',', 1)
        city = parts[0].strip()
        desc = parts[1].strip() if len(parts) > 1 else "Мы тут!"
        
        # Поиск координат по названию города
        location = geolocator.geocode(city)
        if location:
            lat, lon = location.latitude, location.longitude
            travel_points.append((lat, lon, f"<b>{city}</b><br>{desc}"))
            bot.reply_to(message, f"📍 Нашел: {city}. Обновляю карту...")
            update_map()
            bot.send_message(message.chat.id, "✅ Карта успешно обновлена!")
        else:
            bot.reply_to(message, "❌ Не могу найти этот город. Напишите точнее.")
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {str(e)}")

bot.infinity_polling()
