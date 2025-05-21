"""
Vistas personalizadas para autenticación con integración de Loyverse.

Estas vistas extienden el flujo de autenticación estándar para requerir
una conexión activa con Loyverse.
"""

from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .models import LoyverseUserConnection
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

class CustomLoginView(LoginView):
    """
    Vista personalizada de login que verifica la conexión con Loyverse.
    
    Si el usuario no tiene una conexión activa con Loyverse, se le redirige
    al flujo de OAuth2 después de iniciar sesión.
    """
    
    def form_valid(self, form):
        """Procesa el formulario de login válido."""
        # Realizar el login estándar
        auth_login(self.request, form.get_user())
        
        # Verificar si el usuario tiene una conexión Loyverse activa
        try:
            connection = form.get_user().loyverse_connection
            if not connection.is_active:
                messages.warning(
                    self.request,
                    "Tu conexión con Loyverse no está activa. Por favor, reconéctate."
                )
                return redirect('loyverse_integration:connect_loyverse')
        except LoyverseUserConnection.DoesNotExist:
            # Si no tiene conexión, redirigir al flujo OAuth2
            messages.info(
                self.request,
                "Para usar BodegaClick, necesitas conectar tu cuenta con Loyverse."
            )
            return redirect('loyverse_integration:connect_loyverse')
        
        # Si todo está bien, continuar con el flujo normal
        return super().form_valid(form)

