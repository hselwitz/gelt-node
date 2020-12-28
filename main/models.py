from django.db import models


class Transaction(models.Model):
    sender = models.CharField(max_length=255)
    recipient = models.CharField(max_length=255)
    amount = models.IntegerField()

    def __str__(self):
        return str(self.sender) + " to " + str(self.recipient) + " for " + str(self.amount)

    @staticmethod
    def get_last_transaction(self):
        # Returns the last transaction in the chain
        return self.objects.all().order_by('id')[-1]


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
        return Block.objects.all()

    @staticmethod
    def get_last_block():
        # Returns the last block in the chain
        return Block.objects.all().order_by('id')[-1]

