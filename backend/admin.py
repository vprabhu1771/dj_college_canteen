from django.contrib import admin

from django.contrib.auth.admin import UserAdmin
from backend.forms import CustomUserCreationForm, CustomUserChangeForm

from backend.models import Category, AdminUser, CustomerUser, Product, Cart, OrderItem, Order, Brand

from django.utils.html import format_html
from django.db.models import Q

# Register your models here.
class BaseCustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    list_display = ('email', 'gender', 'image_tag', 'is_staff', 'is_active',)
    list_filter = ('email', 'is_staff', 'is_active',)
    search_fields = ('email',)
    ordering = ('email',)

    fieldsets = (
        # (None, {'fields': ('first_name', 'last_name', 'email', 'gender', 'password', 'groups')}),
        ('Basic Information', {'fields': ('first_name', 'last_name', 'gender','password')}),
        ('Contact Information', {'fields': ('email', 'phone')}),
        ('Permissions', {'fields': ('groups', 'is_staff', 'is_active')}),
    )

    add_fieldsets = (
        # (None, {
        #     'classes': ('wide',),
        #     'fields': ('first_name', 'last_name', 'email', 'gender', 'password1', 'password2', 'is_staff', 'is_active', 'groups')}
        #  ),
        ('Basic Information', {'fields': ('first_name', 'last_name', 'gender','password1','password2')}),
        ('Contact Information', {'fields': ('email', 'phone')}),
        ('Permissions', {'fields': ('groups', 'is_staff', 'is_active')}),
    )

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "-"
    image_tag.short_description = 'Image'

# Filter users by group or role (adjust logic if using roles instead of groups)
@admin.register(CustomerUser)
class CustomerAdmin(BaseCustomUserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(groups__name='Customer')


@admin.register(AdminUser)
class AdminUserAdmin(BaseCustomUserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            Q(groups__name='Admin') | Q(groups=None)
        )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ('name',)

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category','price','image_tag',)

    def image_tag(self, obj):
        return format_html('<img src = "{}" width = "150" height="150" />'.format(obj.image_path.url))

    image_tag.short_description = 'Image'

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'custom_user', 'product', 'qty',)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1  # Number of empty forms to display

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'customer_phone','order_date', 'total_amount', 'order_status', 'payment_method', 'order_number')
    list_filter = ('order_status', 'payment_method', 'order_date')
    search_fields = ('order_number', 'customer__username')  # Assuming CustomUser has a username field
    readonly_fields = ('order_number', 'order_date')  # Fields that should be read-only
    inlines = [OrderItemInline]  # Display OrderItem as inline within Order admin

    list_display_links = ('id', 'customer', 'customer_phone', )

    def get_readonly_fields(self, request, obj=None):
        # Additional logic to determine read-only fields
        if obj:  # If editing an existing object
            return self.readonly_fields + ('total_amount',)
        return self.readonly_fields

    def customer_phone(self, obj):
        return obj.customer.phone if obj.customer else "-"

    customer_phone.short_description = 'Customer Phone'