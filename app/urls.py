from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
#router.register(r'usuarios', views.UsuarioViewSet)
router.register(r'servicios', views.ServicioViewSet)
router.register(r'sedes', views.SedeViewSet)
router.register(r'empleados', views.EmpleadoViewSet)
router.register(r'empleados-servicios', views.EmpleadoServicioViewSet)
router.register(r'citas', views.CitaViewSet)
router.register(r'disponibilidades', views.DisponibilidadViewSet)
router.register(r'bloqueos', views.BloqueoViewSet)
router.register(r'publicaciones', views.PublicacionViewSet)
router.register(r'notificaciones', views.NotificacionViewSet)
router.register(r'feedbacks', views.FeedbackViewSet)

urlpatterns = [
    #path('', include(router.urls)),    
    path('cliente/registrar/', views.RegisterUserView.as_view(), name='register'),
    path('usuario/login/', views.LoginView.as_view(), name='login'),
]