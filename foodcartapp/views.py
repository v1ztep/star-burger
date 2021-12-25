import json

from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Order
from .models import OrderItem
from .models import Product


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            },
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
def register_order(request):
    expected_fields = {
        'products': list,
        'firstname': str,
        'lastname': str,
        'phonenumber': str,
        'address': str
    }
    if not all([field in request.data.keys() for field in expected_fields.keys()]):
        return Response(
            'products, firstname, lastname, phonenumber, address: Обязательные поля.',
            status=status.HTTP_400_BAD_REQUEST
        )
    if not all([isinstance(request.data.get(field), type) for field, type in expected_fields.items()]):
        return Response(
            'products(list), firstname(str), lastname(str), phonenumber(str), '
            'address(str): Поля не могут быть пустыми или содержать другой тип данных',
            status=status.HTTP_400_BAD_REQUEST
        )
    if any([not value for value in request.data.values()]):
        return Response(
            'products(list), firstname(str), lastname(str), phonenumber(str), '
            'address(str): Поля не могут быть пустыми или содержать другой тип данных',
            status=status.HTTP_400_BAD_REQUEST
        )

    order = request.data

    recorded_order = Order.objects.create(
        address=order['address'],
        firstname=order['firstname'],
        lastname=order['lastname'],
        phonenumber=order['phonenumber']
    )

    for product in order['products']:
        OrderItem.objects.create(
            order=recorded_order,
            item=Product.objects.get(pk=product['product']),
            quantity=product['quantity']
        )
    return Response({})
