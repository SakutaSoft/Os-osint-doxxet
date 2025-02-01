import glob
import time
import sys
import os
from colorama import init, Fore
import csv
import json
import sqlite3
import logging
import xml.etree.ElementTree as ET
from openpyxl import load_workbook
from concurrent.futures import ThreadPoolExecutor
from pystyle import Colors, Colorate
from termcolor import colored
import re 
print(Fore.GREEN + """
⡀⠀⠀⠀⠀⠀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡠⠀
⠈⣦⡀⠀⠀⠀⠀⠙⢶⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⠖⢂⡞⠀⠀
⠀⣼⡇⠀⠀⠀⠀⠀⠈⣿⣆⠀⠀⢀⡴⠋⠀⠀⣰⣿⠁⠀⢸⣧⠀⠀
⢠⣿⡇⠀⠀⠀⠀⠀⠀⣿⠿⠀⢀⣿⠃⠀⠀⢰⣿⡏⠀⠀⢸⣿⣄⠀
⣪⣷⡆⠀⠀⠀⠀⢀⣜⡛⡟⠀⠸⣟⡆⠀⠀⠘⣛⡳⠀⠀⠈⣿⣿⡄
⢟⣭⣷⡀⠀⠀⢀⣯⣟⡟⠀⠀⠀⠟⣽⡧⠀⢸⣟⠻⡆⠀⠀⢰⣦⣝
⠸⡟⣿⡿⣦⠀⠟⠉⡉⣠⡦⣠⡷⠀⡵⠟⢃⣼⡿⣿⠀⠀⢀⣾⣛⠿
⠀⠀⠻⠇⢿⠀⡆⢾⠃⠛⠡⣉⣠⣤⣤⣶⣿⢹⣿⠈⠀⢀⣼⡿⣿⡆
⠀⠀⠀⠀⢀⣼⣿⣌⠀⢰⢤⣄⡉⠛⠉⣚⠋⢈⣁⣠⣴⡟⣿⣧⠸⠃
⠀⠀⠀⠀⢸⡿⠿⠻⠷⠄⢱⣄⠈⠻⠿⠿⠟⣻⣿⠏⣿⡇⢸⠏⠀⠀
⠀⠀⠀⠀⣸⡷⠀⠀⣠⣴⣧⠙⣷⣤⡀⠚⠿⠿⠋⠰⠛⠁⠀⠀⠀⠀
⠀⠀⢀⣾⣿⣿⣾⣿⣿⣿⡿⠀⠈⢿⣿⡆⠀⠱⣶⣾⣷⡀⠀⠀⠀⠀
⠀⠀⠈⢹⣿⣿⣿⣿⡿⠋⠁⠀⡀⠈⠻⣿⣦⠀⠈⠻⣿⣿⣦⡀⠀⠀
⠀⠀⠀⠠⣭⣿⣿⣿⣴⣶⣶⣿⠁⠀⠀⠘⢿⣧⠀⠀⠙⣿⣿⠻⣦⠀
⠀⠀⠀⠀⣾⣿⣿⣿⠿⠟⠛⠁⠀⠀⠀⠀⠘⣿⡄⠀⠀⠹⣿⣧⠈⢣
⠀⠀⠀⠀⠈⠉⠁⠀⢰⣄⠀⠀⠀⢢⠀⠀⠀⢸⡇⠈⡀⠀⢿⣿⡆⠀
⠀⠀⠀⠀⠀⠀⠀⣠⣿⣿⣷⡀⠀⠈⡇⠀⠀⢸⠇⢰⡇⠀⣼⣿⡇⠀
⠀⠀⠀⠀⠀⢠⣾⠟⡛⠛⠛⢇⠀⣸⡗⠀⠀⠘⢀⣾⠇⢀⣿⣿⠃⠀
⠀⠀⠀⠀⠀⡿⠁⣼⡀⠀⠀⢀⣴⣿⠃⠀⠀⢁⣾⡿⢀⣾⣿⠏⠀⠀
⠀⠀⠀⠀⠀⠇⠀⠈⠻⢶⡾⠿⠛⠁⠀⣀⣴⣿⣿⣶⣿⣿⠋⠀⠀⠀
⠀⠀⠀⣠⣶⡿⣿⣿⣶⣦⣴⣦⣶⣶⣿⣿⣿⣿⣿⠿⠋⠀⠀⠀⠀⠀
⠀⠀⠀⣿⠀⠀⠀⠀⠈⠙⠛⠻⠟⠿⠻⠛⠛⠉⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠈⠀⠀⠀⠀⠀   
Софт для поиска по Database (папка base)
    """)
