from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

sede_read = views.SedeViewSet.as_view({
    'get': 'list'
})

sede_list = views.SedeViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

sede_detail = views.SedeViewSet.as_view({
    'put': 'update',
    'delete': 'destroy'
})

servicio_read = views.ServicioViewSet.as_view({
    'get': 'list'
})

servicio_list = views.ServicioViewSet.as_view({
    'post': 'create'
})

servicio_detail = views.ServicioViewSet.as_view({
    'put': 'update',
    'delete': 'destroy'
})

urlpatterns = [  
    path('cliente/registrar/', views.RegisterUserView.as_view(), name='register'),
    path('usuario/login/', views.LoginView.as_view(), name='login'),
    path('usuario/sedes/', sede_read, name='usuario-sedes'),
    path('usuario/recuperar-contrasena/', views.PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('usuario/restablecer-contrasena/<uuid:token>/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),    
    path('usuario/servicios/', servicio_read, name='usuario-servicios'),
    path('admin/sedes/', sede_list, name='admin-sedes-list'),
    path('admin/sedes/<int:pk>/', sede_detail, name='admin-sedes-detail'),
    path('admin/servicios/', servicio_list, name='admin-servicios-list'),
    path('admin/servicios/<int:pk>/', servicio_detail, name='admin-servicios-detail'),
]