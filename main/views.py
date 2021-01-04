from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import generics
from rest_framework.decorators import api_view

from .blockchain import create_new_block, create_new_transaction, proof_of_work, SignatureError
from .crypto import read_private_key, read_public_key
from .models import Block, Transaction
from .serializers import ChainSerializer, TransactionSerializer

NODE_PUBLIC_KEY = read_public_key()
NODE_PRIVATE_KEY = read_private_key()


def index(request):
    return render(request, "main/index.html")


class Chain(generics.ListCreateAPIView):
    queryset = Block.objects.all()
    serializer_class = ChainSerializer


class Transactions(generics.ListCreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


@api_view(["POST"])
def mine(request):
    if request.method == "POST":
        # Get next proof
        last_block = Block.get_last_block()
        last_proof = last_block.proof
        proof = proof_of_work(last_proof)

        # Reward
        create_new_transaction(sender_name="Gelt", sender_public_key=NODE_PUBLIC_KEY,
                               recipient_name='Gelt', recipient_public_key=NODE_PUBLIC_KEY,
                               amount=1, signature="")

        # Forge new block by adding it to the chain
        new_block = create_new_block(proof)

        response = {
            "message": "New block forged",
            "index": new_block.index,
            "transactions": new_block.transactions,
            "proof": new_block.proof,
            "previous_hash": new_block.previous_hash,
        }

        return JsonResponse(response)


@api_view(["POST"])
def new_transaction(request):
    values = request.POST

    required = ["sender_name", "sender_public_key", "recipient_name", "recipient_public_key",
                "amount", "signature"]
    if not all(k in values for k in required):
        return JsonResponse("Missing values", 400)

    try:
        create_new_transaction(
            values["sender_name"], values["sender_public_key"], values["recipient_name"],
            values["recipient_public_key"], values["amount"], values["signature"]
        )
    except SignatureError:
        return JsonResponse("Invalid signature detected. Transaction denied.")

    new_index = Block.get_last_block().index + 1
    response = {"message": f"Transaction will be added to Block {new_index}"}

    return JsonResponse(response)
