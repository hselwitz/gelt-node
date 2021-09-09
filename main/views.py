import os

from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import generics
from rest_framework.decorators import api_view

from main.blockchain import (
    create_new_block,
    create_new_transaction,
    hash_last_block,
    proof_of_work,
    propagate_node,
    resolve_conflicts,
    sign_transaction,
    SignatureError,
)
from main.crypto import (
    generate_key_pair,
    key_to_str,
    read_private_key,
    read_public_key,
)
from main.models import Block, Transaction, Node
from main.serializers import ChainSerializer, TransactionSerializer

if not (os.path.isfile(r"main/private_key.pem") and os.path.isfile(r"main/public_key.pem")):
    generate_key_pair()

NODE_PUBLIC_KEY = read_public_key()
NODE_PRIVATE_KEY = read_private_key()

NODE_NAME = "H"


def index(request):
    return render(request, "main/index.html")


class Chain(generics.ListAPIView):
    """Provide blockchain view."""
    queryset = Block.chain()
    serializer_class = ChainSerializer


class Transactions(generics.ListAPIView):
    """Provide transactions view."""
    queryset = reversed(Transaction.objects.all())
    serializer_class = TransactionSerializer


def register_node(request, propagate: bool):
    """Register new node locally and optionally share with with all known nodes."""
    node_address = next(request.POST.values())

    # reject previously registered nodes
    if node_address not in Node.objects.all().values_list("url", flat=True):
        Node.objects.create(url=node_address)
        if propagate:
            propagate_node(node_address)
    else:
        return JsonResponse("Node already registered at " + node_address, safe=False)

    return JsonResponse("Registered node at " + node_address, safe=False)


@api_view(["POST"])
def register_node_no_propagate(request):
    """Register node locally without sharing with other nodes"""
    return register_node(request, False)


@api_view(["POST"])
def register_node_propagate(request):
    """Register node locally and share with other nodes"""
    return register_node(request, True)


@api_view(["POST"])
def broadcast_new_block(request):
    """Prompt nodes to download new block data"""
    resolve_conflicts()
    return JsonResponse("Blockchains synced", safe=False)


@api_view(["POST"])
def mine(request):
    """Mine for next block."""
    # Get next proof
    previous_hash = hash_last_block()
    proof = proof_of_work(previous_hash)

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

    # share new block with all known nodes
    resolve_conflicts()

    return JsonResponse(response)


@api_view(["POST"])
def new_transaction(request):
    """Post new transaction to node."""
    values = request.POST

    required = [
        "sender_name",
        "sender_public_key",
        "recipient_name",
        "recipient_public_key",
        "amount",
        "signature",
    ]
    if not all(value in values for value in required):
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

    new_index = Block.last_block().index + 1
    response = {"message": f"Transaction will be added to Block {new_index}"}

    return JsonResponse(response)
