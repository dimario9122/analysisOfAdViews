import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import csv
import threading
import matplotlib.pyplot as plt


URL = 'https://auto.ru/moskva/cars/bmw/x5/10382710/all'
HEADERS = { 'user_agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
            'accept' : '*/*' }
FILENAME = "dataset/ad-info.csv"

# создание get-запроса для получения веб-страницы
def get_html(url, params):
    r = requests.get(url, headers = HEADERS, params = params)
    r.encoding = 'utf-8'
    return r

# функция обработки года выпуска автомобиля
def get_number_of_views_per_day(text):
    number_of_views_per_day = (text.split('(')[1]).split(' ')
    return number_of_views_per_day[0]

# функция обработки цены автомобиля
def get_price(price):
    price = ''.join(filter(lambda x: x.isdigit(), price))
    return price

# функция обработки пробега автомобиля
def get_mileage(mileage):
    mileage = ''.join(filter(lambda x: x.isdigit(), mileage))
    return mileage

# функция записи нужных данных из объявления в CSV-файл
def get_content_fom_ad(url): #need
    ad_info = get_html(url,None)
    soup = BeautifulSoup(ad_info.text, 'html.parser')

    title = soup.find("div", {"class": "CardHead-module__title"})
    if title is None:
        return
    title = title.text

    views = soup.find("div", {"class": "CardHead-module__info-item CardHead-module__views"})
    views = get_number_of_views_per_day(views.text)

    price = soup.find("span", {"class": "OfferPriceCaption__price"})
    price = get_price(price.text)

    year_of_car_production = soup.find("a", {"class": "Link Link_color_black"})
    year_of_car_production = year_of_car_production.text

    mileage = soup.find("li", {"class": "CardInfoRow CardInfoRow_kmAge"})
    mileage = get_mileage(mileage.text)

    # запись данных в CSV-файл
    with open(FILENAME, "a", encoding='utf-8', newline='') as file:
        columns = ["title", "views", "price", "year_of_car_production", "mileage", "href"]
        writer = csv.DictWriter(file, fieldnames=columns)
        data = {"title" : title, "views" : views, "price" : price,
                "year_of_car_production" : year_of_car_production,
                "mileage" : mileage, "href": url}
        writer.writerow(data)


# функция сбора данных на странице
def get_content_on_page(url, page):
    html = get_html(url, params={'page' : page})
    get_content(html.content)

# функция сбора ссылок на страницы сайта
def get_content_and_links_to_other_pages(html):
    soup = BeautifulSoup(html, 'html.parser')
    pagination = soup.find_all('a', class_='ListingPagination-module__page')

    pages = []  # список ссылок на страницы
    for item in pagination:
        pages.append(
            item.get('href')
        )

    # запись названий столбцов в CSV-файл
    with open(FILENAME, "a", encoding='utf-8', newline='') as file:
        columns = ["title", "views", "price", "year_of_car_production", "mileage", "href"]
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()

    t = [0] * len(pages)
    for i in range(len(pages)):
        t[i] = threading.Thread(target=get_content_on_page, args=(URL,i+1,))
        t[i].start()
        t[i].join()

# функция сбора ссылок на странице
def get_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all('a', class_ ='ListingItemTitle-module__link')

    # список ссылок на объявления
    cars_on_page = []
    for item in items:
        cars_on_page.append(
            item.get('href')
        )

    t = [0] * len(cars_on_page)
    for i in range(len(cars_on_page)):
        t[i] = threading.Thread(target = get_content_fom_ad, args = (cars_on_page[i], ))
        t[i].start()
        #t[i].join()

# функция проверки доступности url-адреса
def parse():
    html = get_html(URL, None)
    if html.status_code == 200:
        get_content_and_links_to_other_pages(html.content)
    else:
        print('server is not available')


# функция построение графиков
def draw_addiction(data_form_csv_file_sort):
    # n - выборка анализируемых авто
    n = 20
    fig, ax = plt.subplots()
    axes = [ax, ax.twinx()]

    # Освобождаем место с правой стороны для дополнительной оси Y и снизу для X.
    fig.subplots_adjust(right=0.8)
    fig.subplots_adjust(bottom=0.25)

    # Перемещаем последний стержень оси Y вправо
    axes[-1].spines['right'].set_position(('axes', 1))

    # Чтобы сделать видимой границу самой правой оси, нам нужно включить рамку.
    # Однако это скрывает другие графики, поэтому нам нужно отключить его заполнение.
    axes[-1].set_frame_on(True)
    axes[-1].patch.set_visible(False)
    colors = ('Orange', 'Blue')

    # выбираем даннные и отсортированного CSV-файла
    data1 = data_form_csv_file_sort['price'][:n]
    data2 = data_form_csv_file_sort['views'][:n]

    #price
    axes[0].bar(list(range(0, n)), data1.to_numpy(), color=colors[1])
    axes[0].set_ylabel('Car price, m', color=colors[1])
    axes[0].tick_params(axis='y', colors=colors[1])
    axes[0].set_xticks(list(range(0, n)))
    my_xticks = data_form_csv_file_sort['title'][:n]
    axes[0].set_xticklabels(my_xticks.to_numpy(), rotation=60);

    # views
    axes[1].plot(data2.to_numpy(), marker='o', linestyle='solid', color=colors[0])
    axes[1].set_ylabel('Number of views', color=colors[0])
    axes[1].tick_params(axis='y', colors=colors[0])

    axes[0].set_xlabel('Car name')
    fig.set_size_inches(15, 7)
    plt.show()

# функция визуализации данных
def visualization():
    filename_for_sorted_data = "dataset/ad-info-sorted.csv"
    data_form_csv_file = pd.read_csv(FILENAME, delimiter=',')
    data_form_csv_file_sort = data_form_csv_file.sort_values('views', ascending=False)
    data_form_csv_file_sort.to_csv(filename_for_sorted_data, header=False)
    draw_addiction(data_form_csv_file_sort)

if __name__ == "__main__":
    parse()
    visualization()



