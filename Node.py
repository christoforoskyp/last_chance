import Wallet
import rsa
import Block
import Blockchain
import random
from Transaction import Transaction
from collections import defaultdict


def find_key_by_value(dictionary, target_value):
    for key, value in dictionary.items():
        if value == target_value:
            return key
    return None


def find_cost(transaction):
    if transaction.typeOfTransaction == 0:  # send money
        return transaction.amount + (transaction.amount * 3 / 100)
    elif transaction.typeOfTransaction == 1:  # send message
        return len(transaction.message)


def find_cost_for_validator(transaction):
    if transaction.typeOfTransaction == 0 and transaction.sender_address != -1:  # send money
        return transaction.amount * 3 / 100
    elif transaction.typeOfTransaction == 1:  # send message
        return len(transaction.message)
    else:
        return 0


BASE = "http://127.0.0.1:"


class Node:
    def __init__(self, id, winners):
        self.wallet = None
        self.capacity = 10  # how many transactions need to create a new block
        self.id = id
        self.BCC = 0
        self.mapOfPublicKeys = {}
        self.mapOfBCC = {}
        self.my_blockchain = Blockchain.Blockchain()
        self.capacity_transactions = []
        self.nonce = 0
        self.winners = winners
        self.mint_trans = []
        self.mapofStakeAmount = defaultdict(int)  # this is used to find the amount that each node stakes

    def generate_wallet(self):
        public_key, private_key = rsa.newkeys(1024)
        self.wallet = Wallet.Wallet(private_key, public_key)

    def create_new_block(self, listOfTransactions, prev_hash, validator, index):
        new_block = Block.Block(listOfTransactions, prev_hash, validator, None, index, None)
        self.my_blockchain.chain.append(new_block)
        return new_block

    def sign_transaction(self, transaction_data):
        # Sign the transaction data using the private key
        signature = rsa.sign(transaction_data.encode(), self.wallet.private_key, 'SHA-256')
        return signature

    def create_transaction(self, receiver_address, typeOfTransaction, amount, message):
        print("CREATE Transaction")
        # id  ----> public key / address receiver
        self.nonce += 1  # each node has a personal nonce which is increased every time the node creates a transaction
        # receiver_address = self.mapOfPublicKeys[receiver_id]
        trans = Transaction(self.wallet.public_key, receiver_address, typeOfTransaction, amount, message, self.nonce, 0)
        trans.signature = self.sign_transaction(trans.transaction_data)
        val = self.validate_transaction(trans)
        if val == 200:
            return trans
        else:
            return val

    def verify_signature(self, transaction):
        # Verify the signature using the provided public key
        if rsa.verify(transaction.transaction_data.encode(), transaction.signature,
                      transaction.sender_address) == "SHA-256":
            return True
        return False

    def validate_transaction(self, transaction):

        cost = 0
        if transaction.sender_address != 0:
            if self.verify_signature(transaction) is False:
                return 400
            else:
                cost = find_cost(transaction)
                if cost > self.get_balance(transaction.sender_address):
                    return 401

        if self.check_nonce(transaction) is False and transaction.sender_address != 0:
            return 402
        else:
            if transaction.sender_address != 0:
                sender_id = find_key_by_value(self.mapOfPublicKeys, transaction.sender_address)
                self.mapOfBCC[sender_id] -= cost
            if transaction.receiver_address != 0:
                receiver_id = find_key_by_value(self.mapOfPublicKeys, transaction.receiver_address)
                self.mapOfBCC[receiver_id] += transaction.amount

            if transaction.sender_address == self.wallet.public_key:
                self.BCC -= cost  # remove amount + fee
            if transaction.receiver_address == self.wallet.public_key:
                self.BCC += transaction.amount
            if len(self.capacity_transactions) + 1 == self.capacity:
                self.capacity_transactions.append(transaction)
                self.mint_trans.append(transaction)
                self.mint_block()
                return 200
            else:
                self.capacity_transactions.append(transaction)  # add transaction to the capacity_transactions
                self.mint_trans.append(transaction)
        return 200

    def get_balance(self, address):
        # Retrieve and calculate the balance of the specified address
        balance = 0
        for block in self.my_blockchain.chain:
            for transaction in block.listOfTransactions:
                if transaction.receiver_address == address:
                    balance += transaction.amount
                if transaction.sender_address == address:
                    balance -= transaction.amount

        for transaction in self.capacity_transactions:
            if transaction.receiver_address == address:
                balance += transaction.amount
            if transaction.sender_address == address:
                balance -= transaction.amount
        return balance

    def check_nonce(self, transaction):
        for block in self.my_blockchain.chain:
            for block_chain_transaction in block.listOfTransactions:
                if block_chain_transaction.sender_address == transaction.sender_address:
                    if block_chain_transaction.nonce == transaction.nonce:
                        return False
        for capacity_transaction in self.capacity_transactions:
            if capacity_transaction.sender_address == transaction.sender_address:
                if capacity_transaction.nonce == transaction.nonce:
                    return False
        return True

    def mint_block(self):
        print("MINT BLOCK")
        total_cost = 0  # total cost that will be sent to the validator
        total_stake_amount = 0
        # this is used to find the amount that each node stakes
        mapOfStakes = {}  # this is used for proof of stake algorithm

        for transaction in self.capacity_transactions:
            total_cost += find_cost_for_validator(transaction)  # total cost that will be sent to the validator
            if transaction.receiver_address == 0:
                id = find_key_by_value(self.mapOfPublicKeys, transaction.sender_address)
                self.mapofStakeAmount[id] += transaction.amount
            elif transaction.sender_address == 0:
                id = find_key_by_value(self.mapOfPublicKeys, transaction.sender_address)
                self.mapofStakeAmount[id] -= transaction.amount
        for id in self.mapofStakeAmount:
            mapOfStakes[id] = (total_stake_amount, total_stake_amount + self.mapofStakeAmount[id] - 1)
            total_stake_amount += self.mapofStakeAmount[id]

        hash_digest = int(self.my_blockchain.chain[-1].current_hash, 16)
        random.seed(hash_digest)
        start_range = 0
        if total_stake_amount == 1:
            stop_range = total_stake_amount
        elif total_stake_amount == 0:  # there is no stake yet
            stop_range = int(list(self.mapOfPublicKeys.keys())[-1])  # from 0 to the last node
        else:
            stop_range = total_stake_amount - 1
        step_range = 1
        winner = None
        random_integer = random.randrange(start_range, stop_range, step_range)
        if total_stake_amount == 0:
            index = self.my_blockchain.chain[-1].index + 1
            winner = list(self.mapOfPublicKeys.keys())[random_integer]

        else:
            index = self.my_blockchain.chain[-1].index + 1

            for key, value in mapOfStakes.items():
                lower_bound, upper_bound = value  # Unpack the pair into lower and upper bounds
                if lower_bound <= random_integer <= upper_bound:
                    winner = key
                    break  # Exit the loop once a match is found

        # add winner to map of winners
        self.winners.append(self.mapOfPublicKeys[winner])

        if self.mapOfPublicKeys[winner] == self.wallet.public_key:
            self.BCC += total_cost
            new_block = self.create_new_block(self.capacity_transactions, self.my_blockchain.chain[-1].current_hash,
                                              self.mapOfPublicKeys[winner], index)

        self.capacity_transactions = []  # empty the capacity transactions
        # create a transaction containing transaction for validator
        trans = Transaction(-1, self.mapOfPublicKeys[winner], 0, total_cost, None, None,
                            0)
        self.capacity_transactions.append(trans)
        self.mapOfBCC[winner] += total_cost  # add money for the validator
        return 200

    def validate_block(self, block):

        print("Validate block" + str(block.index))
        if str(block.prev_hash) != str(self.my_blockchain.chain[block.index - 1].current_hash):
            return 403
        # check winner
        elif self.winners[block.index] != block.validator:
            # print("Wrong validator")
            return 404

        self.my_blockchain.chain.append(block)
        return 200

    def validate_chain(self, blockchain):

        for block in blockchain:
            if block.index != 0:
                self.validate_block(block)
            else:
                self.my_blockchain.chain.append(block)
