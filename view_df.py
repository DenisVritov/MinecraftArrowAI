from tabulate import tabulate
import pandas as pd

if __name__ == '__main__':
    df = pd.read_pickle('grid_search_results.pkl')
    print(tabulate(df, headers='keys', tablefmt='psql'))