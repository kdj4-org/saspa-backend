from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(self, email, nombre, password=None, rol='cliente', **extra_fields):
        if not email:
            raise ValueError('El email debe ser proporcionado')
        if not nombre:
            raise ValueError('El nombre debe ser proporcionado')
        if not password:
            raise ValueError('La contraseña debe ser proporcionada')
            
        email = self.normalize_email(email)
        user = self.model(email=email, nombre=nombre, rol=rol, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nombre, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('rol', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')
            
        return self.create_user(email, nombre, password, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):
    ROLES = (
        ('admin', 'Administrador'),
        ('cliente', 'Cliente'),
    )

    email = models.EmailField(unique=True)    
    nombre = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20, blank=True)
    url_foto = models.URLField(blank=True)
    rol = models.CharField(max_length=10, choices=ROLES, default='cliente')

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre']

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="usuario_groups",
        related_query_name="usuario",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="usuario_permissions",
        related_query_name="usuario",
    )

    def __str__(self):
        return f"{self.nombre} ({self.rol})"

class Servicio(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    precio = models.FloatField()
    duracion_minutos = models.IntegerField()

    def __str__(self):
        return self.nombre


class Sede(models.Model):
    direccion = models.CharField(max_length=255)
    barrio = models.CharField(max_length=100, null=True)
    ciudad = models.CharField(max_length=100)
    horario = models.CharField(max_length=100, null=True)
    url_imagen = models.URLField(null=True)

    def __str__(self):
        return f"{self.direccion} - {self.barrio}, {self.ciudad} tiene el horario {self.horario}"


class Empleado(models.Model):
    nombre = models.CharField(max_length=255)
    url_foto = models.URLField()
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre


class EmpleadoServicio(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('empleado', 'servicio')


class Cita(models.Model):
    ESTADOS = [
        ('por aprobar', 'Por aprobar'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('por cancelar', 'Por cancelar'),
        ('cancelada', 'Cancelada'),
        ('concluida', 'Concluida'),
    ]

    fecha_inicio = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADOS)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.fecha_inicio} - {self.estado}"


class Disponibilidad(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    dia = models.CharField(max_length=15)  # ej: "lunes"
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    def __str__(self):
        return f"{self.empleado} - {self.dia}"


class Bloqueo(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    cita = models.ForeignKey(Cita, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()


class Publicacion(models.Model):
    url_imagen = models.URLField()
    fecha = models.DateField()
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE)


class Notificacion(models.Model):
    TIPO_ADMIN = [
        ('solicitud de cita', 'Solicitud de cita'),
        ('cancelacion de cita', 'Cancelación de cita'),
    ]
    TIPO_CLIENTE = [
        ('cita aprobada', 'Cita aprobada'),
        ('cita rechazada', 'Cita rechazada'),
        ('cita cancelada', 'Cita cancelada'),
        ('recordatorio de cita', 'Recordatorio de cita'),
    ]

    tipo = models.CharField(max_length=50)
    mensaje = models.TextField()
    fecha = models.DateTimeField()
    leida = models.BooleanField(default=False)
    usuario = models.ForeignKey(Usuario, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.mensaje


class Feedback(models.Model):
    cita = models.OneToOneField(Cita, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()
    comentario = models.TextField()

    def __str__(self):
        return f"Feedback Cita {self.cita_id}"