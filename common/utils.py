from datetime import datetime, timedelta


products = {
    # 'Tammer-golf simulaattori': 683,  # For winter
    'Tammer-golf 9r': 424,
    # 'Nokiarivergolf River': 89,
    # 'Nokiarivergolf River 9r': 384,
    # 'Nokiarivergolf Rock': 88,
    # 'Nokiarivergolf Rock 9r': 383,
    # 'Golfpirkkala': 42,
    # 'Golfpirkkala 9r': 97,
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


def get_matching_products(course=None):
    """Filter products dict by course name. Returns all if course is None."""
    if course is None:
        return products
    return {k: v for k, v in products.items() if typoless(course) in typoless(k)}


def get_dates(date_delta=5, specific_date=None):
    """Get list of dates to fetch. If specific_date given, return only that."""
    if specific_date is not None:
        return [specific_date]
    return [(datetime.today() + timedelta(days=d)).date() for d in range(date_delta)]
