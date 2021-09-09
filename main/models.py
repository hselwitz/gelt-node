from django.db import models


class Block(models.Model):
    index = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    transactions = models.CharField(max_length=255)
    proof = models.IntegerField()
    previous_hash = models.CharField(max_length=255)

    def __repr__(self):
        return str("Block #" + str(self.index))

    @classmethod
    def chain(cls):
        return cls.objects.all().order_by("-id")

    @classmethod
    def last_block(cls):
        return cls.objects.all().order_by("-id")[0]


class Transaction(models.Model):
    sender_name = models.CharField(max_length=255, blank=True)
    sender_public_key = models.TextField()
    recipient_name = models.CharField(max_length=255, blank=True)
    recipient_public_key = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    amount = models.IntegerField()
    signature = models.CharField(max_length=255)
    validated = models.BooleanField(default=False)

    def __repr__(self):
        return (
            str(self.amount)
            + " Gelt from "
            + self.sender_name
            + " to "
            + self.recipient_name
            + " on "
            + str(self.timestamp)
        )

    @classmethod
    def unvalidated_transactions(cls):
        return cls.objects.filter(validated=False)


class Node(models.Model):
    url = models.CharField(max_length=255)
    date_registered = models.DateTimeField(auto_now_add=True)

    def __repr__(self):
        return str(self.url)

    @classmethod
    def unique_nodes(cls) -> list:
        nodes = list(set([node.url for node in cls.objects.all()]))

        return nodes
