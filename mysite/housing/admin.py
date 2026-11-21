from django.contrib import admin
from .models import Houses, HouseImage, Room, RoomImage, Booking, Comment


class HouseImageInline(admin.TabularInline):
    model = HouseImage
    extra = 1
    readonly_fields = ('preview_image',)

    def preview_image(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="height: 100px;" />'
        return "-"
    preview_image.allow_tags = True
    preview_image.short_description = "Preview"

class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 1
    readonly_fields = ('preview_image',)

    def preview_image(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="height: 100px;" />'
        return "-"
    preview_image.allow_tags = True
    preview_image.short_description = "Preview"

class RoomInline(admin.TabularInline):
    model = Room
    extra = 1
    inlines = [RoomImageInline]

@admin.register(Houses)
class HousesAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'address', 'phone_number')
    list_filter = ('owner',)
    search_fields = ('name', 'address', 'owner__email')
    inlines = [HouseImageInline, RoomInline]

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'house', 'beds', 'price_per_night')
    list_filter = ('beds', 'house')
    search_fields = ('name', 'house__name')

@admin.register(RoomImage)
class RoomImageAdmin(admin.ModelAdmin):
    list_display = ('room', 'preview', 'uploaded_at')
    readonly_fields = ('preview',)

    def preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="height: 100px;" />'
        return "-"
    preview.allow_tags = True
    preview.short_description = "Preview"

@admin.register(HouseImage)
class HouseImageAdmin(admin.ModelAdmin):
    list_display = ('house', 'preview', 'uploaded_at')
    readonly_fields = ('preview',)

    def preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="height: 100px;" />'
        return "-"
    preview.allow_tags = True
    preview.short_description = "Preview"

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'room',
        'user',
        'date_from',
        'date_to',
        'created_at',
    )

    list_filter = (
        'date_from',
        'date_to',
    )

    search_fields = (
        'user__email',
        'room__name',
    )

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('house', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__email', 'house__name', 'content')