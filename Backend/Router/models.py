from django.db import models
from encrypted_model_fields.fields import EncryptedCharField

 
# Create your models here.

class Router(models.Model):
    name = models.CharField(max_length=100)
    ip = models.GenericIPAddressField()
    ssh_username = models.CharField(max_length=50)
    ssh_password = EncryptedCharField(max_length=100) 
    device_type = models.CharField(max_length=50, default='juniper')

    def __str__(self):
        return f"{self.name} ({self.ip})"
