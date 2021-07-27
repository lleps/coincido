from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseRedirect, FileResponse, HttpResponseNotFound
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views import generic
from django import forms

from .models import *

import logging

logger = logging.getLogger('polls')


# Context preprocessor that injects cfg to every request
def from_email(request):
    return {
        "cfg": AppConfig.get(),
    }


def find_answer_for_question(user, question):
    try:
        answer = Answer.objects.get(user=user, question=question)
        return answer.choice
    except Answer.DoesNotExist:
        logger.warning("cannot find answer for user " + str(user) + " question " + str(question) + ". Return 0")
        return 0


def get_first_unanswered_question_index(beneficiario, questions):
    """Returns the index of the first non answered question, or
    -1 if has answered everything"""

    answers = list(Answer.objects.filter(beneficiario=beneficiario))
    min_non_answered_index = 0
    for q in questions:
        responded = False
        for a in answers:
            if a.question.id == q.id:
                responded = True
                break

        if not responded:
            return min_non_answered_index

        min_non_answered_index += 1

    return -1


import io
import xlsxwriter


def excelreport(request, user_index):
    users = User.objects.all()
    if user_index < 0 or user_index >= len(users):
        return HttpResponseNotFound("cant find user index " + str(user_index))

    user = users[user_index]

    buffer = io.BytesIO()
    workbook = xlsxwriter.Workbook(buffer)
    worksheet = workbook.add_worksheet()
    questions = Question.objects.all()

    columns = ['id', 'localidad', 'entrevistador_nombre_apellido',
               'entrevistador_fecha', 'inm_calle', 'inm_numero',
               'inm_barrio', 'inm_localidad', 'inm_departamento',
               'inm_lat', 'inm_lng', 'observaciones',
               # familia
               'cantidad_hogares', 'numero_de_hogar', 'jefe_apellido',
               'jefe_nombre', 'jefe_tipo_documento', 'jefe_numero_documento',
               'jefe_fecha_nacimiento', 'jefe_edad', 'jefe_telefono',
               'jefe_contacto', 'jefe_estado_civil', 'jefe_nacionalidad',
               'jefe_personas_en_hogar', 'nino_apellido', 'nino_nombre',
               'nino_tipo_documento', 'nino_numero_documento']

    for q in questions:
        columns.append(q.question_text)

    row = 1
    bold = workbook.add_format({'bold': True})
    worksheet.write_row(0, 0, columns, bold)

    for b in Beneficiario.objects.filter(usuario_id=user.id):
        if b.familia is None:
            continue

        f = b.familia
        attrs = [b.id, b.usuario.username, b.entrevistador_nombre_apellido,
                 b.entrevistador_fecha, b.inm_calle, b.inm_numero,
                 b.inm_barrio, b.inm_localidad, b.inm_departamento,
                 b.inm_lat, b.inm_lng, b.observaciones,
                 # familia
                 f.cantidad_hogares, f.numero_de_hogar, f.jefe_apellido,
                 f.jefe_nombre, f.jefe_tipo_documento, f.jefe_numero_documento,
                 f.jefe_fecha_nacimiento, f.jefe_edad, f.jefe_telefono,
                 f.jefe_contacto, f.jefe_estado_civil, f.jefe_nacionalidad,
                 f.jefe_personas_en_hogar, f.nino_apellido, f.nino_nombre,
                 f.nino_tipo_documento, f.nino_numero_documento]

        # Rellenar todas las preguntas. Y respuestas.
        for q in questions:
            try:
                answer = Answer.objects.get(question=q, beneficiario=b)
                attrs.append(answer.get_text())
            except Answer.DoesNotExist:
                continue

        worksheet.write_row(row, 0, attrs)
        row += 1

    workbook.close()
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename=user.username + '-reporte.xlsx')


