from Block import Block


class Blockchain:

    def __init__(self):
        self.chain = []

    def to_dict(self):
        # Convert the Blockchain object to a dictionary
        blockchain_dict = {
            "chain": [block.to_dict() for block in self.chain],
        }
        return blockchain_dict

    @classmethod
    def from_dict(cls, blockchain_dict):
        blockchain = cls()
        blockchain.chain = [Block.from_dict(block_dict) for block_dict in blockchain_dict["chain"]]
        return blockchain
