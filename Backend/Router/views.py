from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status

from .models import Router
from .serializers import RouterSerializer

from .helper.router_connection import connect_to_router, disconnect_router, send_command_to_router


class RouterViewSet(viewsets.ModelViewSet):
    queryset = Router.objects.all()
    serializer_class = RouterSerializer

    @action(detail=True, methods=['post'])
    def send_command(self, request, pk=None):
        try:
            router = self.get_object()
            command = request.data.get('command')

            if not command:
                return Response({'error': 'Command is required'}, status=status.HTTP_400_BAD_REQUEST)

            connection = connect_to_router(router)
            output = send_command_to_router(connection, command)
            disconnect_router(connection)

            return Response({'output': output}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)