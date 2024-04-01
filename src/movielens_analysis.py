import requests
from bs4 import BeautifulSoup
import re
from collections import Counter
import time
import os


class Ratings:
    pass


class Tags:
    pass


class Movies:
    pass


class Links:

    # захардкодил курс валют, чтобы не использовать запрещенные модули
    CURRENCY_CODES = {
        '$': 1,
        'FRF': 0.16,
        'A$': 0.65,
        'CA$': 0.74,
        'DEM': 	0.551526,
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
    }

    def __init__(self, path_to_the_file):
        self.movieId = []
        self.imdbId = []
        self.tmdbId = []

        for row in Links.links_file_reader(path_to_the_file):
            self.movieId.append(row[0])
            self.imdbId.append(row[1])
            self.tmdbId.append(row[2])

    # Для минимизации занимаемой памяти использую генератор
    @staticmethod
    def links_file_reader(file_path):
        with open(file_path, 'r') as f:
            lines = f.readlines()[1:]
            for line in lines:
                yield line.strip().split(',')

    @staticmethod
    def calculate_budget(s):
        s = s.split(' ')[0]
        match = re.search("\d", s)
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

            # Добавляю хедер, чтобы симулировать браузер в requests.get()
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

        # Находит все файлы и директории по указанному пути
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
        # Находит все файлы и директории по указанному пути
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
        # Находит все файлы и директории по указанному пути
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

    def top_cost_per_minute(self, n):
        # Находит все файлы и директории по указанному пути
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


links = Links('ml-latest-small/links.csv')
# data = links.get_imdb(['1', '2'], ['Director', 'Directors', 'Genres'])
# links.create_links_csv('test.csv', 0, 2)
# print(data)
# budget = data[0][1][0]
# print(links.calculate_budget(budget))

# print(links.top_directors(10))
# print(links.most_expensive(10))
# print(links.most_profitable(10))
# print(links.longest(10))
# print(links.top_cost_per_minute(10))

# print(links.most_expensive(10))


#########################################################
#########################################################

# step = 100
# for i2 in range(5000, 9744, step):
#
#     lower_bound = i2
#     upper_bound = min(i2 + step, 9743)
#     file_name = 'links_data/links_data_' + str(lower_bound) + '_' + str(upper_bound - 1) + '.csv'
#     # работает от lower_bound включительно до upper_bound не включительно
#     links.create_links_csv(file_name, lower_bound, upper_bound)
#     print(f'{file_name} ready')
#
# lower_bound = 0
# upper_bound = 600
# file_name = 'links_data/links_data_' + str(lower_bound) + '_' + str(upper_bound - 1) + '.csv'
# links.create_links_csv(file_name, lower_bound, upper_bound)
# print(f'{file_name} ready')
#
# lower_bound = 1000
# upper_bound = 1100
# file_name = 'links_data/links_data_' + str(lower_bound) + '_' + str(upper_bound - 1) + '.csv'
# links.create_links_csv(file_name, lower_bound, upper_bound)
# print(f'{file_name} ready')
#
# lower_bound = 3400
# upper_bound = 3500
# file_name = 'links_data/links_data_' + str(lower_bound) + '_' + str(upper_bound - 1) + '.csv'
# links.create_links_csv(file_name, lower_bound, upper_bound)
# print(f'{file_name} ready')
#
# lower_bound = 4100
# upper_bound = 4200
# file_name = 'links_data/links_data_' + str(lower_bound) + '_' + str(upper_bound - 1) + '.csv'
# links.create_links_csv(file_name, lower_bound, upper_bound)
# print(f'{file_name} ready')
