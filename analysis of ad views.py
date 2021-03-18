import requests
from bs4 import BeautifulSoup
import numpy as np
import csv
import threading


URL = 'https://auto.ru/moskva/cars/bmw/x5/10382710/all'
HEADERS = { 'user_agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
            'accept' : '*/*' }

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
    if title == None:
        return
    title = title.text

    views = soup.find("div", {"class": "CardHead-module__info-item CardHead-module__views"})
    views = views.text

    price = soup.find("span", {"class": "OfferPriceCaption__price"})
    price = get_price(price.text)

    year_of_car_production = soup.find("a", {"class": "Link Link_color_black"})
    year_of_car_production = year_of_car_production.text

    mileage = soup.find("li", {"class": "CardInfoRow CardInfoRow_kmAge"})
    mileage = get_mileage(mileage.text)

    FILENAME = "dataset/ad-info.csv"

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

    FILENAME = "dataset/ad-info.csv"

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


if __name__ == "__main__":
    parse()



