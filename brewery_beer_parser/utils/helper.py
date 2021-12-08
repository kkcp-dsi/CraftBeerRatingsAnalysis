import datetime
import locale
import os
import re

from const.beer_scraping import SUB_PATTERN, UNTAPPD_BASE_URL

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


def remove_illegal_chars(name):
    return re.sub("[^0-9a-zA-Z+]+", "_", name)


def convert_text_to_number(text_element, data_type=float):
    if text_element:
        text = text_element.text
        extracted_text = re.sub(SUB_PATTERN, '', text, flags=re.I).strip()
        try:
            if extracted_text == 'N/A':
                return None
            if data_type == float:
                return locale.atof(extracted_text)
            if data_type == int:
                return locale.atoi(extracted_text)
        except Exception as e:
            print(e)
            return None


def construct_untappd_search_url(brewery):
    parsed_query = '+'.join(brewery.lower().split(' '))
    search_query = f'{UNTAPPD_BASE_URL}/search?q={parsed_query}&type=brewery&sort='
    return search_query


def create_google_search_query(brewery):
    google_search_url_template = 'https://www.google.com/search?q=%s&oq=%s'
    parsed_query = '+'.join(brewery.lower().split(' '))
    google_search_url = google_search_url_template % (parsed_query, parsed_query)
    return google_search_url


def construct_url(base_url, part):
    if not base_url or len(base_url) == 0:
        raise RuntimeError(f'base_url is None')
    if not part or len(part) == 0:
        raise RuntimeError(f'part is None')
    if base_url[-1] != '/':
        base_url += '/'
    if part[0] == '/':
        part = part[1:]
    return base_url + part


def get_brewery_info_filename(args, group_name):
    timestamp = datetime.datetime.today().strftime("%Y%m%d%H%M")
    output_file_name = f'{remove_illegal_chars(group_name)}_brewery_info_{timestamp}.csv'
    output_csv_path = os.path.join(args.output_folder, output_file_name)
    return output_csv_path
