from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.http import Http404
from django.template import loader
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.contrib.auth.views import LoginView

from .models import Question, Choice, Answer

import logging

logger = logging.getLogger('polls')


def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    questions = list(Question.objects.all())
    answers = list(Answer.objects.filter(user=request.user))

    # find the first question not answered
    min_non_answered_index = 0
    for q in questions:
        responded = False
        for a in answers:
            if a.question.id == q.id:
                responded = True
                break

        if not responded:
            break

        min_non_answered_index += 1

    context = {
        'latest_question_index': min_non_answered_index,
        'has_completed_poll': min_non_answered_index == len(questions)
    }
    return render(request, 'polls/index.html', context)


class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'


def detail(request, question_id):
    questions = list(Question.objects.all())
    if question_id < 0 or question_id >= len(questions):
        raise Http404("invalid question index: " + str(question_id))

    question = questions[question_id]

    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    context = {
        'question': question,
        'has_answer': False,
        'answer_index': 0,
        'question_index': question_id,
        'question_max': len(questions)
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
