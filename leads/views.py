from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import get_language
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
import json
import logging

# Product model removed with catalog app
from .models import Lead, LeadSource, LeadActivity, SurveySheet
from .forms import LeadForm, QuickQuoteForm, ContactForm

logger = logging.getLogger(__name__)


def parse_request_data(request):
    """Допоміжна функція для парсингу JSON/POST даних"""
    if request.content_type == 'application/json':
        return json.loads(request.body)
    else:
        return request.POST


def add_lead_metadata(lead, request):
    """Додати метадані до заявки"""
    lead.ip_address = get_client_ip(request)
    lead.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
    lead.language = get_language()
    lead.source = get_or_create_source(request)
    lead.source_page = request.META.get('HTTP_REFERER', '')[:500]
    if hasattr(lead, 'referrer'):
        lead.referrer = request.META.get('HTTP_REFERER', '')[:500]


def create_lead_activity(lead, description):
    """Створити активність для заявки"""
    LeadActivity.objects.create(
        lead=lead,
        activity_type='created',
        description=description,
        user='System'
    )


def format_form_errors(form):
    """Форматувати помилки валідації форми"""
    errors = {}
    for field, field_errors in form.errors.items():
        errors[field] = [str(error) for error in field_errors]
    return errors


def get_client_ip(request):
    """Отримати IP адресу клієнта"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_or_create_source(request):
    """Отримати або створити джерело заявки на основі UTM параметрів"""
    utm_source = request.GET.get('utm_source', '')
    utm_medium = request.GET.get('utm_medium', '')
    utm_campaign = request.GET.get('utm_campaign', '')
    
    if utm_source or utm_medium or utm_campaign:
        source_name = f"{utm_source}_{utm_medium}_{utm_campaign}".strip('_')
        source, created = LeadSource.objects.get_or_create(
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
            defaults={'name': source_name or 'Direct'}
        )
        return source
    
    # Створюємо джерело на основі реферера
    referrer = request.META.get('HTTP_REFERER', '')
    if 'google' in referrer.lower():
        source, created = LeadSource.objects.get_or_create(
            name='Google Organic',
            defaults={'utm_source': 'google', 'utm_medium': 'organic'}
        )
    elif 'facebook' in referrer.lower():
        source, created = LeadSource.objects.get_or_create(
            name='Facebook',
            defaults={'utm_source': 'facebook', 'utm_medium': 'social'}
        )
    else:
        source, created = LeadSource.objects.get_or_create(
            name='Direct',
            defaults={'utm_source': 'direct', 'utm_medium': 'none'}
        )
    
    return source


@require_http_methods(["POST"])
def submit_lead(request):
    """Основна функція відправки заявки (AJAX)"""
    try:
        # Парсимо JSON дані
        data = parse_request_data(request)
        
        # Отримуємо продукт якщо передано slug
        product = None
        product_slug = data.get('product_slug')
        if product_slug:
            try:
                product = Product.objects.get(slug=product_slug, is_published=True)
            except Product.DoesNotExist:
                pass
        
        # Створюємо форму
        form = LeadForm(data, product_slug=product_slug)
        
        if form.is_valid():
            # Зберігаємо заявку
            lead = form.save(commit=False)
            
            # Додаємо мета-дані
            add_lead_metadata(lead, request)
            lead.save()
            
            # Створюємо активність
            create_lead_activity(lead, 'Заявка створена через форму на сайті')
            
            # Відправляємо нотифікації
            send_all_notifications(lead)
            
            logger.info(f'Нова заявка створена: {lead.uuid} - {lead.email}')
            
            return JsonResponse({
                'success': True,
                'message': 'Дякуємо! Ваша заявка успішно відправлена.',
                'lead_uuid': str(lead.uuid),
                'redirect_url': f'/leads/thank-you/{lead.uuid}/'
            })
        else:
            # Повертаємо помилки валідації
            return JsonResponse({
                'success': False,
                'errors': format_form_errors(form),
                'message': 'Будь ласка, виправте помилки у формі.'
            })
    
    except Exception as e:
        logger.error(f'Помилка при створенні заявки: {str(e)}')
        return JsonResponse({
            'success': False,
            'message': 'Виникла помилка при відправці заявки. Спробуйте пізніше.',
            'error': str(e) if settings.DEBUG else None
        })


@require_http_methods(["POST"])
def quick_quote(request):
    """Швидкий запит ціни (спрощена форма)"""
    try:
        data = parse_request_data(request)
        
        # Отримуємо продукт
        product = None
        product_id = data.get('product_id')
        if product_id:
            try:
                product = Product.objects.get(id=product_id, is_published=True)
            except Product.DoesNotExist:
                pass
        
        form = QuickQuoteForm(data, product=product)
        
        if form.is_valid():
            lead = form.save(commit=False)
            
            # Додаємо мета-дані
            add_lead_metadata(lead, request)
            lead.save()
            
            # Створюємо активність
            create_lead_activity(lead, f'Швидкий запит ціни для продукту: {product.get_name() if product else "Загальний"}')
            
            logger.info(f'Швидкий запит ціни: {lead.uuid} - {lead.email}')
            
            return JsonResponse({
                'success': True,
                'message': 'Дякуємо! Ми зв\'яжемося з вами найближчим часом.',
                'lead_uuid': str(lead.uuid)
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': format_form_errors(form),
                'message': 'Будь ласка, заповніть всі обов\'язкові поля.'
            })
    
    except Exception as e:
        logger.error(f'Помилка при швидкому запиті: {str(e)}')
        return JsonResponse({
            'success': False,
            'message': 'Виникла помилка. Спробуйте пізніше.'
        })


@require_http_methods(["POST"])
def contact(request):
    """Загальна контактна форма"""
    try:
        data = parse_request_data(request)
        
        form = ContactForm(data)
        
        if form.is_valid():
            lead = form.save(commit=False)
            
            # Додаємо мета-дані
            add_lead_metadata(lead, request)
            lead.save()
            
            # Створюємо активність
            create_lead_activity(lead, 'Заявка через контактну форму')
            
            logger.info(f'Контактна заявка: {lead.uuid} - {lead.email}')
            
            return JsonResponse({
                'success': True,
                'message': 'Дякуємо за звернення! Ми відповімо вам найближчим часом.',
                'lead_uuid': str(lead.uuid)
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': format_form_errors(form),
                'message': 'Будь ласка, виправте помилки у формі.'
            })
    
    except Exception as e:
        logger.error(f'Помилка в контактній формі: {str(e)}')
        return JsonResponse({
            'success': False,
            'message': 'Виникла помилка. Спробуйте пізніше.'
        })


def _normalize_phone(raw: str) -> str:
    """Нормалізує номер телефону до формату +380…"""
    phone = raw.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    if not phone.startswith('+'):
        phone = ('+' if phone.startswith('380') else '+38') + phone
    return phone


def _build_survey_notification(survey: 'SurveySheet') -> str:
    """Форматує читабельне повідомлення для email/Telegram із об'єкта SurveySheet."""
    def row(label, *vals):
        filled = [v for v in vals if v]
        return f'{label}: {" / ".join(filled)}' if filled else ''

    lines = [
        '📋 ОПИТУВАЛЬНИЙ ЛИСТ',
        '',
        f'👤 {survey.contact_person}  |  🏢 {survey.company or "—"}',
        f'📞 {survey.phone}  |  ✉️  {survey.email}',
        f'📍 {survey.address}' if survey.address else '',
        '',
        f'Призначення: {survey.purpose}' if survey.purpose else '',
        '',
        '── Гаряча сторона ──',
        row('Середовище',     survey.hot_medium),
        row('t° вх/вих °C',   survey.hot_temp_in, survey.hot_temp_out),
        row('Витрата кг/год',  survey.hot_flow_in, survey.hot_flow_out),
        row('Тиск кг/см²',    survey.hot_pressure_in, survey.hot_pressure_out),
        row('Δp кПа',         survey.hot_pressure_drop),
        '',
        '── Холодна сторона ──',
        row('Середовище',     survey.cold_medium),
        row('t° вх/вих °C',   survey.cold_temp_in, survey.cold_temp_out),
        row('Витрата кг/год',  survey.cold_flow_in, survey.cold_flow_out),
        row('Тиск кг/см²',    survey.cold_pressure_in, survey.cold_pressure_out),
        row('Δp кПа',         survey.cold_pressure_drop),
        '',
        row('Теплове навантаження кВт', survey.heat_load),
        '',
        '── Конструкційні вимоги ──',
        row('Матеріал пластин', survey.plate_material, f'{survey.plate_material_unit} мм' if survey.plate_material_unit else ''),
        row('Тип під\'єднань',  survey.connection_type, f'{survey.design_pressure} бар' if survey.design_pressure else ''),
        row('Зворотні фланці', survey.flanges, f'{survey.flanges_count} шт.' if survey.flanges_count else ''),
        '',
        f'💬 {survey.comments}' if survey.comments else '',
        '',
        f'⏰ {survey.created_at.strftime("%d.%m.%Y %H:%M")}  |  IP: {survey.ip_address or "—"}',
        f'🔗 {settings.SITE_URL}/admin/leads/surveysheet/{survey.pk}/change/',
    ]
    return '\n'.join(line for line in lines if line is not None)


