import hashlib
import json
from urllib.parse import urlparse

import cryptography
import requests
from django.core import serializers

from .models import Block, Transaction, Node
from main.crypto import verify


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


def create_new_transaction(sender: str, recipient: str, amount: int, signature: str) -> Transaction:
    transaction_details = {"sender": sender, "recipient": recipient, "amount": amount}

    new_transaction = Transaction.objects.create(sender=sender, recipient=recipient, amount=amount,
                                                 signature=signature)

    return new_transaction


def validate_transaction(public_key: str, signature: str):
    """decrypt with public key and ensure given transaction data matches decrypted data"""
    try:
        verify(public_key, signature)
    except cryptography.exceptions.InvalidSignature:
        return "Invalid signature detected. Transaction denied."


def proof_of_work(last_proof: int) -> int:
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

    guess = f"{last_proof}{proof}".encode()
    guess_hash = hashlib.sha256(guess).hexdigest()
    return guess_hash[:4] == "0000"


def register_node(address: str) -> None:
    Node.objects.create(url=urlparse(address).netloc)


def validate_blockchain(blockchain: list) -> bool:
    last_block = blockchain[0]
    current_index = 1

    while current_index < len(blockchain):
        block = blockchain[current_index]
        print(f"{last_block}")
        print(f"{block}")
        print("\n-----------\n")
        # Check that the hash of the block is correct
        if block["previous_hash"] != create_hash(last_block):
            return False

        # Check that the Proof of Work is correct
        if not validate_proof(last_block["proof"], block["proof"]):
            return False

        last_block = block
        current_index += 1

    return True


def resolve_conflicts(self) -> bool:
    """
    This is our Consensus Algorithm, it resolves conflicts
    by replacing our chain with the longest one in the network.
    :return: <bool> True if our chain was replaced, False if not
    """

    neighbours = self.nodes
    new_chain = None

    # We're only looking for chains longer than ours
    max_length = len(self.chain)

    # Grab and verify the chains from all the nodes in our network
    for node in neighbours:
        response = requests.get(f"http://{node}/chain")

        if response.status_code == 200:
            length = response.json()["length"]
            chain = response.json()["chain"]

            # Check if the length is longer and the chain is valid
            if length > max_length and validate_blockchain(chain):
                max_length = length
                new_chain = chain

    # Replace our chain if we discovered a new, valid chain longer than ours
    if new_chain:
        self.chain = new_chain
        return True

    return False
