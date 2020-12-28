from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('mine/', views.mine, name='index'),
    path('transactions/new/', views.new_transaction, name='new_transaction'),
    path('chain/', views.Chain.as_view()),
]
