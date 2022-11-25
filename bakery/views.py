import uuid

from yookassa import Payment as YooPayment
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from rest_framework.decorators import api_view
from phonenumber_field.modelfields import PhoneNumberField
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from .models import User, Order, OrderCake, Payment


class UserSerializer(ModelSerializer):
    phone = PhoneNumberField(unique=False)

    class Meta:
        model = User
        fields = ['name', 'phone', 'email']


class OrderSerializer(ModelSerializer):

    class Meta:
        model = Order
        fields = ['address', 'date', 'time', 'delivcomments', ]


class CakeSerializer(ModelSerializer):

    class Meta:
        model = OrderCake
        fields = ['levels', 'form', 'topping', 'berries', 'decor', 'words', 'comment', 'cost', ]


def register_user(request):
    if 'name' in request.POST or 'email' in request.POST:
        User.objects.update_or_create(
            phone=request.POST['phone'],
            defaults={
                'name': request.POST.get('name'),
                'email': request.POST.get('email'),
            },
        )
    else:
        User.objects.get_or_create(phone=request.POST['phone'])
    return redirect('lk', request.POST['phone'])


def profile(request, phone):
    user = User.objects.get(phone=phone)

    return render(request, 'lk.html', {'user': user})


@transaction.atomic
@api_view(['POST'])
def register_order(request):
    request_payload = request.data
    cake_serializer = CakeSerializer(data=request_payload)
    cake_serializer.is_valid(raise_exception=True)
    order_serializer = OrderSerializer(data=request_payload)
    order_serializer.is_valid(raise_exception=True)
    user_serializer = UserSerializer(data=request_payload)
    user_serializer.is_valid(raise_exception=True)
    user, _ = User.objects.get_or_create(
        phone=user_serializer.validated_data['phone'],
        defaults={
            'name': user_serializer.validated_data['name'],
            'email': user_serializer.validated_data['email'],
        },
    )
    order, _ = Order.objects.get_or_create(
        address=order_serializer.validated_data['address'],
        date=order_serializer.validated_data['date'],
        time=order_serializer.validated_data['time'],
        delivcomments=order_serializer.validated_data.get('delivcomments', ''),
        user=user
    )
    cake = OrderCake.objects.create(
        levels=cake_serializer.validated_data['levels'],
        form=cake_serializer.validated_data['form'],
        topping=cake_serializer.validated_data['topping'],
        berries=cake_serializer.validated_data['berries'],
        decor=cake_serializer.validated_data['decor'],
        words=cake_serializer.validated_data.get('words', ''),
        comment=cake_serializer.validated_data.get('comment', ''),
        cost=cake_serializer.validated_data['cost'],
        order=order
    )
    payment = Payment.objects.create(order=order)
    yoo_payment = YooPayment.create({
        'amount': {
            'value': f'{cake.cost}',
            'currency': 'RUB'
        },
        'confirmation': {
            'type': 'redirect',
            'return_url': request.url  # ПОДСТАВИТЬ НОРМАЛЬНУЮ ССЫЛКУ
        },
        'capture': True,
        'description': f'Заказ №{order.id}'
    }, uuid.uuid4())
    payment.yookassa_payment_id = yoo_payment.id
    payment.save()
    return redirect(yoo_payment.confirmation.confirmation_url)


@api_view(['POST'])
def payment_update(request):
    event = request.data.get('event')
    if event == 'payment.succeeded':
        status = 'succeeded'
    elif event == 'payment.canceled':
        status = 'canceled'
    elif event == 'payment.waiting_for_capture':
        status = 'succeeded'
    else:
        return Response(status=403)
    payment = Payment.get(yookassa_payment_id=request.data['object']['id'])
    payment.status = status
    return Response()
