from django.conf.urls import url
from django.urls import path
from django.contrib.auth import login, logout

from . import views as app_views

app_name = 'polls'
urlpatterns = [
    path('', app_views.index, name='index'),
    path('signup/', app_views.SignUpView.as_view(), name='signup'),
    path('<int:question_id>/', app_views.detail, name='detail'),
    path('<int:question_id>/results/', app_views.results, name='results'),
    path('<int:question_id>/vote/', app_views.vote, name='vote'),
    path('profile/', app_views.profile, name='profile'),
]