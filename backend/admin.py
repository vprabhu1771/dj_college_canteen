from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from backend.forms import CustomUserCreationForm, CustomUserChangeForm
from backend.models import CustomUser, Category, Brand, Product, Cart, OrderItem, Order
from django.utils.html import format_html


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm

    form = CustomUserChangeForm

    model = CustomUser

    list_display = ('email', 'gender', 'image_tag', 'is_staff', 'is_active',)

    list_filter = ('email', 'is_staff', 'is_active',)

    fieldsets = (
        (None, {'fields': ('email', 'gender', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'gender', 'password1', 'password2', 'is_staff', 'is_active')}
         ),
    )

    search_fields = ('email',)

    ordering = ('email',)

    def image_tag(self, obj):
        return format_html('<img src ="{}" width ="150" height="150" />'.format(obj.image.url))

    image_tag.short_description = 'Image'


admin.site.register(CustomUser, CustomUserAdmin)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'image_tag',)

    def image_tag(self, obj):
        return format_html('<img src="{}" width="150" height="150" />'.format(obj.image_path.url))

    image_tag.short_description = 'Image'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('category', 'brand', 'price', 'qty', 'name', 'image_tag',)

    def image_tag(self, obj):
        return format_html('<img src="{}" width="150" height="150" />'.format(obj.image_path.url))

    image_tag.short_description = 'Image'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'custom_user', 'Product', 'qty',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'custom_user', 'order_number', 'order_date', 'total_amount', 'order_status', 'payment_method',
    )
    inlines = [OrderItemInline]