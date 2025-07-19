from rest_framework import serializers
from .models import Router


class RouterSerializer(serializers.ModelSerializer):
    ssh_password = serializers.CharField(write_only=True)

    class Meta:
        model = Router
        fields = "__all__"
    