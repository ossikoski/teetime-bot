from datetime import datetime, timedelta
import json
import requests
import warnings

import numpy as np
import pandas as pd

from common.utils import products


with open('backend/wisegolf_headers.json') as f:
    headers = json.load(f)


def _get_urls(date_delta):
    reservation_urls = []
    for key, value in products.items():
        for delta in range(date_delta):
            date = datetime.today() + timedelta(delta)
            date_str = date.strftime('%Y-%m-%d')
            reservation_urls.append(f'https://api.{key.lower().split(' ')[0]}.fi/api/1.0/reservations/?productid={value}&date={date_str}&golf=1')

    rules_urls = []
    for key, value in products.items():
        rules_urls.append(f'https://api.{key.lower().split(' ')[0]}.fi/api/1.0/reservations/calendarsettings/?productid={value}&date=2025-06-11')

    return reservation_urls, rules_urls

def _get_wisegolf_reservations(date_delta=5):
    """
    Get reservations or other blockers (="rules") in a single dataframe
    """
    last_date = datetime.today() + timedelta(date_delta)

    reservation_urls, rules_urls = _get_urls(date_delta=date_delta)

    dfs = []
    for prod_i in range(len(rules_urls)):  # Loop products
        reservations_df = pd.DataFrame()  # Save all reservations for this product
        players_df = pd.DataFrame()
        comments_df = pd.DataFrame(columns=['start', 'end', 'comment'])  # Add columns because it might be empty later and trying to merge
        for reservation_url in reservation_urls[prod_i*date_delta:prod_i*date_delta+date_delta]:  # Loop days in a product
            # Get reservations for this day
            res = requests.get(reservation_url, headers=headers)

            reservations_daily_df = pd.DataFrame(res.json()['rows'])
            reservations_daily_df.drop(columns=['dateCreated', 'resources', 'isSellable', 'shareId', 'label', 'overrideName',
                                          'quantity', 'isUserReservation'], inplace=True)
            reservations_daily_df['start'] = pd.to_datetime(reservations_daily_df['start'])
            reservations_daily_df['end'] = pd.to_datetime(reservations_daily_df['end'])
            reservations_daily_df['reservationTimeId'] = reservations_daily_df['reservationTimeId'].astype(int)
            reservations_daily_df['status'] = reservations_daily_df['status'].astype(int)
            reservations_df = pd.concat([reservations_df, reservations_daily_df])

            # Get private reservations etc ("resourceComments"), these are shown in wiseapp with the little (i) marker
            try:
                comments_daily_df = pd.DataFrame(res.json()['resourceComments'])
                if not comments_daily_df.empty:
                    comments_daily_df.drop(columns=['resourceId', 'commentId', 'public', 'forceConfirmation', 'deleted'], inplace=True)
                    comments_daily_df['dateTimeStart'] = pd.to_datetime(comments_daily_df['dateTimeStart'])
                    comments_daily_df['dateTimeEnd'] = pd.to_datetime(comments_daily_df['dateTimeEnd'])
                    comments_daily_df.rename(columns={'dateTimeStart': 'start', 'dateTimeEnd': 'end'}, inplace=True)
                    with warnings.catch_warnings():
                        warnings.simplefilter(action='ignore', category=FutureWarning)
                        comments_df = pd.concat([comments_df, comments_daily_df])  # This raises FutureWarning for empty df even though it is checked that it is not empty
            except KeyError:  # No 'resourceComments' in res
                pass


            # Save player data
            players_daily_df = pd.DataFrame(res.json()['reservationsGolfPlayers'])
            players_daily_df['name'] = players_daily_df['firstName'] + ' ' + players_daily_df['familyName']
            players_daily_df.drop(columns=['orderId', 'orderProductId', 'personId', 'isOrderOwner', 'holes', 'isHomeClub',
                                           'isCart', 'isUserReservation', 'clubName', 'clubId', 'clubAbbreviation', 'status',
                                           'usedCategoryId', 'firstName', 'familyName', 'namePublic'], inplace=True)
            players_df = pd.concat([players_df, players_daily_df])

        # Get other blockers (="rules") for a product
        rules_res = requests.get(rules_urls[prod_i], headers=headers)
        rules_df_raw = pd.DataFrame(rules_res.json()['resourceRules'])
        rules_df_raw = rules_df_raw[rules_df_raw['ruleName'] == 'aikaSulku']

        rules_df = pd.DataFrame()
        rules_df['start'] = pd.to_datetime(rules_df_raw['startDate'] + ' ' + rules_df_raw['startTime'])
        rules_df['end'] = pd.to_datetime(rules_df_raw['startDate'] + ' ' + rules_df_raw['endTime'])
        rules_df['comment'] = rules_df_raw['ruleValue'].apply(lambda x: x.get('comment') if isinstance(x, dict) else None)
        rules_df = rules_df[(rules_df['start'] > '2025-06-11') & (rules_df['end'] <= last_date.strftime('%Y-%m-%d'))]

        print(reservations_df.head(50))
        break
        # Blockers come from rules and comments, merge those:
        merged_rules_df = rules_df.merge(comments_df, on=['start', 'end', 'comment'], how='outer')

        # Make one df with reservations and other blockers
        df = pd.concat([reservations_df, merged_rules_df])

        df.sort_values('start', ascending=True, inplace=True)
        df = df.merge(players_df, on='reservationTimeId', how='outer')
        df['product'] = list(products.keys())[prod_i]  # Not quite necessary here but might be good to keep this info for debugging

        dfs.append(df)

    return dfs

