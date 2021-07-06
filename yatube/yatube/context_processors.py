import datetime as dt


def year(request):
    year2 = dt.datetime.today().year
    return {'year': year2}