def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    questions = list(Question.objects.all())
    beneficiarios = Beneficiario.objects.filter(usuario=request.user)
    results = []  # lista de { beneficiarioDNI, beneficiarioNombre, beneficiarioApellido, completoEncuestaONo }

    for b in beneficiarios:
        if b.familia is not None:
            familiaJefeDNI = str(b.familia.jefe_numero_documento)
            familiaJefeNombre = b.familia.jefe_nombre
            familiaJefeApellido = b.familia.jefe_apellido
        else:
            familiaJefeDNI = ""
            familiaJefeNombre = ""
            familiaJefeApellido = ""

        first_unanswered_question = get_first_unanswered_question_index(b, questions)
        results.append({
            'id': b.id,
            'barrio': b.inm_barrio,
            'calle': b.inm_calle,
            'numero': b.inm_numero,
            'entrevistaEfectiva': b.entrevista_efectiva == 'Si' or b.entrevista_efectiva == 'si',
            'entrevistaRazon': b.entrevista_efectiva,
            'first_unanswered_question': first_unanswered_question,
            'completoEncuesta': first_unanswered_question == -1,
            'completoFamilia': b.familia is not None,
            'completoGrupoFamiliar': b.terminado_datos_familia,
            'completoObservaciones': len(b.observaciones) > 0,
            'familiaJefeDNI': familiaJefeDNI,
            'familiaJefeNombre': familiaJefeNombre,
            'familiaJefeApellido': familiaJefeApellido,
        })

    context = {
        'result': results
    }

    return render(request, 'polls/index.html', context)


# TODO: Muestra detalles sobre dicho beneficiario.
def detalle(request, beneficiario_id):
    beneficiario = get_object_or_404(Beneficiario, pk=beneficiario_id)

    if beneficiario.familia is None:
        return Http404("beneficiario incompleto")

    qa = []
    questions = Question.objects.all()

    for q in questions:
        try:
            answer = Answer.objects.get(question=q, beneficiario=beneficiario)
            entry = {
                'q': q.question_text,
                'a': answer.get_text(),
            }

            if answer.image is not None:
                entry['img'] = answer.image
            else:
                entry['img'] = None

            qa.append(entry)
        except Answer.DoesNotExist:
            continue

    context = {
        'pk': beneficiario.id,
        'b': beneficiario,
        'f': beneficiario.familia,
        'qa': qa,
        'permitirGuardarDescripcion': request.user == beneficiario.usuario and len(beneficiario.observaciones) == 0,
        'convivientes': MiembroConviviente.objects.filter(beneficiario=beneficiario),
        'no_convivientes': MiembroNoConviviente.objects.filter(beneficiario=beneficiario),
    }
    logger.info(context)
    return render(request, "polls/detalle.html", context)


# Muestra resumen de todos los beneficiarios.
def resumen(request, user_index):
    usuarios = User.objects.all()
    if user_index < 0 or user_index >= len(usuarios):
        return Http404("Invalid user index: " + str(user_index))

    usuario = usuarios[user_index]
    context = {}

    context['selected_user'] = user_index

    # lista de usuarios primero
    usuarios_result = []
    for u in User.objects.all():
        usuarios_result.append(u.username)

    context['usuarios'] = usuarios_result
    questions = Question.objects.all()
    beneficiarios = Beneficiario.objects.filter(usuario=usuario)

    beneficiarios_result = []
    for b in beneficiarios:

        if b.familia is not None:
            familiaJefeDNI = str(b.familia.jefe_numero_documento)
            familiaJefeNombre = b.familia.jefe_nombre
            familiaJefeApellido = b.familia.jefe_apellido
        else:
            familiaJefeDNI = ""
            familiaJefeNombre = ""
            familiaJefeApellido = ""

        beneficiarios_result.append({
            'id': b.id,
            'barrio': b.inm_barrio,
            'calle': b.inm_calle,
            'numero': b.inm_numero,
            'jefeDNI': b.inm_numero,
            'jefeNombre': b.inm_numero,
            'jefeApellido': b.inm_numero,
            'entrevistaEfectiva': b.entrevista_efectiva == 'Si' or b.entrevista_efectiva == 'si',
            'entrevistaRazon': b.entrevista_efectiva,
            'completoEncuesta': get_first_unanswered_question_index(b, questions) == -1,
            'completoFamilia': b.familia is not None,
            'familiaJefeDNI': familiaJefeDNI,
            'familiaJefeNombre': familiaJefeNombre,
            'familiaJefeApellido': familiaJefeApellido,
        })

    context['result'] = beneficiarios_result

    return render(request, 'polls/resumen.html', context)


