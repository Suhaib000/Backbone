from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status

from .models import Router , RollbackDetials
from .serializers import RouterSerializer , RollbackDetialserializer
from .helper.router_connection import connect_to_router, disconnect_router, send_command_to_router , send_bulk_commands
import json


class RollbackDetialViewSet(viewsets.ModelViewSet):
    queryset = RollbackDetials.objects.all()
    serializer_class = RollbackDetialserializer



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

    @action(detail=True, methods=["post"])
    def generate_policy_commands(self, request, pk=None):
        """
        Generate add/delete commands for migrating terms between policies.
        Expects JSON:
        {
            "router_id_to": 2,
            "policy_from": "Airtel-2-IPv4-fake",
            "policy_to": "term3",
            "terms": ["mobile", "mobinil-3G_blackhole"]
        }
        """
        try:
            router_from = self.get_object()
            router_id_to = request.data.get("router_id_to")
            policy_from = request.data.get("policy_from")
            policy_to = request.data.get("policy_to")
            terms = request.data.get("terms", [])

            if not all([router_id_to, policy_from, policy_to, terms]):
                return Response(
                    {"error": "router_id_to, policy_from, policy_to, and terms are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Connect to source router
            try:
                connection = connect_to_router(router_from)
            except Exception as conn_error:
                return Response(
                    {"error": f"Failed to connect to source router: {str(conn_error)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            add_cmds, del_cmds = [], []

            # Loop over all requested terms
            for term_name in terms:
                cmd = f"show configuration policy-options policy-statement {policy_from} term {term_name} | display set"
                cli_output = send_command_to_router(connection, cmd)

                term_cmds = []

                # 🔑 Rewrite commands to target policy/term
                for line in cli_output.splitlines():
                    line = line.strip()
                    if not line.startswith("set "):
                        continue
                    # Replace old policy + term with the new one
                    rewritten = line.replace(
                        f"policy-statement {policy_from} term {term_name}",
                        f"policy-statement {policy_to} term {term_name}"
                    )
                    term_cmds.append(rewritten)

                # Always add "then reject" at the end
                

                add_cmds.extend(term_cmds)

                # Delete original term from source policy
                del_cmds.append(
                    f"delete policy-options policy-statement {policy_from} term {term_name}"
                )
            extra_cmds = [f"insert policy-options policy-statement {policy_to} term reject after term {term_name}"]

            add_cmds =  add_cmds + extra_cmds  # prepend in bulk

            # Disconnect from router
            disconnect_router(connection)

            # Get destination router object
            try:
                router_to = Router.objects.get(pk=router_id_to)
            except Router.DoesNotExist:
                return Response({"error": "Destination router not found"}, status=404)

            return Response({
                "router_from": router_from.id,
                "router_to": router_to.id,
                "add_commands": add_cmds,
                "delete_commands": del_cmds
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"])
    def apply_policy_commands(self, request):
        """
        Safely apply add/delete commands:
        1️⃣ Add commands to destination router and commit
        2️⃣ If successful, delete commands from source router and commit
        Expects JSON:
        {
          "router_from": 2,
          "router_to": 2,
          "add_commands": [...],
          "delete_commands": [...]
        }
        """
        data = request.data
        router_from_id = data.get("router_from")
        router_to_id = data.get("router_to")
        add_commands = data.get("add_commands", [])
        delete_commands = data.get("delete_commands", [])
        payload = data.get("payload", [])

        print("payload" , payload)

        

        if not all([router_from_id, router_to_id, add_commands, delete_commands]):
            return Response(
                {"error": "router_from, router_to, add_commands, and delete_commands are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            router_from = Router.objects.get(pk=router_from_id)
            router_to = Router.objects.get(pk=router_to_id)
        except Router.DoesNotExist:
            return Response({"error": "Router not found"}, status=404)

        results = {}

        # 1️⃣ Connect and add commands to destination router
        try:
            conn_to = connect_to_router(router_to)
            # for cmd in add_commands:
            #     send_command_to_router(conn_to, cmd)
            add_commands.append("commit")
            output_add = send_bulk_commands(conn_to, add_commands)

            # send_command_to_router(conn_to, "commit")
            results["added_on_router_to"] = True
        except Exception as e:
            results["added_on_router_to"] = False
            results["error_router_to"] = str(e)
            # If adding failed, do not proceed to deletion
            return Response(results, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            disconnect_router(conn_to)

        # 2️⃣ Connect and delete commands from source router
        try:
            conn_from = connect_to_router(router_from)
            delete_commands.append("commit")
            output_delete = send_bulk_commands(conn_from, delete_commands)

            results["deleted_on_router_from"] = True

            RollbackDetials.objects.create(status=False , movement =payload )


        except Exception as e:
            results["deleted_on_router_from"] = False
            results["error_router_from"] = str(e)
        finally:
            disconnect_router(conn_from)

        return Response(results, status=status.HTTP_200_OK)