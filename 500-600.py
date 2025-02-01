import os
import requests
from colorama import init, Fore, Back, Style
from pystyle import Colors, Colorate, Center
import json
import random 
def get_random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (iPad; CPU OS 14_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    ]
    return random.choice(user_agents)

def send_osint_request(query, pages=None):
    if pages is None:
        pages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    pages_str = ','.join(map(str, pages))
    url = f'https://reveng.ee/api/search?q={query}&total=1000&page={pages_str}&pages=3&per_page=150&max_pages=10'
    headers = {'User-Agent': get_random_user_agent()}
    try:
        print(Fore.WHITE + f"Отправляем запрос на страницу {pages}..." + Style.RESET_ALL)
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
    results = send_osint_request(query)
    if results and results.get('results'):
        all_results = results['results']
        for page in range(1, 11):
            additional_results = send_osint_request(query, pages=[page]) 
            if additional_results and additional_results.get('results'):
                all_results.extend(additional_results['results'])
            else:
                break  
        return {'results': all_results}
    else:
        print(Fore.RED + "Нет результатов" + Style.RESET_ALL)
        return None

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
    <html>
    <head>
        <title>OSINT Search Results</title>
        <style>
            body {
                background-color: #1e1e1e;
                color: #f5f5f5;
                font-family: 'Arial', sans-serif;
                margin: 0;
                padding: 20px;
            }
            h1 {
                color: #ffcc00;
                text-align: center;
            }
            ul {
                list-style-type: none;
                padding: 0;
            }
            li {
                background-color: #333;
                margin: 10px 0;
                padding: 15px;
                border-radius: 5px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
            }
            li:hover {
                background-color: #444;
            }
            .key {
                font-weight: bold;
                color: #ffcc00;
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
        html_content += f"<span class='key'>ID:</span> {entry['id']}<br>"
        html_content += f"<span class='key'>Schema:</span> {entry['schema']}<br>"
        
        for key, value_list in properties.items():
            if value_list:
                values = ', '.join(map(str, value_list))
                html_content += f"<span class='key'>{key.replace('_', ' ').title()}:</span> {values}<br>"
        
        html_content += f"<span class='key'>Sources:</span> {source_names}<br>"
        html_content += "</li>"
    
    html_content += "</ul></body></html>"

    with open("osint_results_v2.html", "w", encoding="utf-8") as file:
        file.write(html_content)
    
    print(Fore.GREEN + "Результаты успешно сохранены в osint_results.html" + Style.RESET_ALL)

def ggosint():
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
        else:
            print("Неверный ввод. Пожалуйста, попробуйте снова.")
               
ggosint()