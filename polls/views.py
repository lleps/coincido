from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse, HttpResponseRedirect
from django.http import Http404
from django.template import loader
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.contrib.auth.views import LoginView

from .models import Question, Choice, Answer

import logging

logger = logging.getLogger('polls')


class DetailView(generic.DetailView):
    model = Question
    template_name = 'polls/detail.html'


def index(request):
    # ok. entonces aca tengo que:
    # has_completed_poll: booleano si ya completo todas las polls.
    # last_poll_index: indice de poll que tiene que contestar
    latest_question_list = Question.objects.order_by('-pub_date')[:5]
    context = {'latest_question_list': latest_question_list}
    return render(request, 'polls/index.html', context)


class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'


def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    context = {
        'question': question,
        'has_answer': False,
        'answer_index': 0,
        'question_index': Question.objects.all().count()
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
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = request.POST['choice']
    except (KeyError, Choice.DoesNotExist):
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

        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))
