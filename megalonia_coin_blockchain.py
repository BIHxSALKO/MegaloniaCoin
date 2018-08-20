#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 26 01:53:10 2018

@author: shr3d-t3h-gn4r

Implement Blockchain:

MegaloniaCoin
1 MegaloniaCoin = 1000 megalobits
"""

from hashlib import sha256
from binascii import unhexlify, hexlify
from time import time
from sys import getsizeof
from collections import deque
import random


def double_sha256(i):
    return sha256(sha256(i.encode('utf-8')).hexdigest().encode('utf-8')).hexdigest()


class MerkleRoot:
    @staticmethod
    def endian_switch(i):

        byte_arr = bytearray(unhexlify(i))
        byte_arr.reverse()
        return byte_arr

    @staticmethod
    def hash_mod(node):
        node_hash = sha256(sha256(node).digest()).hexdigest()
        node_hash = hexlify(MerkleRoot().endian_switch(node_hash)).decode("utf-8")
        return node_hash

    def make_nodes(self, transactions, n):
        for i in range(0, len(transactions), n):
            yield transactions[i: i + n]

    def merkle_root(self, transactions):
        tree_list = []
        count = 1
        for i in self.make_nodes(transactions, 2):
            if len(i) == 2:
                left = self.endian_switch(i[0])
                right = self.endian_switch(i[1])

            else:
                left = self.endian_switch(i[0])
                right = self.endian_switch(i[0])

            count += 2
            node = left + right
            parent_hash = self.hash_mod(node)

            tree_list.append(parent_hash)
        if len(tree_list) == 1:
            return tree_list[0]
        else:
            return self.merkle_root(tree_list)


class Header:
    """
    A Header is comprised of a the previous block's hash, the current block's Merkle root, and a nonce valaue
    that solves the hashing puzzle for a successfull block mining
    """
    def __init__(self, hash_prev_block, hash_merkle_root, nonce, version=1, bits=0x207fffff):
        self.hash_prev_block = hash_prev_block
        self.hash_merkle_root = hash_merkle_root
        self.version = version
        self.timestamp = int(time())
        self.bits = bits
        self.nonce = nonce

    def make_block_hash(self):
        block_hash = double_sha256(str(self.timestamp)
                                   + str(self.hash_merkle_root)
                                   + str(self.bits)
                                   + str(self.nonce)
                                   + str(self.hash_prev_block))
        return block_hash


class TxnMemoryPool:
    """
    A TxnMemoryPool is a queue of transactions
    """

    def __init__(self):
        self.list_of_transactions = deque()

    def add_new_txn(self, tx):
        self.list_of_transactions.append(tx)

    def get_txns(self, n):
        txs = []
        for _ in range(n):
            txs.append(self.list_of_transactions.popleft())
        return txs

    def get_size(self):
        return len(self.list_of_transactions)


class Output:
    """
    An Output has a value, an index and a script
    """
    def __init__(self, value, index, script="haxxor"):
        self.value = value / 1000
        self.index = index
        self.script = script


class Transaction:
    """
    A Transaction has a list of inputs that contains the dictionary{sender, recipient, amount}
    """
    def __init__(self, list_of_inputs, in_counter=1, version_number=1):
        self.version_number = version_number
        self.list_of_inputs = list_of_inputs
        self.list_of_outputs = Output(value=1, index=1, script="haxxor")

        self.in_counter = in_counter
        self.out_counter = 1
        self.transaction_hash = double_sha256(str(self.version_number)
                                              + str(self.list_of_inputs)
                                              + str(self.list_of_outputs)
                                              + str(self.in_counter)
                                              + str(self.out_counter))

    def print_transaction(self):
        print(self.list_of_outputs)


class Block:
    """
    Block has a header and stores transactions in a list
    """
    def __init__(self, index, block_header, transactions, block_hash):
        self.magic_number = int(0xD9B4BEF9)
        self.index = index
        self.block_header = block_header
        self.transaction_counter = len(transactions)
        self.transactions = transactions
        self.block_hash = block_hash
        self.block_size = getsizeof(self)

    def print_block(self):
        print(self.block_hash)


class BlockChain:

    MAX_TXNS = 10

    def __init__(self):
        self.chain = []
        self.pool = TxnMemoryPool()
        self.block_reward = 50
        self.make_genesis_block()

    def get_block(self, block_height=None, block_hash=None):
        for block in self.chain:
            if block.index == block_height or block.block_hash == block_hash:
                return block

    def get_transaction(self, transaction_hash):
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.transaction_hash == transaction_hash:
                    return transaction

    def get_chain_length(self):
        return len(self.chain)

    def get_last_block(self):
        return self.chain[self.get_chain_length() - 1]

    def make_genesis_block(self):
        header = Header(hash_prev_block='0000000000000000', hash_merkle_root='0000000000000000', nonce=0)
        block_hash = header.make_block_hash()
        coinbase_txn = Transaction(list_of_inputs={'output amount': 0})
        block = Block(index=0, block_header=header, transactions=[coinbase_txn], block_hash=block_hash)
        self.chain.append(block)

    def make_new_tx(self, sender, recipient, amount, output_amount):
        self.pool.add_new_txn(Transaction(list_of_inputs={'sender': sender,
                                                          'recipient': recipient,
                                                          'input amount': amount,
                                                          'output amount': output_amount}))

    def make_new_header(self, current_transactions_list, nonce):
        block_chain_length = len(self.chain)

        transactions = [txn.transaction_hash for txn in current_transactions_list]

        hash_merkle_root = MerkleRoot().merkle_root(transactions)

        header = Header(
            hash_prev_block=self.chain[block_chain_length - 1].block_hash,
            hash_merkle_root=hash_merkle_root,
            nonce=nonce
        )

        return header

    def make_new_block(self, current_transactions_list, header, block_hash):
        chain_length = len(self.chain)

        block = Block(index=chain_length, block_header=header, transactions=current_transactions_list,
                      block_hash=block_hash)
        self.chain.append(block)
        print("Mined block's height:", block.index, "\n")

    def mine(self):
        while self.pool.get_size() != 0:

            if not self.pool.get_size() < self.MAX_TXNS:
                current_txns_list = self.pool.get_txns(9)
            else:
                current_txns_list = self.pool.get_txns(self.pool.get_size())

            total_tx_fees = 0
            for txn in current_txns_list:
                total_tx_fees += (txn.list_of_inputs['input amount'] - txn.list_of_inputs['output amount'])

            coinbase_txn = Transaction(list_of_inputs={'recipient': "miner's address",
                                                       'output amount': self.block_reward + total_tx_fees})

            current_txns_list.insert(0, coinbase_txn)

            nonce = 0
            target = 0x7fffff * 2 ** (0x8 * (0x20 - 0x3))
            header = self.make_new_header(current_txns_list, nonce=nonce)

            block_hash = header.make_block_hash()

            while not int(block_hash, 16) < target:
                nonce += 1
                header = self.make_new_header(current_txns_list, nonce=nonce)
                block_hash = header.make_block_hash()

            print("Nonce solution to hash puzzle:", nonce)
            print("Solved block hash: ", int(block_hash, 16))

            self.make_new_block(current_transactions_list=current_txns_list,
                                header=header, block_hash=block_hash)

    def print_blockchain(self):
        print("printing all blocks: (height, block_hash) ")
        i = 0
        for block in self.chain:
            print(i, block.block_hash)
            i += 1

    def print_all_transactions(self):
        print("printing all transactions: (count, txn_hash)")
        i = 1
        for block in self.chain:
            for transaction in block.transactions:
                print(i, transaction.transaction_hash)
                i += 1

if __name__ == "__main__":
    blockchain = BlockChain()

    # Let's create a pool of transactions
    tx_mem_pool = []
    names = ['Spongebob', 'Patrick', 'Squidward', 'Plankton', 'Sandy', 'Gary', 'Mr. Krabbs', 'Goku', 'Vegeta',
             'Piccolo', 'Kami', 'Master Roshi', 'Mr. Popo', 'Frieza', 'Jiren', 'Beerus', 'Whis']

    for i in range(0, 91):
        tmp = names
        sender = random.choice(tmp)
        recipient = random.choice([name for name in tmp if name != sender])

        tx = {"sender": sender,
              "recipient": recipient,
              "amount": random.randint(1, 101),
              "fee": i / 1000}
        tx_mem_pool.append(tx)

    for tx in tx_mem_pool:
        blockchain.make_new_tx(sender=tx["sender"],
                               recipient=tx["recipient"],
                               amount=tx["amount"],
                               output_amount=tx["fee"])
    # start mining
    blockchain.mine()

    top_block = blockchain.get_last_block()
    print("Block height of the top of the chain: ", top_block.index)