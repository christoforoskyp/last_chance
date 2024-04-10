from Transaction import Transaction
from Blockchain import Blockchain
from Node import Node
from Block import Block

mapOfPublicKeys = {}
mapOfBCC = {}

mapOfBCC[0] = 0
mapOfBCC[1] = 0
mapOfBCC[2] = 0
mapOfBCC[3] = 0
mapOfBCC[4] = 0

# NODE POUSTRAS
poustras = Node(0, {})
poustras.generate_wallet()

first_transaction = Transaction("", poustras.wallet.public_key, 0, 300, None, None)
Block0 = poustras.create_new_block([first_transaction], 1, 0, 0)

poustras.mapOfBCC = mapOfBCC.copy()
mapOfPublicKeys[0] = poustras.wallet.public_key
poustras.mapOfPublicKeys = mapOfPublicKeys

poustras.BCC = 300
poustras.mapOfBCC[0] = 300

# NODE 1
node1 = Node(1, poustras.winners)
node1.generate_wallet()

node1.mapOfBCC = mapOfBCC.copy()
mapOfPublicKeys[1] = node1.wallet.public_key
node1.mapOfPublicKeys = mapOfPublicKeys
node1.mapOfBCC[0] = 300

node1.validate_chain(poustras.my_blockchain.chain)

# NODE 2
node2 = Node(2, poustras.winners)
node2.generate_wallet()

node2.mapOfBCC = mapOfBCC.copy()
mapOfPublicKeys[2] = node2.wallet.public_key
node2.mapOfPublicKeys = mapOfPublicKeys

node2.mapOfBCC = poustras.mapOfBCC.copy()

node2.validate_chain(poustras.my_blockchain.chain)

# Transaction_1
tr = poustras.create_transaction(poustras.mapOfPublicKeys[1], 0, 70, None)
node1.validate_transaction(tr)
node2.validate_transaction(tr)

trans = poustras.stake_amount(1)
node1.validate_transaction(trans)
node2.validate_transaction(trans)

# 5
trans = node1.stake_amount(50)
poustras.validate_transaction(trans)
node2.validate_transaction(trans)

trans = node1.stake_amount(30)
poustras.validate_transaction(trans)
node2.validate_transaction(trans)

trans = node1.stake_amount(20)
poustras.validate_transaction(trans)
node2.validate_transaction(trans)

# 6
trans = node2.stake_amount(0)
poustras.validate_transaction(trans)
node1.validate_transaction(trans)

trans = node1.stake_amount(60)
poustras.validate_transaction(trans)
node2.validate_transaction(trans)

trans = poustras.stake_amount(3)
node1.validate_transaction(trans)
node2.validate_transaction(trans)

print(node1.capacity_transactions)
node1.validate_block(node1.my_blockchain.chain[-1])

trans = poustras.stake_amount(3)
node1.validate_transaction(trans)
node2.validate_transaction(trans)

print(node1.capacity_transactions)



'''
# NODE 3
node3 = Node(3, poustras.winners)
node3.generate_wallet()

node3.mapOfBCC = mapOfBCC.copy()
mapOfPublicKeys[3] = node3.wallet.public_key
node3.mapOfPublicKeys = mapOfPublicKeys

node3.mapOfBCC = poustras.mapOfBCC.copy()

node3.validate_chain(poustras.my_blockchain.chain)
print(node3.my_blockchain.chain)

tr = poustras.create_transaction(poustras.mapOfPublicKeys[1], 0, 70, None)
node1.validate_transaction(tr)
node2.validate_transaction(tr)
node3.validate_transaction(trans)


trans = poustras.stake_amount(1)
node1.validate_transaction(trans)
node2.validate_transaction(trans)
node3.validate_transaction(trans)


# 5
trans = node1.stake_amount(50)
poustras.validate_transaction(trans)
node2.validate_transaction(trans)
node3.validate_transaction(trans)

# 6
trans = node2.stake_amount(0)
poustras.validate_transaction(trans)
node1.validate_transaction(trans)
node3.validate_transaction(trans)


node3.validate_transaction(trans)



poustras.validate_block(node1.my_blockchain.chain[-1])
node2.validate_block(node1.my_blockchain.chain[-1])
node3.validate_block(node1.my_blockchain.chain[-1])

print(poustras.my_blockchain.chain)
print(node1.my_blockchain.chain)
print(node2.my_blockchain.chain)

print(poustras.BCC)
print(node1.BCC)
print(node2.BCC)
print(node3.BCC)





node2 = Node(2, poustras.winners)
node3 = Node(3, poustras.winners)
node4 = Node(4, poustras.winners)

node2.generate_wallet()
node3.generate_wallet()
node4.generate_wallet()

node2.mapOfBCC = mapOfBCC.copy()
node3.mapOfBCC = mapOfBCC.copy()
node4.mapOfBCC = mapOfBCC.copy()

mapOfPublicKeys[2] = node2.wallet.public_key
mapOfPublicKeys[3] = node3.wallet.public_key
mapOfPublicKeys[4] = node4.wallet.public_key

node2.mapOfPublicKeys = mapOfPublicKeys.copy()
node3.mapOfPublicKeys = mapOfPublicKeys.copy()
node4.mapOfPublicKeys = mapOfPublicKeys.copy()



node2.mapOfBCC[0] = 300
node3.mapOfBCC[0] = 300
node4.mapOfBCC[0] = 300



# 2
tr = poustras.create_transaction(poustras.mapOfPublicKeys[2], 0, 70, None)
node1.validate_transaction(tr)
node2.validate_transaction(tr)

# 3
tr = node1.create_transaction(poustras.mapOfPublicKeys[0], 0, None, "ise megas gay")
poustras.validate_transaction(tr)
node2.validate_transaction(tr)

# 4

poustras.validate_block(node1.my_blockchain.chain[-1])

node2.validate_chain(poustras.my_blockchain.chain)
node3.validate_chain(poustras.my_blockchain.chain)
# print(poustras.my_blockchain.chain)
print(node1.winners)

print(poustras.BCC)
print(poustras.mapOfBCC[0])
print(node1.mapOfBCC[0])
print(node1.BCC)
print(node1.mapOfBCC[1])
print(poustras.mapOfBCC[1])
print(node2.mapOfBCC[1])


tr = node1.create_transaction(poustras.mapOfPublicKeys[0], 1, None, "Ise megalos poustiiiiiiiiiiiis")

poustras.validate_transaction(tr)
tr = node1.create_transaction(poustras.mapOfPublicKeys[0], 1, None, "Ise megalos poustiiiiiiiiiiiis")
poustras.validate_transaction(tr)
'''