class MiembroConvivienteForm(forms.ModelForm):
    class Meta:
        model = MiembroConviviente
        fields = '__all__'
        exclude = ['beneficiario']

    def __init__(self, *args, **kwargs):
        super(MiembroConvivienteForm, self).__init__(*args, **kwargs)

        self.fields["planes"].widget = forms.CheckboxSelectMultiple()
        self.fields["planes"].queryset = TipoDePlan.objects.all()


class MiembroNoConvivienteForm(forms.ModelForm):
    class Meta:
        model = MiembroNoConviviente
        fields = '__all__'
        exclude = ['beneficiario']


class FamiliaForm(forms.ModelForm):
    class Meta:
        model = BeneficiarioFamilia
        fields = '__all__'
        labels = {
            'cantidad_hogares': 'Cantidad de hogares',
            'jefe_apellido': 'Apellido/s',
            'jefe_nombre': 'Nombre/s',
            'jefe_tipo_documento': 'Tipo de documento',
            'jefe_numero_documento': 'Número de documento',
            'jefe_edad': 'Edad',
            'jefe_telefono': 'Teléfono fijo/celular',
            'jefe_contacto': 'Otro teléfono/s o formas de contactarse',
            'jefe_estado_civil': 'Estado civil',
            'jefe_nacionalidad': 'Nacionalidad',
            'jefe_personas_en_hogar': 'Cuantas personas viven en este hogar',
            'jefe_fecha_nacimiento': 'Fecha de nacimiento',
            'nino_nombre': 'Nombre del niño/a',
            'nino_apellido': 'Apellido del niño/a',
            'nino_tipo_documento': 'Tipo de documento',
            'nino_numero_documento': 'Número de documento',
        }

    def __init__(self, *args, **kwargs):
        super(FamiliaForm, self).__init__(*args, **kwargs)

        self.fields["jefe_planes"].widget = forms.CheckboxSelectMultiple()
        self.fields["jefe_planes"].queryset = TipoDePlan.objects.all()

        # self.fields["nino_planes"].widget = forms.CheckboxSelectMultiple()
        # self.fields["nino_planes"].queryset = TipoDePlan.objects.all()


def detalle_observaciones(request, pk):
    beneficiario = get_object_or_404(Beneficiario, pk=pk)
    if request.method == 'POST':
        beneficiario.observaciones = request.POST['observaciones']
        beneficiario.save()

    return HttpResponseRedirect(reverse("polls:index"))


def grupofamiliar_post_conv(request, pk):
    beneficiario = get_object_or_404(Beneficiario, pk=pk)
    no_conv_form = MiembroNoConvivienteForm()

    if request.method == 'POST':
        conv_form = MiembroConvivienteForm(request.POST)

        # agregado, redireccionar al principal.
        if conv_form.is_valid():
            result = conv_form.save()
            result.beneficiario = beneficiario
            result.save()
            return HttpResponseRedirect(reverse("polls:grupofamiliar", args=(pk,)))

        else:
            logger.info("can't save form data")

    else:
        conv_form = MiembroConvivienteForm()

    return render(request, 'polls/grupofamiliar.html', {
        'conv_form': conv_form,
        'no_conv_form': no_conv_form,
        'pk': pk,
        'convivientes': MiembroConviviente.objects.filter(beneficiario=beneficiario),
        'no_convivientes': MiembroNoConviviente.objects.filter(beneficiario=beneficiario),
    })


