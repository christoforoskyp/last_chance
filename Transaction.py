import base64
import rsa


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


def to_map_string(map):
    for j, p_key in map.items():
        map[j] = public_key_to_string(p_key)
    return map


def signature_to_string(signature):
    if signature != 0:
        return base64.b64encode(signature).decode()

    return signature


def string_to_signature(signature_str):
    if signature_str != 0:
        return base64.b64decode(signature_str.encode())
    return signature_str


class Transaction:
    def __init__(self, sender_address, receiver_address, typeOfTransaction, amount, message, nonce, signature):
        self.sender_address = sender_address
        self.receiver_address = receiver_address
        self.typeOfTransaction = typeOfTransaction
        self.amount = None
        self.message = None

        if amount is not None:
            self.amount = amount
            self.transaction_data = str(self.sender_address) + "sends " + str(self.amount) + " to " + str(
                receiver_address)
        if message is not None:
            self.amount = 0
            self.message = message
            self.transaction_data = str(self.sender_address) + "sends " + str(self.message) + " to " + str(
                receiver_address)

        self.nonce = nonce
        self.transaction_id = ""
        self.signature = signature

    def to_dict(self):
        # # print("Convert the Transaction object to a dictionary")
        transaction_dict = {
            "sender_address": public_key_to_string(self.sender_address),
            "receiver_address": public_key_to_string(self.receiver_address),
            "typeOfTransaction": self.typeOfTransaction,
            "amount": self.amount,
            "message": self.message,
            "nonce": self.nonce,
            "transaction_id": self.transaction_id,
            "signature": signature_to_string(self.signature)
        }
        return transaction_dict

    @classmethod
    def from_dict(cls, transaction_dict):
        return cls(
            sender_address=string_to_public_key(transaction_dict["sender_address"]),
            receiver_address=string_to_public_key(transaction_dict["receiver_address"]),
            typeOfTransaction=transaction_dict["typeOfTransaction"],
            amount=transaction_dict["amount"],
            message=transaction_dict["message"],
            nonce=transaction_dict["nonce"],
            signature=string_to_signature(transaction_dict["signature"])
        )