class CustomTokenObtainPairView(APIView):
    """
    Vista personalizada para obtener tokens JWT que verifica la conexión con Loyverse.
    
    Si el usuario no tiene una conexión activa con Loyverse, devuelve un error
    con la URL para iniciar el flujo OAuth2.
    """
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        from rest_framework_simplejwt.views import TokenObtainPairView
        
        # Obtener la vista original
        original_view = TokenObtainPairView.as_view()
        
        try:
            # Ejecutar la vista original
            response = original_view(request._request, *args, **kwargs)
            
            # Si la autenticación fue exitosa
            if hasattr(response, 'data') and 'access' in response.data:
                # Extraer el usuario del token
                from rest_framework_simplejwt.tokens import AccessToken
                token = response.data['access']
                user_id = AccessToken(token)['user_id']
                
                try:
                    user = User.objects.get(id=user_id)
                    
                    # Añadir información básica del usuario a la respuesta
                    response.data['user_id'] = user.id
                    response.data['username'] = user.username
                    response.data['email'] = user.email
                    
                    # Verificar conexión Loyverse
                    try:
                        connection = LoyverseUserConnection.objects.get(user=user)
                        
                        # Añadir información de la conexión a la respuesta
                        response.data['loyverse_connected'] = True
                        response.data['loyverse_active'] = connection.is_active
                        response.data['loyverse_account_name'] = connection.loyverse_account_name
                        
                        if not connection.is_active:
                            # Conexión existe pero no está activa
                            logger.warning(f"Usuario {user.username} (ID: {user.id}) tiene conexión Loyverse inactiva")
                            return Response({
                                'error': 'loyverse_connection_inactive',
                                'message': 'Tu conexión con Loyverse no está activa',
                                'redirect_url': reverse('loyverse_integration:connect_loyverse'),
                                'user_id': user.id,
                                'username': user.username,
                                'email': user.email
                            }, status=status.HTTP_401_UNAUTHORIZED)
                    except LoyverseUserConnection.DoesNotExist:
                        # No tiene conexión
                        logger.warning(f"Usuario {user.username} (ID: {user.id}) no tiene conexión Loyverse")
                        response.data['loyverse_connected'] = False
                        return Response({
                            'error': 'loyverse_connection_required',
                            'message': 'Necesitas conectar tu cuenta con Loyverse',
                            'redirect_url': reverse('loyverse_integration:connect_loyverse'),
                            'user_id': user.id,
                            'username': user.username,
                            'email': user.email
                        }, status=status.HTTP_401_UNAUTHORIZED)
                    
                    # Registrar login exitoso
                    logger.info(f"Login exitoso para usuario {user.username} (ID: {user.id})")
                    
                except User.DoesNotExist:
                    logger.error(f"No se encontró usuario con ID {user_id} al verificar token JWT")
                    return Response({
                        'error': 'user_not_found',
                        'message': 'Usuario no encontrado'
                    }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Devolver la respuesta original
            return response
            
        except Exception as e:
            # Capturar errores de autenticación y proporcionar mensajes más amigables
            error_msg = str(e)
            
            if 'No active account found with the given credentials' in error_msg:
                logger.warning(f"Intento de login fallido: credenciales inválidas. IP: {request.META.get('REMOTE_ADDR')}")
                return Response({
                    'error': 'invalid_credentials',
                    'message': 'Nombre de usuario o contraseña incorrectos'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Registrar otros errores
            logger.error(f"Error en CustomTokenObtainPairView: {error_msg}", exc_info=True)
            return Response({
                'error': 'authentication_error',
                'message': 'Error de autenticación',
                'detail': error_msg if settings.DEBUG else 'Contacta al administrador para más información'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CustomUserRegistrationView(APIView):
    """
    Vista personalizada para registro de usuarios que requiere conexión con Loyverse.
    
    Después de registrar al usuario, devuelve un token temporal y la URL para
    iniciar el flujo OAuth2 con Loyverse.
    """
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        # Validar datos del usuario
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        password_confirm = request.data.get('password_confirm')
        business_name = request.data.get('business_name')
        
        # Validaciones básicas
        errors = {}
        
        if not username:
            errors['username'] = ['El nombre de usuario es obligatorio']
        elif len(username) < 3:
            errors['username'] = ['El nombre de usuario debe tener al menos 3 caracteres']
        elif User.objects.filter(username=username).exists():
            errors['username'] = ['Este nombre de usuario ya está en uso']
        
        if not email:
            errors['email'] = ['El email es obligatorio']
        elif User.objects.filter(email=email).exists():
            errors['email'] = ['Este email ya está registrado']
        
        if not password:
            errors['password'] = ['La contraseña es obligatoria']
        elif len(password) < 8:
            errors['password'] = ['La contraseña debe tener al menos 8 caracteres']
        
        if password != password_confirm:
            errors['password_confirm'] = ['Las contraseñas no coinciden']
        
        if not business_name:
            errors['business_name'] = ['El nombre del negocio es obligatorio']
        
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Crear el usuario
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=request.data.get('first_name', ''),
                last_name=request.data.get('last_name', '')
            )
            
            # Guardar información adicional si es necesario
            if hasattr(user, 'profile'):
                # Si existe un modelo de perfil, guardar el nombre del negocio
                if not hasattr(user, 'profile'):
                    # Si el perfil no se creó automáticamente, crearlo
                    from django.apps import apps
                    Profile = apps.get_model('users', 'Profile')
                    profile = Profile.objects.create(user=user)
                else:
                    profile = user.profile
                
                profile.business_name = business_name
                profile.save()
            else:
                # Registrar que no se pudo guardar el nombre del negocio
                logger.warning(f"No se pudo guardar el nombre del negocio para {username} porque no existe modelo de perfil")
            
            # Iniciar sesión automáticamente si es una solicitud con sesión
            if hasattr(request, 'session'):
                auth_login(request, user)
            
            # Generar tokens JWT
            refresh = RefreshToken.for_user(user)
            
            # Registrar éxito
            logger.info(f"Usuario {username} registrado exitosamente. ID: {user.id}")
            
            # Devolver respuesta con tokens y URL para OAuth2
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'loyverse_connection_required': True,
                'loyverse_connect_url': reverse('loyverse_integration:connect_loyverse'),
                'message': 'Usuario registrado exitosamente. Ahora debes conectar tu cuenta con Loyverse.'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # Registrar el error
            logger.error(f"Error al registrar usuario {username}: {str(e)}", exc_info=True)
            
            # Devolver respuesta de error
            return Response({
                'error': 'Error al crear el usuario',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
