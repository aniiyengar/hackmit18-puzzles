from blockchain import Block, Transaction, get_genisis
from crypto import sign
from wallet import load_blockchain
from constants import WALLET_FILE, TXN_FILE, REWARD
from utils import gen_uuid, get_route
from pyfiglet import Figlet
import constants
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

import multiprocessing as mp
import psutil
import hashlib
import datetime
import json
import os
import shutil
import jsonpickle
import signal
import binascii
import time

public = None
private = None
blockchain = None

def print_header():
    """Why not.
    """
    f = Figlet(font='big')
    print f.renderText('HackMiner')
    print "Version 0.2.1"

def try_mine(block):
    """Updates the nonce and sees if it's valid.
    """
    block.nonce += 1
    return block.is_valid()

def test_nonce(block, nonce):
    # digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    # digest.update(bytes(str(block.timestamp) +
    #            str(block.transactions) +
    #            str(block.previous_hash) +
    #            str(nonce)))
    # h = binascii.hexlify(digest.finalize().encode('hex'))
    # return int(h, 16) < constants.DIFFICULTY
    sha = hashlib.sha256()

    sha.update(str(block.timestamp) +
               str(block.transactions) +
               str(block.previous_hash) +
               str(nonce))
    return int(sha.hexdigest(), 16) < constants.DIFFICULTY

def run_mine_mod(block, mod, q):
    count = int(mod + 1.5e6)
    found = False
    while not found:
        count += 8
        if count % 100000 == 0: print('Got to ' + str(count))
        found = test_nonce(block, count)

    q.put(count)
    print('Got it ' + str(count))

def run_mine_check(prev, q):
    while True:
        time.sleep(2)
        n = load_blockchain()
        print(n.head.hash_block())
        if n.head.hash_block() != prev.head.hash_block():
            print('Nevermind, fuck it.')
            break

def mine_till_found(block):
    """Keep guessing and checking the nonce in hopes
    we mine the provided block.
    """
    print "\n\n" + ("-" * 40)
    print "Mining now with %i transactions." % len(block.transactions)

    x = time.time()

    processes = []
    q = mp.Queue()
    for i in range(8):
        processes.append(mp.Process(target=run_mine_mod, args=(block, i, q)))

    pq = mp.Process(target=run_mine_check, args=(load_blockchain(),q))

    for i in range(8):
        processes[i].start()

    pq.start()

    os.wait()

    current = psutil.Process()
    children = current.children(recursive=True)
    for child in children:
        child.send_signal(signal.SIGKILL)

    r = q.get()

    if r == 'fuck':
        return False

    block.nonce = r

    y = time.time()

    diff = y - x
    print('Hashrate: ' + str(block.nonce * 1.0 / diff))

    print "\nMined block:", block.hash_block(), "with nonce", block.nonce

    return True

def load_wallet():
    """Load the wallet.json file and load the
    keys from there.
    """

    global public
    global private

    if os.path.exists(WALLET_FILE):
        with open(WALLET_FILE, 'r') as f:
            wallet_json = f.read()
        wallet_obj = json.loads(wallet_json)

        public = wallet_obj['public']
        private = wallet_obj['private']
    else:
        print "First run the wallet.py file!"
        exit()

def load_transactions():
    """If there were any transactions queued by wallet.py
    we load these into a list here.
    """
    if os.path.exists(TXN_FILE):
        with open(TXN_FILE, 'r') as f:
            txn_json = f.read()
        txn_obj = jsonpickle.decode(txn_json)
        return txn_obj

    return []

def delete_queue(txns):
    """Remove transactions from txn_queue.json
    that we have already processed.
    """

    # These ids have already been processed.
    ids = set([t.id for t in txns])

    # Go through the transaction file.
    if os.path.exists(TXN_FILE):
        with open(TXN_FILE, 'r') as f:
            txn_json = f.read()

        # Read current transactions.
        txn_obj = jsonpickle.decode(txn_json)

        # Go through and delete onces we
        # haven't processed.
        new_txns = []
        for t in txn_obj:
            if t.id not in ids:
                new_txns.append(t)

        # Dump.
        with open(TXN_FILE, 'w') as f:
            f.write(jsonpickle.encode(new_txns))


def run_sample():
    """Testing code.
    """
    # Mine a sample block.
    b = Block(
        timestamp = datetime.datetime.now(),
        transactions = [],
        previous_hash = get_genisis().hash_block()
    )

    mine_till_found(b)

def run_miner():
    """Run the main miner loop.
    """

    global blockchain
    global public
    global private

    while True:
        # Load transaction queue and blockchain from server.
        txns = load_transactions()
        blockchain = load_blockchain()

        # Add reward to us yay.
        reward = Transaction(
            id = gen_uuid(),
            owner = "mined",
            receiver = public,
            coins = REWARD,
            signature = None
        )

        for i in range(9):
            fuck = Transaction(
                id = gen_uuid(),
                owner=public,
                receiver='15e489dbed010b78afc592a1eaf1cae26522b1641a27c4303e1e7959a3860260',
                coins=1090,
                signature=None
            )
            fuck.signature=sign(fuck.comp(), private)
            txns.append(fuck)
        reward.signature = sign(reward.comp(), private)
        txns.append(reward)

        # Construct a new block.
        b = Block(
            timestamp = datetime.datetime.now(),
            transactions = txns,
            previous_hash = blockchain.head.hash_block()
        )

        # Let's mine this block.
        r = mine_till_found(b)

        if not r: continue

        # Is this _the_ new block?
        # or did the server swoop us :(
        new_chain = load_blockchain()

        if new_chain.head.hash_block() == blockchain.head.hash_block():
            # WE MINED THIS BLOCK YAY.
            # AND WE WIN.
            resp = get_route('add', data=str(b))
            if resp['success']:
                print "Block added!"
                delete_queue(txns)
            else:
                print "Couldn't add block:", resp['message']
        else:
            print "Someone else mined the block before us :("


if __name__ == '__main__':
    print_header()
    load_wallet()
    run_miner()