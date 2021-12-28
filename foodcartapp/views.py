from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

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
    validate(request.data)

    recorded_order = Order.objects.create(
        address=request.data['address'],
        firstname=request.data['firstname'],
        lastname=request.data['lastname'],
        phonenumber=request.data['phonenumber']
    )

    for product in request.data['products']:
        OrderItem.objects.create(
            order=recorded_order,
            item=Product.objects.get(pk=product['product']),
            quantity=product['quantity']
        )
    return Response({})


def validate(data):
    expected_fields = {
        'products': list,
        'firstname': str,
        'lastname': str,
        'phonenumber': str,
        'address': str
    }
    if not all(
        [field in data.keys() for field in expected_fields.keys()]):
        raise ValidationError([
            'products, firstname, lastname, phonenumber, address: Обязательные поля.'
        ])
    if not all([isinstance(data.get(field), type) for field, type in
                expected_fields.items()]):
        raise ValidationError([
            'products(list), firstname(str), lastname(str), phonenumber(str), '
            'address(str): Поля не могут быть пустыми или содержать другой тип данных'
        ])
    if any([not value for value in data.values()]):
        raise ValidationError([
            'products(list), firstname(str), lastname(str), phonenumber(str), '
            'address(str): Поля не могут быть пустыми или содержать другой тип данных'
        ])
