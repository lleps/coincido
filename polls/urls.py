from django.conf.urls import url
from django.urls import path
from django.contrib.auth import login, logout

from . import views as app_views

app_name = 'polls'
urlpatterns = [
    path('', app_views.IndexView.as_view(), name='index'),
    path('signup/', app_views.SignUpView.as_view(), name='signup'),
    path('<int:pk>/', app_views.DetailView.as_view(), name='detail'),
    path('<int:pk>/results/', app_views.ResultsView.as_view(), name='results'),
    path('<int:question_id>/vote/', app_views.vote, name='vote'),
]