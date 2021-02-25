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

from .models import Question, Choice, Answer, Profile, AppConfig

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



def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    # if user has no profile, redirect to the profile to create one
    try:
        request.user.profile
    except:
        return HttpResponseRedirect(reverse('polls:profile'))


    questions = list(Question.objects.all())
    unanswered = get_first_unanswered_question_index(request.user, questions)
    matches = []
    users = list(User.objects.all())
    has_completed_poll = unanswered == -1
    results = []

    if has_completed_poll:
        # compare with every user that finished the poll
        for u in users:
            if get_first_unanswered_question_index(u, questions) != -1:
                continue  # skip users that have not answered everything.

            if not gender_preferences_match(u, request.user):
                continue

            score = 0.0
            max_score = len(questions)
            for q in questions:
                my_answer = find_answer_for_question(request.user, q)
                u_answer = find_answer_for_question(u, q)
                if my_answer == u_answer:
                    score += 1.0

            score = score / max_score * 100.0  # convert score to percent
            results.append({'user': u, 'score': score})

    def take_score(entry):
        return entry['score']

    results.sort(key=take_score, reverse=True)

    context = {
        'latest_question_index': unanswered,
        'has_completed_poll': has_completed_poll,
        'matches': results
    }
    return render(request, 'polls/index.html', context)


class SignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email",)


class SignUpView(generic.CreateView):
    form_class = SignupForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'


def detail(request, question_id):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))


    questions = list(Question.objects.all())
    if question_id < 0 or question_id >= len(questions):
        raise Http404("invalid question index: " + str(question_id))

    question = questions[question_id]

    context = {
        'question': question,
        'has_answer': False,
        'answer_index': 0,
        'question_index': question_id,
        'question_max': len(questions),
        'question_percent': int(question_id/len(questions) * 100)
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

