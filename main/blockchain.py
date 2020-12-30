import hashlib
import json

from django.core import serializers

from .models import Block, Transaction


def create_hash(*args: dict) -> str:
    item_string = ""
    for i in args:
        item_string += json.dumps(i, sort_keys=True)

    item_string = item_string.encode()

    return hashlib.sha256(item_string).hexdigest()


def create_new_block(proof: int):
    last_block = Block.get_last_block()
    serialized_block = serializers.serialize('json', [last_block])
    previous_hash = create_hash(serialized_block)

    unvalidated_transactions = Transaction.get_unvalidated_transactions()

    transactions_to_validate = []
    for t in unvalidated_transactions:
        transactions_to_validate.append(t[0])

    block = Block.objects.create(index=last_block.index + 1, transactions=transactions_to_validate,
                                 proof=proof,
                                 previous_hash=previous_hash)

    unvalidated_transactions.update(validated=True)

    return block


def create_new_transaction(sender: str, recipient: str, amount: int) -> None:
    last_transaction = Transaction.get_last_transaction()
    serialized_transaction = serializers.serialize('json', [last_transaction])
    previous_hash = create_hash(serialized_transaction)

    Transaction.objects.create(sender=sender, recipient=recipient, previous_hash=previous_hash,
                               amount=amount)


def proof_of_work(last_proof: int) -> int:
    """
    Simple Proof of Work Algorithm:
     - Find a number p' such that hash(pp') contains leading 4 zeroes, where p is the previous p'
     - p is the previous proof, and p' is the new proof
    """

    proof = 0
    while validate_proof(last_proof, proof) is False:
        proof += 1

    return proof


def validate_proof(last_proof: int, proof: int) -> bool:
    """
    Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeroes?
    last_proof: <int> Previous Proof
    proof: Current Proof
    return: True if correct, False if not.
    """

    guess = f'{last_proof}{proof}'.encode()
    guess_hash = hashlib.sha256(guess).hexdigest()
    return guess_hash[:4] == "0000"


def validate_transaction():
    pass
