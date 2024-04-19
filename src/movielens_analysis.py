import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from collections import Counter
import os
import pytest

import matplotlib.pyplot as plt


# Метод для jupyter notebook
def visualize_dict(d, x_name, y_name, title):
    plt.figure(figsize=(20, 10))
    plt.bar(d.keys(), d.values())
    plt.xlabel(x_name)
    plt.ylabel(y_name)
    plt.title(title)
    plt.xticks(rotation=45)
    plt.show()


# Вспомогательный метод для тестов
def is_sorted_by_value_desc(dictionary):
    values = list(dictionary.values())
    return all(values[i] >= values[i + 1] for i in range(len(values) - 1))

def file_reader(file_path):
    with open(file_path, 'r') as file:
        header = file.readline()
        for line in file:
            yield line.strip().split(',')

class Tests:
    def test_links(self):
        links = Links('ml-latest-small/links.csv')
        assert isinstance(links, Links)

        # Достаю с IMDB информацию по первому фильму из файла
        data = links.get_imdb(['1'], ['Director'])
        assert data == [['1', ['John Lasseter']]]

        # Создаю вспомогательный файл
        file_name = 'test.csv'
        links.create_links_csv(file_name, 0, 1)
        assert os.path.exists(file_name)
        os.remove(file_name)

        # Паршу строку из аргумента, пересчитываю валюту по актуальному курсу к доллару
        converted_budget = links.calculate_budget('€1234')
        assert 1333.0 - converted_budget < 1

        # Обращаюсь к генератору за следующей (в этом случае первой) строкой файла
        toy_story_ids = next(links.links_file_reader('ml-latest-small/links.csv'))
        assert toy_story_ids == ['1', '0114709', '862']

        # Нахожу 3 самых режиссеров с наибольшим числом фильмов
        top_directors_data = links.top_directors(3)
        assert isinstance(top_directors_data, dict)
        assert is_sorted_by_value_desc(top_directors_data)
        top_3_directors = list(top_directors_data.keys())
        assert top_3_directors == ['Woody Allen', 'Alfred Hitchcock', 'Clint Eastwood']

        # 3 самых дорогих фильма
        most_expensive_data = links.most_expensive(3)
        assert isinstance(most_expensive_data, dict)
        assert is_sorted_by_value_desc(most_expensive_data)
        top_3_expensive = list(most_expensive_data.keys())
        assert top_3_expensive == ['Мстители: Война бесконечности', 'Звёздные войны: Последние джедаи',
                                   'Пираты Карибского моря: На краю света']

        # 3 самых прибыльных фильма
        most_profitable_data = links.most_profitable(3)
        assert isinstance(most_profitable_data, dict)
        assert is_sorted_by_value_desc(most_profitable_data)
        top_3_profitable = list(most_profitable_data.keys())
        assert top_3_profitable == ['Аватар', 'Титаник', 'Звёздные войны: Пробуждение Силы']

        # Самые долгие фильмы, в т.ч. многосерийные
        longest_data = links.longest(3)
        assert isinstance(longest_data, dict)
        assert is_sorted_by_value_desc(longest_data)
        top_3_longest = list(longest_data.keys())
        assert top_3_longest == ['Гражданская война', 'Roots', 'Крестный отец: Трилогия 1901-1980']

        # Самые дорогие в производстве на минуту хронометража
        top_cost_per_minute_data = links.top_cost_per_minute(3)
        assert isinstance(top_cost_per_minute_data, dict)
        assert is_sorted_by_value_desc(top_cost_per_minute_data)
        top_3_top_cost_per_minute = list(top_cost_per_minute_data.keys())
        assert top_3_top_cost_per_minute == ['Терминатор 2 - 3D', 'Рапунцель: Запутанная история',
                                             'Лига справедливости']

        # Жанры с самым долгим средним хронометражем
        longest_by_genre_data = links.longest_by_genre(3)
        assert isinstance(longest_by_genre_data, dict)
        assert is_sorted_by_value_desc(longest_by_genre_data)
        top_3_longest_by_genre = list(longest_by_genre_data.keys())
        assert top_3_longest_by_genre == ['History', 'War', 'Biography']

    def test_movies(self):
        movies = Movies('ml-latest-small/movies.csv')
        assert isinstance(movies, Movies)

        # Обращаюсь к генератору за следующей (в этом случае первой) строкой файла
        toy_story_info = next(movies.movies_file_reader('ml-latest-small/movies.csv'))
        assert toy_story_info == (1, 'Toy Story', 1995, ['Adventure', 'Animation', 'Children', 'Comedy', 'Fantasy'])

        # Словарь с количеством фильмов для каждого года
        data = movies.dist_by_release()
        assert isinstance(data, dict)
        assert is_sorted_by_value_desc(data)
        assert list(data.keys())[0] == 2002

        # Словарь жанров по частоте
        data = movies.dist_by_genres()
        assert isinstance(data, dict)
        assert is_sorted_by_value_desc(data)
        assert list(data.keys())[0] == 'Drama'

        # Словарь индивидуальных фильмов с самым большим числом жанров
        data = movies.most_genres(10)
        assert isinstance(data, dict)
        assert is_sorted_by_value_desc(data)
        assert list(data.keys())[0] == 'Rubber'

        # Словарь десятилетий с соответствующими тройками самых популярных жанров
        data = movies.trends_over_time()
        assert isinstance(data, dict)
        assert list(data.values())[-1] == ['Comedy', 'Drama', 'Action']