def _send_survey_notifications(survey: 'SurveySheet') -> None:
    """Відправляє email та Telegram-нотифікацію про новий опитувальний лист."""
    message = _build_survey_notification(survey)

    # ── Email ──────────────────────────────────────────────────────────────────
    try:
        from django.core.mail import send_mail
        from .models import NotificationSettings as NS
        ns = NS.get_settings()
        if ns.email_enabled and ns.email_recipients:
            recipients = [e.strip() for e in ns.email_recipients.split(',') if e.strip()]
            send_mail(
                subject=f'Новий опитувальний лист — {survey.contact_person} ({survey.company or survey.email})',
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=True,
            )
    except Exception as exc:
        logger.warning(f'Survey email notification failed: {exc}')

    # ── Telegram ───────────────────────────────────────────────────────────────
    try:
        import requests as req
        from .models import NotificationSettings as NS
        ns = NS.get_settings()
        if ns.telegram_enabled and ns.telegram_bot_token and ns.telegram_chat_id:
            req.post(
                f'https://api.telegram.org/bot{ns.telegram_bot_token}/sendMessage',
                json={'chat_id': ns.telegram_chat_id, 'text': message},
                timeout=8,
            )
    except Exception as exc:
        logger.warning(f'Survey Telegram notification failed: {exc}')


