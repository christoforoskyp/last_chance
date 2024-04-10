import time
import requests
import rsa
from flask import Flask
from flask_restful import Api, Resource, reqparse
import Block
import Node
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


def to_map_string(map):
    for j, p_key in map.items():
        map[j] = public_key_to_string(p_key)
    return map


def to_map_string(map):
    for j, p_key in map.items():
        map[j] = public_key_to_string(p_key)
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
urls = {'0': 5000}
node = Node.Node(0, [0])
node.generate_wallet()
first_transaction = Transaction(-1, node.wallet.public_key, 0, 5100, None, None, 0)
node.mapOfBCC[0] = 5100
node.BCC = 5100
Block0 = node.create_new_block([first_transaction], 1, 0, 0)
node.mapOfPublicKeys[0] = node.wallet.public_key
public_keys = node.mapOfPublicKeys

user_id = 0
IP = "http://127.0.0.1:"


class sendBlockChain(Resource):
    def get(self):
        return node.my_blockchain.to_dict()


api.add_resource(sendBlockChain, "/blockchain")


class Home(Resource):
    def get(self):
        return str("USER " + str(node.id))


api.add_resource(Home, "/")


class create_id(Resource):  # create id fo the other nodes
    def get(self, port):
        global user_id
        user_id += 1  # every time the id is + 1
        urls[user_id] = port  # update the urls map
        node.mapOfBCC[user_id] = 0
        return user_id


api.add_resource(create_id, "/create_id/<int:port>")

public_key_args = reqparse.RequestParser()
public_key_args.add_argument("public_key", type=str, help="Put the public key", required=True)  # used for the


# public key


class get_public_key(Resource):  # the other node send to node it's public key
    def post(self, users_id):
        args = public_key_args.parse_args()

        node.mapOfPublicKeys[users_id] = string_to_public_key(args["public_key"])

        s = node.wallet.public_key

        s = public_key_to_string(node.wallet.public_key)

        s = string_to_public_key(s)

        to_string = node.mapOfPublicKeys.copy()
        readytosend = to_map_string(to_string)

        for i, url in urls.items():
            if i != '0':
                requests.post(IP + str(url) + "/receive_addresses",
                              json={'mapOfKeys': readytosend,
                                    'mapOfUrls': urls, 'mapOfBCC': node.mapOfBCC})

        return 200


api.add_resource(get_public_key, "/get_public_key/<int:users_id>")

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
                        typeoftrans = 0

                    else:
                        mes = args["message"]
                        typeoftrans = 1

                    ad = node.mapOfPublicKeys[int(args["address"])]
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


api.add_resource(createTransactionResource, "/create_transaction")

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
        node.mint_trans = []
        args = val_block_args.parse_args()
        block = Block.Block.from_dict(args["block"])
        val = node.validate_block(block)
        return val


api.add_resource(validateBlockResource, "/validate_block")

stake_args = reqparse.RequestParser()
stake_args.add_argument("amount", help="Put the stake amount", required=True)


class stake_amount(Resource):
    def post(self):
        # give me stake amount
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
            length = len(node.my_blockchain.chain)
            trans = node.create_transaction(0, 0, amount - stake_amount, None)  # from cli
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

        return 200


api.add_resource(stake_amount, "/stake")


def find_key_by_value(dictionary, target_value):
    for key, value in dictionary.items():
        if target_value == 0:
            return 0
        if value == target_value:
            return key
    # If the value is not found, you might want to handle this case appropriately
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
        return {"Balance: ": str(node.mapOfBCC[node.id])}


api.add_resource(Balance, "/balance")

if __name__ == '__main__':
    app.run(debug=True)
