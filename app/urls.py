from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
#router.register(r'usuarios', views.UsuarioViewSet)
router.register(r'servicios', views.ServicioViewSet)
router.register(r'empleados', views.EmpleadoViewSet)
router.register(r'empleados-servicios', views.EmpleadoServicioViewSet)
router.register(r'citas', views.CitaViewSet)
router.register(r'disponibilidades', views.DisponibilidadViewSet)
router.register(r'bloqueos', views.BloqueoViewSet)
router.register(r'publicaciones', views.PublicacionViewSet)
router.register(r'notificaciones', views.NotificacionViewSet)
router.register(r'feedbacks', views.FeedbackViewSet)

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

empleado_read = views.EmpleadoViewSet.as_view({
	'get': 'list'
})

urlpatterns = [
    #path('', include(router.urls)),    
    path('cliente/registrar/', views.RegisterUserView.as_view(), name='register'),
    path('usuario/login/', views.LoginView.as_view(), name='login'),
    path('usuario/sedes/', sede_read, name='usuario-sedes'),
    path('usuario/recuperar-contrasena/', views.PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('usuario/restablecer-contrasena/<uuid:token>/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),    
    path('admin/sedes/', sede_list, name='admin-sedes-list'),
    path('admin/sedes/<int:pk>/', sede_detail, name='admin-sedes-detail'),
	path('cliente/equipo/', empleado_read, name='team-visualization'),
]