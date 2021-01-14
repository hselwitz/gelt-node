import hashlib
import json
from urllib.parse import urlparse

import cryptography
from django.core import serializers
from django.http import JsonResponse

from main.crypto import verify, str_sig_to_byes, deserialize_str_key
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
    # TODO: create hash from dict object

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
    transaction_data = {
        "sender_public_key": sender_public_key,
        "recipient_public_key": recipient_public_key,
        "amount": int(amount),
    }

    print(transaction_data)

    validate_transaction(sender_public_key, signature, transaction_data)

    new_transaction = Transaction.objects.create(
        sender_name=sender_name,
        sender_public_key=sender_public_key,
        recipient_name=recipient_name,
        recipient_public_key=recipient_public_key,
        amount=amount,
        signature=signature,
    )

    return new_transaction


def validate_transaction(public_key: str, signature: str, message: dict):
    """verify signature with public key"""

    signature = str_sig_to_byes(signature)
    public_key = deserialize_str_key(public_key)

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


shain = [
    {
        "index": 29,
        "timestamp": "2021-01-06T07:13:48.635044Z",
        "transactions": "",
        "proof": 161606,
        "previous_hash": "01f4d41dafe08a9209588bea8df4e470bdfc7269bde4dc48dde69e79c6ea5cc6"
    },
    {
        "index": 28,
        "timestamp": "2021-01-06T06:54:40.265904Z",
        "transactions": "",
        "proof": 98615,
        "previous_hash": "629d36dca05b9f4827ee438f77eb8f4791ff53f813bba4a6d89b76105c5fdf93"
    },
    {
        "index": 27,
        "timestamp": "2021-01-06T06:53:43.365587Z",
        "transactions": "",
        "proof": 30034,
        "previous_hash": "95b16cebcaf69478d23b065fa20c71f4687d0bdd77cad9540217bca8a6ff3bb3"
    },
    {
        "index": 26,
        "timestamp": "2021-01-06T06:03:41.328301Z",
        "transactions": "",
        "proof": 159963,
        "previous_hash": "d0f590f980e2377d20776bd60704b8ebe634a0d8f2f8bd37bdbd6187c006f6cd"
    },
]


def validate_blockchain(blockchain) -> bool:
    for b in range(0, len(blockchain) - 1):
        # validate proofs
        if not validate_proof(blockchain[b + 1].proof, blockchain[b].proof):
            return False

        # validate hashes
        if blockchain[b]['previous_hash'] != create_hash(blockchain[b + 1]):
            return False

        # print(blockchain[b]['previous_hash'] == create_hash(blockchain[b + 1]))
        # print(blockchain[b]['previous_hash'])
        # print(create_hash(blockchain[b + 1]))

    return True


def resolve_conflicts() -> bool:
    pass