GREEN = "\033[92m"
WHITE = "\033[97m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

text_formats = ['.csv', '.txt', '.sql', '.xlsx', '.json', '.log']
def setup_logger():
    logger = logging.getLogger('search_logger')
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler('search_log.txt', mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger

logger = setup_logger()

def fast_print(text, interval=0.01):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        
def search_in_file(file_path, value):
    encodings = ['utf-8', 'utf-16', 'utf-32', 'iso-8859-1', 'iso-8859-2', 'iso-8859-3', 'iso-8859-4', 'iso-8859-5', 'iso-8859-6', 'iso-8859-7', 'iso-8859-8', 'iso-8859-9', 'iso-8859-15', 'windows-1250', 'windows-1251', 'windows-1252', 'windows-1253', 'windows-1254', 'windows-1255', 'windows-1256', 'windows-1257', 'windows-1258']
    results = []
    value=str(value)
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                for line in f:
                    if value in line:
                        results.append(line.strip())
            if results: 
                break
        except Exception as e:
            logger.debug(f"Ошибка при попытке открыть файл {file_path} с кодировкой {encoding}: {e}")
    if not results:
        logger.error(f"{RED}Не удалось прочитать файл {file_path} с предложенными кодировками.{RESET}")
    
    return results

def dbsearch(db_file, value):
    found_results = []
    start_time = time.time()
    try:
        found_results = search_in_file(db_file, value)
        if found_results:
            logger.info(f"{GREEN}Найдено {len(found_results)} результатов в файле {db_file}{RESET}")
    except Exception as e:
        logger.error(f"{RED}Ошибка при обработке файла {db_file}: {e}{RESET}")
    elapsed_time = time.time() - start_time
    if elapsed_time > 1000:
        logger.warning(f"{YELLOW}Поиск в файле {db_file} занял больше 1000 секунд.{RESET}")
    
    return found_results

def search_in_base_folder(value):
    start_time = time.time()
    all_found_results = []
    base_directory = 'base'
    db_files = []
    for ext in text_formats:
        db_files.extend(glob.glob(os.path.join(base_directory, '*' + ext)))
    try:
        with open('результаты_поиска.txt', 'w', encoding='utf-8') as f:
            f.write(f'Поисковой запрос: {value}\n')
            logger.info(f"{CYAN}Запуск поиска по базе данных с запросом: '{value}'{RESET}")
            for db in db_files:
                found_results = dbsearch(db, value)

                if found_results:
                    all_found_results.extend(found_results)
                    for result in found_results:
                        f.write(result + '\n')
    except Exception as ex:
        logger.error(f"{RED}Ошибка при записи результатов в файл: {ex}{RESET}")
    finally:
        elapsed_time = time.time() - start_time
        logger.info(f"{GREEN}Найдено {len(all_found_results)} результатов за {elapsed_time:.2f} секунд.{RESET}")
def bd1():
    fast_print(f"{GREEN}Введите поисковой запрос: {RESET}")
    search_query = input(f"{WHITE}")
    fast_print(f"{WHITE}🔍 Поиск...\n")
    search_in_base_folder(search_query)
    logger.info(f"{GREEN}Поиск завершен. Результаты сохранены в 'результаты_поиска.txt'.{RESET}")
    
ENCODINGS = ['utf-8', 'windows-1251', 'latin-1']
def print_message(message, color="white", bold=False):
    if bold:
        message = colored(message, color, attrs=['bold'])
    else:
        message = colored(message, color)
    print(message)
def print_header(title):
    print(colored(f'\n{"=" * 80}', "blue"))
    print(colored(f'*** {title} ***', "yellow", attrs=['bold']))
    print(colored(f'{"=" * 80}\n', "blue"))
def search_phone_number_in_folder(folder_path):
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        print_message(f'Ошибка: "{folder_path}" не является папкой или не существует.', "magenta", bold=True)
        return
    print_header("Поиск результатов")
    search_value = input(colored('Введите запрос: ', "cyan")).strip()
    if not search_value:
        print_message('Ошибка: запрос не может быть пустым.', "red", bold=True)
        return
    found_any = False
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            file_path = os.path.join(root, filename)
            if os.path.isfile(file_path):
                found = False
                for encoding in ENCODINGS:
                    try:
                        with open(file_path, 'r', encoding=encoding) as file:
                            for line in file:
                                if search_value in line:
                                    found_any = True
                                    if not found:
                                        print_header(f'Найден {search_value} в файле: {file_path}')
                                        found = True
                                    print_message(f'Заголовок: {search_value}', "yellow", bold=True)
                                    parts = re.split(r'\t|u+|m+|p+|t+|w+|q+|h+|y+|i+|g+', line.strip())
                                    for part in parts:
                                        print_message(f'[+] {part.strip()}', "green")
                                    print(colored('°' * 80, "blue"))
                    except (UnicodeDecodeError, FileNotFoundError):
                        continue
    if not found_any:
        print_message('Ничего не найдено.', "magenta", bold=True)
    print_message('Нажмите Enter для выхода...', "yellow")
    input()

text_formats = ['.csv', '.txt', '.sql', '.xlsx', '.json', '.log']

def dbsearch(db, value):
    found_results = []
    try:
        with open(db, 'r', encoding='utf-8') as f:
            Fline = f.readline()  
            
        with open(db, 'r', encoding='utf-8') as f:
            for line in f:
                if value in line:  
                    fdata = line.replace(',', ';').replace('\t', '    ').split(';')  
                    sdata = Fline.replace(',', ';').replace('\t', '    ').split(';')  
                    found_data = []
                    for i in range(len(fdata)):
                        if len(fdata[i]) < 80: 
                            if i < len(sdata):
                                key = sdata[i].strip()  
                                val = fdata[i].strip() if fdata[i].strip() else 'не найден'  
                                if key:  
                                    key_colored = Colorate.Horizontal(Colors.green_to_white, key)
                                    val_colored = Colorate.Horizontal(Colors.green_to_white, val)
                                    found_data.append(('  ├ ' + key_colored + ' -> ' + val_colored, '  ├ ' + key + ' -> ' + val))

                    found_data = [line for line in found_data if ': не найден' not in line[1]]  
                    if found_data:
                        
                        db_colored = '└──│ База данных -> ' + db
                        found_data.insert(0, (db_colored, '└──│ База данных -> ' + db))
                        found_results.append(found_data)
    except BaseException as e:
        print(Colorate.Horizontal(Colors.green_to_white, '[ ! ] Ошибка: ' + str(e)))
    return found_results

def search_in_directory(directory, value):
    start_time = time.time()
    all_found_results = []
    db_files = []
    for ext in text_formats:
        db_files.extend(glob.glob(os.path.join(directory, '*' + ext)))
    db_files = [db for db in db_files if os.path.basename(db) != 'результаты_поиска.txt']

    try:
        for db in db_files:
            found_results = dbsearch(db, value)
            if found_results:
                all_found_results.extend(found_results)
                for result in found_results:
                    for colored_line, _ in result:
                        print(colored_line)
                    print('\n')
    except Exception as ex:
        print(ex)
    finally:
        end_time = time.time()
        elapsed_time = end_time - start_time
        summary_text = f'\n🔍 Поисковой запрос: {value}\n📊 Всего найдено результатов: {len(all_found_results)}\n'
        summary_text += f'⏳Затраченное время: {elapsed_time:.2f} секунд\n' if elapsed_time <= 60 else f'⏳Затраченное время: {elapsed_time / 60:.2f} минут\n'
        print(Colorate.Horizontal(Colors.green_to_white, summary_text))

if __name__ == '__main__':
    print("""
    1. Поиск по бд Новый
    2. Поиск по бд Старый
    3. Поиск. по бд Новый V2
    """)
    
    choice = input("Выбери вариант (1 или 2): ")

    if choice == '1':
        bd2()
    elif choice == '2':
        bd1()
    elif choice =='3':
        folder_path = 'base'
        search_phone_number_in_folder(folder_path)

    else:
        print("Некорректный выбор, пожалуйста, введите 1 или 2 - 3.")