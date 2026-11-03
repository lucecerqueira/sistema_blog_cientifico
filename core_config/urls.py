from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.svg', permanent=True)),
    path('', include('ds_platform.urls')),
    path('accounts/', include('allauth.urls')),  # allauth já traz accounts/password/reset/ e accounts/password/change/
    
    # Ou se preferir usar os endpoints diretos do Django Auth:
    path('recuperar-senha/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('recuperar-senha/sucesso/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('resetar/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('resetar/concluido/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