def grupofamiliar_terminar(request, pk):
    beneficiario = get_object_or_404(Beneficiario, pk=pk)
    beneficiario.terminado_datos_familia = True
    beneficiario.save()
    return HttpResponseRedirect(reverse("polls:index"))


def grupofamiliar_post_no_conv(request, pk):
    beneficiario = get_object_or_404(Beneficiario, pk=pk)
    conv_form = MiembroConvivienteForm()

    if request.method == 'POST':
        no_conv_form = MiembroNoConvivienteForm(request.POST)

        # agregado, redireccionar al principal.
        if no_conv_form.is_valid():
            result = no_conv_form.save()
            result.beneficiario = beneficiario
            result.save()
            return HttpResponseRedirect(reverse("polls:grupofamiliar", args=(pk,)))

    else:
        no_conv_form = MiembroNoConvivienteForm()

    return render(request, 'polls/grupofamiliar.html', {
        'conv_form': conv_form,
        'no_conv_form': no_conv_form,
        'pk': pk,
        'convivientes': MiembroConviviente.objects.filter(beneficiario=beneficiario),
        'no_convivientes': MiembroNoConviviente.objects.filter(beneficiario=beneficiario),
    })


def grupofamiliar(request, pk):
    beneficiario = get_object_or_404(Beneficiario, pk=pk)

    if request.method == 'POST':
        # guardado
        return HttpResponseRedirect(reverse("polls:grupofamiliar"))

    else:
        conv_form = MiembroConvivienteForm()
        no_conv_form = MiembroNoConvivienteForm()

        return render(request, 'polls/grupofamiliar.html', {
            'conv_form': conv_form,
            'no_conv_form': no_conv_form,
            'pk': pk,
            'convivientes': MiembroConviviente.objects.filter(beneficiario=beneficiario),
            'no_convivientes': MiembroNoConviviente.objects.filter(beneficiario=beneficiario),
        })


def familia(request, pk):
    beneficiario = get_object_or_404(Beneficiario, pk=pk)

    if request.method == 'POST':
        form = FamiliaForm(request.POST)

        if form.is_valid():
            new_familia = form.save()
            beneficiario.familia = new_familia
            beneficiario.save()

            # agregar entradas a la tabla con jefe e hijo
            # si no existen
            if MiembroConviviente.objects.filter(beneficiario_id=beneficiario.id).count() == 0:
                f = new_familia
                jefe_m = MiembroConviviente.objects.create(
                    beneficiario=beneficiario,
                    nombre=f.jefe_nombre,
                    apellido=f.jefe_apellido,
                    tipo_de_documento=f.jefe_tipo_documento,
                    numero_de_documento=f.jefe_numero_documento,
                    edad=f.jefe_edad,
                    identidad_de_genero=f.jefe_identidad_de_genero,
                    parentesco="Jefe/a",
                    estado_civil=f.jefe_estado_civil,
                    estudios_alcanzados=f.jefe_estudios_alcanzados,
                    trabajo_remunerado=f.jefe_trabajo_remunerado,
                    ingresos_por_trabajo=f.jefe_ingresos_por_trabajo,
                    cobertura_de_salud=f.jefe_cobertura_de_salud,
                    discapacidad=f.jefe_discapacidad,
                    certificado_de_discapacidad=f.jefe_certificado_de_discapacidad,
                    enfermedad_cronica=f.jefe_enfermedad_cronica,
                    embarazo_en_curso=f.jefe_embarazo_en_curso,
                )
                jefe_m.planes.set(f.jefe_planes.all())

                nino_m = MiembroConviviente.objects.create(
                    beneficiario=beneficiario,
                    nombre=f.nino_nombre,
                    apellido=f.nino_apellido,
                    tipo_de_documento=f.nino_tipo_documento,
                    numero_de_documento=f.nino_numero_documento,
                    edad=f.nino_edad,
                    identidad_de_genero=f.nino_identidad_de_genero,
                    parentesco=f.nino_parentesco,
                    estado_civil="-",
                    estudios_alcanzados=f.nino_educacion,
                    trabajo_remunerado="-",
                    ingresos_por_trabajo="0",
                    cobertura_de_salud=f.nino_cobertura_de_salud,
                    discapacidad=f.nino_discapacidad,
                    certificado_de_discapacidad=f.nino_certificado_de_discapacidad,
                    enfermedad_cronica=f.nino_enfermedad_cronica,
                    embarazo_en_curso=False,
                )

            return HttpResponseRedirect(reverse('polls:index'))

        return render(request, 'polls/familia.html', {'form': form, 'pk': pk})

    else:
        # obtener grupo familiar final
        if beneficiario.familia is None:
            form = FamiliaForm()
        else:
            form = FamiliaForm(instance=beneficiario.familia)

        return render(request, 'polls/familia.html', {'form': form, 'pk': pk})


