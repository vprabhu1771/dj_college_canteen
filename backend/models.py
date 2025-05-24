import datetime

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser
from .manager import CustomUserManager

class Gender(models.TextChoices):
    MALE = 'M', _('Male')
    FEMALE = 'F', _('Female')

class GenderedImageField(models.ImageField):

    def pre_save(self, model_instance, add):
        value = super().pre_save(model_instance, add)
        if not value or not hasattr(model_instance, self.attname):
            # If no image provided or new instance
            # default gender
            gender = model_instance.gender if hasattr(model_instance, 'gender') else Gender.MALE
            if gender == Gender.MALE:
                value = 'profile/male_avatar.png'
            elif gender == Gender.FEMALE:
                value = 'profile/female_avatar.png'
            else:
                # fallback default image
                value = 'profile/default_image.jpg'

        elif model_instance.gender != getattr(model_instance, f"{self.attname}_gender_cache", None):
            # If gender has changed
            gender = model_instance.gender
            if gender == Gender.MALE:
                value = 'profile/male_avatar.png'
            elif gender == Gender.FEMALE:
                value = 'profile/female_avatar.png'
            else:
                # fallback default image
                value = 'profile/default_image.jpg'
        setattr(model_instance, f"{self.attname}_gender_cache", model_instance.gender)
        return value


class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, default=Gender.MALE)
    image = GenderedImageField(upload_to='profile/', blank=True)
    phone = models.CharField(max_length=10, unique=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['gender', 'phone',]
    objects = CustomUserManager()

    def __str__(self):
        return self.email

class CustomerUser(CustomUser):
    class Meta:
        proxy = True
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'


class AdminUser(CustomUser):
    class Meta:
        proxy = True
        verbose_name = 'Admin'
        verbose_name_plural = 'Admins'

class Category(models.Model):
    id=models.BigAutoField(primary_key=True)
    name=models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        db_table='category'

class Brand(models.Model):
    id=models.BigAutoField(primary_key=True)
    name=models.CharField(max_length=255)
    image_path = models.ImageField (upload_to='brand',null=True,blank=True,default='no_image_available.jpg')

    def __str__(self):
        return self.name

    class Meta:
        db_table='brand'

class Product(models.Model):
    id = models.BigAutoField(primary_key=True)

    name = models.CharField(max_length=255)

    category=models.ForeignKey(Category,null=True,blank=True,on_delete=models.SET_NULL, related_name='products')

    brand=models.ForeignKey(Brand,null=True,blank=True,on_delete=models.SET_NULL)

    price=models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)

    qty=models.IntegerField(null=True,blank=True)

    alert_stock=models.IntegerField(null=True,blank=True)

    image_path = models.ImageField(upload_to='product',null=True,blank=True,default='no_image_available.jpg')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'product'

class Cart(models.Model):
    id = models.BigAutoField(primary_key=True)
    custom_user = models.ForeignKey(CustomUser,on_delete=models.SET_NULL,blank=True,null=True)
    product =  models.ForeignKey(Product,on_delete=models.SET_NULL,blank=True,null=True)
    qty = models.IntegerField()

    def __str__(self):
        return str(self.qty)

    def total_price(self):
        return self.qty * self.product.price if self.product else 0

    @classmethod
    def grand_total(cls, customer_id):
        cart_items = cls.objects.filter(custom_user_id=customer_id)
        total = sum(item.total_price() for item in cart_items)
        return total

    class Meta:
        db_table = 'cart'

# Order
class OrderStatus(models.TextChoices):
    PENDING = 'PENDING',_('Pending')
    APPROVED = 'APPROVED',_('Approved')
    REJECTED = 'REJECTED',_('Rejected')

class PaymentMethodStatus(models.TextChoices):
    CASH = 'CASH',_('CASH')
    UPI = 'UPI',_('UPI')
    CARD = 'CARD',_('CARD')

class Order(models.Model):
    id = models.BigAutoField(primary_key=True)
    customer = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, blank=True, null=True)
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    order_status = models.CharField(
        max_length=255,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )
    payment_method = models.CharField(
        max_length=255,
        choices=PaymentMethodStatus.choices,
        default=PaymentMethodStatus.CASH
    )


    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        today = datetime.date.today().strftime('%Y-%m-%d')
        last_order = Order.objects.filter(order_date__date=today).order_by('-id').first()
        if last_order:
            last_number = int(last_order.order_number.split()[-1])
            next_number = str(last_number + 1).zfill(3)
        else:
            next_number = '001'
        return f"{today} {next_number}"

    def __str__(self):
        return f"{self.order_date.strftime('%d-%m-%Y %H:%M:%S')} {self.customer} {self.total_amount}"

    class Meta:
        db_table = 'order'

# OrderItem
class OrderItem(models.Model):
    id = models.BigAutoField(primary_key=True)
    # order = models.ForeignKey(Order, on_delete=models.CASCADE)
    # order = models.ForeignKey(Order, on_delete=models.SET_NULL, blank=True, null=True)
    order = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, blank=True, null=True)
    qty = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.IntegerField()

    # item_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"{self.order} {self.product.name} {self.qty} {self.unit_price} {self.amount}"

    class Meta:
        db_table = 'order_items'