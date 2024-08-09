import smtplib
import ssl
from django.core.mail import send_mail, EmailMessage, get_connection
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from datetime import datetime, timedelta
from .forms import ServiceSelectionForm, PersonalInformationForm
from .models import Maid, Booking
import certifi
import logging
from email.mime.image import MIMEImage
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def home_view(request):
    if request.method == 'POST':
        form = ServiceSelectionForm(request.POST)
        if form.is_valid():
            request.session['booking_data'] = form.cleaned_data
            return redirect('select_maid')
    else:
        form = ServiceSelectionForm()
    maids = Maid.objects.all()
    return render(request, 'booking/home.html', {'form': form, 'maids': maids})


def select_maid(request):
    maids = Maid.objects.all()
    return render(request, 'booking/select_maid.html', {'maids': maids})


def select_schedule(request, maid_id):
    maid = get_object_or_404(Maid, id=maid_id)
    if request.method == 'POST':
        date = request.POST.get('date')
        time_slot = request.POST.get('time_slot')
        booking_data = request.session.get('booking_data')
        booking_data['maid'] = maid_id
        booking_data['scheduled_time'] = f"{date} {time_slot}"
        request.session['booking_data'] = booking_data
        return redirect('personal_info')
    return render(request, 'booking/select_schedule.html', {'maid': maid})


def get_availability(request, maid_id, date):
    maid = get_object_or_404(Maid, id=maid_id)
    booking_data = request.session.get('booking_data', {})

    total_minutes = booking_data.get('rooms', 0) * 30
    if booking_data.get('clean_bathroom'):
        total_minutes += 30
    if booking_data.get('clean_kitchen'):
        total_minutes += 30
    additional_services = booking_data.get('additional_services', [])
    total_minutes += len(additional_services) * 30
    service_duration = timedelta(minutes=total_minutes)

    available_times = []
    for time_slot in calculate_available_times(maid, date, total_minutes):
        start_time = datetime.strptime(time_slot, '%H:%M').time()
        if Booking.is_time_slot_available(maid, datetime.strptime(date, '%Y-%m-%d').date(), start_time, service_duration):
            available_times.append(time_slot)

    return JsonResponse({'time_slots': available_times})


def calculate_available_times(maid, date, total_minutes):
    start_time = timedelta(hours=8)
    end_time = timedelta(hours=18)
    break_duration = timedelta(hours=1)
    service_duration = timedelta(minutes=total_minutes)

    available_times = []
    current_time = start_time
    while current_time + service_duration <= end_time:
        available_times.append((datetime.combine(datetime.strptime(date, '%Y-%m-%d').date(),
                                                 (datetime.min + current_time).time())).strftime('%H:%M'))
        current_time += service_duration + break_duration

    return available_times


def personal_info(request):
    if request.method == 'POST':
        form = PersonalInformationForm(request.POST)
        if form.is_valid():
            booking_data = request.session.get('booking_data')
            maid_id = booking_data['maid']
            maid = get_object_or_404(Maid, id=maid_id)
            booking_data['maid'] = maid

            date = booking_data['scheduled_time'].split(' ')[0]
            time = booking_data['scheduled_time'].split(' ')[1]
            scheduled_time = datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')

            booking_data.pop('scheduled_time')

            total_cost = calculate_total_cost(booking_data)

            booking = Booking(
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                phone_number=form.cleaned_data['phone_number'],
                address=form.cleaned_data['address'],
                city=form.cleaned_data['city'],
                state=form.cleaned_data['state'],
                zip_code=form.cleaned_data['zip_code'],
                country=form.cleaned_data['country'],
                additional_info=form.cleaned_data['additional_info'],
                rooms=booking_data['rooms'],
                clean_bathroom=booking_data.get('clean_bathroom', False),
                clean_kitchen=booking_data.get('clean_kitchen', False),
                additional_services=booking_data.get('additional_services', []),
                maid=maid,
                scheduled_time=scheduled_time,
                total_cost=total_cost
            )
            booking.save()
            send_confirmation_email(booking)
            return redirect('confirmation')
    else:
        form = PersonalInformationForm()
    return render(request, 'booking/personal_info.html', {'form': form})


def calculate_total_cost(booking_data):
    cost = booking_data['rooms'] * 30
    if booking_data.get('clean_bathroom'):
        cost += 25
    if booking_data.get('clean_kitchen'):
        cost += 25
    additional_services_count = len(booking_data.get('additional_services', []))
    cost += additional_services_count * 15
    return cost


def send_confirmation_email(booking):
    subject = '💗KAWAII SPARKLE - Booking Confirmation💗'
    from_email = settings.EMAIL_HOST_USER
    to = booking.email

    # Create the plain text message
    text_content = (f'Thank you for your booking, {booking.first_name}!\n\nHere are the details:\n'
                    f'Your Maid: {booking.maid.name}\n'
                    f'Date and Time: {booking.scheduled_time}\n'
                    f'Total Cost: ${booking.total_cost}\n'
                    f'Your Address: {booking.address}, {booking.city}, {booking.state}, {booking.zip_code}, {booking.country}\n'
                    f'See you!')

    # Create the HTML message
    html_content = render_to_string('booking/confirmation_email.html', {'booking': booking})

    # Create the email
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")

    # Attach the maid's profile picture
    try:
        with open(booking.maid.profile_picture.path, 'rb') as image_file:
            image = MIMEImage(image_file.read())
            image.add_header('Content-ID', '<maid_profile_picture>')
            image.add_header('Content-Disposition', 'inline', filename=booking.maid.profile_picture.name)
            msg.attach(image)
    except Exception as e:
        logger.error(f"Error attaching image: {e}")

    # Send the email
    try:
        context = ssl.create_default_context(cafile=certifi.where())
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.starttls(context=context)
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            msg.send()

        logger.info(f'Confirmation email sent to {booking.email}')
    except Exception as e:
        logger.error(f'Error sending email: {e}')
        raise


def confirmation(request):
    return render(request, 'booking/confirmation.html')


def test_email(request):
    subject = 'Test Email'
    message = 'This is a test email.'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = ['mashabodovskaya@gmail.com']
    try:
        context = ssl.create_default_context(cafile=certifi.where())
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.starttls(context=context)
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)

            email_message = f"Subject: {subject}\n\n{message}"
            server.sendmail(email_from, recipient_list, email_message)
        logger.info('Test email sent successfully')
        return HttpResponse('Test email sent successfully')
    except Exception as e:
        logger.error(f'Error sending test email: {e}')
        return HttpResponse(f'Error sending test email: {e}')
