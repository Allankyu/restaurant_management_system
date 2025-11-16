from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('orders/', include('orders.urls')),
    path('inventory/', include('inventory.urls')),
    path('reservations/', include('reservations.urls')),
    path('reports/', include('reports.urls')),
    path('accounts/', include('accounts.urls')),
    path('payments/', include('payments.urls')),
    
    # Additional features (comment out for now if not created yet)
    # path('suppliers/', include('suppliers.urls')),
    # path('waste/', include('waste.urls')),
    # path('scheduling/', include('scheduling.urls')),
    # path('feedback/', include('feedback.urls')),
    # path('loyalty/', include('loyalty.urls')),
    # path('expenses/', include('expenses.urls')),
    # path('kitchen/', include('kitchen.urls')),
    # path('api/', include('api.urls')),
    # path('delivery/', include('delivery.urls')),
    
     # Authentication URLs - POINT TO YOUR ACCOUNTS TEMPLATES
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='accounts/logout.html', next_page='login'), name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



