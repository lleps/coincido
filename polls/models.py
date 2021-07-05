import datetime

from django.db import models
from django.db.models import CASCADE
from django.utils import timezone
from django.contrib.auth.models import User


# sobre quien es la encuesta.
# las referencias son para el.
class Beneficiario(models.Model):
    # usuario que registro el beneficiario
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    # entrevistador
    entrevistador_nombre_apellido = models.CharField(max_length=100, help_text="Nombre y apellido del entrevistador",
                                                     default="")
    entrevistador_fecha = models.DateField(help_text="Fecha", auto_now_add=True)

    # datos generales del inmueble
    inm_calle = models.CharField(max_length=256, help_text="Calle", default="")
    inm_numero = models.IntegerField(help_text="Número", default=0)
    inm_barrio = models.CharField(max_length=256, help_text="Barrio", default="")
    inm_localidad = models.CharField(max_length=100, help_text="Localidad", default="")
    inm_departamento = models.CharField(max_length=100, help_text="Departament", default="")
    inm_lat = models.DecimalField(max_digits=22, decimal_places=16, blank=True, default=0)
    inm_lng = models.DecimalField(max_digits=22, decimal_places=16, blank=True, default=0)

    # entrevista efectiva
    ENTREVISTA_EFECTIVA_CHOICES = [
        ('si', 'Si'),
        ('rechazo', 'No: Rechazo'),
        ('lote-baldio', 'No: Lote Baldío'),
        ('se-mudo', 'No: Se mudó'),
        ('otros', 'No: Otros'),
    ]
    entrevista_efectiva = models.CharField(choices=ENTREVISTA_EFECTIVA_CHOICES, max_length=100)

    # datos del niño
    dni = models.IntegerField(help_text="DNI del beneficiario")
    nombre = models.CharField(max_length=80, help_text="Nombre del beneficiario")
    apellido = models.CharField(max_length=80, help_text="Apellido del beneficiario")
    direccion = models.CharField(max_length=300, help_text="Dirección del beneficiario", default="Direccion linea 1")
    observaciones = models.CharField(max_length=3000, help_text="Observaciones sobre el beneficiario",
                                     default="",
                                     blank=True)


    def __str__(self):
        return str(self.dni) + " " + str(self.nombre) + " " + str(self.apellido)


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')

    def __str__(self):
        return self.question_text

    def was_published_recently(self):
        return self.pub_date >= timezone.now() - datetime.timedelta(days=1)


class AppConfig(models.Model):
    frase_mejores_candidatos = models.CharField(default="mejores candidatos:", max_length=1024,
                                                help_text="Frase mostrada cuando se muestran los mejores candidatos")

    frase_inicial = models.CharField(default="completa la encuesta", max_length=1024,
                                     help_text="Frase mostrada a las personas que todavia no completaron cuestionario")

    frase_elegir_genero = models.CharField(default="completa los datos", max_length=1024, blank=True)

    afinidad_cantidad_gente = models.IntegerField(default=3, help_text="Cantidad de gente mostrada en afinidad")

    color_principal = models.CharField(default="#ff0000", max_length=10, help_text="Color de la barra")

    color_fondo = models.CharField(default="#ffffff", max_length=10)

    frase_logo = models.CharField(default="coincido.com.ar", max_length=1024, help_text="Frase al lado del logo")

    imagen_logo = models.ImageField(help_text="Imagen del logo")

    imagen_fondo = models.ImageField(help_text="Imagen del fondo de la página")

    imagen_principal = models.ImageField(help_text="Imagen principal, mostrada en login, registro y menu", default="")

    pedir_genero = models.BooleanField(help_text="Solo matchear gente del género que buscan", default=True)

    pedir_email = models.BooleanField(help_text="Pedir email en el registro", default=True)

    @staticmethod
    def get():
        try:
            return AppConfig.objects.first()
        except:
            config = AppConfig.objects.create()
            return config


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    choice_image = models.ImageField(null=True, blank=True)


# Cada respuesta esta ligada a un beneficiario y a un usuario. También dice de que pregunta es,
# y que opción escogió.
class Answer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    beneficiario = models.ForeignKey(Beneficiario, on_delete=models.CASCADE, null=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.IntegerField(default=0)  # choice picked in the answer


class Profile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Hombre'),
        ('F', 'Mujer'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M',)
    gender_preference = models.CharField(max_length=1, choices=GENDER_CHOICES, default='F',)
