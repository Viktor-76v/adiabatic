from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Lead, LeadSource, EmailTemplate, NotificationSettings, LeadActivity, SurveySheet


class LeadActivityInline(admin.TabularInline):
    """Inline для активності заявки"""
    model = LeadActivity
    extra = 0
    readonly_fields = ['created_at']
    fields = ['activity_type', 'description', 'user', 'created_at']
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    """Адмінка для заявок"""
    list_display = [
        'name', 'email', 'phone', 'company', 'product_name', 
        'get_inquiry_type_display', 'status', 'created_at'
    ]
    list_filter = [
        'status', 'inquiry_type', 
        'consent_gdpr', 'consent_marketing', 'created_at', 'source'
    ]
    search_fields = ['name', 'email', 'phone', 'company', 'message']
    list_editable = ['status']
    readonly_fields = [
        'created_at', 'updated_at', 'ip_address', 
        'user_agent', 'referrer', 'get_full_contact'
    ]
    
    inlines = [LeadActivityInline]
    
    fieldsets = (
        (_('Основна інформація'), {
            'fields': ('name', 'email', 'phone', 'company', 'position')
        }),
        (_('Деталі заявки'), {
            'fields': ('inquiry_type', 'product_name', 'subject', 'message', 'budget_range', 'project_timeline')
        }),
        (_('Статус та примітки'), {
            'fields': ('status', 'internal_notes', 'contacted_at')
        }),
        (_('Технічна інформація'), {
            'fields': ('source', 'source_page', 'referrer', 'ip_address', 'user_agent', 'language'),
            'classes': ('collapse',)
        }),
        (_('GDPR згода'), {
            'fields': ('consent_gdpr', 'consent_marketing')
        }),
        (_('Дати'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('source')
    
    def get_full_contact(self, obj):
        """Повна контактна інформація"""
        return obj.get_full_contact()
    get_full_contact.short_description = _('Повний контакт')
    
    actions = ['mark_as_contacted', 'mark_as_spam']
    
    def mark_as_contacted(self, request, queryset):
        """Позначити як зв'язалися"""
        updated = queryset.update(status='contacted')
        self.message_user(
            request,
            f'Оновлено статус для {updated} заявок на "Зв\'язалися"'
        )
    mark_as_contacted.short_description = _('Позначити як "Зв\'язалися"')
    
    def mark_as_spam(self, request, queryset):
        """Позначити як спам"""
        updated = queryset.update(status='spam')
        self.message_user(
            request,
            f'Позначено {updated} заявок як спам'
        )
    mark_as_spam.short_description = _('Позначити як спам')


@admin.register(LeadSource)
class LeadSourceAdmin(admin.ModelAdmin):
    """Адмінка для джерел заявок"""
    list_display = ['name', 'utm_source', 'utm_medium', 'utm_campaign', 'is_active', 'created_at']
    list_filter = ['is_active', 'utm_source', 'utm_medium']
    search_fields = ['name', 'utm_source', 'utm_campaign']
    list_editable = ['is_active']


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    """Адмінка для email шаблонів"""
    list_display = ['name', 'template_type', 'is_active', 'updated_at']
    list_filter = ['template_type', 'is_active']
    search_fields = ['name', 'subject_uk', 'subject_ru', 'subject_en']
    list_editable = ['is_active']
    
    fieldsets = (
        (_('Основна інформація'), {
            'fields': ('name', 'template_type', 'is_active')
        }),
        (_('Українська мова'), {
            'fields': ('subject_uk', 'content_uk')
        }),
        (_('Російська мова'), {
            'fields': ('subject_ru', 'content_ru')
        }),
        (_('Англійська мова'), {
            'fields': ('subject_en', 'content_en')
        }),
    )


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    """Адмінка для налаштувань нотифікацій"""
    list_display = ['__str__', 'email_enabled', 'telegram_enabled', 'viber_enabled', 'updated_at']
    
    fieldsets = (
        (_('Email налаштування'), {
            'fields': (
                'email_enabled', 'email_recipients', 'email_subject_template'
            )
        }),
        (_('Telegram налаштування'), {
            'fields': (
                'telegram_enabled', 'telegram_bot_token', 'telegram_chat_id'
            )
        }),
        (_('Viber налаштування'), {
            'fields': (
                'viber_enabled', 'viber_bot_token', 'viber_admin_id'
            )
        }),
        (_('Загальні налаштування'), {
            'fields': (
                'notification_delay', 'max_retries'
            )
        }),
    )
    
    def has_add_permission(self, request):
        """Дозволити створення тільки одного об'єкта"""
        return not NotificationSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Заборонити видалення"""
        return False


@admin.register(SurveySheet)
class SurveySheetAdmin(admin.ModelAdmin):
    """Адмінка опитувальних листів."""

    # ── List view ─────────────────────────────────────────────────────────────
    list_display = [
        'contact_person', 'company', 'phone', 'email',
        'hot_medium', 'cold_medium',
        'colored_status', 'created_at',
    ]
    list_filter  = ['status', 'language', 'created_at']
    search_fields = [
        'contact_person', 'company', 'email', 'phone',
        'purpose', 'hot_medium', 'cold_medium', 'comments',
    ]
    list_editable = ['status'] if False else []   # ← керується через actions
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    readonly_fields = [
        'uuid', 'ip_address', 'language', 'source_page',
        'created_at', 'updated_at',
    ]

    # ── Actions ───────────────────────────────────────────────────────────────
    actions = ['mark_in_progress', 'mark_responded', 'mark_closed']

    def mark_in_progress(self, request, qs):
        n = qs.update(status='in_progress')
        self.message_user(request, _(f'Статус змінено на «Опрацьовується» для {n} записів.'))
    mark_in_progress.short_description = _('→ Опрацьовується')

    def mark_responded(self, request, qs):
        n = qs.update(status='responded')
        self.message_user(request, _(f'Статус змінено на «Відповідь надана» для {n} записів.'))
    mark_responded.short_description = _('→ Відповідь надана')

    def mark_closed(self, request, qs):
        n = qs.update(status='closed')
        self.message_user(request, _(f'Статус змінено на «Закрито» для {n} записів.'))
    mark_closed.short_description = _('→ Закрито')

    # ── Colored badge ─────────────────────────────────────────────────────────
    BADGE_COLORS = {
        'new':         ('#b45309', '#fffbeb'),   # amber
        'in_progress': ('#1d4ed8', '#eff6ff'),   # blue
        'responded':   ('#15803d', '#f0fdf4'),   # green
        'closed':      ('#6b7280', '#f9fafb'),   # gray
    }

    @admin.display(description=_('Статус'), ordering='status')
    def colored_status(self, obj):
        color, bg = self.BADGE_COLORS.get(obj.status, ('#000', '#fff'))
        label = obj.get_status_display()
        return format_html(
            '<span style="background:{bg};color:{fg};padding:2px 8px;'
            'border-radius:4px;font-size:0.8em;font-weight:600;">{label}</span>',
            bg=bg, fg=color, label=label,
        )

    # ── Detail fieldsets ──────────────────────────────────────────────────────
    fieldsets = (
        (_('Дані замовника'), {
            'fields': (
                ('company', 'address'),
                ('contact_person', 'phone', 'email'),
            ),
        }),
        (_('Робочі умови'), {
            'fields': (
                'purpose',
                ('hot_medium',       'cold_medium'),
                ('hot_temp_in',      'hot_temp_out',
                 'cold_temp_in',     'cold_temp_out'),
                ('hot_flow_in',      'hot_flow_out',
                 'cold_flow_in',     'cold_flow_out'),
                ('hot_pressure_in',  'hot_pressure_out',
                 'cold_pressure_in', 'cold_pressure_out'),
                ('hot_pressure_drop','cold_pressure_drop'),
                'heat_load',
            ),
        }),
        (_('Теплофізичні властивості'), {
            'classes': ('collapse',),
            'fields': (
                ('hot_thermo_temp',   'cold_thermo_temp'),
                ('hot_density',       'cold_density'),
                ('hot_specific_heat', 'cold_specific_heat'),
                ('hot_conductivity',  'cold_conductivity'),
                ('hot_viscosity',     'cold_viscosity'),
            ),
        }),
        (_('Конструкційні вимоги'), {
            'fields': (
                ('plate_material',  'plate_material_unit'),
                ('connection_type', 'design_pressure'),
                ('flanges',         'flanges_count'),
            ),
        }),
        (_('Коментарі'), {
            'fields': ('comments',),
        }),
        (_('Опрацювання'), {
            'fields': ('status', 'internal_notes'),
        }),
        (_('Метадані'), {
            'classes': ('collapse',),
            'fields': (
                'uuid',
                ('ip_address', 'language', 'source_page'),
                ('created_at', 'updated_at'),
            ),
        }),
    )


@admin.register(LeadActivity)
class LeadActivityAdmin(admin.ModelAdmin):
    """Адмінка для активності заявок"""
    list_display = ['lead', 'activity_type', 'user', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['lead__name', 'lead__email', 'description']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        """Заборонити ручне додавання активності"""
        return False