@require_http_methods(["POST"])
def survey_submit(request):
    """Зберігає опитувальний лист у таблицю SurveySheet і надсилає нотифікації."""
    try:
        d = request.POST

        contact_person = d.get('contact_person', '').strip()
        email          = d.get('email', '').strip()
        raw_phone      = d.get('phone', '').strip()

        if not contact_person or not email or not raw_phone:
            return JsonResponse({
                'success': False,
                'message': 'Заповніть обов\'язкові поля: Конт. особа, Email, Телефон.',
            }, status=400)

        def v(k):
            return d.get(k, '').strip()

        survey = SurveySheet(
            # Дані замовника
            company        = v('company'),
            address        = v('address'),
            phone          = _normalize_phone(raw_phone),
            email          = email,
            contact_person = contact_person,
            # Призначення
            purpose        = v('purpose'),
            # Гаряча сторона
            hot_medium        = v('hot_medium'),
            hot_temp_in       = v('hot_temp_in'),
            hot_temp_out      = v('hot_temp_out'),
            hot_flow_in       = v('hot_flow_in'),
            hot_flow_out      = v('hot_flow_out'),
            hot_pressure_in   = v('hot_pressure_in'),
            hot_pressure_out  = v('hot_pressure_out'),
            hot_pressure_drop = v('hot_pressure_drop'),
            # Холодна сторона
            cold_medium        = v('cold_medium'),
            cold_temp_in       = v('cold_temp_in'),
            cold_temp_out      = v('cold_temp_out'),
            cold_flow_in       = v('cold_flow_in'),
            cold_flow_out      = v('cold_flow_out'),
            cold_pressure_in   = v('cold_pressure_in'),
            cold_pressure_out  = v('cold_pressure_out'),
            cold_pressure_drop = v('cold_pressure_drop'),
            heat_load          = v('heat_load'),
            # Теплофізичні властивості
            hot_thermo_temp   = v('hot_thermo_temp'),
            hot_density       = v('hot_density'),
            hot_specific_heat = v('hot_specific_heat'),
            hot_conductivity  = v('hot_conductivity'),
            hot_viscosity     = v('hot_viscosity'),
            cold_thermo_temp   = v('cold_thermo_temp'),
            cold_density       = v('cold_density'),
            cold_specific_heat = v('cold_specific_heat'),
            cold_conductivity  = v('cold_conductivity'),
            cold_viscosity     = v('cold_viscosity'),
            # Конструкційні вимоги
            plate_material      = v('plate_material'),
            plate_material_unit = v('plate_material_unit'),
            connection_type     = v('connection_type'),
            design_pressure     = v('design_pressure'),
            flanges             = v('flanges'),
            flanges_count       = v('flanges_count'),
            # Коментарі та мета
            comments    = v('comments'),
            ip_address  = get_client_ip(request),
            language    = get_language(),
            source_page = request.META.get('HTTP_REFERER', '')[:500],
        )
        survey.save()
        _send_survey_notifications(survey)

        logger.info(f'SurveySheet #{survey.pk} ({survey.uuid}) — {survey.email}')

        return JsonResponse({
            'success': True,
            'message': 'Дякуємо! Опитувальний лист отримано. Ми зв\'яжемося з вами найближчим часом.',
        })

    except Exception as e:
        logger.error(f'survey_submit error: {e}')
        return JsonResponse({
            'success': False,
            'message': 'Виникла помилка. Будь ласка, спробуйте пізніше.',
            'error': str(e) if settings.DEBUG else None,
        }, status=500)


