from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .models import (
    Servicio, Sede, Empleado, EmpleadoServicio,
    Cita, Disponibilidad, Bloqueo, Publicacion, 
    Notificacion, Feedback, PasswordResetToken, Imagen
)
from .serializers import (
    UsuarioSerializer, ServicioSerializer, SedeSerializer,
    EmpleadoAdminSerializer, EmpleadoClienteSerializer, EmpleadoServicioSerializer, CitaSerializer,
    DisponibilidadSerializer, BloqueoSerializer, PublicacionSerializer,
    NotificacionSerializer, FeedbackSerializer, PasswordResetRequestSerializer, 
    PasswordResetConfirmSerializer
)
from datetime import datetime, timedelta, timezone
from django.utils import timezone as tz
import jwt
from django.conf import settings
from django.urls import reverse
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
import requests
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import UploadImageSerializer

User = get_user_model()
EXPIRY_MINUTES = 30
MAX_IMAGE_SIZE = 1024 * 1024 * 10

class RegisterUserView(APIView):
    def post(self, request):
        serializer = UsuarioSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            payload = {
                'id': user.id,
                'email': user.email,
                'username': user.rol,
                "exp": datetime.now(timezone.utc) + timedelta(days=365*5),
                "iat": datetime.now(timezone.utc)
            }
            token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm='HS256')
            return Response({
                'message': "User registered successfully",
                'Authorization': f"{str(token)}",
                'user': UsuarioSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):    
    def authenticate_user(self, email, password):
        user = User.objects.get(email=email)
        if user.check_password(password):
            return user
        raise User.DoesNotExist

    def post(self, request):        
        email = request.data.get('email')
        password = request.data.get('password')
        try:
            user = self.authenticate_user(email, password)            
            payload = {
                "user_id": user.id,
                "email": user.email,
                "rol": user.rol,
                "exp": datetime.now(timezone.utc) + timedelta(days=365*5),
                "iat": datetime.now(timezone.utc)
            }
            token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm='HS256')
            return Response({
                'Authorization': f"{str(token)}",
                'user': UsuarioSerializer(user).data
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)        

class PasswordResetRequestView(APIView):
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                token = PasswordResetToken.objects.create(
                    usuario=user,
                    expires_at=tz.now() + timedelta(minutes=EXPIRY_MINUTES)                    
                )
                reset_url = reverse('password-reset-confirm', kwargs={'token': str(token.token)})
                full_reset_url = request.build_absolute_uri(reset_url)

                expiry_minutes = EXPIRY_MINUTES
                site_name = getattr(settings, 'SITE_NAME', 'Tu Aplicación')

                context = {
                    'user': user,
                    'reset_url': full_reset_url,
                    'expiry_minutes': expiry_minutes,
                    'site_name': site_name,
                }

                subject = render_to_string('emails/password_reset_subject.txt', context).strip()
                text_body = render_to_string('emails/password_reset_body.txt', context)
                html_body = render_to_string('emails/password_reset_body.html', context)

                try:
                    email_message = EmailMultiAlternatives(
                        subject=subject,
                        body=text_body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[user.email],
                    )
                    email_message.attach_alternative(html_body, "text/html")
                    email_message.send(fail_silently=False)
                
                except Exception as e:
                    print("Error al enviar correo electrónico de restablecimiento de contraseña:", e)
                    pass
                return Response({'message': 'Se ha enviado un enlace de recuperación a tu correo electrónico si la cuenta existe.'}, status=status.HTTP_200_OK)
            except User.DoesNotExist:                
                return Response({'message': 'Se ha enviado un enlace de recuperación a tu correo electrónico si la cuenta existe.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class PasswordResetConfirmView(APIView):
    def post(self, request, token):    
        try:
            password_reset_token = PasswordResetToken.objects.get(token=token)
            if not password_reset_token.is_valid():
                return Response({'error': 'El enlace de restablecimiento es inválido o ha expirado.'}, status=status.HTTP_400_BAD_REQUEST)

            user = password_reset_token.usuario
            serializer = PasswordResetConfirmSerializer(data=request.data, context={'user': user})
            if serializer.is_valid():
                new_password = serializer.validated_data['new_password']
                user.set_password(new_password)
                user.save()
                password_reset_token.delete()
                return Response({'message': 'Tu contraseña ha sido restablecida exitosamente.'}, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PasswordResetToken.DoesNotExist:
            return Response({'error': 'El enlace de restablecimiento es inválido.'}, status=status.HTTP_400_BAD_REQUEST)

class ServicioViewSet(viewsets.ModelViewSet):
    queryset = Servicio.objects.all()
    serializer_class = ServicioSerializer

    def create(self, request, *args, **kwargs):
        serializer = ServicioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {"mensaje": "Servicio creado correctamente."},
            status=status.HTTP_201_CREATED
        )

    def list(self, request):
        servicios = Servicio.objects.all()
        serializer = ServicioSerializer(servicios, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)        
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            {"mensaje": "Servicio actualizado correctamente."},
            status=status.HTTP_200_OK
        )
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"mensaje": "Servicio eliminado correctamente."},
            status=status.HTTP_200_OK
        )

