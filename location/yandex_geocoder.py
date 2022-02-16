import requests


def fetch_coordinates(apikey, place):
    base_url = 'https://geocode-maps.yandex.ru/1.x'
    params = {'geocode': place, 'apikey': apikey, 'format': 'json'}
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']
    if not found_places:
        return
    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(' ')
    return lon, lat
