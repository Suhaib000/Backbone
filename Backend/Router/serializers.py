from rest_framework import serializers
from .models import Router , RollbackDetials


class RouterSerializer(serializers.ModelSerializer):
    ssh_password = serializers.CharField(write_only=True)

    class Meta:
        model = Router
        fields = "__all__"




class RollbackDetialserializer(serializers.ModelSerializer):

    class Meta:
        model = RollbackDetials
        fields = "__all__"