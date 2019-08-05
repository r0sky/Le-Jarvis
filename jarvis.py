import telebot
from telebot import types
import time
import datetime
from datetime import timedelta
import threading
import wikipedia as wp
import random
import requests
from bs4 import BeautifulSoup as bs
import json
import urllib
import tweepy
from tweepy import OAuthHandler
import pandas as pd
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import logging
from gtts import gTTS
# coding=<utf-8>

bot_token = "<YOURTOKEN>"
bot = telebot.TeleBot(token=bot_token)
chat_id = "<YOURCHATID>"  # number


def viki():
    wp.set_lang('tr')
    try:  # try to load the wikipedia page
        random_page = wp.random(pages=1)
        daily_wiki = "**Wikili Sabahlar:  \n" + random_page + " \n\n" + wp.summary(str(random_page.encode('utf-8')), sentences=5)
        bot.send_message(chat_id, daily_wiki)
    except wp.exceptions.PageError:
        # if a "PageError" was raised, ignore it and continue to next link
        bot.send_message(chat_id, "no wiki today, you are free :)")


def eksi():
    proxies = {'http': 'http://user:pass@10.10.1.10:3128/'}
    site = 'https://eksisozluk.com/'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    r = requests.get(site, headers=headers, proxies=proxies)
    url = r.url
    soup = bs(r.content, 'html.parser')
    gundems = soup.find(class_='topic-list partial').find_all('li')

    topic_list_nice = []
    topic_list_popular = []
    topic_list_entrynumber = []
    topic_list_name = []
    topic_merged = []

    for topic in gundems[:9]:
        baslik = topic.find('a')
        if baslik is not None:
            temp = str(baslik.get_text())
            number = temp.split()[-1]
            text = ' '.join(temp.split()[:-1])
            popular = url + str(baslik.get('href'))
            nice = popular[:-7] + "nice"

            topic_merged.append(temp)
            topic_list_name.append(text)
            topic_list_nice.append(nice)
            topic_list_popular.append(popular)
            topic_list_entrynumber.append(number)

    bot.send_message(chat_id, "Gundem: \n\n" + " \n".join(topic_merged))

    for nice in topic_list_nice:
        url = nice
        r = requests.get(url, headers=headers)
        soup = bs(r.content, 'html.parser')

        if soup.find(id='entry-item-list'):
            entryler = soup.find(id='entry-item-list').find_all('li')
            iceriks = []
            for entry in entryler[:2]:
                icerik = entry.find(class_='content').get_text(strip=True)
                iceriks.append(icerik)
        bot.send_message(chat_id, "Gundem Basliklari: \n\n" + " \n\n".join(iceriks) + "\n" + nice)


def readUrl(url):
    with urllib.request.urlopen(url) as url:
        data = json.loads(url.read().decode())
    return data


def fahrenheit_converter(fahrenheit):
    return str((fahrenheit-32)/1.8)[:4]


def weather():
    api_key = "<YOURAPIKEY>"
    url = 'http://dataservice.accuweather.com/currentconditions/v1/%s?apikey=%s&details=true' % (317880, api_key)
    dat = readUrl(url)
    x = dat[0]
    current_temperature = str(x.get('Temperature')['Metric']['Value'])
    current_feel_temperature = str(x.get('RealFeelTemperature')['Metric']['Value'])
    current_weathertext = x.get('WeatherText')

    daily_url = "http://dataservice.accuweather.com/forecasts/v1/daily/1day/317880?apikey=<YOURAPIKEY>"
    data = readUrl(daily_url)
    daily_maximum = fahrenheit_converter(data['DailyForecasts'][0]['Temperature']['Maximum']['Value'])
    daily_minimum = fahrenheit_converter(data['DailyForecasts'][0]['Temperature']['Minimum']['Value'])
    daily_text = data['Headline']['Text']
    daily_day = data['DailyForecasts'][0]['Day']['IconPhrase']
    daily_night = data['DailyForecasts'][0]['Night']['IconPhrase']

    bot.send_message(chat_id, "Anlık Hava Durumu: \n\n" + "Sıcaklık: " + current_temperature + "\nHissedilen: " + current_feel_temperature + "\nGökyüzü: " + current_weathertext)
    bot.send_message(chat_id, "Günlük Hava Durumu: \n\n" + "Minimum: "+daily_minimum + "\nMaximum: " + daily_maximum + "\nÖzet: " + daily_text + "\nGün özet: " + daily_day + "\nGece özet: " + daily_night)


@bot.message_handler(content_types=['location'])
def handle_location(message):
    print("{0}, {1}".format(message.location.latitude, message.location.longitude))
    global lat
    lat = str(message.location.latitude)
    global lon
    lon = str(message.location.longitude)
    markup = types.ReplyKeyboardMarkup(row_width=2)
    action1 = types.KeyboardButton('/twit_analysis')
    action2 = types.KeyboardButton('/exit')
    markup.add(action1, action2)
    bot.send_message(chat_id, "Bu lokasyonla ne yapayım?", reply_markup=markup)

    @bot.message_handler(commands=['twit_analysis'])
    def send_welcome(message):
        tweet_analysis(lat, lon)
        print(lat, lon)

# bot.send_message(chat_id,"no wiki today, you are free :)")


