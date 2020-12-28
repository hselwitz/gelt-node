from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # path('mine/', views.Mine.as_view()),
    # path('transactions/new/', views.NewTransaction.as_view()),
    path('chain/', views.Chain.as_view()),
]
