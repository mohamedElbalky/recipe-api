

from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from rest_framework import authentication, permissions

from .serializers import (
    UserSerializer,
    AuthTokenSerializer,
)

class CreateUserView(CreateAPIView):
    """create a new user in the system"""
    serializer_class = UserSerializer
    

class CreateTokenView(ObtainAuthToken):
    """create a new authtoken for the user"""
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
    
class ManageUserView(RetrieveUpdateAPIView):
    """Manage theauthenticated user"""
    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """retrieve and returrn the authenticated user"""
        return self.request.user
        
