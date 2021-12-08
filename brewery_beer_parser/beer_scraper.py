from tqdm import tqdm
import glob

import time
import pandas as pd
import requests
from bs4 import BeautifulSoup

from const.beer_scraping import HEADERS
from utils.app_argparser import create_parse_args
from utils.helper import *


def extract_beers_by_brewery(soup, brewery_name, output_folder):
    def extract_element(tag, cls):
        element = beer_item.find(tag, class_=cls)
        return re.sub(SUB_PATTERN, '', element.text, flags=re.I).strip() if element else None

    beer_list_section = soup.find("div", {'class': ['beer-list', 'distinct-list']})
    if beer_list_section:
        beer_list = []
        for beer_item in beer_list_section.find_all('div', class_='beer-item'):
            beer_url_tag = beer_item.find('a', class_='label')
            beer_url = construct_url(UNTAPPD_BASE_URL,
                                     beer_url_tag.get('href') if beer_url_tag else None)
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


def main(args):
    breweries = read_brewery_files(args)

    if args.state_filter:
        breweries = breweries[breweries.state.isin(args.state_filter)]

    group_by_state = breweries.groupby('state')

    for group_name, group in group_by_state:
        group_path = os.path.join(args.output_folder, remove_illegal_chars(group_name))
        if not os.path.exists(group_path):
            os.makedirs(group_path, exist_ok=True)
        print(f'Started downloading for {group_name}')
        for _, row in tqdm(group.iterrows(), total=len(group)):
            brewery_untappd_url = row['brewery_id']
            brewery_name = row['name']
            if brewery_untappd_url:
                beer_page = requests.get(construct_url(brewery_untappd_url, 'beer'),
                                         headers=HEADERS)
                if beer_page.ok:
                    soup = BeautifulSoup(beer_page.content, "html.parser")
                    extract_beers_by_brewery(soup, brewery_name, group_path)

            time.sleep(args.timeout)
        print(f'Finished downloading for {group_name}')


def read_brewery_files(args):
    all_files = glob.glob(args.brewery_file + "/*.csv")
    li = []
    for filename in all_files:
        df = pd.read_csv(filename, index_col=None, header=0)
        li.append(df)
    breweries = pd.concat(li, axis=0, ignore_index=True)
    return breweries


if __name__ == "__main__":
    main(create_parse_args().parse_args())
