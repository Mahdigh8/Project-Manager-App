from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.views import ObtainAuthToken
from .serializers import CreateUserSerializer, AuthTokenSerializer, UserSerializer


class CreateUserView(CreateAPIView):
    """User Registeration View"""

    serializer_class = CreateUserSerializer


class CreateTokenView(ObtainAuthToken):
    """Create a new auth token for user"""

    serializer_class = AuthTokenSerializer


class ManageUserView(RetrieveUpdateAPIView):
    """Retrive and Update user view"""

    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
