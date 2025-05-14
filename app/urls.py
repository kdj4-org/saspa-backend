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

empleado_read = views.EmpleadoClienteViewSet.as_view({
    'get': 'list'
})

empleado_list = views.EmpleadoAdminViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

empleado_detail = views.EmpleadoAdminViewSet.as_view({
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

publicacion_read = views.PublicacionViewSet.as_view({
    'get' : 'list'
})

publicacion_create = views.PublicacionViewSet.as_view({
    'post': 'create'
})

publicacion_destroy = views.PublicacionViewSet.as_view({
    'delete': 'destroy'
})

empleado_servicio_read = views.EmpleadoServicioViewSet.as_view({
    'get': 'list'
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
    path('cliente/equipo/', empleado_read, name='cliente-equipo'),
    path('admin/empleados/', empleado_list, name='admin-empleados-list'),
    path('admin/empleados/<int:pk>/', empleado_detail, name='admin-empleados-detail'),
    path('admin/servicios/', servicio_list, name='admin-servicios-list'),
    path('admin/servicios/<int:pk>/', servicio_detail, name='admin-servicios-detail'),
    path('admin/subir-imagen/', views.UploadImageView.as_view(), name='upload-image'),
    path('admin/eliminar-imagen/<str:file_id>/', views.DeleteImageView.as_view(), name='delete-image'),
    path('usuario/publicaciones/', publicacion_read, name='usuario-publicaciones'),
    path('admin/publicaciones/', publicacion_create, name='admin-publicaciones-create'),
    path('admin/publicaciones/<int:pk>/', publicacion_destroy, name='admin-publicaciones-delete'),
    path('usuario/empleados/<int:empleado_id>/servicios/', empleado_servicio_read, name='usuario-servicios-read'),
]