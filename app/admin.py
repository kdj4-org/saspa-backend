from django.contrib import admin
from .models import Usuario, Servicio, Empleado, Sede, Cita, Notificacion, Publicacion, Feedback, Disponibilidad, Bloqueo, EmpleadoServicio

admin.site.register(Usuario)
admin.site.register(Servicio)
admin.site.register(Empleado)
admin.site.register(Sede)
admin.site.register(Cita)
admin.site.register(Notificacion)
admin.site.register(Publicacion)
admin.site.register(Feedback)
admin.site.register(Disponibilidad)
admin.site.register(Bloqueo)
admin.site.register(EmpleadoServicio)
