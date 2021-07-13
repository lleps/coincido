import datetime

from django.db import models
from django.db.models import CASCADE
from django.utils import timezone
from django.contrib.auth.models import User


# datos sociales sobre un beneficiario.
# por ahora omitir grupo familiar; solamente
# el que esta a cargo y eso.
class BeneficiarioFamilia(models.Model):
    CANTIDAD_HOGARES_CHOICES = [
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
    ]
    ESTADO_CIVIL_CHOICES = [
        ('soltero', 'SOLTERO/A'),
        ('casado', 'CASADO/A'),
        ('divorciado', 'DIVORCIADO/A'),
        ('en-pareja', 'EN PAREJA/CONCUBINATO'),
        ('separado', 'SEPARADO/A DE HECHO'),
        ('viudo', 'VIUDO/A'),
    ]
    TIPO_DOCUMENTO_CHOICES = [
        ('libreta-civica', 'Libreta Civica'),
        ('libreta-de-enrolamiento', 'Libreta De enrolamiento'),
        ('dni', 'DNI'),
        ('doc-extranjero', 'Doc. Extranjero'),
        ('nunca-tuvo', 'Nunca Tuvo'),
        ('otro', 'Otro'),
    ]

    # datos del hogar
    cantidad_hogares = models.CharField(max_length=120, choices=CANTIDAD_HOGARES_CHOICES, default='1')
    numero_de_hogar = models.CharField(max_length=120, choices=CANTIDAD_HOGARES_CHOICES, default='1')

    # datos del jefe/a
    jefe_apellido = models.CharField(max_length=120)
    jefe_nombre = models.CharField(max_length=120)
    jefe_tipo_documento = models.CharField(max_length=120, choices=TIPO_DOCUMENTO_CHOICES, default='dni')
    jefe_numero_documento = models.IntegerField()
    jefe_fecha_nacimiento = models.DateField()
    jefe_edad = models.IntegerField()
    jefe_telefono = models.CharField(max_length=50)
    jefe_contacto = models.CharField(max_length=100)
    jefe_estado_civil = models.CharField(max_length=100, choices=ESTADO_CIVIL_CHOICES)
    jefe_nacionalidad = models.CharField(max_length=120)
    jefe_personas_en_hogar = models.IntegerField()

    # datos del niño/a
    nino_apellido = models.CharField(max_length=120)
    nino_nombre = models.CharField(max_length=120)
    nino_tipo_documento = models.CharField(max_length=120, choices=TIPO_DOCUMENTO_CHOICES, default='dni')
    nino_numero_documento = models.IntegerField()


