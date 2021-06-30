from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("mine/", views.mine, name="mine"),
    path("transactions/", views.Transactions.as_view()),
    path("transactions/new/", views.new_transaction, name="new_transaction"),
    path("blockchain/", views.Chain.as_view()),
    path("registernode/", views.register_node_propagate, name="register_node_propagate"),
    path(
        "registernodenoprop/", views.register_node_no_propagate, name="register_node_no_propagate"
    ),
    path("broadcastnewblock/", views.broadcast_new_block, name="broadcast_new_block"),
]
