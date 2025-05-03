from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from .models import (
    Servicio, Sede, Empleado, EmpleadoServicio,
    Cita, Disponibilidad, Bloqueo, Publicacion, 
    Notificacion, Feedback, PasswordResetToken
)
from .serializers import (
    UsuarioSerializer, ServicioSerializer, SedeSerializer,
    EmpleadoSerializer, EmpleadoServicioSerializer, CitaSerializer,
    DisponibilidadSerializer, BloqueoSerializer, PublicacionSerializer,
    NotificacionSerializer, FeedbackSerializer, PasswordResetRequestSerializer, 
    PasswordResetConfirmSerializer
)
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdmin, IsAdmin
from datetime import datetime, timedelta, timezone
from django.utils import timezone as tz
import jwt
from django.conf import settings
from django.urls import reverse
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

User = get_user_model()
EXPIRY_MINUTES = 30

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
                'access': f"Bearer {str(token)}",
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
                'access': f"Bearer {str(token)}",
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

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer    

class EmpleadoServicioViewSet(viewsets.ModelViewSet):
    queryset = EmpleadoServicio.objects.all()
    serializer_class = EmpleadoServicioSerializer    

class CitaViewSet(viewsets.ModelViewSet):
    queryset = Cita.objects.all()
    serializer_class = CitaSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.rol == 'admin' or user.is_staff:
            return self.queryset
        elif user.rol == 'cliente':
            return self.queryset.filter(usuario=user)
        return self.queryset.none()
    
    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        cita = self.get_object()
        cita.estado = 'aprobada'
        cita.save()
        return Response({'status': 'cita aprobada'})
    
    @action(detail=True, methods=['post'])
    def rechazar(self, request, pk=None):
        cita = self.get_object()
        cita.estado = 'rechazada'
        cita.save()
        return Response({'status': 'cita rechazada'})

class DisponibilidadViewSet(viewsets.ModelViewSet):
    queryset = Disponibilidad.objects.all()
    serializer_class = DisponibilidadSerializer

class BloqueoViewSet(viewsets.ModelViewSet):
    queryset = Bloqueo.objects.all()
    serializer_class = BloqueoSerializer

class PublicacionViewSet(viewsets.ModelViewSet):
    queryset = Publicacion.objects.all()
    serializer_class = PublicacionSerializer

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