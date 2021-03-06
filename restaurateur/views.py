import copy
from operator import itemgetter

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from geopy import distance

from foodcartapp.models import Order
from foodcartapp.models import Product
from foodcartapp.models import Restaurant
from location.models import DeliveryLocation
from location.models import RestaurantLocation
from location.yandex_geocoder import fetch_coordinates


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    default_availability = {restaurant.id: False for restaurant in restaurants}
    products_with_restaurants = []
    for product in products:

        availability = {
            **default_availability,
            **{item.restaurant_id: item.availability for item in product.menu_items.all()},
        }
        orderer_availability = [availability[restaurant.id] for restaurant in restaurants]

        products_with_restaurants.append(
            (product, orderer_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurants': products_with_restaurants,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


def serialize_restaurants(restaurants):
    restaurant_locations = {
        location.address: {'lon': location.lon, 'lat': location.lat}
        for location in RestaurantLocation.objects.all()
    }

    serialized_restaurants = []
    for restaurant in restaurants:
        restaurant_coordinates = restaurant_locations.get(restaurant.address)
        if not restaurant_coordinates:
            restaurant_coordinates = fetch_coordinates(settings.YANDEX_GEOCODER_API, restaurant.address)
            if restaurant_coordinates:
                RestaurantLocation.objects.get_or_create(
                    address=restaurant.address,
                    lon=restaurant_coordinates['lon'],
                    lat=restaurant_coordinates['lat']
                )

        serialized_restaurants.append(
            {
                'name': restaurant.name,
                'available_items': [menu_item.product.name for menu_item in restaurant.menu_items.all() if menu_item.availability],
                'coordinates': restaurant_coordinates,
            }
        )
    return serialized_restaurants


def get_distance_to_user(end_point, user_position):
    return round(distance.distance(
        user_position,
        end_point
    ).km, 2)


def get_available_restaurants(order_items_names, restaurants):
    available_restaurants = []
    for restaurant in restaurants:
        if order_items_names.issubset(restaurant['available_items']):
            available_restaurants.append(restaurant)
    return available_restaurants


def add_distance_to_user(restaurants, order_coordinates):
    for restaurant in restaurants:
        if order_coordinates:
            restaurant['order_distance'] = get_distance_to_user(
                (restaurant['coordinates']['lat'],
                 restaurant['coordinates']['lon']),
                (order_coordinates['lat'], order_coordinates['lon'])
            )
        else:
            restaurant['order_distance'] = 0
    return restaurants


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    raw_orders = Order.objects.filter(status='RAW').prefetch_related('items__product').total_price()
    restaurants = Restaurant.objects.prefetch_related('menu_items__product')
    serialized_restaurants = serialize_restaurants(restaurants)
    raw_orders_addresses = {order.address for order in raw_orders}
    delivery_locations = {
        location.address: {'lon':location.lon, 'lat':location.lat}
        for location in DeliveryLocation.objects.filter(address__in=raw_orders_addresses)
    }

    orders_details = []
    for order in raw_orders:
        order_items_names = {order_item.product.name for order_item in order.items.all()}
        order_coordinates = delivery_locations.get(order.address)

        if not order_coordinates:
            order_coordinates = fetch_coordinates(settings.YANDEX_GEOCODER_API, order.address)
            if order_coordinates:
                DeliveryLocation.objects.get_or_create(
                    address=order.address,
                    lon=order_coordinates['lon'],
                    lat=order_coordinates['lat']
                )

        available_restaurants = get_available_restaurants(
            order_items_names, copy.deepcopy(serialized_restaurants)
        )
        available_restaurants_with_distance = add_distance_to_user(
            available_restaurants, order_coordinates
        )

        sorted_available_restaurants = sorted(
            available_restaurants_with_distance, key=itemgetter('order_distance')
        )

        order_details = {
            'id': order.id,
            'status': order.get_status_display(),
            'payment_method': order.get_payment_method_display(),
            'total_price': order.total_price,
            'firstname': order.firstname,
            'lastname': order.lastname,
            'phonenumber': order.phonenumber,
            'address': order.address,
            'comment': order.comment,
            'restaurants': sorted_available_restaurants,
        }
        orders_details.append(order_details)

    return render(request, template_name='order_items.html', context={
        'order_items': orders_details
    })
