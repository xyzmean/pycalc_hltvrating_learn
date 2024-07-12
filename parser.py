import requests
from bs4 import BeautifulSoup
import numpy as np
import os
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Настройка логирования
logging.basicConfig(filename='player_stats.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def debug_get_player_stats_hltv(url, filename, debug_folder="web"):
    """Получает статистику игрока, сохраняет HTML каждой страницы в папке для отладки
       и использует Selenium для обхода блокировок.
    """

    if not os.path.exists(debug_folder):
        os.makedirs(debug_folder)

    try:
        # Создаем экземпляр драйвера Chrome (без указания пути)
        driver = webdriver.Chrome()

        # Открываем страницу
        driver.get(url)

        # Ждем загрузки блока статистики
        try:
            stats_block = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "statistics"))
            )
        except TimeoutException:
            logging.error(f"Блок статистики не найден на странице: {url}")
            driver.quit()
            return None

        # Получаем HTML-код страницы после выполнения JavaScript
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')

        # Сохраняем HTML-код страницы в файл
        page_filename = os.path.join(debug_folder, f"{filename}.html")
        with open(page_filename, 'w', encoding='utf-8') as f:
            f.write(soup.prettify())

        # Находим блок статистики по классу 'statistics'
        stats_block = soup.find('div', class_='statistics')
        if not stats_block:
            logging.warning(f"Блок статистики не найден на странице: {url}")
            driver.quit()
            return None

        # Находим все строки статистики внутри блока
        stats_rows = stats_block.find_all('div', class_='stats-row')
        if not stats_rows:
            logging.warning(f"Строки статистики не найдены на странице: {url}")
            driver.quit()
            return None

        stats = {}
        for stats_row in stats_rows:
            stat_name = stats_row.find_all('span')[0].text.strip()
            stat_value = stats_row.find_all('span')[1].text.strip()
            stats[stat_name] = stat_value

        with open(filename + ".txt", 'w', encoding='utf-8') as f:
            f.write(str(stats))
        logging.info(f"Статистика игрока сохранена в файл: {filename}")

        # Извлекаем нужные значения и преобразуем их в числа
        kdr = float(stats.get('K/D Ratio', 0))
        damage_per_round = float(stats.get('Damage / Round', 0))
        kills_per_round = float(stats.get('Kills / round', 0))
        assists_per_round = float(stats.get('Assists / round', 0))
        headshot_percent = float(stats.get('Headshot %', '0%').replace('%', '')) / 100
        rating = float(stats.get('Rating 2.0', 0))  # Получаем рейтинг из stats

        logging.info(f"Извлеченные данные для {name}: KDR={kdr}, DPR={damage_per_round}, KPR={kills_per_round}, APR={assists_per_round}, HSP={headshot_percent}, Rating={rating}")

        driver.quit()  # Закрываем браузер сразу после получения данных
        return [kdr, damage_per_round, kills_per_round, assists_per_round, headshot_percent, rating]

    except Exception as e:
        logging.error(f"Ошибка при обработке страницы {url}: {e}")
        driver.quit()  # Закрываем браузер в случае ошибки
        return None

# Читаем данные игроков из файла
players_data = []
with open("top_100_players.ini", "r", encoding="utf-8") as file:
    for line in file:
        name, url_part = line.strip().split(" - ")
        url = url_part + "?startDate=2023-07-12&endDate=2024-07-12"
        players_data.append((name, url))

# Создаем пустые списки для хранения данных
data = []
ratings = []

# Обрабатываем данные для каждого игрока по очереди
for name, url in players_data:
    filename = f"{name}"

    try:
        player_data = debug_get_player_stats_hltv(url, filename)

        if player_data is not None:
            # Проверяем, есть ли нулевые значения в статистике
            if any(v == 0 for v in player_data[:-1]):
                print(f"Пропускаем игрока {name} из-за нулевых значений в статистике.")
                continue

            # Добавляем данные игрока в списки
            data.append(player_data[:-1])
            ratings.append(player_data[-1])

            # Преобразуем списки в матрицы NumPy
            data_matrix = np.array(data)
            ratings_matrix = np.array(ratings).reshape(-1, 1)

            # Вычисляем промежуточные веса
            data_with_ones = np.c_[data_matrix, np.ones(data_matrix.shape[0])]
            weights, *_ = np.linalg.lstsq(data_with_ones, ratings_matrix, rcond=None)

            # Выводим информацию в консоль
            print(f"Данные получены для игрока: {name}")
            print(f"Матрица данных:\n{data_matrix}")
            print(f"Матрица рейтингов:\n{ratings_matrix}")
            print(f"Веса:\n{weights}")

            # Сохраняем матрицы и веса в файлы
            np.savetxt("player_stats_matrix.ini", data_matrix, delimiter=",")
            np.savetxt("player_ratings_matrix.ini", ratings_matrix, delimiter=",")
            np.savetxt("player_weights_matrix.ini", weights, delimiter=",")
            print("Матрицы и веса сохранены в файлы.")
    except Exception as e:
        print(f"Произошла ошибка при обработке игрока {name}: {e}")
        continue
