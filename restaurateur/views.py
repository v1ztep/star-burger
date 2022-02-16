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
    serialized_restaurants = []
    for restaurant in restaurants:
        serialized_restaurants.append(
            {
                'name': restaurant.name,
                'available_items': [menu_item.product.name for menu_item in restaurant.menu_items.all() if menu_item.availability],
                'coordinates': fetch_coordinates(settings.YANDEX_GEOCODER_API, restaurant.address),
            }
        )
    return serialized_restaurants


def get_distance_to_user(end_point, user_position):
    return round(distance.distance(
        user_position,
        end_point
    ).km, 2)


def get_available_restaurants(order_items, restaurants, order_coordinates):
    available_restaurants = []
    for restaurant in restaurants:
        if order_items.issubset(restaurant['available_items']):
            if order_coordinates:
                restaurant['order_distance'] = get_distance_to_user(
                    (restaurant['coordinates'][1], restaurant['coordinates'][0]),
                    (order_coordinates[1], order_coordinates[0])
                )
            else:
                restaurant['order_distance'] = 0
            available_restaurants.append(restaurant)
    return available_restaurants


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = Order.objects.prefetch_related('items__product').total_price()
    restaurants = Restaurant.objects.prefetch_related('menu_items__product')
    serialized_restaurants = serialize_restaurants(restaurants)
    delivery_locations = {
        location.address: (location.lon, location.lat)
        for location in DeliveryLocation.objects.all()
    }

    orders_items = []
    for order in orders:
        order_items = {order_item.product.name for order_item in order.items.all()}
        order_coordinates = delivery_locations.get(order.address)

        if not order_coordinates:
            order_coordinates = fetch_coordinates(settings.YANDEX_GEOCODER_API, order.address)
            if order_coordinates:
                DeliveryLocation.objects.get_or_create(
                    address=order.address,
                    lon=order_coordinates[0],
                    lat=order_coordinates[1]
                )

        available_restaurants = get_available_restaurants(
            order_items, copy.deepcopy(serialized_restaurants), order_coordinates
        )

        sorted_available_restaurants = sorted(
            available_restaurants, key=itemgetter('order_distance')
        )

        order_filling = {
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

        orders_items.append(order_filling)

    return render(request, template_name='order_items.html', context={
        'order_items': orders_items
    })
