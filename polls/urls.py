from django.conf.urls import url
from django.urls import path
from django.contrib.auth import login, logout

from . import views as app_views

app_name = 'polls'
urlpatterns = [
    path('', app_views.index, name='index'),
    path('signup/', app_views.SignUpView.as_view(), name='signup'),
    path('beneficiario/', app_views.beneficiario, name='beneficiario'),
    path('resumen/<int:user_index>', app_views.resumen, name='resumen'),
    path('detalle/<int:beneficiario_id>', app_views.detalle, name='detalle'),
    path('familia/<int:pk>/', app_views.familia, name='familia'),
    path('grupofamiliar/<int:pk>/', app_views.grupofamiliar, name='grupofamiliar'),
    path('grupofamiliar_post_conv/<int:pk>/', app_views.grupofamiliar_post_conv, name='grupofamiliar_post_conv'),
    path('grupofamiliar_post_no_conv/<int:pk>/', app_views.grupofamiliar_post_no_conv, name='grupofamiliar_post_no_conv'),
    path('grupofamiliar_terminar/<int:pk>/', app_views.grupofamiliar_terminar, name='grupofamiliar_terminar'),
    path('upload_img/<int:beneficiario_id>/<int:question_id>/', app_views.upload_img, name='upload_img'),
    path('<int:pk>/<int:question_id>/', app_views.detail, name='detail'),
    path('<int:pk>/<int:question_id>/results/', app_views.results, name='results'),
    path('<int:pk>/<int:question_id>/vote/', app_views.vote, name='vote'),
]