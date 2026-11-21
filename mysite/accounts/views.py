from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .forms import RegisterForm
from .forms import RegisterForm, EmailAuthenticationForm
from django.contrib.auth.decorators import login_required
from housing.models import Booking
from django.utils.timezone import now

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home')
    else:
        form = RegisterForm()

    template = 'accounts/register.html'
    return render(request, template, {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = EmailAuthenticationForm()

    template = 'accounts/login.html'
    return render(request, template, {'form': form})


def user_logout(request):
    logout(request)
    return redirect('home')


@login_required
def owner_profile(request):
    if request.user.role != 'hotel_owner':
        return redirect('home')

    houses = request.user.houses.all()

    template = 'accounts/house_owner_profile.html'

    return render(request, template, {
        'houses': houses,
    })

@login_required
def user_profile(request):
    today = now().date()

    bookings = Booking.objects.filter(
        user=request.user,
        date_to__gte=today
    ).select_related('room').order_by('date_from')

    template = 'accounts/user_profile.html'

    return render(request, template, {
        'bookings': bookings,
    })