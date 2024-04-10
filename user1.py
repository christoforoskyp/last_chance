import time
import requests
import rsa
from flask import Flask
from flask_restful import Api, Resource, reqparse
import Block
import Node
from Transaction import Transaction
from Blockchain import Blockchain


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


def to_map_RSA(map):
    for j, p_key in map.items():
        map[j] = string_to_public_key(p_key)
    return map


LOCK_SERVICE_URL = 'http://127.0.0.1:5009'

LOCK_ACQUIRE_TIMEOUT = 10  # Timeout in seconds


def acquire_lock():
    try:
        response = requests.get(f'{LOCK_SERVICE_URL}/acquire_lock', timeout=LOCK_ACQUIRE_TIMEOUT)
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.exceptions.Timeout:
        print("Timeout: Failed to acquire the lock within the specified time.")
        return False


def release_lock():
    response = requests.post(f'{LOCK_SERVICE_URL}/release_lock')
    if response.status_code == 200:
        return True
    else:
        return False


app = Flask(__name__)
api = Api(app)

BASE = "http://127.0.0.1:5000/"  # NODE_0's ip
IP = "http://127.0.0.1:"
urls = {}

blockchain_args = reqparse.RequestParser()
blockchain_args.add_argument("blockchain", help="Put the blockchain", required=True)
global node


class BlockchainResource(Resource):
    def post(self):
        args = blockchain_args.parse_args()
        global node
        answer = args["blockchain"]
        node.my_blockchain.chain = answer
        return answer


api.add_resource(BlockchainResource, "/blockchain")


class Home(Resource):  # first thing that happens
    def get(self):
        my_id = requests.get(BASE + "create_id/5001")  # send to NODE_0 my port and get my id
        global node
        node = Node.Node(my_id.json(), [0])  # create my Node, with the id NODE_0 gave me
        node.generate_wallet()

        answer = requests.post(BASE + "get_public_key/" + str(node.id),
                               json={"public_key": public_key_to_string(node.wallet.public_key)})

        blockchain = requests.get(BASE + "blockchain")
        node.my_blockchain = Blockchain.from_dict(blockchain.json())
        return str("USER " + str(node.id))


api.add_resource(Home, "/")

addresses_args = reqparse.RequestParser()
addresses_args.add_argument("mapOfKeys", type=dict, help="Put the map", required=True)
addresses_args.add_argument("mapOfUrls", type=dict, help="Put the urls", required=True)
addresses_args.add_argument("mapOfBCC", type=dict, help="Put the BCC", required=True)


class FillAddresses(Resource):
    def post(self):
        args = addresses_args.parse_args()
        global node, urls
        node.mapOfPublicKeys = to_map_RSA(args["mapOfKeys"])
        node.mapOfBCC = args["mapOfBCC"]
        urls = args["mapOfUrls"]

        return 200


api.add_resource(FillAddresses, "/receive_addresses")

trans_args = reqparse.RequestParser()
trans_args.add_argument("address", help="Put the address", required=True)
trans_args.add_argument("message", help="Put the address", required=True)


