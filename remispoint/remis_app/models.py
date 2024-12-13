# models.py

from django.db import models

# Tabla Localidad
class Localidad(models.Model):
    id_localidad = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=255)

    class Meta:
        db_table = 'Localidad'

    def __str__(self):
        return self.nombre

# Tabla Cliente
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
    tipo_cuenta = models.IntegerField(choices=TIPO_CUENTA_CHOICES)
    id_localidad = models.ForeignKey(Localidad, on_delete=models.CASCADE)

    class Meta:
        db_table = 'Clientes'

    def __str__(self):
        return self.nombre

# Tabla Chofer
class Chofer(models.Model):
    id_chofer = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    nro_tel = models.CharField(max_length=20)
    licencia = models.CharField(max_length=50)

    class Meta:
        db_table = 'Chofer'

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


# Tabla Auto
class Auto(models.Model):
    patente = models.CharField(primary_key=True, max_length=50)
    tipo = models.CharField(max_length=100)  # Tipo de auto
    foto = models.CharField(max_length=100)  # Foto del auto
    anio_modelo = models.IntegerField()  # Año del modelo
    propietario = models.CharField(max_length=100)  # Propietario del auto
    vtv = models.DateField()  # Fecha de vencimiento de VTV
    venc_patente = models.DateField()  # Fecha de vencimiento de patente
    id_remiseria = models.CharField(max_length=100)  # Remisería

    class Meta:
        db_table = 'Autos'

    def __str__(self):
        return f"{self.tipo} - {self.patente}"
    
class ChoferAuto(models.Model):
    patente = models.ForeignKey(Auto, on_delete=models.CASCADE, db_column="patente")
    id_chofer = models.ForeignKey(Chofer, on_delete=models.CASCADE, db_column="id_chofer")
    turno = models.CharField(max_length=50)
    disponibilidad = models.BooleanField()

    class Meta:
        db_table = "ChoferAuto"
        managed = False  # Evita que Django intente gestionar la tabla
        unique_together = (("patente", "id_chofer"),)  # Define la clave primaria compuesta

# Tabla Viaje
class Viaje(models.Model):
    id_viaje = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        db_column="id_cliente"  # Especifica el nombre exacto de la columna
    )
    dir_salida = models.CharField(max_length=255)
    dir_destino = models.CharField(max_length=255)
    hora = models.TimeField()
    fecha = models.DateField()
    id_precio = models.IntegerField()  # Relación con tabla de precios
    cod_tipo_pago = models.CharField(max_length=50)  # Código de tipo de pago
    id_remiseria = models.CharField(max_length=100)  # Remisería
    inicio = models.TimeField()  # Hora de inicio del viaje
    fin = models.TimeField()  # Hora de fin del viaje
    patente = models.ForeignKey(
        Auto,
        on_delete=models.CASCADE,
        db_column="patente"
    )# Patente del auto asignado
    estado = models.CharField(max_length=50)  # Estado del viaje (Ej. 'En progreso', 'Finalizado')

    class Meta:
        db_table = 'Viajes'
        managed = False  # Para que no sea gestionada por Django

    def __str__(self):
        return f"Viaje {self.id_viaje} - Cliente {self.id_cliente.nombre}"

# Tabla PedidosCliente (ya estaba incluida previamente)
class PedidosCliente(models.Model):
    id_pedido = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        db_column="id_cliente"  # Especifica el nombre exacto de la columna
    )
    dir_salida = models.CharField(max_length=255)
    dir_destino = models.CharField(max_length=255)
    estado_pedido = models.CharField(max_length=100)


    class Meta:
        db_table = "PedidoCliente"
        managed = False  # Para que no sea gestionada por Django

    def __str__(self):
        return f"Pedido {self.id_pedido} de cliente {self.id_cliente}"