class SedeViewSet(viewsets.ModelViewSet):
    queryset = Sede.objects.all()
    serializer_class = SedeSerializer
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"mensaje": "Sede eliminada correctamente."},
            status=status.HTTP_200_OK
        ) 

class EmpleadoClienteViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoClienteSerializer

class EmpleadoAdminViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoAdminSerializer
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"mensaje": "Empleado eliminado correctamente."},
            status=status.HTTP_200_OK
        )

class EmpleadoServicioViewSet(viewsets.ModelViewSet):
    queryset = EmpleadoServicio.objects.all()
    serializer_class = EmpleadoServicioSerializer

    def list(self, request, empleado_id):
        try:
            empleado = Empleado.objects.get(id=empleado_id)
        except Empleado.DoesNotExist:
            return Response({"error": "No existe el empleado"}, status=status.HTTP_404_NOT_FOUND)

        ids_servicios = (
            EmpleadoServicio.objects
            .filter(empleado=empleado)
            .values_list('servicio_id', flat=True)
        )
        servicios = Servicio.objects.filter(id__in=ids_servicios)
        serializer = ServicioSerializer(servicios, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, empleado_id):
        try:
            empleado = Empleado.objects.get(id=empleado_id)
        except Empleado.DoesNotExist:
            return Response({"error": "No existe el empleado"}, status=status.HTTP_404_NOT_FOUND)
        
        servicio_id = request.data.get('servicio_id')
        if not servicio_id:
            return Response({"error": "Falta el servicio"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            servicio = Servicio.objects.get(id=servicio_id)
        except Servicio.DoesNotExist:
            return Response({"error": "Servicio no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        
        if EmpleadoServicio.objects.filter(empleado=empleado, servicio=servicio).exists():
            return Response({"error": "Este empleado ya esta vinculado a este servicio"}, status=status.HTTP_400_BAD_REQUEST)

        EmpleadoServicio.objects.create(empleado=empleado, servicio=servicio)

        return Response({"empleado_id": empleado_id, "servicio_id": servicio_id, "mensaje": "Empleado vinculado correctamente"}, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, empleado_id, servicio_id):
        try:
            vinculacion = EmpleadoServicio.objects.get(empleado_id=empleado_id, servicio_id=servicio_id)
        except EmpleadoServicio.DoesNotExist:
            return Response({"error": "No existe la vinculacion"}, status=status.HTTP_404_NOT_FOUND)
        
        vinculacion.delete()
        citas = Cita.objects.filter(servicio=servicio_id, empleado=empleado_id)
        for cita in citas:
            cita.estado = 'cancelada'
            cita.save()
        return Response({"empleado_id": empleado_id, "servicio_id": servicio_id, "mensaje": "Servicio desvinculado correctamente del empleado"}, status=status.HTTP_200_OK)

class CitaViewSet(viewsets.ModelViewSet):
    queryset = Cita.objects.all()
    serializer_class = CitaSerializer

    def list(self, request):
        estado = request.query_params.get('estado')
        orden = request.query_params.get('orden')

        citas = self.queryset
        if estado:
            estados_validos = [choice[0] for choice in Cita.ESTADOS]
            if estado not in estados_validos:
                return Response(
                    {"error": f"Estado '{estado}' no válido. Opciones: {estados_validos}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            citas = citas.filter(estado=estado)

        if orden == 'desc':
            citas = citas.order_by('-fecha_inicio')
        else:
            citas = citas.order_by('fecha_inicio')
        
        serializer = CitaSerializer(citas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def update(self, request, pk=None):
        cita = self.get_object()
        nuevo_estado = request.data.get('estado')
        estados_validos = [choice[0] for choice in Cita.ESTADOS]
        dias_ingles_a_espanol = {
            'monday': 'lunes',
            'tuesday': 'martes',
            'wednesday': 'miércoles',
            'thursday': 'jueves',
            'friday': 'viernes',
            'saturday': 'sábado',
            'sunday': 'domingo'
        }

        if nuevo_estado not in estados_validos:
            return Response(
                {"error": f"Estado '{nuevo_estado}' no válido. Opciones: {estados_validos}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        estado_actual = cita.estado
        transiciones = {
            'por aprobar': ['aprobada', 'rechazada'],
            'aprobada': ['cancelada', 'concluida'],
        }

        if nuevo_estado == estado_actual:
            return Response(
                {'mensaje': f"La cita ya se encuentra en estado '{estado_actual}'"},
                status=status.HTTP_200_OK
            )

        if estado_actual in transiciones and nuevo_estado in transiciones[estado_actual]:
            if nuevo_estado == 'aprobada':
                fecha_inicio = cita.fecha_inicio
                duracion = cita.servicio.duracion_minutos
                fecha_fin = fecha_inicio + timedelta(minutes=duracion)
                dia = dias_ingles_a_espanol[fecha_inicio.strftime('%A').lower()]

                disponible = Disponibilidad.objects.filter(
                    empleado = cita.empleado,
                    dia = dia,
                    hora_inicio__lte = fecha_inicio.time(),
                    hora_fin__gte = fecha_fin.time()
                ).exists()
                if not disponible:
                    return Response({"error": "El empleado no tiene disponibilidad para esta cita"}, status=status.HTTP_400_BAD_REQUEST)
                
                hay_bloqueo = Bloqueo.objects.filter(
                    empleado = cita.empleado,
                    fecha_inicio__lt=fecha_fin,
                    fecha_fin__gt=fecha_inicio
                ).exists()
                if hay_bloqueo:
                    return Response({"error": "El empleado tiene un bloqueo en ese horario'"}, status=status.HTTP_400_BAD_REQUEST)
                
                Bloqueo.objects.create(
                    empleado = cita.empleado,
                    cita = cita,
                    fecha_inicio = fecha_inicio,
                    fecha_fin = fecha_fin
                )
            if nuevo_estado == 'cancelada':
                Bloqueo.objects.filter(
                    cita = cita
                ).delete()
            cita.estado = nuevo_estado
            cita.save()
            return Response(
                {'mensaje': f"Estado de la cita actualizado correctamente a '{nuevo_estado}'"},
                status=status.HTTP_200_OK
            )

        return Response(
            {'mensaje': f"No se puede cambiar el estado de '{estado_actual}' a '{nuevo_estado}'"},
            status=status.HTTP_400_BAD_REQUEST
        )

class DisponibilidadViewSet(viewsets.ModelViewSet):
    queryset = Disponibilidad.objects.all()
    serializer_class = DisponibilidadSerializer

    def list(self, request):
        response = []
        empleados = Empleado.objects.all()

        for empleado in empleados:
            horario = {}
            horario["empleado_id"] = empleado.id
            disponibilidad = []
            bloques = Disponibilidad.objects.filter(empleado = empleado.id)

            for bloque in bloques:
                if all(d["dia"] != bloque.dia for d in disponibilidad):
                    disponibilidad.append({"dia": bloque.dia, "bloques": [{"hora_inicio": bloque.hora_inicio, "hora_fin": bloque.hora_fin}]})
                else:
                    for dia in disponibilidad:
                        if dia["dia"] == bloque.dia:
                            dia["bloques"].append({"hora_inicio": bloque.hora_inicio, "hora_fin": bloque.hora_fin})
            
            horario["disponibilidad"] = disponibilidad

            response.append(horario)
        
        return Response(response, status=status.HTTP_200_OK)
    
    def create(self, request, pk=None):
        disponibilidad = request.data.get("disponibilidad")
        empleado = Empleado.objects.get(id=pk)
        if empleado:
            for dia in disponibilidad:
                if dia.get("dia"):
                    bloques = dia.get("bloques")
                    for bloque in bloques:
                        if bloque.get('hora_inicio') and bloque.get('hora_fin'):
                            Disponibilidad.objects.create(
                                empleado = empleado,
                                dia = dia.get('dia'),
                                hora_inicio = bloque.get('hora_inicio'),
                                hora_fin = bloque.get('hora_fin')
                            )
        response = {"mensaje": "Disponibilidad creada correctamente."}
        return Response(response, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        disponibilidad = request.data.get("disponibilidad")
        empleado = Empleado.objects.get(id=pk)
        if empleado:
            Disponibilidad.objects.filter(empleado=empleado).delete()
            for dia in disponibilidad:
                if dia.get("dia"):
                    bloques = dia.get("bloques")
                    for bloque in bloques:
                        if bloque.get('hora_inicio') and bloque.get('hora_fin'):
                            Disponibilidad.objects.create(
                                empleado = empleado,
                                dia = dia.get('dia'),
                                hora_inicio = bloque.get('hora_inicio'),
                                hora_fin = bloque.get('hora_fin')
                            )
        response = {"mensaje": "Disponibilidad actualizada correctamente."}
        return Response(response, status=status.HTTP_200_OK)

class BloqueoViewSet(viewsets.ModelViewSet):
    queryset = Bloqueo.objects.all()
    serializer_class = BloqueoSerializer

class PublicacionViewSet(viewsets.ModelViewSet):
    queryset = Publicacion.objects.all()
    serializer_class = PublicacionSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"mensaje": "Publicación eliminada correctamente."},
            status=status.HTTP_200_OK
        )

class NotificacionViewSet(viewsets.ModelViewSet):
    queryset = Notificacion.objects.all()
    serializer_class = NotificacionSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.rol == 'admin' or user.is_staff:
            return self.queryset
        return self.queryset.filter(usuario=user)

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.rol == 'admin' or user.is_staff:
            return self.queryset
        return self.queryset.filter(cita__usuario=user)
 
class UploadImageView(APIView):
    MAX_FILE_SIZE = 1024 * 1024 * 10
    ALLOWED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
    
    def post(self, request):
        serializer = UploadImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image_file = serializer.validated_data['data']
        original_name = serializer.validated_data['filename']
        ext = f".{original_name.split('.')[-1].lower()}"

        if ext not in self.ALLOWED_EXTENSIONS:
            return Response({
                "error": f"Formato no permitido. Aceptados: {', '.join(self.ALLOWED_EXTENSIONS)}",
                "success": False
            }, status=status.HTTP_400_BAD_REQUEST)

        if image_file.size > self.MAX_FILE_SIZE:
            return Response({
                "error": f"Archivo demasiado grande. Máx: {self.MAX_FILE_SIZE/1024/1024}MB",
                "success": False
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            image_file.seek(0)
            file_content = image_file.read()
            image_file.seek(0)

            auth = (settings.IMAGEKIT_PRIVATE_KEY, '')
            files = {
                'file': (original_name, file_content),
                'fileName': (None, original_name),
            }

            response = requests.post(
                'https://upload.imagekit.io/api/v1/files/upload',
                auth=auth,
                files=files,
                data={
                    'publicKey': settings.IMAGEKIT_PUBLIC_KEY,
                }
            )

            if response.status_code != 200:
                raise Exception(f"Error en ImageKit: {response.text}")

            data = response.json()

            imagen = Imagen.objects.create(
                file_id=data['fileId'],
                file_path=data['url'],
                file_name=original_name,
                size=image_file.size
            )

            return Response({
                "success": True,
                "filePath": data['url'],
                "fileId": data['fileId'],
                "dbId": imagen.id,
                "message": "Imagen subida correctamente"
            })

        except Exception as e:
            return Response({"error": str(e), "success": False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeleteImageView(APIView):
    def delete(self, request,file_id):
        """
        Endpoint para eliminar imágenes de ImageKit y la base de datos
        """
        if not file_id:
            return Response(
                {"error": "Se requiere el fileId de la imagen", "success": False},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            auth = (settings.IMAGEKIT_PRIVATE_KEY, '')
            response = requests.delete(
                f'https://api.imagekit.io/v1/files/{file_id}',
                auth=auth,
                timeout=10
            )
            
            if response.status_code == 204:
                deleted_count, _ = Imagen.objects.filter(file_id=file_id).delete()
                
                if deleted_count == 0:
                    return Response(
                        {
                            "success": True,
                            "message": "Imagen eliminada de ImageKit pero no encontrada en la base de datos"
                        },
                        status=status.HTTP_200_OK
                    )
                
                return Response(
                    {
                        "success": True,
                        "message": "Imagen eliminada correctamente de ImageKit y la base de datos"
                    },
                    status=status.HTTP_200_OK
                )
            else:
                error_data = response.json()
                error_msg = error_data.get('message', 'Error desconocido al eliminar la imagen')
                return Response(
                    {"error": error_msg, "success": False},
                    status=response.status_code
                )
                
        except requests.exceptions.Timeout:
            return Response(
                {"error": "Tiempo de espera agotado al contactar ImageKit", "success": False},
                status=status.HTTP_408_REQUEST_TIMEOUT
            )
            
        except Exception as e:
            return Response(
                {"error": str(e), "success": False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
