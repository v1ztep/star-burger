from collections import OrderedDict

import phonenumbers
from django.db import transaction
from django.http import JsonResponse
from django.templatetags.static import static
from phonenumbers import PhoneNumberFormat
from phonenumbers import is_valid_number
from phonenumbers.phonenumberutil import NumberParseException
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import CharField
from rest_framework.serializers import ModelSerializer
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
@transaction.atomic
def register_order(request):
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    recorded_order = Order.objects.create(
        address=serializer.validated_data['address'],
        firstname=serializer.validated_data['firstname'],
        lastname=serializer.validated_data['lastname'],
        phonenumber=serializer.validated_data['phonenumber']
    )
    products = serializer.validated_data['products']

    OrderItem.objects.bulk_create([
        OrderItem(
            order=recorded_order,
            product=product['product'],
            quantity=product['quantity'],
            total_price=product['product'].price * product['quantity']
        )
        for product in products
    ])

    return Response(serializer.data)


class OrderItemSerializer(ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']


class OrderSerializer(ModelSerializer):
    products = OrderItemSerializer(many=True, allow_empty=False, write_only=True)
    phonenumber = CharField()

    class Meta:
        model = Order
        fields = ['products', 'firstname', 'lastname', 'address', 'phonenumber']

    def validate_phonenumber(self, value):
        try:
            parsed_phone = phonenumbers.parse(value, 'RU')
        except NumberParseException:
            raise ValidationError('Некорректный номер телефона')

        if not is_valid_number(parsed_phone):
            raise ValidationError('Некорректный номер телефона')
        standardized_phone = phonenumbers.format_number(
            parsed_phone, PhoneNumberFormat.E164
        )
        return standardized_phone