def tweet_analysis(lat, lon):
    consumer_key = '<TWITTERKEY>'
    consumer_secret = '<TWITTERSECRET>'
    access_token = '<TWITTERTOKEN>'
    access_token_secret = '<TWITTERTOKENSECRET>'

    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, retry_count=3, retry_delay=60)
    tweet_text = []
    import socket
    try:
        for tweet in tweepy.Cursor(api.search, geocode=lat + ',' + lon + ',' + '0.3km', result_type='recent', count=100, tweet_mode='extended').items(200):
            tweet_text.append(tweet.full_text)
        allwords = ""
    # for tweet in  tweet_text:
        allwords = allwords + " \n\n".join(tweet_text[:20])
        bot.send_message(chat_id, allwords)
    except socket.timeout:
        print('ops')


def notes():
    with open("not.json","r") as myfile:
        data = myfile.read()
    obj = json.loads(data)
    message = ""
    for key in obj["notlar"].keys():
        message = message + "\n\n" + key.upper() + "\n\n" + "\n".join(obj["notlar"].get(key))
    bot.send_message(chat_id, "İşte notların: \n\n\n" + message)


def note_add(full_message):
    with open("not.json","r") as myfile:
        data = myfile.read()
    obj = json.loads(data)
    category = full_message.split()[1]
    if category not in list(obj['notlar'].keys()):
        bot.send_message(chat_id, "Yeni kategori oluşturuluyor! \n\n" + category)
        message = " ".join(full_message.split()[2:])
        obj['notlar'].update({category : [message] })
        with open('not.json', 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=4)
        bot.send_message(chat_id, "Başarıyla eklendi! \n\n" + message)
    else:
        message = " ".join(full_message.split()[2:])
        obj['notlar'][category].append(message)
        with open('not.json', 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=4)
        bot.send_message(chat_id, "Başarıyla eklendi! \n\n" + message)


def note_delete(full_message):
    with open("not.json","r") as myfile:
        data = myfile.read()
    obj = json.loads(data)
    category = full_message.split()[1]
    if category not in list(obj['notlar'].keys()):
        bot.send_message(chat_id, "Böyle kategori yok! \n\n" + category)
    else:
        if len(full_message.split()) == 2 :
            notes = obj['notlar'][category]
            obj['notlar'].pop(category, None)
            with open('not.json', 'w', encoding='utf-8') as f:
                json.dump(obj, f, ensure_ascii=False, indent=4)
            bot.send_message(chat_id, "Kategori Silindi! \n\n" + category + "\n\n" + "\n".join(notes))
        elif len(full_message.split()) > 2:
            to_be_deleted = obj['notlar'][category][int(full_message.split()[2])-1]
            obj['notlar'][category].remove(to_be_deleted)
            with open('not.json', 'w', encoding='utf-8') as f:
                json.dump(obj, f, ensure_ascii=False, indent=4)
            bot.send_message(chat_id, "Başarıyla silindi! \n\n" + to_be_deleted)


def talk_to_me(message):
    speech = " ".join(message.split()[1:])
    lang = "tr"
    myobj = gTTS(text=speech, lang=lang, slow=False)
    myobj.save("speech.mp3")
    audio = open('speech.mp3', 'rb')  # should use io without saving
    bot.send_audio(chat_id, audio)


def all_methods():
    @bot.message_handler(commands=['selam'])
    def send_welcome(message):
        bot.reply_to(message, 'selam :)')

    @bot.message_handler(commands=['naber'])
    def send_welcome(message):
        bot.reply_to(message, 'iyidir aslan ne olsun iste')

    @bot.message_handler(commands=['hava'])
    def send_welcome(message):
        weather()

    @bot.message_handler(commands=['exit'])
    def send_welcome(message):
        markup = types.ReplyKeyboardRemove(selective=False)
        bot.send_message(chat_id, "Okay..", reply_markup=markup)

    @bot.message_handler(commands=['viki'])
    def send_welcome(message):
        viki()

    @bot.message_handler(commands=['eksi'])
    def send_welcome(message):
        eksi()

    @bot.message_handler(commands=['not'])
    def send_welcome(message):
        notes()

    @bot.message_handler(commands=['notekle'])
    def send_welcome(message):
        note_add(message.text)

    @bot.message_handler(commands=['notsil'])
    def send_welcome(message):
        note_delete(message.text)

    @bot.message_handler(commands=['konus'])
    def send_welcome(message):
        talk_to_me(message.text)

    @bot.message_handler(commands=['help'])
    def send_welcome(message):
        start()

command_list = ['/viki', '/eksi', '/selam', '/naber', '/hava', '/exit', '/not', '/notekle', '/notsil', '/konus', '/help']


def start():
    bot.send_message(chat_id, "Merhaba efendim. Ben Jarvis. Size yardımcı olabilmem için kullanabileceğiniz bazı komutlar aşağıda yer almaktadır. Hizmetinizdeyim.\n\n" + "\n".join(command_list))


gunaydin = ["harika bir gun", "hazir misin?", "enerjiii", "su icmeyi unutma", "hadi abi spor zamani", "bomba bir gun", "niye uyandin ki", "niye varsin ki"]


def alarm():
    target_time = datetime.time(7, 0, 0)  # server time : tsi-3
    now = datetime.datetime.now()
    alarm_time = datetime.datetime.combine(now.date(), target_time)
    while True:
        now = datetime.datetime.now()
        time.sleep((alarm_time - now).total_seconds())
        viki()
        eksi()
        weather()
        stri = random.choice(gunaydin) + " " + str(datetime.datetime.now())
        bot.send_message(chat_id, stri)
        alarm_time = alarm_time + timedelta(seconds=86400)


t2 = threading.Thread(target=all_methods)
t1 = threading.Thread(target=alarm)

t1.start()
t2.start()

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as err:
        logging.error(err)
        time.sleep(15)
