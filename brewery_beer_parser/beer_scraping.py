import os
from tqdm import tqdm

import time
import argparse
import pandas as pd
import requests
from bs4 import BeautifulSoup

from const.beer_scraping import HEADERS
from utils.helper import *


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
                if 'https://untappd.com/' == untappd_brewery_url:
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
            try: 
                total_check_ins = locale.atoi(stats[0].text)
                unique_user_check_ins = locale.atoi(stats[1].text)
                last_four_week_check_ins = locale.atoi(stats[2].text)
            except ValueError:
                total_check_ins = stats[0].text
                unique_user_check_ins = stats[1].text
                last_four_week_check_ins = stats[2].text
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


def extract_beers_by_brewery(soup, brewery_name, output_folder):
    def extract_element(tag, cls):
        element = beer_item.find(tag, class_=cls)
        return re.sub(SUB_PATTERN, '', element.text, flags=re.I).strip() if element else None

    beer_list_section = soup.find("div", {'class': ['beer-list', 'distinct-list']})
    if beer_list_section:
        beer_list = []
        for beer_item in beer_list_section.find_all('div', class_='beer-item'):
            beer_url = 'https://untappd.com/' + beer_item.find('a', class_='label').get('href')
            beer_name = extract_element('p', 'name')
            beer_style = extract_element('p', 'style')
            beer_desc = extract_element('p', 'desc')
            beer_abv = extract_element('div', 'abv')
            beer_ibu = extract_element('div', 'ibu')

            beer_average_rating = convert_text_to_number(beer_item.find('span', class_='num'),
                                                         float)
            beer_num_ratings = convert_text_to_number(beer_item.find('div', class_='raters'), int)
            beer_added = extract_element('div', 'date')
            beer_list.append((beer_url,
                              beer_name,
                              beer_style,
                              beer_desc,
                              beer_abv,
                              beer_ibu,
                              beer_average_rating,
                              beer_num_ratings,
                              beer_added))

        beer_list_pd = pd.DataFrame(beer_list, columns=['beer_url', 'beer_name', 'beer_style',
                                                        'beer_desc', 'beer_abv', 'beer_ibu',
                                                        'beer_average_rating', 'beer_num_ratings',
                                                        'beer_added'])
        beer_list_pd.to_csv(
            os.path.join(output_folder, f'{remove_illegal_chars(brewery_name)}.csv'))


def create_parse_args():
    parser = argparse.ArgumentParser(description='beer data downloader')
    parser.add_argument('-i',
                        '--brewery_file',
                        dest='brewery_file',
                        action='store',
                        required=True)
    parser.add_argument('-o',
                        '--output_folder',
                        dest='output_folder',
                        action='store',
                        required=True)
    parser.add_argument('-s',
                        '--state_filter',
                        nargs='+',
                        dest='state_filter',
                        required=True)
    parser.add_argument('-t',
                        '--timeout',
                        dest='timeout',
                        type=float,
                        default=0.5,
                        required=False)
    parser.add_argument('--use_google',
                        dest='use_google',
                        action='store_true')
    return parser


def main(args):
    breweries = pd.read_csv(args.brewery_file, delimiter=',')
    if args.state_filter:
        breweries = breweries[breweries.state.isin(args.state_filter)]

    group_by_state = breweries.groupby('state')

    for group_name, group in group_by_state:
        group_path = os.path.join(args.output_folder, remove_illegal_chars(group_name))
        if not os.path.exists(group_path):
            os.makedirs(group_path, exist_ok=True)
        print(f'Started downloading for {group_name}')
        brewery_series_list = []
        for _, row in tqdm(group.iterrows(), total=len(group)):
            brewery_name = row['name']
            if args.use_google:
                brewery_untappd_url = resolve_brewery_untapp_url_google(brewery_name)
                time.sleep(45)
            else:
                brewery_untappd_url = resolve_brewery_untappd_url(brewery_name)
                time.sleep(args.timeout)

            if brewery_untappd_url:
                beer_page = requests.get(brewery_untappd_url + '/beer',
                                         headers={'User-agent': 'your bot 0.1'})
                if beer_page.ok:
                    soup = BeautifulSoup(beer_page.content, "html.parser")
                    brewery_untappd_info = extract_brewery_info(soup)
                    if brewery_untappd_info:
                        brewery_info = pd.Series(extract_brewery_info(soup))
                        extract_beers_by_brewery(soup, brewery_name, group_path)
                        brewery_series_list.append(pd.concat([row, brewery_info]))
            time.sleep(args.timeout)

        if brewery_series_list:
            output_file_name = f'{remove_illegal_chars(group_name)}_brewery_info.csv'
            output_csv_path = os.path.join(args.output_folder, output_file_name)
            pd.DataFrame(brewery_series_list).to_csv(output_csv_path)

        print(f'Finished downloading for {group_name}')


if __name__ == "__main__":
    main(create_parse_args().parse_args())