def thank_you(request):
    """Загальна сторінка подяки"""
    context = {
        'page_title': 'Дякуємо за заявку!',
    }
    return render(request, 'leads/thank_you.html', context)


def lead_form(request):
    """Сторінка з формою заявки"""
    context = {
        'page_title': 'Залишити заявку',
    }
    return render(request, 'leads/lead_form.html', context)


def thank_you_detail(request, lead_uuid):
    """Персоналізована сторінка подяки"""
    lead = get_object_or_404(Lead, uuid=lead_uuid)
    
    context = {
        'page_title': 'Дякуємо за заявку!',
        'lead': lead,
    }
    return render(request, 'leads/thank_you_detail.html', context)


# Додано інтеграції (використовуючи наявні імпорти та стиль коду)
def send_telegram_notification(lead):
    """Відправка нотифікації в Telegram"""
    try:
        from .models import NotificationSettings
        import requests
        
        settings_obj = NotificationSettings.get_settings()
        
        if not settings_obj.telegram_enabled or not settings_obj.telegram_bot_token:
            return False
        
        message = f"""
🔔 *Нова заявка на сайті!*

👤 *Клієнт:* {lead.name}
📧 *Email:* {lead.email}
📱 *Телефон:* {lead.phone}

💼 *Компанія:* {lead.company or 'Не вказано'}
🎯 *Тип запиту:* {lead.get_inquiry_type_display()}

📝 *Повідомлення:*
{lead.message}

🌐 *Мова:* {lead.language}
📍 *IP:* {lead.ip_address}
🔗 *Джерело:* {lead.source.name if lead.source else 'Невідоме'}

⏰ *Час:* {lead.created_at.strftime('%d.%m.%Y %H:%M')}
        """
        
        url = f"https://api.telegram.org/bot{settings_obj.telegram_bot_token}/sendMessage"
        payload = {
            'chat_id': settings_obj.telegram_chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            # Створюємо активність
            LeadActivity.objects.create(
                lead=lead,
                activity_type='telegram_sent',
                description='Нотифікацію відправлено в Telegram',
                user='System'
            )
            logger.info(f'Telegram нотифікація відправлена для заявки {lead.uuid}')
            return True
        else:
            logger.error(f'Помилка Telegram API: {response.text}')
            return False
            
    except Exception as e:
        logger.error(f'Помилка відправки Telegram: {str(e)}')
        return False


def send_viber_notification(lead):
    """Відправка нотифікації в Viber"""
    try:
        from .models import NotificationSettings
        import requests
        
        settings_obj = NotificationSettings.get_settings()
        
        if not settings_obj.viber_enabled or not settings_obj.viber_bot_token:
            return False
        
        message = f"""
🔔 Нова заявка на сайті!

👤 Клієнт: {lead.name}
📧 Email: {lead.email}
📱 Телефон: {lead.phone}

💼 Компанія: {lead.company or 'Не вказано'}
🎯 Тип запиту: {lead.get_inquiry_type_display()}

📝 Повідомлення:
{lead.message}

🌐 Мова: {lead.language}
📍 IP: {lead.ip_address}
🔗 Джерело: {lead.source.name if lead.source else 'Невідоме'}

⏰ Час: {lead.created_at.strftime('%d.%m.%Y %H:%M')}
        """
        
        url = f"https://chatapi.viber.com/pa/send_message"
        headers = {
            'X-Viber-Auth-Token': settings_obj.viber_bot_token
        }
        payload = {
            'receiver': settings_obj.viber_admin_id,
            'type': 'text',
            'text': message
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            # Створюємо активність
            LeadActivity.objects.create(
                lead=lead,
                activity_type='viber_sent',
                description='Нотифікацію відправлено в Viber',
                user='System'
            )
            logger.info(f'Viber нотифікація відправлена для заявки {lead.uuid}')
            return True
        else:
            logger.error(f'Помилка Viber API: {response.text}')
            return False
            
    except Exception as e:
        logger.error(f'Помилка відправки Viber: {str(e)}')
        return False


def send_email_notification(lead):
    """Відправка email нотифікації"""
    try:
        from django.core.mail import send_mail
        from .models import NotificationSettings
        
        settings_obj = NotificationSettings.get_settings()
        
        if not settings_obj.email_enabled:
            return False
        
        subject = settings_obj.email_subject_template.format(name=lead.name)
        
        message = f"""
Нова заявка на сайті Adiabatic

Клієнт: {lead.name}
Email: {lead.email}
Телефон: {lead.phone}
Компанія: {lead.company or 'Не вказано'}

Тип запиту: {lead.get_inquiry_type_display()}

Повідомлення:
{lead.message}

Додаткова інформація:
- Мова: {lead.language}
- IP адреса: {lead.ip_address}
- Джерело: {lead.source.name if lead.source else 'Невідоме'}
- Дата створення: {lead.created_at.strftime('%d.%m.%Y %H:%M')}

Переглянути в адмінці: {settings.SITE_URL}/admin/leads/lead/{lead.id}/
        """
        
        recipients = [email.strip() for email in settings_obj.email_recipients.split(',')]
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False
        )
        
        # Створюємо активність
        LeadActivity.objects.create(
            lead=lead,
            activity_type='email_sent',
            description=f'Email відправлено на {", ".join(recipients)}',
            user='System'
        )
        
        logger.info(f'Email нотифікацію відправлено для заявки {lead.uuid}')
        return True
        
    except Exception as e:
        logger.error(f'Помилка відправки email: {str(e)}')
        return False


def send_all_notifications(lead):
    """Відправка всіх налаштованих нотифікацій"""
    results = {
        'email': send_email_notification(lead),
        'telegram': send_telegram_notification(lead),
        'viber': send_viber_notification(lead)
    }
    
    logger.info(f'Нотифікації для заявки {lead.uuid}: {results}')
    return results