# Define un conviviente de un beneficiario
class MiembroConviviente(models.Model):
    ESTADO_CIVIL_CHOICES = [
        ('soltero', 'SOLTERO/A'),
        ('casado', 'CASADO/A'),
        ('divorciado', 'DIVORCIADO/A'),
        ('en-pareja', 'EN PAREJA/CONCUBINATO'),
        ('separado', 'SEPARADO/A DE HECHO'),
        ('viudo', 'VIUDO/A'),
    ]
    TIPO_DOCUMENTO_CHOICES = [
        ('libreta-civica', 'Libreta Civica'),
        ('libreta-de-enrolamiento', 'Libreta De enrolamiento'),
        ('dni', 'DNI'),
        ('doc-extranjero', 'Doc. Extranjero'),
        ('nunca-tuvo', 'Nunca Tuvo'),
        ('otro', 'Otro'),
    ]
    IDENTIDAD_DE_GENERO_CHOICES = [
        ('Mujer', 'Mujer'),
        ('Varón', 'Varón'),
        ('Disidencia', 'Disidencia'),
    ]
    PARENTESCO_CHOICES = [
        ('Jefe', 'Jefe'),
        ('Cónyuge/pareja', 'Cónyuge/pareja'),
        ('Hijo/a', 'Hijo/a'),
        ('Yerno/nuera', 'Yerno/nuera'),
        ('Nieto/a', 'Nieto/a'),
        ('Padre/madre', 'Padre/madre'),
        ('Suegro/a', 'Suegro/a'),
        ('Otro familiar', 'Otro familiar'),
        ('No familiar', 'No familiar'),
    ]
    TRABAJO_REMUNERADO_CHOICES = [
        ('Formal', 'Formal'),
        ('Informal', 'Informal'),
        ('Autónomo', 'Autónomo'),
        ('Jubilación/retiro', 'Jubilación/retiro'),
        ('Desocupado', 'Desocupado'),
    ]
    OTROS_INGRESOS_CHOICES = [
        ('AUH', 'AUH'),
        ('AUE', 'AUE'),
        ('Tarjeta Alimentar', 'Tarjeta Alimentar'),
        ('Potenciar Inclusión Joven', 'Potenciar Inclusión Joven'),
        ('Argentina Hace', 'Argentina Hace'),
        ('Potenciar Trabajo', 'Potenciar Trabajo'),
        ('Fondo Desempleo', 'Fondo Desempleo'),
        ('Pensión Madre de 7 hijos', 'Pensión Madre de 7 hijos'),
        ('Pensión por discapacidad', 'Pensión por discapacidad'),
        ('IFE', 'IFE'),
        ('Otros', 'Otros'),
    ]
    COBERTURA_DE_SALUD_CHOICES = [
        ('No posee', 'No posee'),
        ('Pre paga', 'Pre paga'),
        ('APROSS', 'APROSS'),
        ('PAMI', 'PAMI'),
        ('PROFE', 'PROFE'),
        ('Otros', 'Otros'),
    ]
    DISCAPACIDAD_CHOICES = [
        ('No', 'No'),
        ('Motriz', 'Motriz'),
        ('Intelectual', 'Intelectual'),
        ('Sensorial', 'Sensorial'),
        ('Multidiscapacidad', 'Multidiscapacidad'),
    ]
    CERTIFICADO_DE_DISCAPACIDAD_CHOICES = [
        ('Si, Vigente', 'Si, Vigente'),
        ('Si, No vigente', 'Si, No Vigente'),
        ('En trámite', 'En trámite'),
        ('No', 'No'),
    ]

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    tipo_de_documento = models.CharField(max_length=100, choices=TIPO_DOCUMENTO_CHOICES)
    numero_de_documento = models.IntegerField()
    edad = models.IntegerField()
    identidad_de_genero = models.CharField(max_length=80, verbose_name="Identidad de género", choices=IDENTIDAD_DE_GENERO_CHOICES)
    parentesco = models.CharField(max_length=80, verbose_name="Parentezco c/jefe/a flia", choices=PARENTESCO_CHOICES)
    estado_civil = models.CharField(max_length=80, verbose_name="Estado civíl", choices=PARENTESCO_CHOICES)
    estudios_alcanzados = models.CharField(verbose_name="Estudios alcanzados", max_length=50)
    trabajo_remunerado = models.CharField(max_length=80, choices=TRABAJO_REMUNERADO_CHOICES)
    otros_ingresos = models.CharField(max_length=80, choices=OTROS_INGRESOS_CHOICES)
    cobertura_de_salud = models.CharField(max_length=80, choices=COBERTURA_DE_SALUD_CHOICES)
    discapacidad = models.CharField(max_length=80, choices=DISCAPACIDAD_CHOICES)
    certificado_de_discapacidad = models.CharField(max_length=80, choices=CERTIFICADO_DE_DISCAPACIDAD_CHOICES, default="No")
    enfermedad_cronica = models.CharField(max_length=80, verbose_name="Enf. Crónica", default="No")
    embarazo_en_curso = models.BooleanField(default=False)


class MiembroNoConviviente(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    observaciones = models.CharField(max_length=100, default="")


# sobre quien es la encuesta.
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
    inm_codigo_postal = models.CharField(max_length=60, default="")

    # entrevista efectiva
    ENTREVISTA_EFECTIVA_CHOICES = [
        ('si', 'Si'),
        ('rechazo', 'No: Rechazo'),
        ('lote-baldio', 'No: Lote Baldío'),
        ('se-mudo', 'No: Se mudó'),
        ('otros', 'No: Otros'),
    ]
    entrevista_efectiva = models.CharField(choices=ENTREVISTA_EFECTIVA_CHOICES, max_length=100)

    # beneficiario familia
    familia = models.OneToOneField(
        BeneficiarioFamilia,
        on_delete=models.CASCADE,
        null=True,
    )


class Question(models.Model):
    question_text = models.CharField(max_length=200, verbose_name="Texto")
    pub_date = models.DateTimeField('date published')
    allow_other = models.BooleanField(verbose_name='Permitir otros', help_text="Permitir opción 'Otros'")
    allow_image = models.BooleanField(verbose_name='Permitir poner una imágen')

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
    other_text = models.CharField(max_length=128, default='')
    image = models.ImageField(null=True, blank=True)


class Profile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Hombre'),
        ('F', 'Mujer'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M',)
    gender_preference = models.CharField(max_length=1, choices=GENDER_CHOICES, default='F',)
