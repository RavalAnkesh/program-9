import json
from web3 import Web3
from solcx import compile_standard, install_solc
import os
from dotenv import load_dotenv
from web3.middleware import ExtraDataToPOAMiddleware

# Load environment variables (optional)
load_dotenv()

# Step 1: Read Solidity contract
with open("./SimpleStorage.sol", "r") as file:
    simple_storage_file = file.read()

# Step 2: Install Solidity compiler
print("Installing Solidity compiler 0.6.0 ...")
install_solc("0.6.0")

# Step 3: Compile contract 
compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"SimpleStorage.sol": {"content": simple_storage_file}},
        "settings": {
            "outputSelection": {
                "*": {
                    "*": ["abi", "metadata", "evm.bytecode", "evm.bytecode.sourceMap"]
                }
            }
        },
    },
    solc_version="0.6.0",
)

# Save compiled output
with open("compiled_code.json", "w") as file:
    json.dump(compiled_sol, file, indent=4)

# Step 4: Extract bytecode and ABi
bytecode = compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]["evm"]["bytecode"]["object"]
abi = json.loads(compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]["metadata"])["output"]["abi"]

# ✅ Print bytecode and ABI
#print("\n================ BYTECODE ================")
#print(bytecode)
#print("\n================ ABI ================")
#print(json.dumps(abi, indent=4))*

# ✅ Save bytecode and ABI to files for reference
with open("bytecode.txt", "w") as file:
    file.write(bytecode)

with open("abi.json", "w") as file:
    json.dump(abi, file, indent=4)

# Step 5: Connect to Ganache
w3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:7545"))
chain_id = 1337  # Ganache default chain ID

if chain_id == 4:
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    print(w3.clientVersion)

# Your Ganache account details
my_address = "0x9ac4CC5C5d65637718cfD7585687404fd3c00A5A"
private_key = os.getenv("PRIVATE_KEY")

# Step 6: Create contract instance in Python
SimpleStorage = w3.eth.contract(abi=abi, bytecode=bytecode)
nonce = w3.eth.get_transaction_count(my_address)

# Step 7: Build and sign deployment transaction
transaction = SimpleStorage.constructor().build_transaction(
    {
        "chainId": chain_id,
        "gasPrice": w3.eth.gas_price,
        "from": my_address,
        "nonce": nonce,
    }
)
signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)

print("\nDeploying Contract...")
tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)

# Step 8: Wait for deployment
print("Waiting for transaction to finish...")
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f" Done! Contract deployed to: {tx_receipt.contractAddress}")

# Step 9: Interact with deployed contract
simple_storage = w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)
print(f"Initial Stored Value: {simple_storage.functions.retrieve().call()}")

# Step 10: Update stored value
greeting_transaction = simple_storage.functions.store(15).build_transaction(
    {
        "chainId": chain_id,
        "gasPrice": w3.eth.gas_price,
        "from": my_address,
        "nonce": nonce + 1,
    }
)
signed_greeting_txn = w3.eth.account.sign_transaction(
    greeting_transaction, private_key=private_key
)

# ✅ Fixed typo (eth instead of et)
tx_greeting_hash = w3.eth.send_raw_transaction(signed_greeting_txn.raw_transaction)

print("Updating stored value...")
w3.eth.wait_for_transaction_receipt(tx_greeting_hash)

print(f"Updated Stored Value: {simple_storage.functions.retrieve().call()}")

