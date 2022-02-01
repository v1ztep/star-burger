from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import DecimalField
from django.db.models import F
from django.db.models import Sum
from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def total_price(self):
        total_price = self.annotate(
            total_price=Sum(
                F('items__total_price'),
                output_field=DecimalField()
            )
        )
        return total_price


class Order(models.Model):
    STATUS = [
        ('RAW', 'Необработанный'),
        ('FINISHED', 'Обработанный'),
    ]

    address = models.CharField(
        'адрес',
        max_length=100,
        db_index=True
    )
    firstname = models.CharField(
        'имя',
        max_length=50,
        db_index=True
    )
    lastname = models.CharField(
        'фамилия',
        max_length=50,
        db_index=True
    )
    phonenumber = PhoneNumberField(
        'номер телефона',
        max_length=20,
        db_index=True
    )
    status = models.CharField(
        max_length=8, choices=STATUS, default='RAW',
        verbose_name='статус', db_index=True)

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f'{self.firstname} {self.lastname} {self.address}'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, verbose_name='заказ',
        related_name='items',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product, verbose_name='товар',
        related_name='order_items',
        on_delete=models.CASCADE
    )
    quantity = models.PositiveSmallIntegerField(
        verbose_name='количество',
        validators=[MinValueValidator(1)]
    )
    total_price = models.DecimalField(
        max_digits=8, decimal_places=2,
        verbose_name='сумма одного товара', default=0,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = 'элемент заказа'
        verbose_name_plural = 'элементы заказа'

    def __str__(self):
        return f'{self.product} ' \
               f'{self.order.firstname} ' \
               f'{self.order.lastname} ' \
               f'{self.order.address}'