# prueba con forms
class AgregarBeneficiarioForm(forms.Form):
    ENTREVISTA_EFECTIVA_CHOICES = [
        ('si', 'Si'),
        ('rechazo', 'No: Rechazo'),
        ('lote-baldio', 'No: Lote Baldío'),
        ('se-mudo', 'No: Se mudó'),
        ('otros', 'No: Otros'),
    ]

    # entrevistador
    nombre_y_apellido_del_entrevistador = forms.CharField(max_length=100)
    fecha = forms.DateField(initial=timezone.now(), disabled=True)

    # calle
    calle = forms.CharField(max_length=128)
    numero = forms.IntegerField()
    barrio = forms.CharField(max_length=128)
    localidad = forms.CharField(max_length=128)
    codigo_postal = forms.CharField(max_length=50)
    departamento = forms.CharField(max_length=128)

    # entrevista efectiva o no
    entrevista_efectiva = forms.ChoiceField(choices=ENTREVISTA_EFECTIVA_CHOICES,
                                            help_text="Elija Si si la entrevista se puede completar, o alguna de "
                                                      "las razones si no se puede completar.")
    observaciones = forms.CharField(label='Observaciones (opcional)', widget=forms.Textarea, max_length=256,
                                    required=False)

    inm_lat = forms.FloatField(widget=forms.HiddenInput(), required=False, label="", label_suffix="")
    inm_lng = forms.FloatField(widget=forms.HiddenInput(), required=False, label="", label_suffix="")


# Vista para agregar un beneficiario
def beneficiario(request):
    if request.method == "POST":

        # create a form instance and populate it with data from the request:
        form = AgregarBeneficiarioForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            Beneficiario.objects.create(
                usuario=request.user,
                entrevistador_nombre_apellido=data['nombre_y_apellido_del_entrevistador'],
                entrevistador_fecha=data['fecha'],
                inm_calle=data['calle'],
                inm_numero=data['numero'],
                inm_barrio=data['barrio'],
                inm_localidad=data['localidad'],
                inm_departamento=data['departamento'],
                inm_codigo_postal=data['codigo_postal'],
                inm_lat=data['inm_lat'],
                inm_lng=data['inm_lng'],
                entrevista_efectiva=data['entrevista_efectiva'],
            )
            return HttpResponseRedirect(reverse('polls:index'))

    elif request.method == "GET":
        form = AgregarBeneficiarioForm()

        return render(request, 'polls/beneficiario.html', {'form': form})


class UploadImageForm(forms.Form):
    imagen = forms.ImageField(label="", label_suffix="")


