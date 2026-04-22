from datetime import datetime, timedelta
import json
import requests
import warnings

import numpy as np
import pandas as pd

from common.utils import products, get_matching_products, get_dates


with open('backend/wisegolf_headers.json') as f:
    headers = json.load(f)


def _get_urls(dates, filtered_products):
    reservation_urls = []
    for key, value in filtered_products.items():
        for date in dates:
            date_str = date.strftime('%Y-%m-%d')
            reservation_urls.append(f'https://api.{key.lower().split(' ')[0]}.fi/api/1.0/reservations/?productid={value}&date={date_str}')

    rules_urls = []
    for key, value in filtered_products.items():
        rules_urls.append(f'https://api.{key.lower().split(' ')[0]}.fi/api/1.0/reservations/calendarsettings/?productid={value}&date={dates[0].strftime("%Y-%m-%d")}')

    return reservation_urls, rules_urls

def _get_wisegolf_reservations(dates, filtered_products):
    """
    Get reservations or other blockers (="rules") in a single dataframe
    """
    last_date = max(dates) + timedelta(days=1)
    num_dates = len(dates)

    reservation_urls, rules_urls = _get_urls(dates, filtered_products)

    dfs = []
    for prod_i in range(len(rules_urls)):  # Loop products
        reservations_df = pd.DataFrame()  # Save all reservations for this product
        players_df = pd.DataFrame()
        comments_df = pd.DataFrame(columns=['start', 'end', 'comment'])  # Add columns because it might be empty later and trying to merge
        for reservation_url in reservation_urls[prod_i*num_dates:prod_i*num_dates+num_dates]:  # Loop days in a product
            # Get reservations for this day
            res_json = requests.get(reservation_url, headers=headers).json()
            if res_json['success'] == False:
                raise requests.HTTPError(f"Error fetching data for {reservation_url}: {res_json['errors'][0]['message']}")
            
            reservations_daily_df = pd.DataFrame(res_json['rows'])
            reservations_daily_df.drop(columns=['dateCreated', 'resources', 'isSellable', 'shareId', 'label', 'overrideName',
                                          'quantity', 'isUserReservation'], inplace=True)
            reservations_daily_df['start'] = pd.to_datetime(reservations_daily_df['start'])
            reservations_daily_df['end'] = pd.to_datetime(reservations_daily_df['end'])
            reservations_daily_df['reservationTimeId'] = reservations_daily_df['reservationTimeId'].astype(int)
            reservations_daily_df['status'] = reservations_daily_df['status'].astype(int)
            reservations_df = pd.concat([reservations_df, reservations_daily_df])

            # Get private reservations etc ("resourceComments"), these are shown in wiseapp with the little (i) marker
            try:
                comments_daily_df = pd.DataFrame(res_json['resourceComments'])
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


            # Save player data, not available for simulators:
            if 'reservationsGolfPlayers' in res_json:
                players_daily_df = pd.DataFrame(res_json['reservationsGolfPlayers'])
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

        # Blockers come from rules and comments, merge those:
        if not rules_df.empty and not comments_df.empty:
            merged_rules_df = rules_df.merge(comments_df, on=['start', 'end', 'comment'], how='outer')
        else:
            merged_rules_df = pd.DataFrame(columns=['reservationTimeId'])
        
        df = pd.concat([reservations_df, merged_rules_df])
        df.sort_values('start', ascending=True, inplace=True)
        df = df.merge(players_df, on='reservationTimeId', how='outer')
        df['product'] = list(filtered_products.keys())[prod_i]  # Not quite necessary here but might be good to keep this info for debugging

        dfs.append(df)

    return dfs

def get_wisegolf_teetimes(date_delta=5, players_looking_to_play=2, course=None, specific_date=None):
    """
    Get free teetimes as a df, that has columns:
    -tee_time
    -players
    -handicaps
    -total_hcp
    -product

    Logic:
    -First generate possible teetimes and remove from those.
    -This is because only reservations, not free teetimes, are available via API
    """
    dates = get_dates(date_delta, specific_date)
    filtered_products = get_matching_products(course)

    tee_dfs = []
    for prod_i, res_df in enumerate(_get_wisegolf_reservations(dates, filtered_products)):
        # Generate all possible tee times in 10min intervals
        for i, date in enumerate(dates):
            start_time = datetime.combine(date, datetime.strptime("06:00", "%H:%M").time())
            end_time = datetime.combine(date, datetime.strptime("20:50", "%H:%M").time())
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
                
                # if not isinstance(row['name'], float) and 'Reserved' in row['name']:  # For debugging blockers
                #     print(row)
                if not isinstance(row.get('comment'), float) or row['status'] == 4:  # If row doesn't have a comment, it is nan, i.e. type float
                    tee_idx_to_drop.append(i)
                # Add player info
                if not pd.isna(row['handicapActive']):
                    tee_df.at[i, 'handicaps'].append(float(row['handicapActive']))
                    tee_df.at[i, 'players'].append(str(row['name']))

        # Filter teetimes:
        tee_df.drop(tee_idx_to_drop, inplace=True)
        tee_df = tee_df[tee_df['handicaps'].apply(len) <= 4 - players_looking_to_play]
        tee_df['total_hcp'] = tee_df['handicaps'].apply(sum).round(1)  # Summing floats gives some random decimals
        tee_df = tee_df[tee_df['total_hcp'] < 110 - players_looking_to_play*35]
        
        tee_df['product'] = list(filtered_products.keys())[prod_i]
        tee_df.reset_index(inplace=True)
        tee_dfs.append(tee_df)

    return tee_dfs

if __name__ == '__main__':
    # get_wisegolf_teetimes()
    # print(get_wisegolf_teetimes())
    print(get_wisegolf_teetimes(date_delta=1)[0].tail(10))
    # df = get_wisegolf_teetimes()[0]
    # print(df[df['tee_time'] > '2025-06-14 20:00'].head(30))
