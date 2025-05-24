from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

from backend.models import Cart, CustomUser, Gender, Category, Product, Order, OrderItem

from django.contrib.auth.hashers import make_password
from django.http import JsonResponse

# Create your views here.
def home(request):
    user = request.user
    data = {}

    # Handle cart data for authenticated users
    if user.is_authenticated:
        cart_items = Cart.objects.filter(custom_user=user)
        grand_total = Cart.grand_total(customer_id=user.id)

        data['cart_items'] = cart_items
        data['grand_total'] = grand_total
        data['cart_count'] = cart_items.count()
    else:
        data['cart_items'] = []
        data['grand_total'] = 0
        data['cart_count'] = 0

    # Load all categories for navbar or dropdowns
    categories = Category.objects.prefetch_related('products').all()
    data['categories'] = categories

    # Category filter check
    category_name = request.GET.get('category')  # e.g., "Women"
    if category_name:
        category = get_object_or_404(Category, name=category_name)

        data['category_present'] = True
        data['page_title'] = category.name
        data['categories'] = categories

        for cat in categories:
            print(cat.name)
            print(cat.products.all())  # This will now work!

        return render(request, 'frontend/product.html', data)

    # If no category is selected, show the default homepage
    data['category_present'] = False
    return render(request, 'frontend/home.html', data)

def auth_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Authenticate the user
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # Login the user
            login(request, user)
            return redirect('home')  # Redirect to a success page
        else:
            messages.error(request, 'Invalid email or password')
    return render(request, 'frontend/auth/login.html')

def auth_logout(request):
    logout(request)  # Log out the user
    return redirect('home')  # Redirect to the login page or home page

def register(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        gender = request.POST.get('gender', Gender.MALE)
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirmPassword', '')

        # Validate required fields
        if not email or not phone or not password or not confirm_password:
            messages.error(request, 'All fields are required.')
        elif password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        elif CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
        elif CustomUser.objects.filter(phone=phone).exists():
            messages.error(request, 'Phone number already exists.')
        else:
            # Create the user
            CustomUser.objects.create(
                email=email,
                phone=phone,
                gender=gender,
                password=make_password(password),
            )
            messages.success(request, 'Account created successfully. Please login.')
            return redirect('login')  # Change 'login' to your actual login URL name

    return render(request, 'frontend/auth/register.html')

@login_required  # Ensures the user is authenticated
def cart(request):
    # Get the current logged-in user
    user = request.user

    # Print user email for debugging (only if the user is authenticated)
    if user.is_authenticated:
        print(user.email)

        # Filter cart items for the current user
        cart_items = Cart.objects.filter(custom_user=user)

        # Calculate the grand total for the cart
        grand_total = Cart.grand_total(customer_id=user.id)

        # Prepare the data to be passed to the template
        data = {
            'cart_items': cart_items,  # Pass the filtered cart items to the template
            'grand_total': grand_total,
            'page_title': 'Cart',  # You can set the page title as per your requirement
            'cart_count': cart_items.count()
        }
    else:
        # If the user is not authenticated, handle accordingly
        data = {
            'cart_items': [],  # No cart items for unauthenticated users
            'page_title': 'Cart',  # Page title remains the same
            'error_message': 'You need to log in to view your cart.'  # Optional error message
        }

    return render(request, 'frontend/cart.html', data)

@login_required
def add_to_cart(request, product_id):
    # Get the product the user wants to add
    product = get_object_or_404(Product, id=product_id)

    # Check if this product already exists in the user's cart
    cart_item, created = Cart.objects.get_or_create(
        product=product,
        custom_user=request.user,  # Use your user field name
        defaults={'qty': 1}
    )

    if not created:
        # Product already in cart, increase quantity
        cart_item.qty += 1
        cart_item.save()
        messages.info(request, f'Increased quantity for {product.name}.')
    else:
        messages.success(request, f'Added {product.name} to your cart.')

    return redirect('cart')  # Or redirect to product detail page

@login_required
def increase_quantity(request, id):
    cart_item = get_object_or_404(Cart, id=id, custom_user=request.user)

    if cart_item:
        # Increase the quantity
        cart_item.qty += 1
        cart_item.save()
        messages.success(request, f'Quantity increased for {cart_item.product.name} in your cart.')
    else:
        messages.error(request, 'Cart item not found.')

    return redirect('cart')  # Adjust as necessary

@login_required
def decrease_quantity(request, id):
    cart_item = get_object_or_404(Cart, id=id, custom_user=request.user)

    # Decrease the quantity, ensuring it doesn't go below 1
    if cart_item.qty > 1:
        cart_item.qty -= 1
        cart_item.save()
        messages.success(request, f'Quantity decreased for {cart_item.product.name} in your cart.')
    else:
        messages.warning(request, f'Cannot decrease quantity for {cart_item.product.name} below 1.')

    return redirect('cart')  # Adjust as necessary

@login_required
def remove_from_cart(request, id):
    cart_item = get_object_or_404(Cart, id=id, custom_user=request.user)

    # Remove the cart item
    product_name = cart_item.product.name
    cart_item.delete()

    messages.success(request, f'{product_name} removed from your cart.')
    return redirect('cart')  # Adjust as necessary


@login_required
def clear_cart(request):
    cart_items = Cart.objects.filter(custom_user=request.user)

    if cart_items.exists():
        cart_items.delete()
        messages.success(request, 'Cart cleared successfully.')
    else:
        messages.error(request, 'No items found in the cart.')

    return redirect('cart')  # Adjust as necessary

@login_required
def proceed_to_checkout(request):
    user = request.user

    # Filter cart items for the current user
    cart_items = Cart.objects.filter(custom_user=user)

    # Calculate subtotal
    subtotal = sum(item.product.price * item.qty for item in cart_items)

    # Define a fixed shipping charge (you can also calculate dynamically)
    shipping = 50 if cart_items else 0  # ₹50 shipping if there are items

    # Calculate total
    total = subtotal + shipping

    # Prepare data to send to the template
    data = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
        'page_title': 'Cart',
        'cart_count': cart_items.count(),
    }

    return render(request, 'frontend/order.html', data)

@login_required
def place_order(request):
    user = request.user
    cart_items = Cart.objects.filter(custom_user=user)

    if not cart_items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('cart')

    # Calculate total amount
    total_amount = sum(item.product.price * item.qty for item in cart_items)

    # Create the order
    order = Order.objects.create(
        customer=user,
        total_amount=total_amount,
        payment_method=request.POST.get('payment_method', 'UPI'),  # Default to 'CASH' if not provided
        order_status='PENDING'
    )

    # Create order items
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            qty=item.qty,
            unit_price=item.product.price,
            amount=item.product.price * item.qty,
            discount=0  # Adjust if you have discount logic
        )

    # Clear the cart
    cart_items.delete()

    # Send confirmation email
    subject = f"Order Confirmation - {order.order_number}"
    message = (
        f"Dear {user.first_name},\n\n"
        f"Thank you for your order #{order.order_number}.\n"
        f"Total Amount: ₹{order.total_amount}\n\n"
        f"We will notify you once your order is shipped.\n\n"
        f"Best regards,\n"
        f"Your Company Name"
    )
    # send_mail(
    #     subject,
    #     message,
    #     settings.DEFAULT_FROM_EMAIL,
    #     [user.email],
    #     fail_silently=False,
    # )

    messages.success(request, f"Order #{order.order_number} placed successfully!")
    # return redirect('home')  # Redirect to a success page or order summary

    # Return success response
    return JsonResponse({'success': True})