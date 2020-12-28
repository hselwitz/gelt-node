import hashlib
import json

from .models import Block, Transaction


class Blockchain():
    def __init__(self):
        self.chain = Block.chain()
        self.current_transactions = []

    def new_block(self, proof: int, previous_hash: str = None) -> dict:
        """
        Create a new Block in the Blockchain
        proof: The proof given by the Proof of Work algorithm
        previous_hash: (Optional) Hash of previous Block
        return: New Block
        """
        chain = Block.chain()

        Block.objects.create(index=len(chain) + 1, transactions=self.current_transactions,
                             proof=proof,
                             previous_hash=previous_hash or self.create_hash(chain[-1]))

        # Reset the current list of transactions
        self.current_transactions = []

        return Block.get_last_block()

    def new_transaction(self, sender: str, recipient: str, amount: int) -> int:
        """
        Creates a new transaction to go into the next mined Block
        sender: Address of the Sender
        recipient: Address of the Recipient
        amount: Amount
        return:  The index of the Block that will hold this transaction
        """

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        Transaction.objects.create(sender=sender, recipient=recipient, amount=amount)

        return Block.get_last_block()


def create_hash(block: dict) -> str:
    """
    Creates a SHA-256 hash of a Block
    block: Block
    return: Hash
    """

    # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
    block_string = json.dumps(block, sort_keys=True).encode()
    return hashlib.sha256(block_string).hexdigest()


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