def detail(request, pk, question_id):
    beneficiario = get_object_or_404(Beneficiario, pk=pk)

    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    questions = list(Question.objects.all())
    if question_id < 0 or question_id >= len(questions):
        raise Http404("invalid question index: " + str(question_id))

    question = questions[question_id]

    col_size = 4  # bootstrap column size depending on choice count
    choices = question.choice_set.all()
    choice_count = len(choices)
    if choice_count == 2:
        col_size = 6
    elif choice_count == 3:
        col_size = 4
    elif choice_count == 4:
        col_size = 6
    elif choice_count == 5:
        col_size = 4

    is_image = choice_count > 0 and choices[0].choice_image

    selected_choices = []

    context = {
        'id': beneficiario.pk,
        'question': question,
        'has_answer': False,
        'answer_index': 0,
        'selected_choices': selected_choices,  # for multiple choice
        'question_index': question_id,
        'observations': '',
        'other_text': '',
        'question_max': len(questions),
        'question_percent': int((question_id + 1) / len(questions) * 100),
        'is_last': question_id == len(questions) - 1,
        'is_first': question_id == 0,
        'prev_question_id': question_id - 1,
        'col_size': col_size,
        'is_image': is_image
    }

    answer = None

    try:
        answer = Answer.objects.get(user=request.user, beneficiario=beneficiario, question=question)
        context['has_answer'] = True
        context['answer_index'] = answer.choice
        context['observations'] = answer.observations
        context['other_text'] = answer.other_text
        logger.info("found answer for such question: " + str(answer.choice))

        # add selected_choices list
        if question.multiple_choice:
            options = answer.choice_multiple.split()
            for opt in options:
                selected_choices.append(int(opt))

    except Answer.DoesNotExist:
        logger.info("can't find answer")

    # add image field
    if question.allow_image:
        form = UploadImageForm()

        # add image (if it has one)
        if answer is not None and answer.image:
            form = UploadImageForm(initial={'imagen': answer.image})
            logger.info("set to form the image of answer.image")

        else:
            logger.info("answer is none or IDK but img doesnt exists")
        context['img_form'] = form

    return render(request, 'polls/detail.html', context)


class DNIFotosForm(forms.Form):
    jefe_foto_dorso = forms.ImageField(label="Jefe/a de familia / Dorso del DNI")
    jefe_foto_frente = forms.ImageField(label="Jefe/a de familia / Frente del DNI")
    nino_foto_dorso = forms.ImageField(label="Niño/a / Dorso del DNI")
    nino_foto_frente = forms.ImageField(label="Niño/a / Frente del DNI")


def dnifotos(request, beneficiario_id):
    beneficiario = get_object_or_404(Beneficiario, pk=beneficiario_id)
    if request.method == 'POST':
        form = DNIFotosForm(request.POST, request.FILES)
        if form.is_valid():
            DNIFotos.objects.filter(beneficiario_id=beneficiario.id).delete()  # delete existing in case it exists
            data = form.cleaned_data
            fotos = DNIFotos.objects.create(
                beneficiario=beneficiario,
                jefe_foto_dorso=data['jefe_foto_dorso'],
                jefe_foto_frente=data['jefe_foto_frente'],
                nino_foto_dorso=data['nino_foto_dorso'],
                nino_foto_frente=data['nino_foto_frente'],
            )
            fotos.save()
            return HttpResponseRedirect(reverse('polls:index'))

    else:
        try:
            inst = DNIFotos.objects.get(beneficiario_id=beneficiario.id)
            form = DNIFotosForm(initial={
                'jefe_foto_dorso': inst.jefe_foto_dorso,
                'jefe_foto_frente': inst.jefe_foto_frente,
                'nino_foto_dorso': inst.nino_foto_dorso,
                'nino_foto_frente': inst.nino_foto_frente,
                })
        except:
            form = DNIFotosForm()

    return render(request, 'polls/dnifotos.html', {'pk': beneficiario.id, 'form': form})