class createTransactionResource(Resource):

    def post(self):
        ret = 0
        while ret < 4:
            if acquire_lock():
                try:
                    args = trans_args.parse_args()
                    typeoftrans = -1
                    amount = None  # Assuming a default value for amount
                    mes = None
                    if args["message"].isdigit():
                        amount = int(args["message"])
                        # print(amount)
                        typeoftrans = 0

                    else:
                        mes = args["message"]
                        typeoftrans = 1

                    ad = node.mapOfPublicKeys[args["address"]]
                    length = len(node.my_blockchain.chain)
                    trans = node.create_transaction(ad, typeoftrans, amount, mes)  # from cli
                    print("Transaction Nonce: ", trans.nonce)
                    if trans == 400 or trans == 401 or trans == 402:
                        return trans
                    readytrans = trans.to_dict()
                    block_from_winner = None
                    for i, url in urls.items():
                        if i != str(node.id):
                            re = requests.post(IP + str(url) + "/validate_transaction",
                                               json={'transaction': readytrans})
                            if type(re.json()) is dict:
                                block_from_winner = re.json()

                    if len(node.my_blockchain.chain) > length and node.my_blockchain.chain[
                        -1].validator == node.wallet.public_key:  # if I won then I have to send the block to everyone

                        readyblock = node.my_blockchain.chain[-1].to_dict()
                        for i, url in urls.items():
                            if i != str(node.id):
                                re = requests.post(IP + str(url) + "/validate_block",
                                                   json={"block": readyblock})
                                if re.json() != 200:
                                    return re.json()
                        return 200
                    elif block_from_winner is not None:
                        blocktobrod = Block.Block.from_dict(block_from_winner)
                        validator_id = find_key_by_value(node.mapOfPublicKeys, blocktobrod.validator)
                        readyblock = blocktobrod.to_dict().copy()
                        node.validate_block(blocktobrod)
                        for i, url in urls.items():
                            if i != str(node.id) and i != validator_id:
                                re = requests.post(IP + str(url) + "/validate_block",
                                                   json={"block": readyblock})
                                if re.json() != 200:
                                    return re.json()
                    return 200
                finally:
                    # Release the lock when transaction creation is complete
                    release_lock()
                    return 200

            else:
                print(f"Node {node.id} failed to acquire the transaction lock.")
                ret += 1
                time.sleep(1)
        print("Failed to create transaction after 3 attempts")
        return 408


api.add_resource(createTransactionResource, "/create_transaction/")

val_trans_args = reqparse.RequestParser()
val_trans_args.add_argument("transaction", type=dict, help="Put the transaction for validation", required=True)


class validateTransactionResource(Resource):
    def post(self):
        args = val_trans_args.parse_args()
        tr = Transaction.from_dict(args["transaction"])

        # start of insanity
        length = len(node.my_blockchain.chain)
        ans = node.validate_transaction(tr)
        if ans != 200:
            return ans

        if len(node.my_blockchain.chain) > length and node.my_blockchain.chain[
            -1].validator == node.wallet.public_key:  # if I won then I have to send the block to everyone
            readyblock = node.my_blockchain.chain[-1].to_dict()
            return readyblock

        return 200


api.add_resource(validateTransactionResource, "/validate_transaction")

val_block_args = reqparse.RequestParser()
val_block_args.add_argument("block", type=dict, help="Put the block for validation", required=True)


class validateBlockResource(Resource):
    def post(self):
        args = val_block_args.parse_args()
        block = Block.Block.from_dict(args["block"])
        val = node.validate_block(block)
        return val


api.add_resource(validateBlockResource, "/validate_block")

stake_args = reqparse.RequestParser()
stake_args.add_argument("amount", help="Put the stake amount", required=True)


