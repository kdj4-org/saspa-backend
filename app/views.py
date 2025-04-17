from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from .models import (
    Servicio, Sede, Empleado, EmpleadoServicio,
    Cita, Disponibilidad, Bloqueo, Publicacion, 
    Notificacion, Feedback
)
from .serializers import (
    UsuarioSerializer, ServicioSerializer, SedeSerializer,
    EmpleadoSerializer, EmpleadoServicioSerializer, CitaSerializer,
    DisponibilidadSerializer, BloqueoSerializer, PublicacionSerializer,
    NotificacionSerializer, FeedbackSerializer
)
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdmin, IsAdmin
from datetime import datetime, timedelta, timezone
import jwt
from django.conf import settings

User = get_user_model()

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


class ServicioViewSet(viewsets.ModelViewSet):
    queryset = Servicio.objects.all()
    serializer_class = ServicioSerializer
    permission_classes = [IsAdminOrReadOnly]

class SedeViewSet(viewsets.ModelViewSet):
    queryset = Sede.objects.all()
    serializer_class = SedeSerializer
    permission_classes = [IsAdminOrReadOnly]

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAdmin]

class EmpleadoServicioViewSet(viewsets.ModelViewSet):
    queryset = EmpleadoServicio.objects.all()
    serializer_class = EmpleadoServicioSerializer
    permission_classes = [IsAdmin]

class CitaViewSet(viewsets.ModelViewSet):
    queryset = Cita.objects.all()
    serializer_class = CitaSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsOwnerOrAdmin | IsAdmin]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        if user.rol == 'admin' or user.is_staff:
            return self.queryset
        elif user.rol == 'cliente':
            return self.queryset.filter(usuario=user)
        return self.queryset.none()
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def aprobar(self, request, pk=None):
        cita = self.get_object()
        cita.estado = 'aprobada'
        cita.save()
        return Response({'status': 'cita aprobada'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def rechazar(self, request, pk=None):
        cita = self.get_object()
        cita.estado = 'rechazada'
        cita.save()
        return Response({'status': 'cita rechazada'})

class DisponibilidadViewSet(viewsets.ModelViewSet):
    queryset = Disponibilidad.objects.all()
    serializer_class = DisponibilidadSerializer
    permission_classes = [IsAdmin]

class BloqueoViewSet(viewsets.ModelViewSet):
    queryset = Bloqueo.objects.all()
    serializer_class = BloqueoSerializer
    permission_classes = [IsAdmin]

class PublicacionViewSet(viewsets.ModelViewSet):
    queryset = Publicacion.objects.all()
    serializer_class = PublicacionSerializer
    permission_classes = [IsAdminOrReadOnly]

class NotificacionViewSet(viewsets.ModelViewSet):
    queryset = Notificacion.objects.all()
    serializer_class = NotificacionSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'update', 'partial_update']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        if user.rol == 'admin' or user.is_staff:
            return self.queryset
        return self.queryset.filter(usuario=user)

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.rol == 'admin' or user.is_staff:
            return self.queryset
        return self.queryset.filter(cita__usuario=user)