class Ratings:

    def __init__(self, file_path):
        self.userId = []
        self.movieId = []
        self.rating = []
        self.timestamp = []

        for row in file_reader(file_path):
            self.userId.append(row[0])
            self.movieId.append(row[1])
            self.rating.append(row[2])
            self.timestamp.append(row[3])
    
    def top_movies_by_rating(self):
        top_movies_id = []
        for idx, movie in enumerate(self.movieId):
            if self.rating[idx] == 5.0:
                top_movies_id.append(movie)
        
        counter = Counter(top_movies_id)
        top_movies = dict(counter.most_common(15))
        # соотнести с названиями из movies.csv
        return top_movies

    def ratings_distribution(self):
        counter = Counter(self.rating)
        ratings = dict(counter.most_common())
        sorted_dict = dict(sorted(ratings.items()))
        distribution = list(sorted_dict.values())
        labels = ['0.5', '1.0', '1.5', '2.0', '2.5', '3.0', '3.5', '4.0', '4.5', '5.0']
        plt.pie(distribution, labels=labels)
        plt.show()

class Tags:

    def __init__(self, path_to_the_file):
        self.userId = []
        self.movieId = []
        self.tag = []
        self.timestamp = []

        for row in file_reader(path_to_the_file):
            self.userId.append(row[0])
            self.movieId.append(row[1])
            self.tag.append(row[2])
            self.timestamp.append(row[3])

    def most_active_user(self):
        counter = Counter(self.userId)
        users = dict(counter.most_common(15))
        return users
    
    def most_common_tags(self):
        counter = Counter(self.tag)
        tags = dict(counter.most_common(15))
        return tags


class Movies:
    def __init__(self, path_to_the_file):
        self.movieId = []
        self.title = []
        self.release_year = []
        self.genres = []

        for row in Movies.movies_file_reader(path_to_the_file):
            self.movieId.append(row[0])
            self.title.append(row[1])
            self.release_year.append(row[2])
            self.genres.append(row[3])

    @staticmethod
    def movies_file_reader(file_path):
        with open(file_path, 'r') as f:
            lines = f.readlines()[1:]
            for line in lines:
                if line.isspace():
                    continue
                line = line.strip()
                fields = []
                field = ''
                in_quotes = False
                for ch in line:
                    if ch == ',' and not in_quotes:
                        field = field.strip()
                        fields.append(field)
                        field = ''
                    elif ch == '"':
                        in_quotes = not in_quotes
                    else:
                        field += ch
                field = field.strip()
                fields.append(field)
                full_title = fields[1]
                match = re.search(r'\(\d+\)$', full_title)
                release_year = None
                if match:
                    release_year = int(match.group()[1:-1])
                if not release_year:
                    continue

                match = re.search(r'.+\(', full_title)
                title = match.group()[:-1].strip()
                movie_id = int(fields[0])
                genres = fields[2].split('|')
                yield movie_id, title, release_year, genres

    # Распределение фильмов по году выпуска
    def dist_by_release(self):
        counter = Counter(self.release_year)
        release_years = dict(counter.most_common())
        return release_years

    # Самые популярные жанры
    def dist_by_genres(self):
        counter = Counter()
        for current_movie_genres in self.genres:
            counter.update(current_movie_genres)
        genres = dict(counter.most_common())
        return genres

    # Топ фильмов по количеству жанров
    def most_genres(self, n):
        unsorted_movies = {}
        for i in range(len(self.movieId)):
            unsorted_movies[self.title[i]] = len(self.genres[i])
        movies = {k: v for k, v in sorted(unsorted_movies.items(), key=lambda item: item[1], reverse=True)[:n]}
        return movies

    def trends_over_time(self):
        start_decade = min(self.release_year) - min(self.release_year) % 10
        end_decade = max(self.release_year) - max(self.release_year) % 10
        decades = {}
        for i in range(start_decade, end_decade + 1, 10):
            counter = Counter()
            for j in range(i, i + 10):
                indices = [i for i, x in enumerate(self.release_year) if x == j]
                for index in indices:
                    counter.update(self.genres[index])
            top_3 = list(dict(counter.most_common(3)).keys())
            decades[f'{i}-{i + 9}'] = top_3

        return decades


