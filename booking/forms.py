from django import forms
from .models import Booking


class ServiceSelectionForm(forms.ModelForm):
    ADDITIONAL_SERVICES_CHOICES = [
        ('laundry', 'Laundry'),
        ('washing_dishes', 'Washing Dishes'),
        ('ironing', 'Ironing'),
        ('microwave_cleaning', 'Microwave Cleaning'),
        ('refrigerator_cleaning', 'Refrigerator Cleaning'),
        ('wash_oven', 'Wash Oven'),
        ('cleaning_kitchen_cabinets', 'Cleaning Kitchen Cabinets'),
        ('window_cleaning', 'Window Cleaning'),
        ('remove_tray_for_pets', 'Remove Tray for Pets'),
        ('easy_meal_prepping', 'Easy Meal Prepping')
    ]

    additional_services = forms.MultipleChoiceField(
        choices=ADDITIONAL_SERVICES_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Booking
        fields = ['rooms', 'clean_bathroom', 'clean_kitchen', 'additional_services']


class PersonalInformationForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'address', 'city', 'state', 'zip_code', 'country', 'additional_info']
