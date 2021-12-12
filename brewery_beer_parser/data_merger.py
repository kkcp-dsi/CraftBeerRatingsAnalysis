import os
import pandas as pd

def merge_all_beers():
    path = r'brewery_beers'
    extension = '.csv'
    csv_list = []
       
    for root, dirs, files in os.walk(path):
        for filename in files:
            if os.path.splitext(filename)[-1] == extension:
                csv_list.append(os.path.join(root, filename))
    
    frames = []
    for file in csv_list:
        state_and_brewery = file.split('/')
        df = pd.read_csv(file, index_col=False)
        df.insert(1, 'brewery', state_and_brewery[2].split('.')[0])
        df.insert(2, 'state', state_and_brewery[2])
        df['state'] = state_and_brewery[1]
        df['brewery'] = state_and_brewery[2].split('.')[0]
        df.drop(df.columns[df.columns.str.contains('unnamed',case = False)],axis = 1, inplace = True)
        frames.append(df)
    
    pd.concat(frames).to_csv('all_beers.csv')

    return None

def merge_al_breweries():
    breweries_path = r'Breweries'
    extension = '.csv'
    breweries_list = []

    for root, dirs, files in os.walk(breweries_path):
        for filename in files:
            if os.path.splitext(filename)[-1] == extension:
                breweries_list.append(os.path.join(root, filename))
    brewery_frames = []
    for file in breweries_list:
        df = pd.read_csv(file, index_col=False)
        df.drop(df.columns[df.columns.str.contains('unnamed',case = False)],axis = 1, inplace = True)
        brewery_frames.append(df)
    pd.concat(brewery_frames).to_csv('all_beers.csv')
    return None

if __name__ == '__main__':
    merge_all_beers()
    merge_al_breweries()
