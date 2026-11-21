from decimal import Decimal
from django.db import models
from django.db.models import Avg
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.conf import settings
from geopy.geocoders import Nominatim
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now

# Create your models here.

phone_regex = RegexValidator(
    regex=r'^\+?\d{9,15}$',
    message="Номер телефона должен быть в формате: '+999999999'. Допускается до 15 цифр."
)

class Houses(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='houses'
    )

    name = models.CharField(_('Name'), max_length=128)
    description = models.TextField(_('Description'), null=True, blank=True)
    address = models.CharField(_('Address'), max_length=256, null=True, blank=True)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    phone_number = models.CharField(
        _('Phone number'),
        validators=[phone_regex],
        max_length=17,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        print("SAVE CALLED")  # <-- debug

        if self.address:
            geolocator = Nominatim(user_agent="django_housing_app")
            location = geolocator.geocode(self.address, language="en")

            print("GEOCODE:", self.address)
            print("RESULT:", location)

            if location:
                self.latitude = location.latitude
                self.longitude = location.longitude

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class HouseImage(models.Model):
    house = models.ForeignKey(Houses, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='housing_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.house.name}"



class Room(models.Model):
    house = models.ForeignKey(Houses, on_delete=models.CASCADE, related_name='rooms', verbose_name=_("House"))
    name = models.CharField(_("Room name"), max_length=128)
    description = models.TextField(_("Description"), blank=True, null=True)
    beds = models.PositiveIntegerField(_("Beds"), default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    sofas = models.PositiveIntegerField(_("Sofas"), default=0, validators=[MaxValueValidator(5)])
    floor = models.PositiveIntegerField(_("Floor"), default=1, validators=[MinValueValidator(1), MaxValueValidator(100)])
    smoking_allowed = models.BooleanField(_("Smoking allowed"), default=False)
    has_balcony = models.BooleanField(_("Balcony"), default=False)
    has_tv = models.BooleanField(_("TV"), default=False)
    has_air_conditioning = models.BooleanField(_("Air conditioning"), default=False)
    has_wifi = models.BooleanField(_("Wi-Fi"), default=False)
    price_per_night = models.DecimalField(_("Price per night"), max_digits=8, decimal_places=2)
    discount = models.PositiveSmallIntegerField(_("Discount (%)"), default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    is_active = models.BooleanField(_("Room is available"), default=True)
    def __str__(self):
        return _("%(name)s (%(beds)s bed(s))") % {
            "name": self.name,
            "beds": self.beds
        }

    def is_available(self, start_date, end_date):
        if not self.is_active:
            return False

        today = now().date()

        overlapping = self.bookings.filter(
            date_to__gte=today,
            date_from__lt=end_date,
            date_to__gt=start_date
        )

        return not overlapping.exists()

    @property
    def discounted_price(self):
        if self.discount > 0:
            return self.price_per_night * (Decimal(100) - self.discount) / Decimal(100)
        return self.price_per_night


class RoomImage(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='room_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.room.name}"
    
    def delete(self, *args, **kwargs):
        self.image.delete(save=False)
        super().delete(*args, **kwargs)


class Booking(models.Model):
    SOURCE_WEBSITE = 'website'
    SOURCE_OFFLINE = 'offline'

    SOURCE_CHOICES = [
        (SOURCE_WEBSITE, 'Website'),
        (SOURCE_OFFLINE, 'Offline'),
    ]

    source = models.CharField(
        max_length=16,
        choices=SOURCE_CHOICES,
        default=SOURCE_WEBSITE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings'
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    email = models.EmailField()

    date_from = models.DateField()
    date_to = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} → {self.room}"



    
class Comment(models.Model):
    house = models.ForeignKey('Houses', related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField(blank=True)
    rating = models.PositiveSmallIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('house', 'user')

    def __str__(self):
        return f"{self.user.email} — {self.rating}★ — {self.content[:40]}"