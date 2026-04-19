from datetime import datetime


products = {
    # 'Tammer-golf simulaattori': 683,  # For winter
    'Tammer-golf 9r': 424,
    'Nokiarivergolf River': 89,
    'Nokiarivergolf River 9r': 384,
    'Nokiarivergolf Rock': 88,
    'Nokiarivergolf Rock 9r': 383,
    'Golfpirkkala': 42,
    'Golfpirkkala 9r': 97,
}

weekdays = {
    'ma': 0,
    'ti': 1,
    'ke': 2,
    'to': 3,
    'pe': 4,
    'la': 5,
    'su': 6
}

def typoless(s):
    """E.g. for comparing products/course names"""
    return s.lower().replace('-', '').replace(' ', '')


def weekday_to_date_delta(weekday_abbr):
    """If you give today's weekday, date delta is 0."""
    return (weekdays[weekday_abbr] - datetime.today().weekday() + 7) % 7