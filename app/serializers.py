from rest_framework import serializers
from .models import (
    Usuario, Servicio, Sede, Empleado, EmpleadoServicio,
    Cita, Disponibilidad, Bloqueo, Publicacion, Notificacion, Feedback, Imagen
)
from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from drf_extra_fields.fields import Base64ImageField

User = get_user_model()

class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = Usuario
        fields = ['id', 'email', 'nombre', 'telefono', 'url_foto', 'rol', 'password','is_active']
        extra_kwargs = {
            'password': {'write_only': True},
            'is_active': {'read_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        return Usuario.objects.create_user(**validated_data, password=password)

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for (key, value) in validated_data.items():
            setattr(instance, key, value)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=6, required=True, write_only=True, style={'input_type': 'password'})
    confirm_new_password = serializers.CharField(min_length=6, required=True, write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        if data['new_password'] != data.get('confirm_new_password'):
            raise serializers.ValidationError({"confirm_new_password": "Las contraseñas no coinciden."})
        
        user = self.context.get('user')
        if not user:
            raise serializers.ValidationError("Error interno del servidor al validar la contraseña.")
        
        try:
            password_validation.validate_password(data['new_password'], user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"new_password", list(e.messages)})
        
        return data

class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = '__all__'

    def validate_name(self, value):
        if self.instance:
            if Servicio.objects.exclude(pk=self.instance.pk).filter(nombre=value).exists():
                raise serializers.ValidationError("Ya existe un servicio con ese nombre.")
        else:
            if Servicio.objects.filter(nombre=value).exists():
                raise serializers.ValidationError("Ya existe un servicio con ese nombre.")
        return value

class SedeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sede
        fields = '__all__'

class EmpleadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empleado
        fields = '__all__'
        
    def validate_sede(self, value):
        if not Sede.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("La sede asignada no existe.")
        return value
    
class EmpleadoClienteSerializer(EmpleadoSerializer):
    sede = serializers.SerializerMethodField()
    servicios = serializers.SerializerMethodField()
    
    class Meta:
        model = Empleado
        fields = '__all__'
    
    def get_sede(self, obj):
        return obj.sede.barrio if obj.sede else None
    
    def get_servicios(self, obj):
        servicios_qs = Servicio.objects.filter(
            id__in=EmpleadoServicio.objects.filter(empleado=obj).values_list('servicio_id', flat=True)
        )
        return list(servicios_qs.values_list('nombre', flat=True))

class EmpleadoAdminSerializer(EmpleadoSerializer):
    sede_id = serializers.PrimaryKeyRelatedField(
        queryset=Sede.objects.all(), 
        source='sede'
    )
    
    class Meta:
        model = Empleado
        fields = ['id', 'sede_id', 'nombre', 'url_foto']

class EmpleadoServicioSerializer(serializers.ModelSerializer):
    empleado = EmpleadoSerializer(read_only=True)
    empleado_id = serializers.PrimaryKeyRelatedField(
        queryset=Empleado.objects.all(), 
        source='empleado', 
        write_only=True
    )
    servicio = ServicioSerializer(read_only=True)
    servicio_id = serializers.PrimaryKeyRelatedField(
        queryset=Servicio.objects.all(), 
        source='servicio', 
        write_only=True
    )
    
    class Meta:
        model = EmpleadoServicio
        fields = '__all__'

class CitaSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    usuario_id = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(),
        source='usuario',
        write_only=True
    )
    servicio = ServicioSerializer(read_only=True)
    servicio_id = serializers.PrimaryKeyRelatedField(
        queryset=Servicio.objects.all(),
        source='servicio',
        write_only=True
    )
    empleado = EmpleadoSerializer(read_only=True)
    empleado_id = serializers.PrimaryKeyRelatedField(
        queryset=Empleado.objects.all(),
        source='empleado',
        write_only=True
    )
    sede = SedeSerializer(read_only=True)
    sede_id = serializers.PrimaryKeyRelatedField(
        queryset=Sede.objects.all(),
        source='sede',
        write_only=True
    )
    
    class Meta:
        model = Cita
        fields = '__all__'
        read_only_fields = ['estado']

class DisponibilidadSerializer(serializers.ModelSerializer):
    empleado = EmpleadoSerializer(read_only=True)
    empleado_id = serializers.PrimaryKeyRelatedField(
        queryset=Empleado.objects.all(),
        source='empleado',
        write_only=True
    )
    
    class Meta:
        model = Disponibilidad
        fields = '__all__'

class BloqueoSerializer(serializers.ModelSerializer):
    empleado = EmpleadoSerializer(read_only=True)
    empleado_id = serializers.PrimaryKeyRelatedField(
        queryset=Empleado.objects.all(),
        source='empleado',
        write_only=True
    )
    cita = CitaSerializer(read_only=True)
    cita_id = serializers.PrimaryKeyRelatedField(
        queryset=Cita.objects.all(),
        source='cita',
        write_only=True
    )
    
    class Meta:
        model = Bloqueo
        fields = '__all__'

class PublicacionSerializer(serializers.ModelSerializer):
    servicio = ServicioSerializer(read_only=True)
    servicio_id = serializers.PrimaryKeyRelatedField(
        queryset=Servicio.objects.all(),
        source='servicio',
        write_only=True
    )
    
    class Meta:
        model = Publicacion
        fields = ['id', 'url_imagen', 'fecha', 'servicio', 'servicio_id']

class NotificacionSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    usuario_id = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(),
        source='usuario',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Notificacion
        fields = '__all__'

class FeedbackSerializer(serializers.ModelSerializer):
    cita = CitaSerializer(read_only=True)
    cita_id = serializers.PrimaryKeyRelatedField(
        queryset=Cita.objects.all(),
        source='cita',
        write_only=True
    )
    
    class Meta:
        model = Feedback
        fields = '__all__'
    
class UploadImageSerializer(serializers.Serializer):
    filename = serializers.CharField()
    data = Base64ImageField() 