# endpoint to upload images to a response
def upload_img(request, beneficiario_id, question_id):
    questions = list(Question.objects.all())
    if question_id < 0 or question_id >= len(questions):
        return Http404("invalid question index: " + question_id)

    question = questions[question_id]

    logger.info("question gfound!")
    beneficiario = get_object_or_404(Beneficiario, pk=beneficiario_id)
    logger.info("beneficiario found!")

    if request.method == 'POST':
        form = UploadImageForm(request.POST, request.FILES)

        if form.is_valid():
            # crear u obtener una "response".
            try:
                answer = Answer.objects.get(user=request.user, beneficiario=beneficiario, question=question)
            except Answer.DoesNotExist:
                answer = Answer.objects.create(user=request.user, beneficiario=beneficiario, question=question)

            answer.image = form.cleaned_data['imagen']
            answer.save()
            return HttpResponseRedirect(reverse('polls:detail', args=(beneficiario_id, question_id,)))

    return HttpResponseRedirect(reverse('polls:detail', args=(beneficiario_id, question_id,)))


def results(request, pk, question_id):
    beneficiario = get_object_or_404(Beneficiario, pk=pk)
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'polls/results.html', {'question': question})


def vote(request, pk, question_id):
    beneficiario = get_object_or_404(Beneficiario, pk=pk)
    questions = list(Question.objects.all())
    if question_id < 0 or question_id >= len(questions):
        return Http404("invalid question index: " + question_id)

    question = questions[question_id]

    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    selected_choice = "99"
    selected_choices = ""

    # Parse selected choices from the post
    try:
        if question.multiple_choice:
            selected_choices = ""
            first = True
            for i in range(50):
                opt_selected = request.POST.get('check' + str(i), '')
                if opt_selected:
                    if not first:
                        selected_choices += " "

                    selected_choices += str(i)

                first = False

            logger.info("selected choices: " + selected_choices)

        else:
            selected_choice = request.POST['choice']

        other_text = request.POST.get('other_text', '')
        logger.info("other_text detectado a " + other_text)
        observations = request.POST.get('observations', '')

    except KeyError:
        # Redisplay the question voting form.
        # TODO display with all the metadata
        return render(request, 'polls/detail.html', {
            'question': question,
            'error_message': "No elegiste ninguna opción.",
        })

    else:
        # Get or create an answer for such question
        try:
            answer = Answer.objects.get(user=request.user, beneficiario=beneficiario, question=question)
        except Answer.DoesNotExist:
            answer = Answer.objects.create(user=request.user, beneficiario=beneficiario, question=question)

        answer.choice = selected_choice
        answer.choice_multiple = selected_choices
        answer.observations = observations

        if int(selected_choice) == 99:
            answer.other_text = other_text
            logger.info("response: other: " + other_text)

        answer.save()

        # Ver si tengo que saltear preguntas
        choices = Choice.objects.filter(question=question)
        next_question = question_id + 1
        if 0 <= int(selected_choice) < len(choices):
            choice = choices[int(selected_choice)]
            if choice.next_question != -1:
                # responder con choice -1 desde: la siguiente,
                # hasta la que saltea.
                counter = question_id + 1
                while counter < choice.next_question:
                    # ir creando respuestas
                    q = questions[counter]
                    try:
                        answer = Answer.objects.get(user=request.user, beneficiario=beneficiario, question=q)
                    except Answer.DoesNotExist:
                        answer = Answer.objects.create(user=request.user, beneficiario=beneficiario, question=q)

                    logger.info("answer question idx " + str(counter) + " to 99.")
                    answer.choice = 99
                    answer.save()
                    counter += 1

                next_question = choice.next_question

        logger.info("Selected choice: user " + request.user.username +
                    " question " + question.question_text +
                    " choice: " + selected_choice)

        if next_question < len(questions):  # redirect to next question
            return HttpResponseRedirect(reverse('polls:detail', args=(pk, next_question,)))
        else:  # no more questions, redirect to home
            return HttpResponseRedirect(reverse('polls:index'))


# Vista para registrarse
class SignupFormWithEmail(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email",)


class SignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username",)


def get_sign_up_form():
    try:
        if AppConfig.get().pedir_email:
            return SignupFormWithEmail
        else:
            return SignupForm
    except:
        return SignupFormWithEmail


class SignUpView(generic.CreateView):
    form_class = get_sign_up_form()
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'
