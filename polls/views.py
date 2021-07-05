from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseRedirect
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


def get_first_unanswered_question_index(user, beneficiario, questions):
    """Returns the index of the first non answered question, or
    -1 if has answered everything"""

    answers = list(Answer.objects.filter(user=user, beneficiario=beneficiario))
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


def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    questions = list(Question.objects.all())
    beneficiarios = Beneficiario.objects.filter(usuario=request.user)
    results = []  # lista de { beneficiarioDNI, beneficiarioNombre, beneficiarioApellido, completoEncuestaONo }

    for b in beneficiarios:
        results.append({
            'beneficiarioDNI': b.dni,
            'beneficiarioNombre': b.nombre,
            'beneficiarioApellido': b.apellido,
            'completoEncuesta': get_first_unanswered_question_index(request.user, b, questions) == -1,
        })

    context = {
        'result': results
    }

    return render(request, 'polls/index.html', context)


# Muestra resumen de todos los beneficiarios.
def resumen(request):
    beneficiarios = Beneficiario.objects.all()
    results = []
    for b in beneficiarios:
        results.append({
            'beneficiarioDNI': b.dni,
            'beneficiarioNombre': b.nombre,
            'beneficiarioApellido': b.apellido
        })

    return render(request, 'polls/index.html')


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
    departamento = forms.CharField(max_length=128)

    # entrevista efectiva o no
    entrevista_efectiva = forms.ChoiceField(choices=ENTREVISTA_EFECTIVA_CHOICES,
                                            help_text="Elija Si si la entrevista se puede completar, o alguna de "
                                                      "las razones si no se puede completar.")
    observaciones = forms.CharField(label='Observaciones (opcional)', widget=forms.Textarea, max_length=256)


# Vista para agregar un beneficiario
def beneficiario(request):
    if request.method == "POST":
        # get all
        # if validation fails, re-render view.
        try:
            dni = int(request.POST['dni'])
            nombre = request.POST['nombre']
            apellido = request.POST['apellido']
            direccion = request.POST['direccion']
            observaciones = request.POST.get('observaciones', '')

            if dni < 100000 or dni > 999999999 or len(nombre) < 3 or len(apellido) < 3:
                raise ValueError()

            Beneficiario.objects.create(
                usuario=request.user,
                dni=dni,
                nombre=nombre,
                apellido=apellido,
                direccion=direccion,
                observaciones=observaciones
            )
            return HttpResponseRedirect(reverse('polls:index'))

        except (KeyError, ValueError):
            return render(request, 'polls/beneficiario.html', {
                'error': 'Los datos no son válidos. Verifique nombre, apellido y DNI.',
            })

    elif request.method == "GET":
        form = AgregarBeneficiarioForm()

        return render(request, 'polls/beneficiario.html', {'form': form})


def detail(request, dni, question_id):
    beneficiario = get_object_or_404(Beneficiario, dni=dni)

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

    context = {
        'dni': dni,
        'question': question,
        'has_answer': False,
        'answer_index': 0,
        'question_index': question_id,
        'question_max': len(questions),
        'question_percent': int((question_id+1)/len(questions) * 100),
        'is_last': question_id == len(questions) - 1,
        'is_first': question_id == 0,
        'prev_question_id': question_id - 1,
        'col_size': col_size,
        'is_image': is_image
    }

    try:
        answer = Answer.objects.get(user=request.user, beneficiario=beneficiario, question=question)
        context['has_answer'] = True
        context['answer_index'] = answer.choice
        logger.info("found answer for such question: " + str(answer.choice))
    except Answer.DoesNotExist:
        logger.info("can't find answer")

    return render(request, 'polls/detail.html', context)


def results(request, dni, question_id):
    beneficiario = get_object_or_404(Beneficiario, dni=dni)
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'polls/results.html', {'question': question})


def vote(request, dni, question_id):
    beneficiario = get_object_or_404(Beneficiario, dni=dni)
    questions = list(Question.objects.all())
    if question_id < 0 or question_id >= len(questions):
        return Http404("invalid question index: " + question_id)

    question = questions[question_id]

    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    try:
        selected_choice = request.POST['choice']
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
        answer.save()

        logger.info("Selected choice: user " + request.user.username +
                    " question " + question.question_text +
                    " choice: " + selected_choice)

        if question_id + 1 < len(questions):  # redirect to next question
            return HttpResponseRedirect(reverse('polls:detail', args=(dni, question_id + 1,)))
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
