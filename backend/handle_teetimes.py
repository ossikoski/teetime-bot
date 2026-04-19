from datetime import datetime, timedelta

import pandas as pd

from backend.wisegolf import get_wisegolf_teetimes
from common.utils import products, weekdays, typoless, weekday_to_date_delta


def find_free_blocks(dfs, date_delta=5, players_looking_to_play=2):
    """Find blocks ("From xx:xx to xx:xx") that are completely free from the given dfs."""
    empty_dfs = []
    for df in dfs:  # Per product
        # Take only empty tees to make blocks  # TODO ?
        empty_tee_df = df[df['players'].apply(lambda x: len(x) == 0)].copy()
        # Calculate gaps in minutes
        diff = empty_tee_df['tee_time'].diff().dt.total_seconds().div(60)

        # Make a blocks df, where start a new block when gap is not 10 minutes or date changes
        date_change = empty_tee_df['tee_time'].dt.date != empty_tee_df['tee_time'].dt.date.shift()
        block_id = ((diff != 10) | date_change).cumsum()
        blocks_df = empty_tee_df.groupby(block_id)['tee_time'].agg(['first', 'last'])

        # Blocks with only 10mins show the time, if more it shows "xx to yy"
        blocks_df.loc[blocks_df['first'] == blocks_df['last'], 'block'] = blocks_df['first'].dt.strftime('%H:%M')

        mask = blocks_df['first'] != blocks_df['last']
        blocks_df.loc[mask, 'block'] = (
            blocks_df.loc[mask, 'first'].dt.strftime('%H:%M') + ' to ' + blocks_df.loc[mask, 'last'].dt.strftime('%H:%M')
        )

def get_teetimes(dfs, course=None, product=None, weekday_abbr=None):
    """Filter teetimes based on params"""
    if course:  # Only take dfs that match the course
        product_idx = []
        wanted_products = []
        for i, key in enumerate(list(products.keys())):
            if typoless(course) in typoless(key):  # Lower and replace for typos
                product_idx.append(i)
                wanted_products.append(key)
    if product:
        product_idx = [i for i, product in enumerate(list(products.keys())) if typoless(product) in typoless(key)]
    dfs = [dfs[i] for i in product_idx]

    if weekday_abbr:  # Filter dfs if weekday given
        date_delta = weekday_to_date_delta(weekday_abbr)
        if date_delta == 0:  # If wanted day is today, keep time in the wanted date to not show old times.
            wanted_date = datetime.today() + timedelta(weekday_to_date_delta(weekday_abbr))
        else:
            wanted_date = datetime.today().date() + timedelta(weekday_to_date_delta(weekday_abbr))
    for i, df in enumerate(dfs):
        # print(dfs[i].head(50))
        # print(df.dtypes)
        # print(wanted_date.strftime('%Y-%m-%d'))
        # print(type(wanted_date))
        mask = (wanted_date.strftime('%Y-%m-%d'))
        dfs[i] = dfs[i][dfs[i]['tee_time'].dt.date == pd.to_datetime(wanted_date).date()]
        # dfs[i] = dfs[i][(dfs[i]['tee_time'] >= pd.to_datetime(wanted_date)) & ()]#wanted_date.strftime('%Y-%m-%d')]
        break


if __name__ == '__main__':
    teetime_dfs = get_wisegolf_teetimes()

    find_free_blocks(dfs=teetime_dfs)
    # get_teetimes(dfs=teetime_dfs, course='tammer', weekday_abbr='la')
