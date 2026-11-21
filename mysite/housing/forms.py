from django import forms
from django.forms import CheckboxSelectMultiple
from .models import Houses, HouseImage, Room, RoomImage, Comment, Booking
from django.forms import inlineformset_factory
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

class HouseForm(forms.ModelForm):
    class Meta:
        model = Houses
        fields = ['name', 'description', 'address', 'phone_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

HouseImageFormSet = inlineformset_factory(
    Houses, HouseImage, fields=('image',), extra=8, max_num=8, can_delete=True
)

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = [
            'name', 'description', 'beds', 'sofas', 'floor',
            'smoking_allowed', 'has_balcony', 'has_tv',
            'has_air_conditioning', 'has_wifi',
            'price_per_night', 'discount'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'beds': forms.NumberInput(attrs={'class': 'form-control'}),
            'sofas': forms.NumberInput(attrs={'class': 'form-control'}),
            'floor': forms.NumberInput(attrs={'class': 'form-control'}),
            'smoking_allowed': forms.CheckboxInput(attrs={'class': 'form-check-input large-checkbox'}),
            'has_balcony': forms.CheckboxInput(attrs={'class': 'form-check-input large-checkbox'}),
            'has_tv': forms.CheckboxInput(attrs={'class': 'form-check-input large-checkbox'}),
            'has_air_conditioning': forms.CheckboxInput(attrs={'class': 'form-check-input large-checkbox'}),
            'has_wifi': forms.CheckboxInput(attrs={'class': 'form-check-input large-checkbox'}),
            'price_per_night': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['smoking_allowed', 'has_balcony', 'has_tv', 'has_air_conditioning', 'has_wifi']:
            self.fields[field].initial = False


RoomImageFormSet = inlineformset_factory(
    Room, RoomImage, fields=('image',), extra=4, max_num=4, can_delete=True
)

class RoomImageForm(forms.ModelForm):
    class Meta:
        model = RoomImage
        fields = ('image',)
    image = forms.ImageField(required=False)

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['rating', 'content']
        widgets = {
            'rating': forms.RadioSelect(
                choices=[(i, f'{i} ★') for i in range(1, 6)],
                attrs={'class': 'form-check-input rating-stars'}
            ),
            'content': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Leave your comment... (optional)'
            }),
        }

class BookingForm(forms.ModelForm):
    date_range = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Select dates'),
        })
    )

    class Meta:
        model = Booking
        fields = (
            'first_name',
            'last_name',
            'email',
            'date_from',
            'date_to',
        )
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'date_from': forms.HiddenInput(),
            'date_to': forms.HiddenInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        date_range = cleaned_data.get('date_range')

        if not date_range:
            raise forms.ValidationError(_("Please select check-in and check-out dates."))

        try:
            start, end = date_range.split(' to ')
            cleaned_data['date_from'] = start
            cleaned_data['date_to'] = end
        except ValueError:
            raise forms.ValidationError(_("Invalid date range."))

        if cleaned_data['date_from'] >= cleaned_data['date_to']:
            raise forms.ValidationError(_("Check-out date must be after check-in date."))

        return cleaned_data