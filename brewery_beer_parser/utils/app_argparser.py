import argparse


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
