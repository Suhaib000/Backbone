from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status

from .models import Router
from .serializers import RouterSerializer
from .helper.router_connection import connect_to_router, disconnect_router, send_command_to_router
import json

class RouterViewSet(viewsets.ModelViewSet):
    queryset = Router.objects.all()
    serializer_class = RouterSerializer

    @action(detail=True, methods=["get"])
    def policies(self, request, pk=None):
        try:
            # 1. Get router details
            router = self.get_object()

            # 2. Connect to router
            try:
                connection = connect_to_router(router)
            except Exception as conn_error:
                # If connection fails, raise error immediately
                return Response(
                    {"error": f"Failed to connect to router: {str(conn_error)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # 3. Run command in JSON format
            raw_json = send_command_to_router(connection, "show configuration policy-options | display json")
            data = json.loads(raw_json)

            # Extract policy statement names and terms
            policy_statements = data.get("configuration", {}).get("policy-options", {}).get("policy-statement", [])
            policies = [{"name": p.get("name"), "terms": [t.get("name") for t in p.get("term", [])]} for p in policy_statements]

            # 5. Disconnect
            disconnect_router(connection)

            # 6. Return policies
            return Response({
                "router": router.name,
                "policies": policies
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
