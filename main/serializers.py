from rest_framework import serializers

from .models import Block, Transaction


class ChainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = ["index", "timestamp", "transactions", "proof", "previous_hash"]


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["sender", "recipient", "timestamp", "amount", "hash", "validated"]
