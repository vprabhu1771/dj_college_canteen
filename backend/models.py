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

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['gender']
    objects = CustomUserManager()

    def __str__(self):
        return self.email

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
    image_path = models.ImageField (upload_to='brand',null=True,blank=True,default='no-image-available.jpg')

    def __str__(self):
        return self.name

    class Meta:
        db_table='brand'

class Product(models.Model):
    id = models.BigAutoField(primary_key=True)

    name = models.CharField(max_length=255)

    category=models.ForeignKey(Category,null=True,blank=True,on_delete=models.SET_NULL)

    brand=models.ForeignKey(Brand,null=True,blank=True,on_delete=models.SET_NULL)

    price=models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)

    qty=models.IntegerField(null=True,blank=True)

    alert_stock=models.IntegerField(null=True,blank=True)

    image_path = models.ImageField(upload_to='product',null=True,blank=True,default='no-image-available.jpg')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'product'

class Cart(models.Model):
    id = models.BigAutoField(primary_key=True)
    custom_user = models.ForeignKey(CustomUser,on_delete=models.SET_NULL,blank=True,null=True)
    Product =  models.ForeignKey(Product,on_delete=models.SET_NULL,blank=True,null=True)
    qty = models.IntegerField()

    def __str__(self):
        return str(self.qty)

    def total_price(self):
        return self.qty * self.product.price if self.product else 0

    def grand_total(self):
        cart_items = Cart.objects.filter(custom_user=self.custom_user)
        total = sum (element.total_price()for element in cart_items)

    class Meta:
        db_table = 'cart'

class OrderStatus(models.TextChoices):
    PENDING = 'PENDING',_('Pending')
    APPROVED = 'APPROVED',_('Approved')
    REJECTED = 'REJECTED',_('Rejected')

class PaymentMethod(models.TextChoices):
    CASH = 'CASH',_('CASH')
    UPI = 'UPI',_('UPI')
    CARD = 'CARD',_('CARD')


class Order(models.Model):
    id=models.BigAutoField(primary_key=True)
    custom_user = models.ForeignKey(CustomUser,on_delete=models.SET_NULL,blank=True,null=True)
    order_number = models.CharField(max_length=255,blank=True,null=True)
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)
    order_status = models.CharField(
        max_length=255,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )
    payment_method = models.CharField(
        max_length=255,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH
    )

    class Meta:
        db_table = 'order'

class OrderItem(models.Model):
    id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(Order,on_delete=models.SET_NULL,blank=True,null=True)
    product = models.ForeignKey(Product,on_delete=models.SET_NULL,blank=True,null=True)
    qty = models.IntegerField(null=True,blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount = models.IntegerField(blank=True,null=True,default=0)

    def calculate_total_amount(self):
        if self.price and self.qty:
            subtotal = self.price * self.qty
            if self.discount > 0:
                discount_amount = (subtotal * self.discount) / 100
                total_amount = subtotal - discount_amount
            else:
                total_amount = subtotal
            return total_amount
        return 0

    def save(self, *args, **kwargs):
        # Automatically update amount based on the calculated total amount
        self.amount = self.calculate_total_amount()
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'order_items'