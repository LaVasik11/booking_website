import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, HttpResponseForbidden
from django.template.loader import render_to_string
from .forms import HouseForm, HouseImageFormSet, RoomForm, RoomImageFormSet, CommentForm, BookingForm, RoomImageForm, Booking
from .models import Houses, Room, Comment, HouseImage, RoomImage
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from math import floor
from django.forms.models import inlineformset_factory
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from django.views.decorators.http import require_POST


def housing(request):
    houses = Houses.objects.prefetch_related('images').all()

    context = {
        "houses": houses
    }

    return render(request, "housing/housing.html", context)

def house_page(request, pk):
    house = get_object_or_404(Houses, pk=pk)
    user = request.user
    form = CommentForm()
    active_rooms = house.rooms.filter(is_active=True)

    def user_has_booking():
        if not user.is_authenticated:
            return False
        return Booking.objects.filter(
            user=user,
            room__house=house
        ).exists()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        page = request.POST.get('page')
        content = request.POST.get('content', '').strip()
        rating = request.POST.get('rating')

        if not user.is_authenticated:
            return JsonResponse({"error": "You must log in to comment."})

        if not user_has_booking():
            return JsonResponse({
                "error": "Only users who have booked a room in this hotel can leave a review."
            })

        if Comment.objects.filter(house=house, user=user).exists():
            return JsonResponse({"error": "You have already rated this house."})

        if rating:
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.house = house
                comment.user = user
                comment.save()

        paginator = Paginator(
            house.comments.exclude(content="").order_by('-created_at'),
            9
        )
        try:
            comments = paginator.page(page or 1)
        except:
            comments = paginator.page(1)

        comments_html = render_to_string(
            "housing/comments_list.html",
            {"comments": comments},
            request=request
        )
        return JsonResponse({"success": True, "comments_html": comments_html})

    elif request.method == "POST":
        if not user.is_authenticated:
            messages.error(request, "You must log in to comment.")
            return redirect(request.path)

        if not user_has_booking():
            messages.error(
                request,
                "Only users who have booked a room in this hotel can leave a review."
            )
            return redirect(request.path)

        if Comment.objects.filter(house=house, user=user).exists():
            messages.error(request, "You have already rated this house.")
            return redirect(request.path)

        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.house = house
            comment.user = user
            comment.save()
            messages.success(request, "Your comment was added successfully!")
            return redirect(request.path)
        else:
            messages.error(request, "Please correct the errors below.")

    page = request.GET.get('page', 1)
    paginator = Paginator(
        house.comments.exclude(content="").order_by('-created_at'),
        9
    )
    try:
        comments = paginator.page(page)
    except:
        comments = paginator.page(1)

    existing_comment = None
    has_booking = False
    if user.is_authenticated:
        existing_comment = Comment.objects.filter(house=house, user=user).first()
        has_booking = user_has_booking()

    average_rating = house.comments.aggregate(avg=Avg('rating'))['avg'] or 0
    full_stars = floor(average_rating)
    half_star = 1 if average_rating - full_stars >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star

    context = {
        "house": house,
        "rooms": active_rooms,
        "pk": pk,
        "form": form,
        "comments": comments,
        "existing_comment": existing_comment,
        "has_booking": has_booking,
        "average_rating": average_rating,
        "full_stars": range(full_stars),
        "half_star": half_star,
        "empty_stars": range(empty_stars),
    }

    return render(request, 'housing/house_page.html', context)


@login_required
def add_house(request):
    if request.user.role != 'hotel_owner':
        return redirect('home')

    if request.method == 'POST':
        form = HouseForm(request.POST)
        formset = HouseImageFormSet(request.POST, request.FILES, prefix='images')
        if form.is_valid() and formset.is_valid():
            house = form.save(commit=False)
            house.owner = request.user
            house.save()
            formset.instance = house
            formset.save()
            messages.success(request, "Hotel successfully created.")
            return redirect('house_page', pk=house.pk)
    else:
        form = HouseForm()
        formset = HouseImageFormSet(prefix='images')

    return render(
        request, 
        'housing/add_house.html', 
        {'form': form, 'formset': formset}
    )



@login_required
def edit_house(request, pk):
    house = get_object_or_404(Houses, id=pk, owner=request.user)
    User = get_user_model()
    offline_user = User.objects.get(email='offline@booking.com')

    if request.method == 'POST':

        if 'room_id' in request.POST:
            room = get_object_or_404(Room, id=request.POST['room_id'], house=house)
            date_from_str = request.POST.get('date_from')
            date_to_str = request.POST.get('date_to')

            try:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
                date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
            except:
                messages.error(request, _("Invalid dates"))
                return redirect('edit_house', pk=house.id)

            if date_from > date_to:
                messages.error(request, _("Invalid dates"))
                return redirect('edit_house', pk=house.id)

            conflict = room.bookings.filter(
                date_from__lte=date_to,
                date_to__gte=date_from
            ).exists()

            if conflict:
                messages.error(request, _("Room is already booked for these dates"))
                return redirect('edit_house', pk=house.id)

            Booking.objects.create(
                user=offline_user,
                room=room,
                first_name=request.POST.get('first_name', '—'),
                last_name='—',
                email='offline@booking',
                date_from=date_from,
                date_to=date_to,
                source=Booking.SOURCE_OFFLINE
            )

            messages.success(request, _("Dates successfully blocked"))
            return redirect('edit_house', pk=house.id)

        form = HouseForm(request.POST, instance=house)
        formset = HouseImageFormSet(request.POST, request.FILES, instance=house)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, _("House updated successfully"))
            return redirect('owner_profile')

    else:
        form = HouseForm(instance=house)
        formset = HouseImageFormSet(instance=house)

    booked_ranges_by_room = {}
    for room in house.rooms.all():
        booked_ranges_by_room[room.id] = [
            {
                "from": booking.date_from.isoformat(),
                "to": booking.date_to.isoformat(),
            }
            for booking in room.bookings.filter(date_to__gte=now().date())
        ]

    context = {
        'form': form,
        'formset': formset,
        'house': house,
        'pk': pk,
        'booked_ranges_by_room': booked_ranges_by_room,
    }

    return render(request, 'housing/edit_house.html', context)



