from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.http import Http404
from django.template import loader
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.contrib.auth.views import LoginView

from .models import Question, Choice, Answer, Profile, AppConfig, Beneficiario

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


def get_first_unanswered_question_index(user, questions):
    """Returns the index of the first non answered question, or
    -1 if has answered everything"""

    answers = list(Answer.objects.filter(user=user))
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


def gender_preferences_match(user1, user2):
    try:
        profile1 = user1.profile
        profile2 = user2.profile
        return profile1.gender == profile2.gender_preference and profile2.gender == profile1.gender_preference
    except:
        return False


# index. Si completo tod0 le muestra resultados, si no, le da un boton para responder.
# como debe ser ahora:
# - Tener un boton para "agregar" sobre un nuevo beneficiario.
#   "Registrar beneficiario". Que te envie a la "creacion" de un beneficiario.
#   En esa creacion te diga: DNI, Nombre, etc.
#   Entonces vos podrias ver que beneficiarios tenias registrados a tu usuario.
#   Y desde ahi te dice:
#      Beneficiario 12423424 (Asd_Asd)
#               FORMULARIO COMPLETADO ((o te diga: FORMULARIO NO COMPLETADO. COMPLETAR)).
# Esto es trabajar en la capa: CARGADO DE DATOS POR MUNICIPIOS.

def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    # Renderizar sólo beneficiarios registrados a mi nombre.
    # Debo buscar un array de: { beneficiarioDNI, beneficiarioNombre, beneficiarioApellido, completoEncuestaONo }
    # Si no es asi, llevarme

    # Esta logica se debe mover abajo.
    # Entonces: Dos cosas.
    # - Lista de beneficiarios
    # Boton de agregar nuevo beneficiario
    # En la UI.

    # esto moverlo abajo.
    questions = list(Question.objects.all())
    unanswered = get_first_unanswered_question_index(request.user, questions)
    users = list(User.objects.all())
    has_completed_poll = unanswered == -1

    beneficiarios = Beneficiario.objects.filter(usuario=request.user)
    results = []  # lista de { beneficiarioDNI, beneficiarioNombre, beneficiarioApellido, completoEncuestaONo }
    for b in beneficiarios:
        results.append({
            'beneficiarioDNI': b.dni,
            'beneficiarioNombre': b.nombre,
            'beneficiarioApellido': b.apellido,
            'completoEncuesta': False,
        })

    context = {
        'result': results
    }

    return render(request, 'polls/index.html', context)


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


def detail(request, question_id):
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
        answer = Answer.objects.get(user=request.user, question=question)
        context['has_answer'] = True
        context['answer_index'] = answer.choice
        logger.info("found answer for such question: " + str(answer.choice))
    except Answer.DoesNotExist:
        logger.info("can't find answer")

    return render(request, 'polls/detail.html', context)


def results(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'polls/results.html', {'question': question})


def vote(request, question_id):
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
            answer = Answer.objects.get(user=request.user, question=question)
        except Answer.DoesNotExist:
            answer = Answer.objects.create(user=request.user, question=question)

        answer.choice = selected_choice
        answer.save()

        logger.info("Selected choice: user " + request.user.username +
                    " question " + question.question_text +
                    " choice: " + selected_choice)

        if question_id + 1 < len(questions):  # redirect to next question
            return HttpResponseRedirect(reverse('polls:detail', args=(question_id + 1,)))
        else:  # no more questions, redirect to home
            return HttpResponseRedirect(reverse('polls:index'))


def profile(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    if request.method == "GET":
        context = {
            'gender': 'M',
            'gender_preference': 'F'
        }
        try:
            p = request.user.profile
            context['gender'] = p.gender
            context['gender_preference'] = p.gender_preference
        except:  # ignore, set to defaults
            pass

        logger.info("context is " + str(context))
        return render(request, 'polls/profile.html', context)
    elif request.method == "POST":

        # make the profile for this user
        try:
            profile = Profile.objects.get(user=request.user)

        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=request.user)


        profile.gender = request.POST['gender']
        profile.gender_preference = request.POST['gender_preference']
        profile.save()

        logger.warning("g")

        return HttpResponseRedirect(reverse('polls:index'))

