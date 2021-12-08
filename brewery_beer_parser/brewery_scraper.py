from tqdm import tqdm

import time
import random
import pandas as pd
import requests
from bs4 import BeautifulSoup

from const.beer_scraping import HEADERS
from utils.app_argparser import create_parse_args
from utils.helper import *
from utils.helper import get_brewery_info_filename


def resolve_brewery_untappd_url(brewery):
    search_url = construct_untappd_search_url(brewery)
    page = requests.get(search_url, headers=HEADERS)
    if page.ok:
        soup = BeautifulSoup(page.content, 'html.parser')
        results_section = soup.find('div', class_='results-container')
        brewery_url = results_section.find('a')
        if brewery_url:
            return construct_url(UNTAPPD_BASE_URL, results_section.find('a').get('href'))
        else:
            print(f'cannot resolve {search_url}')
        return None
    else:
        print(page)
    return None


def resolve_brewery_untapp_url_google(brewery):
    google_search_url = create_google_search_query(f'untappd {brewery}')
    page = requests.get(google_search_url, HEADERS)
    if page.ok:
        soup = BeautifulSoup(page.text, 'html.parser')
        for a_tag in soup.find_all('a'):
            href = a_tag.get('href')
            if UNTAPPD_BASE_URL in href:
                untappd_brewery_url = href.split('&')[0].replace('/url?q=', '')
                if UNTAPPD_BASE_URL == untappd_brewery_url.strip('/'):
                    return None
                return untappd_brewery_url
    else:
        return page
    return None


def extract_brewery_info(soup):
    rating_info = soup.find("div", {'class': ['box', 'b_info']})
    if not rating_info:
        return None

    brewery_id_tag = rating_info.find('a', class_='label')
    brewery_id = brewery_id_tag.get('href') if brewery_id_tag else None

    brewery_desc_tag = rating_info.find('div', class_='beer-descrption-read-less')
    brewery_desc = brewery_desc_tag.text.strip() if brewery_desc_tag else None

    average_rating_tag = rating_info.find('div', class_='caps')
    average_rating = float(average_rating_tag.get('data-rating')) if average_rating_tag else None

    num_of_ratings = convert_text_to_number(rating_info.find('p', class_='raters'), float)
    num_of_beers = convert_text_to_number(rating_info.find('p', class_='count'), int)

    stats_tag = rating_info.find('div', class_='stats')
    if stats_tag:
        stats = stats_tag.find_all('span', class_='count')
        if len(stats) != 3:
            total_check_ins = locale.atoi(stats[0].text)
            unique_user_check_ins = locale.atoi(stats[1].text)
            last_four_week_check_ins = locale.atoi(stats[2].text)
        else:
            raise RuntimeError(f'Can`t extract stats for the brewery {stats_tag}')

    return {
        'brewery_id': brewery_id,
        'average_rating': average_rating,
        'num_of_ratings': num_of_ratings,
        'num_of_beers': num_of_beers,
        'total_check_ins': total_check_ins,
        'unique_user_check_ins': unique_user_check_ins,
        'last_four_week_check_ins': last_four_week_check_ins,
        'brewery_desc': brewery_desc
    }


def main(args):
    breweries = pd.read_csv(args.brewery_file, delimiter=',')
    if args.state_filter:
        breweries = breweries[breweries.state.isin(args.state_filter)]

    group_by_state = breweries.groupby('state')

    for group_name, group in group_by_state:
        print(f'Started downloading for {group_name}')
        brewery_series_list = []
        for _, row in tqdm(group.iterrows(), total=len(group)):
            brewery_name = row['name']
            brewery_untappd_url = resolve_brewery_untapp_url_google(
                brewery_name) if args.use_google else resolve_brewery_untappd_url(brewery_name)

            if brewery_untappd_url:
                beer_page = requests.get(construct_url(brewery_untappd_url, 'beer'),
                                         headers=HEADERS)
                if beer_page.ok:
                    soup = BeautifulSoup(beer_page.content, "html.parser")
                    brewery_untappd_info = extract_brewery_info(soup)
                    if brewery_untappd_info:
                        brewery_info = pd.Series(brewery_untappd_info)
                        brewery_series_list.append(pd.concat([row, brewery_info]))
            if args.use_google:
                time.sleep(random.randint(40, 50))
            else:
                time.sleep(args.timeout)

        if brewery_series_list:
            pd.DataFrame(brewery_series_list).to_csv(get_brewery_info_filename(args, group_name))

        print(f'Finished downloading for {group_name}')


if __name__ == "__main__":
    main(create_parse_args().parse_args())
