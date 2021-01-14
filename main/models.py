from django.db import models


class Block(models.Model):
    index = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    transactions = models.CharField(max_length=255)
    proof = models.IntegerField()
    previous_hash = models.CharField(max_length=255)

    def __str__(self):
        return str(self.proof)

    @staticmethod
    def chain():
        return Block.objects.all().order_by("-id")

    @staticmethod
    def get_last_block():
        return Block.objects.all().order_by("-id")[0]


class Transaction(models.Model):
    sender_name = models.CharField(max_length=255, blank=True)
    sender_public_key = models.TextField()
    recipient_name = models.CharField(max_length=255, blank=True)
    recipient_public_key = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    amount = models.IntegerField()
    signature = models.CharField(max_length=255)
    validated = models.BooleanField(default=False)

    def __str__(self):
        return self.signature

    @staticmethod
    def get_last_transaction():
        return Transaction.objects.all().order_by("-id")[0]

    @staticmethod
    def get_unvalidated_transactions():
        return Transaction.objects.filter(validated=False).values_list("signature")


class Node(models.Model):
    url = models.CharField(max_length=255)
    date_registered = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.url)

    @staticmethod
    def get_set_of_nodes():
        return set(Node.objects.all())