@login_required
def delete_house(request, pk):
    house = get_object_or_404(Houses, pk=pk)

    if request.user != house.owner and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to delete this hotel.")
    if request.method == "POST":

        for img in house.images.all():
            if img.image:
                img.image.delete(save=False)
            img.delete()

        for room in house.rooms.all():
            for room_img in room.images.all():
                if room_img.image:
                    room_img.image.delete(save=False)
                room_img.delete()

            room.delete()

        house.delete()

        return redirect('owner_profile')

    return redirect('delete_house_confirm', pk=pk)


@login_required
def delete_house_confirm(request, pk):
    house = get_object_or_404(Houses, pk=pk)

    if request.user != house.owner and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to delete this hotel.")

    if request.user == house.owner:
        cancel_url = reverse('edit_house', kwargs={'pk': house.id})
    else:
        cancel_url = request.META.get('HTTP_REFERER', reverse('housing'))

    return render(request, 'housing/delete_house_confirm.html', {
        'house': house,
        'pk': pk,
        'cancel_url': cancel_url,
    })


@login_required
def add_room(request, pk):
    house = get_object_or_404(Houses, pk=pk, owner=request.user)

    if request.method == 'POST':
        form = RoomForm(request.POST)
        formset = RoomImageFormSet(request.POST, request.FILES, prefix='images')  # <--- prefix
        if form.is_valid() and formset.is_valid():
            room = form.save(commit=False)
            room.house = house
            room.save()
            formset.instance = room
            formset.save()
            messages.success(request, "Room added.")
            return redirect('house_page', pk=house.id)
    else:
        form = RoomForm()
        formset = RoomImageFormSet(prefix='images')

    return render(request, 'housing/add_room.html', {
        'form': form,
        'formset': formset,
        'house': house,
        'pk': pk,
    })

@login_required
def edit_room(request, pk):
    room = get_object_or_404(Room, pk=pk)
    house = room.house
    local_messages = []
    if not (request.user.is_superuser or request.user == house.owner):
        return HttpResponseForbidden("You do not have permission to edit this room.")
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        formset = RoomImageFormSet(request.POST, request.FILES, instance=room)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('edit_house', pk=house.id)
        else:
            local_messages.append({
                'type': 'danger',
                'text': "There were errors in the form. Please fix them and try again."
            })
            print("Form errors:", form.errors)
            print("Formset errors:", formset.errors)
    else:
        form = RoomForm(instance=room)
        formset = RoomImageFormSet(instance=room)

    feature_fields = [
        form['smoking_allowed'],
        form['has_balcony'],
        form['has_tv'],
        form['has_air_conditioning'],
        form['has_wifi'],
    ]

    context = {
        'form': form,
        'formset': formset,
        'room': room,
        'house': house,
        'feature_fields': feature_fields,
        'pk': pk,
        'local_messages': local_messages,
    }
    return render(request, 'housing/edit_room.html', context)

def delete_room(request, pk):
    room = get_object_or_404(Room, pk=pk)
    house_id = room.house.id
    room.delete()
    messages.success(request, "Room has been deleted.")
    return redirect('house_page', pk=house_id)



def room_detail(request, pk):
    room = get_object_or_404(Room, id=pk)
    images = room.images.all()
    delete_room_confirm = _("Are you sure you want to delete this room?")
    
    context = {
        'room': room,
        'images': images,
        'pk': pk,
        'delete_room_confirm': delete_room_confirm,
    }
    
    return render(request, 'housing/room_detail.html', context)

def room_booking(request, pk):
    room = get_object_or_404(Room, pk=pk)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            date_from = form.cleaned_data['date_from']
            date_to = form.cleaned_data['date_to']

            if date_from >= date_to:
                messages.error(request, _("Invalid dates"))
                return redirect('room_booking', pk=room.id)

            conflict = room.bookings.filter(
                date_from__lt=date_to,
                date_to__gt=date_from
            ).exists()

            if conflict:
                messages.error(request, _("Room is already booked for these dates"))
                return redirect('room_booking', pk=room.id)

            booking = form.save(commit=False)
            booking.room = room

            if request.user.is_authenticated:
                booking.user = request.user
                if not booking.email:
                    booking.email = request.user.email

            booking.save()

            messages.success(request, _("Booking successfully created"))
            return redirect('booking_success', pk=room.id)

    else:
        initial = {}

        if request.user.is_authenticated:
            initial = {
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
            }

        form = BookingForm(initial=initial)

    booked_ranges = [
        {
            "from": b.date_from.isoformat(),
            "to": b.date_to.isoformat()
        }
        for b in room.bookings.filter(date_to__gte=now().date())
    ]

    return render(request, 'housing/room_booking.html', {
        'room': room,
        'form': form,
        'booked_ranges': booked_ranges,
    })

def booking_success(request, pk):
    room = get_object_or_404(Room, pk=pk)
    context = {"room": room, "pk": room.pk}
    template = 'housing/booking_success.html'
    return render(request, template, context)

@login_required
@require_POST
def toggle_room_active(request, pk):
    room = get_object_or_404(Room, pk=pk)
    house = room.house

    if not (request.user.is_superuser or request.user == house.owner):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    room.is_active = not room.is_active
    room.save(update_fields=['is_active'])

    return JsonResponse({
        'is_active': room.is_active
    })