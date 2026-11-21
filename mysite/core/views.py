from django.shortcuts import render
from housing.models import Houses
from django.utils.translation import get_language


def home(request):
    lang = get_language()
    houses = list(Houses.objects.all().values(
        'id', 'name', 'address', 'latitude', 'longitude'
    ))
    for h in houses:
        h['lang'] = lang
    return render(request, 'index.html', {'houses': houses})