from django.contrib import admin

from main.models import Block, Transaction, Node


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    pass


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    pass


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    pass
