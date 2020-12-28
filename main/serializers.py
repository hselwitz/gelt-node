from rest_framework import serializers
from .models import Block


class ChainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = ['index', 'timestamp', 'transactions', 'proof', 'previous_hash']