class stake_amount(Resource):
    def post(self):
        # check if the node has already staked amount
        args = stake_args.parse_args()
        amount = int(args["amount"])
        stake_amount = 0
        for block in node.my_blockchain.chain:
            for transaction in block.listOfTransactions:
                if transaction.sender_address == node.wallet.public_key and transaction.receiver_address == 0:
                    stake_amount += transaction.amount
                elif transaction.sender_address == 0 and transaction.receiver_address == node.wallet.public_key:
                    stake_amount -= transaction.amount

        for transaction in node.capacity_transactions:  # find the staked amount so far
            if transaction.sender_address == node.wallet.public_key and transaction.receiver_address == 0:
                stake_amount += transaction.amount
            elif transaction.sender_address == 0 and transaction.receiver_address == node.wallet.public_key:
                stake_amount -= transaction.amount

        if amount > stake_amount:  # if I want to stake more
            # trans = node.create_transaction(0, 0, amount - stake_amount, None)
            length = len(node.my_blockchain.chain)
            trans = node.create_transaction(0, 0, amount - stake_amount, None)  # from cli
            if trans == 400 or trans == 401 or trans == 402:
                return trans
            # broadcast:
            readytrans = trans.to_dict()
            block_from_winner = None
            for i, url in urls.items():
                if i != str(node.id):
                    re = requests.post(IP + str(url) + "/validate_transaction",
                                       json={'transaction': readytrans})
                    if type(re.json()) is dict:
                        block_from_winner = re.json()

            if len(node.my_blockchain.chain) > length and node.my_blockchain.chain[
                    -1].validator == node.wallet.public_key:  # if I won then I have to send the block to everyone
                readyblock = node.my_blockchain.chain[-1].to_dict()
                for i, url in urls.items():
                    if i != str(node.id):
                        re = requests.post(IP + str(url) + "/validate_block",
                                           json={"block": readyblock})
                        if re.status_code != 200:
                            return re
            elif block_from_winner is not None:
                blocktobrod = Block.Block.from_dict(block_from_winner)
                validator_id = find_key_by_value(node.mapOfPublicKeys, blocktobrod.validator)
                readyblock = blocktobrod.to_dict().copy()
                node.validate_block(blocktobrod)
                for i, url in urls.items():
                    if i != str(node.id) and i != validator_id:
                        # print("send block to:" + str(url))
                        re = requests.post(IP + str(url) + "/validate_block",
                                           json={"block": readyblock})
                        if re.json() != 200:
                            return re.json()

            return 200

        elif amount < stake_amount:  # if I want to stake less
            trans = Transaction(0, node.wallet.public_key, 0, stake_amount - amount, None, None, 0)
            # broadcast(trans)
            readytrans = trans.to_dict()
            block_from_winner = None
            for i, url in urls.items():
                if i != str(node.id):
                    re = requests.post(IP + str(url) + "/validate_transaction",
                                       json={'transaction': readytrans})
                    if type(re.json()) is dict:
                        block_from_winner = re.json()

            length = len(node.my_blockchain.chain)
            val = node.validate_transaction(trans)
            if val == 400 or val == 401 or val == 402:
                return val

            if len(node.my_blockchain.chain) > length and node.my_blockchain.chain[
                -1].validator == node.wallet.public_key:  # if I won then I have to send the block to everyone
                readyblock = node.my_blockchain.chain[-1].to_dict()
                for i, url in urls.items():
                    if i != str(node.id):
                        re = requests.post(IP + str(url) + "/validate_block",
                                           json={"block": readyblock})
                        if re.status_code != 200:
                            return re
            elif block_from_winner is not None:
                blocktobrod = Block.Block.from_dict(block_from_winner)
                validator_id = find_key_by_value(node.mapOfPublicKeys, blocktobrod.validator)
                readyblock = blocktobrod.to_dict().copy()
                node.validate_block(blocktobrod)
                for i, url in urls.items():
                    if i != str(node.id) and i != validator_id:
                        re = requests.post(IP + str(url) + "/validate_block",
                                           json={"block": readyblock})
                        if re.json() != 200:
                            return re.json()

            return 200

        return 200


api.add_resource(stake_amount, "/stake")


def find_key_by_value(dictionary, target_value):
    for key, value in dictionary.items():
        if target_value == 0:
            return 0
        if value == target_value:
            return key
    return None


class View(Resource):  # for testing
    def get(self):
        listOfTrans = []

        for transaction in node.my_blockchain.chain[-1].listOfTransactions:
            listOfTrans.append(transaction.to_dict())

        listOfTrans.append(
            {"validator: ": find_key_by_value(node.mapOfPublicKeys, node.my_blockchain.chain[-1].validator), "Num of "
                                                                                                             "Blocks: ":
                str(len(node.my_blockchain.chain))})

        return listOfTrans


api.add_resource(View, "/view")


class Balance(Resource):
    def get(self):
        global node
        return {"Balance: ": str(node.mapOfBCC[str(node.id)])}


api.add_resource(Balance, "/balance")

if __name__ == '__main__':
    app.run(port=5001, debug=True)
