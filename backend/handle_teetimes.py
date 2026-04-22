from datetime import datetime, timedelta

import pandas as pd

from backend.wisegolf import get_wisegolf_teetimes
from common.utils import weekdays


def find_free_blocks(dfs):
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

def handle_teetime_dfs(dfs):
    """Handle different dataframes into one and sort by time"""
    if len(dfs) == 1:
        return dfs[0]
    df = pd.concat(dfs)
    df.sort_values('tee_time')
    return df


if __name__ == '__main__':
    teetime_dfs = get_wisegolf_teetimes()

    find_free_blocks(dfs=teetime_dfs)
