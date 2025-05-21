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
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .models import LoyverseUserConnection

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
                
                # Verificar conexión Loyverse
                try:
                    connection = LoyverseUserConnection.objects.get(user=user)
                    if not connection.is_active:
                        # Conexión existe pero no está activa
                        return Response({
                            'error': 'loyverse_connection_inactive',
                            'message': 'Tu conexión con Loyverse no está activa',
                            'redirect_url': reverse('loyverse_integration:connect_loyverse')
                        }, status=status.HTTP_401_UNAUTHORIZED)
                except LoyverseUserConnection.DoesNotExist:
                    # No tiene conexión
                    return Response({
                        'error': 'loyverse_connection_required',
                        'message': 'Necesitas conectar tu cuenta con Loyverse',
                        'redirect_url': reverse('loyverse_integration:connect_loyverse')
                    }, status=status.HTTP_401_UNAUTHORIZED)
                
            except User.DoesNotExist:
                pass  # Dejar que la vista original maneje este error
        
        # Devolver la respuesta original
        return response

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
        business_name = request.data.get('business_name')
        
        if not all([username, email, password]):
            return Response({
                'error': 'Se requieren nombre de usuario, email y contraseña'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si el usuario ya existe
        if User.objects.filter(username=username).exists():
            return Response({
                'username': ['Este nombre de usuario ya está en uso']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=email).exists():
            return Response({
                'email': ['Este email ya está registrado']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Crear el usuario
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            # Guardar información adicional si es necesario
            if hasattr(user, 'profile') and business_name:
                user.profile.business_name = business_name
                user.profile.save()
            
            # Iniciar sesión automáticamente
            auth_login(request, user)
            
            # Generar tokens JWT
            refresh = RefreshToken.for_user(user)
            
            # Devolver respuesta con tokens y URL para OAuth2
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user_id': user.id,
                'username': user.username,
                'loyverse_connection_required': True,
                'loyverse_connect_url': reverse('loyverse_integration:connect_loyverse')
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # Registrar el error
            logger.error(f"Error al registrar usuario {username}: {str(e)}", exc_info=True)
            
            # Devolver respuesta de error
            return Response({
                'error': f'Error al crear el usuario: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