def get_wisegolf_teetimes(date_delta=5, players_looking_to_play=2):
    """
    Get available teetimes as a df
    """
    tee_dfs = []
    for prod_i, res_df in enumerate(_get_wisegolf_reservations(date_delta=date_delta)):
        # Generate all possible tee times in 10min intervals
        for i in range(date_delta):
            start_time = datetime.combine(datetime.today().date() + timedelta(i), datetime.strptime("06:00", "%H:%M").time())
            end_time = datetime.combine(datetime.today().date() + timedelta(i), datetime.strptime("20:50", "%H:%M").time())
            if i == 0:
                tee_times = pd.date_range(start=start_time, end=end_time, freq='10min')
            else:
                tee_times = tee_times.append(pd.date_range(start=start_time, end=end_time, freq='10min'))

        tee_df = pd.DataFrame({'tee_time': tee_times})
        tee_df['players'] = tee_df['tee_time'].apply(lambda _: [])  # Player names for this teetime
        tee_df['handicaps'] = tee_df['tee_time'].apply(lambda _: [])  # Players handicaps for this teetime
        tee_df['total_hcp'] = 0  # Total hcp for this teetime

        tee_idx_to_drop = []
        for row_i, row in res_df.iterrows():
            # Loop tee times this reservation/blocker overlaps with
            
            for i in tee_df[(tee_df['tee_time'] >= row['start']) & (tee_df['tee_time'] + timedelta(0, 0, 0, 0, 10) <= row['end'])].index:   
                # Mark rows with a blocker to be dropped
                if not isinstance(row['comment'], float) or row['status'] == 4:  # If row doesn't have a comment, it is nan, i.e. type float
                    tee_idx_to_drop.append(i)
                # Add player info
                if not pd.isna(row['handicapActive']):
                    tee_df.at[i, 'handicaps'].append(float(row['handicapActive']))
                    tee_df.at[i, 'players'].append(str(row['name']))

        # Filter teetimes:
        tee_df.drop(tee_idx_to_drop, inplace=True)
        tee_df = tee_df[tee_df['handicaps'].apply(len) <= 4 - players_looking_to_play]
        tee_df['total_hcp'] = tee_df['handicaps'].apply(sum)
        tee_df = tee_df[tee_df['total_hcp'] < 110 - players_looking_to_play*35]
        
        tee_df['product'] = list(products.keys())[prod_i]

        tee_dfs.append(tee_df)

    return tee_dfs

if __name__ == '__main__':
    # get_wisegolf_teetimes()
    # print(get_wisegolf_teetimes())
    print(get_wisegolf_teetimes()[0].head(50))
    # df = get_wisegolf_teetimes()[0]
    # print(df[df['tee_time'] > '2025-06-14 20:00'].head(30))
