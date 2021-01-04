import hashlib
import json
from urllib.parse import urlparse

import cryptography
from django.core import serializers

from main.crypto import verify
from .models import Block, Transaction, Node


class SignatureError(Exception):
    pass


def create_hash(*args: dict) -> str:
    item_string = ""
    for i in args:
        item_string += json.dumps(i, sort_keys=True)

    item_string = item_string.encode()

    return hashlib.sha256(item_string).hexdigest()


def create_new_block(proof: int) -> Block:
    last_block = Block.get_last_block()
    serialized_block = serializers.serialize("json", [last_block])
    previous_hash = create_hash(serialized_block)

    unvalidated_transactions = Transaction.get_unvalidated_transactions()

    transactions_to_validate = []
    for t in unvalidated_transactions:
        transactions_to_validate.append(t[0])

    block = Block.objects.create(
        index=last_block.index + 1,
        transactions=transactions_to_validate,
        proof=proof,
        previous_hash=previous_hash,
    )

    unvalidated_transactions.update(validated=True)

    return block


def create_new_transaction(
        sender_name: str,
        sender_public_key: str,
        recipient_name: str,
        recipient_public_key: str,
        amount: int,
        signature: str,
) -> Transaction:
    transaction_data = {"sender_public_key": sender_public_key,
                        "recipient_public_key": recipient_public_key, "amount": amount}

    new_transaction = Transaction.objects.create(
        sender_name=sender_name,
        sender_public_key=sender_public_key,
        recipient_name=recipient_name,
        recipient_public_key=recipient_public_key,
        amount=amount,
        signature=signature,
    )

    return new_transaction

    # TODO: validate


def validate_transaction(public_key: str, signature: str, message: dict):
    """verify signature with public key"""
    try:
        verify(public_key, signature, message)
    except cryptography.exceptions.InvalidSignature:
        raise SignatureError

    # TODO: and is unique


def proof_of_work(last_proof: int) -> int:
    proof = 0
    while validate_proof(last_proof, proof) is False:
        proof += 1

    return proof


def validate_proof(last_proof: int, proof: int) -> bool:
    """Validates the proof, hash must contain four leading zeros"""

    guess = f"{last_proof}{proof}".encode()
    guess_hash = hashlib.sha256(guess).hexdigest()
    return guess_hash[:4] == "0000"


def register_node(address: str) -> None:
    Node.objects.create(url=urlparse(address).netloc)


def validate_blockchain() -> bool:
    pass


def resolve_conflicts() -> bool:
    pass
