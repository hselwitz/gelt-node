import requests
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import generics
from rest_framework.decorators import api_view

from .blockchain import (
    create_new_block,
    create_new_transaction,
    proof_of_work,
    sign_transaction,
    SignatureError,
    propagate_node,
)
from .crypto import (
    read_private_key,
    read_public_key,
    key_to_str,
)
from .models import Block, Transaction, Node
from .serializers import ChainSerializer, TransactionSerializer

NODE_PUBLIC_KEY = read_public_key()
NODE_PRIVATE_KEY = read_private_key()
NODE_NAME = "H"


def index(request):
    return render(request, "main/index.html")


class Chain(generics.ListCreateAPIView):
    queryset = Block.objects.all()
    serializer_class = ChainSerializer


class Transactions(generics.ListCreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


@api_view(["POST"])
def register_node(request):
    address = request.POST.get("url")
    # url = urlparse(address).netloc

    # reject already registered node
    if address not in Node.objects.all().values_list("url", flat=True):
        Node.objects.create(url=address)
        propagate_node(address)
    else:
        return JsonResponse("Node already registered at " + address, safe=False)

    return JsonResponse("Registered node at " + address, safe=False)


@api_view(["POST"])
def mine(request):
    if request.method == "POST":
        # Get next proof
        last_block = Block.get_last_block()
        last_proof = last_block.proof
        proof = proof_of_work(last_proof)

        # signature for new block
        signature = sign_transaction(
            sender_public_key=key_to_str(NODE_PUBLIC_KEY),
            recipient_public_key=key_to_str(NODE_PUBLIC_KEY),
            amount=1,
            private_key=NODE_PRIVATE_KEY,
        )

        # reward to self for forging new block
        create_new_transaction(
            sender_name="Gelt",
            sender_public_key=key_to_str(NODE_PUBLIC_KEY),
            recipient_name=NODE_NAME,
            recipient_public_key=key_to_str(NODE_PUBLIC_KEY),
            amount=1,
            signature=signature,
        )

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

    required = [
        "sender_name",
        "sender_public_key",
        "recipient_name",
        "recipient_public_key",
        "amount",
        "signature",
    ]
    if not all(k in values for k in required):
        return JsonResponse("Missing values", safe=False)

    try:
        create_new_transaction(
            values["sender_name"],
            values["sender_public_key"],
            values["recipient_name"],
            values["recipient_public_key"],
            values["amount"],
            values["signature"],
        )
    except SignatureError:
        return JsonResponse("Invalid signature detected. Transaction denied.", safe=False)

    new_index = Block.get_last_block().index + 1
    response = {"message": f"Transaction will be added to Block {new_index}"}

    return JsonResponse(response)
