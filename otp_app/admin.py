from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.hashers import check_password
from django_otp.admin import OTPAdminSite, OTPAdminAuthenticationForm
from django_otp.plugins.otp_totp.admin import TOTPDeviceAdmin
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.contrib.auth.models import Group as AuthGroup

from otp_app.models import CustomUser


class CustomOTPAuthenticationForm(OTPAdminAuthenticationForm):
    otp_token = forms.CharField(required=True, label='OTP', max_length=6)

    def __init__(self, request=None, *args, **kwargs):
        """
        The 'request' parameter is set for custom auth use by subclasses.
        The form data comes in via the standard 'data' kwarg.
        """
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

        # Set the max length and label for the "username" field.
        self.username_field = UserModel._meta.get_field('email')
        self.fields['username'].max_length = self.username_field.max_length or 254
        self.fields['username'].label = 'Email'

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            self.user_cache = CustomUser.objects.filter(
                email=username, is_staff=True, is_superuser=True).first()
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            elif not check_password(password, self.user_cache.password):
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)
        self.clean_otp(self.get_user())

        return self.cleaned_data


class OTPAdmin(OTPAdminSite):
    login_template = 'admin_custom_login.html'


admin_site = OTPAdmin(name='OTPAdmin')

admin.site.unregister(AuthGroup)
admin_site.site_header = 'Admin OTP'
admin_site.site_url = None
admin_site.site_title = 'Admin OTP'
admin_site.login_form = CustomOTPAuthenticationForm
admin.site.unregister(TOTPDevice)
UserModel = get_user_model()


@admin.register(TOTPDevice)
class CustomTOTPDeviceAdmin(TOTPDeviceAdmin):
    list_display = ['user', 'name', ]

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if 'confirmed' in fieldsets[0][-1]['fields']:
            fieldsets[0][-1]['fields'].remove('confirmed')
        fields = [fieldsets[0]]
        qr_field = [fieldsets[-1]] if fieldsets[-1][0] is None else []
        if qr_field:
            fields.extend(qr_field)
        return fields


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'email',
        'first_name',
        'last_name',)
    list_filter = (
        'is_superuser',
        'is_active',)
    search_fields = ('first_name', 'last_name', 'email')
    ordering = ('first_name',)
    list_per_page = 50

    fieldsets = [
        [None, {'fields': ['email', 'password']}],
        ['Personal info', {'fields': ['first_name', 'last_name', 'mobile_number']}],
        ['Permissions', {
            'fields': ['is_active', 'is_superuser'],
        }],
        ['Important dates', {'fields': ['last_login', 'date_joined']}],
    ]


for model_cls, model_admin in admin.site._registry.items():
    admin_site.register(model_cls, model_admin.__class__)
