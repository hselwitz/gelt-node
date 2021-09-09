import hashlib
import json
from copy import deepcopy

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
from main.models import Block, Transaction, Node


class SignatureError(Exception):
    pass


class BlockchainError(Exception):
    pass


def create_hash(*args: dict) -> str:
    """Hash transaction data."""
    item_string = ""
    for i in args:
        item_string += json.dumps(i, sort_keys=True)

    item_string = item_string.encode()

    return hashlib.sha256(item_string).hexdigest()


def hash_last_block() -> str:
    """Hash most recent block."""
    last_block = model_to_dict(Block.last_block())
    last_block.pop("id")
    previous_hash = create_hash(last_block)

    return previous_hash


def create_new_block(proof: int) -> Block:
    """Create new block and validate outstanding transactions."""
    previous_hash = hash_last_block()
    unvalidated_transactions = Transaction.unvalidated_transactions()
    transactions_to_validate = list(
        unvalidated_transactions.values("sender_name", "recipient_name", "timestamp", "amount")
    )

    block = Block.objects.create(
        index=Block.last_block().index + 1,
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
    """Validate transaction data and post to transaction database."""
    transaction_data = {
        "sender_public_key": sender_public_key,
        "recipient_public_key": recipient_public_key,
        "amount": int(amount),
    }

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
    """Sign transaction with private key."""
    transaction_data = {
        "sender_public_key": sender_public_key,
        "recipient_public_key": recipient_public_key,
        "amount": amount,
    }
    signature = bytes_sig_to_str(sign(private_key, transaction_data))

    return signature


def validate_transaction(public_key: str, signature: str, message: dict):
    """Verify signature with public key."""
    signature = str_sig_to_bytes(signature)
    public_key = deserialize_str_key(public_key)

    try:
        verify(public_key, signature, message)
    except cryptography.exceptions.InvalidSignature:
        raise SignatureError


def proof_of_work(previous_hash: str) -> int:
    """Find valid proof with mining function."""
    proof = 0
    while validate_proof(previous_hash, proof) is False:
        proof += 1

    return proof


def validate_proof(previous_hash: str, proof: int) -> bool:
    """Validate the proof if hash contains four leading zeros."""
    guess = f"{previous_hash}{proof}".encode()
    guess_hash = hashlib.sha256(guess).hexdigest()
    return guess_hash[:4] == "0000"


def validate_blockchain(blockchain: list) -> bool:
    """Confirm if all proofs and hashes are valid for a given blockchain."""
    blockchain = deepcopy(list(reversed(blockchain)))

    # validate proofs
    for block in range(1, len(blockchain) - 1):
        if not validate_proof(blockchain[block]["previous_hash"], blockchain[block]["proof"]):
            raise BlockchainError("Invalid proof")

    # validate hashes
    for block in range(0, len(blockchain) - 1):
        blockchain[block].pop("timestamp")
        if create_hash(blockchain[block]) != blockchain[block + 1]["previous_hash"]:
            raise BlockchainError("Invalid hash")

    return True


def propagate_node(new_node: str):
    """Register a given node url with all known existing nodes."""
    for url in list(Node.objects.all().values_list("url", flat=True))[:-1]:
        try:
            requests.post(url + r"/registernodenoprop/", data={url: new_node})
        except requests.exceptions.ConnectionError:
            print("Could not reach node at " + url + " to share new node")


def broadcast_new_block() -> None:
    """Alert all known nodes of a new block. Other nodes will download the blockchain, validate,
    and replace their version if needed."""
    for url in list(Node.objects.all().values_list("url", flat=True)):
        try:
            requests.post(url + r"/broadcastnewblock/")
        except requests.exceptions.ConnectionError:
            print("Could not reach node at " + url + " to broadcast new block")


def download_blockchains() -> list:
    """Download all blockchains from known nodes."""
    blockchains = []
    nodes = Node.unique_nodes()
    for node in nodes:
        try:
            r = requests.get(node + "/blockchain/").json()
        except requests.exceptions.ConnectionError:
            print("Could not reach node at " + node + " to download its blockchain")
        else:
            blockchains.append(r)

    return blockchains


def resolve_conflicts() -> None:
    """Validate the longest known node and if valid replace local blockchain."""
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
            Block.objects.create(
                index=block["index"],
                timestamp=block["timestamp"],
                transactions=block["transactions"],
                proof=block["proof"],
                previous_hash=block["previous_hash"],
            )
