from django.core import serializers
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import generics
from rest_framework.decorators import api_view

from .blockchain import Blockchain, proof_of_work, create_hash
from .models import Block, Transaction
from .serializers import ChainSerializer

NODE_ID = '403c839596bd42cca49c10a71d88bec8'


def index(request):
    return render(request, 'main/index.html')


class Chain(generics.ListCreateAPIView):
    queryset = Block.objects.all()
    serializer_class = ChainSerializer


@api_view(['POST'])
def mine(request):
    if request.method == 'POST':
        # Run the proof of work algorithm to get the next proof
        last_block = Block.get_last_block()
        last_proof = last_block.proof
        proof = proof_of_work(last_proof)

        # Reward for finding the proof
        # The sender is "0" to signify that this node has mined a new coin
        Transaction.objects.create(sender="0", recipient=NODE_ID, amount=1)

        # # Forge the new Block by adding it to the chain
        serialized_block = serializers.serialize('json', [last_block])
        previous_hash = create_hash(serialized_block)
        block = Block.objects.create(index=last_block.index + 1, transactions="", proof=proof,
                                     previous_hash=previous_hash)

        response = {
            "message": "New Block Forged",
            "index": block.index,
            "transactions": block.transactions,
            "proof": block.proof,
            "previous_hash": block.previous_hash,
        }

        return JsonResponse(response)


@api_view(['POST'])
def new_transaction(request):
    values = request.get_json()

    required = ["sender", "recipient", "amount"]
    if not all(k in values for k in required):
        return JsonResponse("Missing values", 400)

    bc = Blockchain()
    bc.new_transaction(values["sender"], values["recipient"], values["amount"])

    new_index = Block.get_last_block()['index']
    response = {"message": f"Transaction will be added to Block {new_index}"}

    return JsonResponse(response)