class Links:
    # Захардкодил курс валют, чтобы не использовать запрещенные модули. Нужно для html-парсинга IMDB
    CURRENCY_CODES = {
        '$': 1,
        'FRF': 0.16,
        'A$': 0.65,
        'CA$': 0.74,
        'DEM': 0.551526,
        '€': 1.08,
        '£': 1.26,
        '¥': 0.0066,
        'ISK': 0.0072,
        'HK$': 0.12,
        'CHF': 1.11,
        'NZ$': 0.59825,
        'RUR': 0.011,
        'DKK': 0.14,
        'ITL': 0.00054,
        'ESP': 0.00648877,
        'BEF': 0.0267636,
        '₹': 0.012,
        'SEK': 0.092,
        'ATS': 0.0785113,
        'R$': 0.20,
        'NOK': 0.091,
        'FIM': 0.18052616,
        'SGD': 0.74,
        'THB': 0.027334474,
        'PLN': 0.24988861,
        '₩': 0.00074,
        'CN¥': 0.138499,
        'NT$': 0.03128,
        '₪': 0.27,
        'CZK': 0.042,
        'HUF': 0.0027,
        'NLG': 0.48695953,
        'BND': 0.73959387,
    }

    def __init__(self, path_to_the_file):
        self.movieId = []
        self.imdbId = []
        self.tmdbId = []

        for row in Links.links_file_reader(path_to_the_file):
            self.movieId.append(row[0])
            self.imdbId.append(row[1])
            self.tmdbId.append(row[2])

    @staticmethod
    def links_file_reader(file_path):
        with open(file_path, 'r') as f:
            lines = f.readlines()[1:]
            for line in lines:
                yield line.strip().split(',')

    # Переводит любую валюту на IMDB в доллары
    @staticmethod
    def calculate_budget(s):
        s = s.split(' ')[0]
        match = re.search(r"\d", s)
        currency, amount = 'N/A', 0
        if match:
            index = match.start()
            currency_raw, amount_raw = s[:index], s[index:]
            currency = currency_raw.strip()
            amount = int(amount_raw.replace(',', ''))

        if currency == 'N/A' or currency not in Links.CURRENCY_CODES:
            if currency != 'N/A':
                print(f'New currency code: {currency}. {lower_bound}-{upper_bound}')
            return amount

        return Links.CURRENCY_CODES[currency] * amount

    # Создает файл file_name в csv-формате с полями Directors,Budget,Gross worldwide,Runtime,Genres,Title для
    # использования в других методах
    def create_links_csv(self, file_name, lower_bound, upper_bound):
        with open(file_name, 'w') as f:
            f.write('movieId,Directors,Budget,Gross worldwide,Runtime,Genres,Title\n')

            movie_list = []
            for i in range(lower_bound, upper_bound):
                movie_list.append(self.movieId[i])
            imdb_data = self.get_imdb(movie_list, ['Director', 'Directors', 'Budget', 'Gross worldwide', 'Runtime',
                                                   'Genres', 'Title'])
            for i in range(len(imdb_data)):
                # movieId
                line = '"' + imdb_data[i][0] + '",'

                # Directors
                if imdb_data[i][1] != 'N/A':
                    line += '"' + imdb_data[i][1][0] + '","'
                elif imdb_data[i][2] != 'N/A':
                    line += '"' + ','.join(imdb_data[i][2]) + '","'
                else:
                    line += '"0","'

                # Budget
                if imdb_data[i][3] == 'N/A':
                    line += '0","'
                else:
                    try:
                        budget_raw = imdb_data[i][3][0]
                        budget = Links.calculate_budget(budget_raw)
                        line += str(budget) + '","'
                    except Exception:
                        print(f'Exception on budget {budget_raw}. movieId: {imdb_data[i][0]}')
                        line += '0","'

                # Gross worldwide
                if imdb_data[i][4] == 'N/A':
                    line += '0","'
                else:
                    try:
                        gross_raw = imdb_data[i][4][0]
                        gross = Links.calculate_budget(gross_raw)
                        line += str(gross) + '","'
                    except Exception:
                        print(f'Exception on gross {gross_raw}. movieId: {imdb_data[i][0]}')
                        line += '0","'

                # Runtime
                if imdb_data[i][5] == 'N/A':
                    line += '0",'
                else:
                    runtime_raw = imdb_data[i][5][0]

                    try:
                        runtime_parts = runtime_raw.split()
                        total_minutes = 0

                        for j in range(len(runtime_parts)):
                            if 'hour' in runtime_parts[j]:
                                total_minutes += int(runtime_parts[j - 1]) * 60
                            elif 'minute' in runtime_parts[j]:
                                total_minutes += int(runtime_parts[j - 1])
                        line += str(total_minutes) + '",'
                    except Exception:
                        print(f'Exception on runtime {runtime_raw}. movieId: {imdb_data[i][0]}')
                        line += '0",'

                if imdb_data[i][6] == 'N/A':
                    line += '"0",'
                else:
                    line += '"' + ','.join(imdb_data[i][6]) + '",'

                if imdb_data[i][7] == 'N/A':
                    line += '"0"\n'
                else:
                    line += '"' + imdb_data[i][7][0] + '"\n'

                f.write(line)

    def get_imdb(self, list_of_movies, list_of_fields):
        imdb_info = []
        for movie in list_of_movies:
            if movie not in self.movieId:
                raise ValueError(f'{movie} is not present in the list of movieId\'s')
            index = self.movieId.index(movie)

            imdb_link = f'http://www.imdb.com/title/tt{self.imdbId[index].zfill(7)}/'

            # Добавляю хедер, чтобы симулировать браузер в requests.get(), с дефолтным агентом imdb не парсится
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                              '(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'}

            try:
                response = requests.get(imdb_link, headers=headers)

                soup = BeautifulSoup(response.text, 'html.parser')

                current_movie_data = [movie]

                for field in list_of_fields:
                    try:
                        if field == 'Runtime':
                            field_element = soup.find(string=field).parent
                            contents = field_element.find_next_sibling().get_text()
                            current_movie_data.append([contents])
                            continue

                        if field == 'Genres':
                            genres = soup.select_one('div.ipc-chip-list__scroller')
                            contents = [genre.string for genre in genres.contents]
                            current_movie_data.append(contents)
                            continue

                        if field == 'Title':
                            title = soup.find(class_='hero__primary-text').get_text()
                            current_movie_data.append([title])
                            continue

                        field_element = soup.find(lambda tag: tag.get_text() == field)
                        row_element = field_element.parent
                        li_children = row_element.find_all('li')
                        contents = [li_child.get_text() for li_child in li_children]
                        current_movie_data.append(contents)
                    except AttributeError:
                        current_movie_data.append('N/A')

                imdb_info.append(current_movie_data)
            except requests.ConnectionError as e:
                print(f"A Network problem occurred: {e}")
            except requests.Timeout as e:
                print(f"Request timed out: {e}")
            except requests.TooManyRedirects as e:
                print(f"Too many redirects: {e}")
            except requests.RequestException as e:
                print(f"An error occurred: {e}")

        imdb_info.sort(key=lambda x: int(x[0]), reverse=True)
        return imdb_info

    # Люди с наибольшим количеством срежиссированных фильмов
    def top_directors(self, n):
        counter = Counter()
        # Находит все файлы и директории по указанному пути
        files = os.listdir('links_data')

        for file in files:
            with open(os.path.join("links_data", file), 'r') as f:
                lines = f.readlines()
                for line in lines[1:]:  # Skip the header
                    directors = line.split('","')[1]

                    directors.replace('"', '')
                    directors = directors.split(',')
                    if directors[0] != '0':
                        counter.update(directors)
        directors = dict(counter.most_common(n))

        return directors

    def most_expensive(self, n):
        files = os.listdir('links_data')

        unsorted_budgets = {}
        for file in files:
            with open(os.path.join("links_data", file), 'r') as f:
                lines = f.readlines()
                for line in lines[1:]:  # Skip the header
                    budget_raw = line.split('","')[2]
                    budget = float(budget_raw)
                    title = line.split('","')[6][:-2]
                    unsorted_budgets[title] = budget

        budgets = dict(sorted(unsorted_budgets.items(), key=lambda item: item[1], reverse=True)[:n])
        return budgets

    def most_profitable(self, n):
        files = os.listdir('links_data')

        unsorted_profits = {}
        for file in files:
            with open(os.path.join("links_data", file), 'r') as f:
                lines = f.readlines()
                for line in lines[1:]:  # Skip the header
                    profit_raw = line.split('","')[3]
                    profit = float(profit_raw)
                    title = line.split('","')[6][:-2]
                    unsorted_profits[title] = profit

        profits = dict(sorted(unsorted_profits.items(), key=lambda item: item[1], reverse=True)[:n])
        return profits

    def longest(self, n):
        files = os.listdir('links_data')

        unsorted_runtimes = {}
        for file in files:
            with open(os.path.join("links_data", file), 'r') as f:
                lines = f.readlines()
                for line in lines[1:]:  # Skip the header
                    runtime_raw = line.split('","')[4]
                    runtime_minutes = int(runtime_raw)
                    title = line.split('","')[6][:-2]
                    unsorted_runtimes[title] = runtime_minutes

        runtimes = dict(sorted(unsorted_runtimes.items(), key=lambda item: item[1], reverse=True)[:n])
        return runtimes

    # Самые дорогие фильмы по цене в минуту
    def top_cost_per_minute(self, n):
        files = os.listdir('links_data')

        unsorted_costs = {}
        for file in files:
            with open(os.path.join("links_data", file), 'r') as f:
                lines = f.readlines()
                for line in lines[1:]:  # Skip the header
                    budget_raw = line.split('","')[2]
                    budget = float(budget_raw)
                    runtime_raw = line.split('","')[4]
                    runtime_minutes = int(runtime_raw)
                    cost = 0
                    if runtime_minutes != 0:
                        cost = budget / runtime_minutes
                    title = line.split('","')[6][:-2]
                    unsorted_costs[title] = cost

        costs = dict(sorted(unsorted_costs.items(), key=lambda item: item[1], reverse=True)[:n])
        return costs

    # Самые долгие фильмы по жанрам
    def longest_by_genre(self, n):
        counter = Counter()
        genres_total_time = {}

        files = os.listdir('links_data')

        for file in files:
            with open(os.path.join("links_data", file), 'r') as f:
                lines = f.readlines()
                for line in lines[1:]:  # Skip the header
                    genres_line = line.split('","')[5]
                    genres = genres_line.split(',')
                    counter.update(genres)

                    runtime_raw = line.split('","')[4]
                    runtime_minutes = int(runtime_raw)
                    for genre in genres:
                        if genre not in genres_total_time:
                            genres_total_time[genre] = runtime_minutes
                        else:
                            genres_total_time[genre] += runtime_minutes

        genres_total_count = dict(counter)
        genres_by_length = {}
        for genre in genres_total_count:
            if genres_total_count[genre] != 0:
                genres_by_length[genre] = genres_total_time[genre] / genres_total_count[genre]
            else:
                genres_by_length[genre] = 0

        genres_by_length_sorted = dict(sorted(genres_by_length.items(), key=lambda item: item[1], reverse=True)[:n])

        return genres_by_length_sorted
