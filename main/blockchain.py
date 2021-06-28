import hashlib
import json

import cryptography
import requests
from django.forms.models import model_to_dict

from main.crypto import (
    verify,
    str_sig_to_bytes,
    deserialize_str_key,
    bytes_sig_to_str,
    sign,
)
from .models import Block, Transaction, Node


class SignatureError(Exception):
    pass


class BlockchainError(Exception):
    pass


def create_hash(*args: dict) -> str:
    """hashes transaction data"""

    item_string = ""
    for i in args:
        item_string += json.dumps(i, sort_keys=True)

    item_string = item_string.encode()

    return hashlib.sha256(item_string).hexdigest()


def create_new_block(proof: int) -> Block:
    last_block = model_to_dict(Block.get_last_block())
    last_block.pop("id", None)
    previous_hash = create_hash(last_block)

    unvalidated_transactions = Transaction.get_unvalidated_transactions()

    transactions_to_validate = []
    for t in unvalidated_transactions:
        transactions_to_validate.append(t[0])

    block = Block.objects.create(
        index=last_block["index"] + 1,
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


def sign_transaction(
    sender_public_key: str, recipient_public_key: str, amount: int, private_key
) -> str:
    transaction_data = {
        "sender_public_key": sender_public_key,
        "recipient_public_key": recipient_public_key,
        "amount": amount,
    }
    signature = bytes_sig_to_str(sign(private_key, transaction_data))

    return signature


def validate_transaction(public_key: str, signature: str, message: dict):
    """verify signature with public key"""

    signature = str_sig_to_bytes(signature)
    public_key = deserialize_str_key(public_key)

    try:
        verify(public_key, signature, message)
    except cryptography.exceptions.InvalidSignature:
        raise SignatureError

    # TODO: and is unique


def proof_of_work(last_proof: int) -> int:
    """mining function to find valid proof"""

    proof = 0
    while validate_proof(last_proof, proof) is False:
        proof += 1

    return proof


def validate_proof(last_proof: int, proof: int) -> bool:
    """Validates the proof, hash must contain four leading zeros"""

    guess = f"{last_proof}{proof}".encode()
    guess_hash = hashlib.sha256(guess).hexdigest()
    return guess_hash[:4] == "0000"


def register_node(node_address: str, url_to_register: str) -> None:
    headers = {"Referer": url_to_register}
    requests.post(node_address, headers=headers)


def export_blockchain() -> list:
    bc = list(Block.chain().values())
    bc = [{k: v for k, v in d.items() if k != "timestamp"} for d in bc]
    return bc


def validate_blockchain(blockchain: list) -> bool:
    # validate proofs
    for block in range(0, len(blockchain) - 1):
        if not validate_proof(blockchain[block]["proof"], blockchain[block + 1]["proof"]):
            raise BlockchainError(
                "Invalid proof", block, blockchain[block]["proof"], blockchain[block + 1]["proof"]
            )

    # validate hashes
    for block in range(0, len(blockchain) - 2):
        if (
            create_hash(blockchain[block].pop("timestamp", None))
            != blockchain[block + 1]["previous_hash"]
        ):
            raise BlockchainError("Invalid hash")

    return True


def propagate_node(new_node: str):
    for url in list(Node.objects.all().values_list("url", flat=True))[:-1]:
        try:
            r = requests.post(url + r"/registernodenoprop/", data={url: new_node})
            print(r.text)
            print(url + r"/registernodenoprop/")
        except requests.exceptions.ConnectionError:
            print("Could not reach node at " + url + " to share new node")


def download_blockchains() -> list:
    """downloads all blockchains from known nodes"""

    blockchains = []
    nodes = Node.get_unique_nodes()
    for node in nodes:
        try:
            r = requests.get(node + "/chain/").json()
        except requests.exceptions.ConnectionError:
            print("Could not reach node at " + node + " to download its blockchain")
        else:
            blockchains.append(r)

    return blockchains


def resolve_conflicts() -> None:
    """validates the longest known node and if valid replaces local blockchain"""

    local_chain_length = Block.objects.count()
    blockchains = download_blockchains()
    longest_bc = max(blockchains, key=len)
    longest_bc_length = len(longest_bc)

    if longest_bc_length > local_chain_length:
        try:
            validate_blockchain(longest_bc)
        except BlockchainError:
            raise BlockchainError("Invalid blockchain on foreign node, please remove the node.")

        Block.objects.all().delete()

        for block in longest_bc:
            Block(
                index=block["index"],
                timestamp=block["timestamp"],
                transactions=block["transactions"],
                proof=block["proof"],
                previous_hash=block["previous_hash"],
            ).save()
