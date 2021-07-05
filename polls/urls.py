from django.conf.urls import url
from django.urls import path
from django.contrib.auth import login, logout

from . import views as app_views

app_name = 'polls'
urlpatterns = [
    path('', app_views.index, name='index'),
    path('signup/', app_views.SignUpView.as_view(), name='signup'),
    path('beneficiario/', app_views.beneficiario, name='beneficiario'),
    path('resumen/', app_views.resumen, name='resumen'),
    path('familia/<int:pk>/', app_views.familia, name='familia'),
    path('<int:pk>/<int:question_id>/', app_views.detail, name='detail'),
    path('<int:pk>/<int:question_id>/results/', app_views.results, name='results'),
    path('<int:pk>/<int:question_id>/vote/', app_views.vote, name='vote'),
]