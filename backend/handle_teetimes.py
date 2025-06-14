from datetime import datetime, timedelta

import pandas as pd

from wisegolf import get_wisegolf_teetimes
from common.utils import products, weekdays

def find_free_blocks(dfs, date_delta=5, players_looking_to_play=2):
    for df in dfs:  # Per product
        # Take only empty tees to make blocks
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
        print(blocks_df)

def get_teetimes(dfs, course=None, product=None, weekday_abbr=None):
    if weekday_abbr:  # Filter dfs if weekday given
        date_delta = _weekday_to_date_delta(weekday_abbr)
        if date_delta == 0:  # If wanted day is today, keep time in the wanted date to not show old times.
            wanted_date = datetime.today() + timedelta(_weekday_to_date_delta(weekday_abbr))
        else:
            wanted_date = datetime.today().date() + timedelta(_weekday_to_date_delta(weekday_abbr))
    for i, df in enumerate(dfs):
        print(dfs[i].head(50))
        print(df.dtypes)
        print(wanted_date.strftime('%Y-%m-%d'))
        print(type(wanted_date))
        mask = (wanted_date.strftime('%Y-%m-%d'))
        dfs[i] = dfs[i][dfs[i]['tee_time'].dt.date == pd.to_datetime(wanted_date).date()]
        # dfs[i] = dfs[i][(dfs[i]['tee_time'] >= pd.to_datetime(wanted_date)) & ()]#wanted_date.strftime('%Y-%m-%d')]
        print(dfs[i])
        break

def _weekday_to_date_delta(weekday_abbr):
    """If you give today's weekday, date delta is 0."""
    return (weekdays[weekday_abbr] - datetime.today().weekday() + 7) % 7

if __name__ == '__main__':
    teetime_dfs = get_wisegolf_teetimes()

    #find_free_blocks(dfs=teetime_dfs)
    # get_teetimes(dfs=teetime_dfs, weekday_abbr='la')