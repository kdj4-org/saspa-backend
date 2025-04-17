from rest_framework import serializers
from .models import (
    Usuario, Servicio, Sede, Empleado, EmpleadoServicio,
    Cita, Disponibilidad, Bloqueo, Publicacion, Notificacion, Feedback
)
from django.contrib.auth import get_user_model

User = get_user_model()

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'email', 'nombre', 'telefono', 'url_foto', 'rol', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True},
            'is_active': {'read_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = '__all__'

class SedeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sede
        fields = '__all__'

class EmpleadoSerializer(serializers.ModelSerializer):
    sede = SedeSerializer(read_only=True)
    sede_id = serializers.PrimaryKeyRelatedField(
        queryset=Sede.objects.all(), 
        source='sede', 
        write_only=True
    )
    
    class Meta:
        model = Empleado
        fields = '__all__'

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
    class Meta:
        model = Publicacion
        fields = '__all__'

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