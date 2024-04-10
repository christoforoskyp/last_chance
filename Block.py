import hashlib
import time

import rsa

from Transaction import Transaction

def public_key_to_string(public_key):
    if public_key == -1 or public_key == 0:
        return public_key
    public_key_pem = public_key.save_pkcs1(format='PEM').decode('utf-8')
    return public_key_pem


def string_to_public_key(public_key_str):
    if public_key_str == -1 or public_key_str == 0:
        return public_key_str
    public_key_bytes = public_key_str.encode('utf-8')
    public_key = rsa.PublicKey.load_pkcs1(public_key_bytes)
    return public_key

class Block:
    def __init__(self, listOfTransactions, prev_hash, validator, timestamp, index, current_hash):
        self.listOfTransactions = listOfTransactions
        self.prev_hash = prev_hash
        self.timestamp = timestamp if timestamp else time.time()  # Use current time if timestamp is not provided
        if current_hash is not None:
            self.current_hash = current_hash
        else:
            self.current_hash = self.findHash()
        self.validator = validator
        self.index = index

    def findHash(self):
        data = str(self.listOfTransactions) + str(self.prev_hash) + str(self.timestamp)
        return hashlib.sha256(data.encode()).hexdigest()

    def to_dict(self):
        # print("Convert the Block object to a dictionary")
        # print(len(self.listOfTransactions))
        block_dict = {
            "listOfTransactions": [transaction.to_dict() for transaction in self.listOfTransactions],
            "prev_hash": self.prev_hash,
            "timestamp": self.timestamp,
            "current_hash": self.current_hash,
            "validator": public_key_to_string(self.validator),
            "index": self.index
        }
        return block_dict

    @classmethod
    def from_dict(cls, block_dict):
        return cls(
            listOfTransactions=[Transaction.from_dict(transaction_dict) for transaction_dict in block_dict["listOfTransactions"]],
            prev_hash=block_dict["prev_hash"],
            validator=string_to_public_key(block_dict["validator"]),
            timestamp=block_dict["timestamp"],
            index=block_dict["index"],
            current_hash=block_dict["current_hash"]
        )

