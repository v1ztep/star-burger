import phonenumbers
from django.http import JsonResponse
from django.templatetags.static import static
from phonenumbers import PhoneNumberFormat
from phonenumbers import is_valid_number
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import CharField
from rest_framework.serializers import ListField
from rest_framework.serializers import Serializer
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
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    recorded_order = Order.objects.create(
        address=serializer.validated_data['address'],
        firstname=serializer.validated_data['firstname'],
        lastname=serializer.validated_data['lastname'],
        phonenumber=serializer.validated_data['phonenumber']
    )

    for product in serializer.validated_data['products']:
        OrderItem.objects.create(
            order=recorded_order,
            item=Product.objects.get(pk=product['product']),
            quantity=product['quantity']
        )
    return Response({})


class OrderSerializer(Serializer):
    products = ListField()
    firstname = CharField()
    lastname = CharField()
    phonenumber = CharField()
    address = CharField()

    def validate_phonenumber(self, value):
        parsed_phone = phonenumbers.parse(value, "RU")
        if not is_valid_number(parsed_phone):
            raise ValidationError('Wrong phonenumber')

        standardized_phone = phonenumbers.format_number(
            parsed_phone, PhoneNumberFormat.E164
        )
        return standardized_phone
