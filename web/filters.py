from datetime import datetime
from .main import app


@app.template_filter('currency')
def format_currency(value):
    value = float(value)
    return "{:,.2f}".format(value)


@app.template_filter('shortdate')
def shortdate(value):
    try:
        value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
        value = value.strftime('%d/%m %H:%M')
    except Exception:
        value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S+03:00')
        value = value.strftime('%d/%m %H:%M')
    return value


@app.template_filter('logdate')
def logdate(value):
    return value.strftime('%d/%m %H:%M')

