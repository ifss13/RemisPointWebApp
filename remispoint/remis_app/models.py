# models.py

from django.db import models
from django.contrib.auth.models import User

class Localidad(models.Model):
    id_localidad = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=255)

    class Meta:
        db_table = 'Localidad'

    def __str__(self):
        return self.nombre

class Cliente(models.Model):
    CLIENTE = 1
    CHOFER = 2
    BASE = 3

    TIPO_CUENTA_CHOICES = [
        (CLIENTE, 'Cliente'),
        (CHOFER, 'Chofer'),
        (BASE, 'Base'),
    ]
    id_cliente = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    direccion = models.CharField(max_length=200)
    correo = models.EmailField()
    password = models.CharField(max_length=100)
    tipo_cuenta = models.IntegerField()
    id_localidad = models.ForeignKey(Localidad, on_delete=models.CASCADE)

    class Meta:
        db_table = 'Clientes'  # Especifica el esquema y la tabla

    def __str__(self):
        return self.nombre
