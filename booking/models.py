from django.db import models
from datetime import datetime, timedelta


class Maid(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField()
    profile_picture = models.ImageField(upload_to='maid_pics/')
    available_times = models.JSONField()

    def __str__(self):
        return self.name


class Booking(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    country = models.CharField(max_length=100)
    additional_info = models.CharField(max_length=300, blank=True, null=True)
    rooms = models.PositiveIntegerField()
    clean_bathroom = models.BooleanField(default=False)
    clean_kitchen = models.BooleanField(default=False)
    additional_services = models.JSONField()
    maid = models.ForeignKey(Maid, on_delete=models.CASCADE, default=1)
    scheduled_time = models.DateTimeField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.scheduled_time}"

    @staticmethod
    def is_time_slot_available(maid, date, start_time, duration):
        end_time = (datetime.combine(date, start_time) + duration).time()
        overlapping_bookings = Booking.objects.filter(
            maid=maid,
            scheduled_time__date=date,
            scheduled_time__time__gte=start_time,
            scheduled_time__time__lt=end_time
        )
        return not overlapping_bookings.exists()
