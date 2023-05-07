import json
import requests
from web3 import Web3
from eth_account import Account
from eth_account.signers.local import LocalAccount
from .models import PurplePayFactoryContract, PaymentBurnerAddress, PurplePayMultisigContract
import threading


def print_statement_with_line(module, line, variable_name, variable, delimiter="*"):
    print(f'{delimiter * 100}')
    print(f'Module: {module} :: Line: {line} :: {variable_name} :: {variable}')
    print(f'{delimiter * 100}')
    return


blockexplorer_urls = {
    '5': {
        'name': 'goerli',
        'block_explorer': 'etherscan',
        'base_url': 'https://api-goerli.etherscan.io/api'
    },
    '137': {
        'name': 'polygon mainnet',
        'block_explorer': 'blastapi',
        'base_url': 'https://polygon-mainnet.public.blastapi.io/'
    }
}

asharan_etherscan_api_key = "G99IM24UWSWJT5EIWZA65NNPUE216M95QV"

endpoints = {
    '5': {
        'name': 'goerli',
        'url': "https://rpc.ankr.com/eth_goerli"
    },
    '137': {
        'name': 'polygon mainnet',
        'url': "https://polygon-mainnet.public.blastapi.io"
    }
}

goerli_endpoint = "https://rpc.ankr.com/eth_goerli"
# purple_pay_multisig_addresses = {
#     '5': {
#         'name': 'goerli',
#         'address': "0xCF193782f2eBC069ae05eC0Ef955E4B042D000Dd"
#     },
#     '137': {
#         'name': 'polygon mainnet',
#         'address': "0xf229ceB323115a30EDEd92A953BA5c581e99751C"
#     }
# }

# purple_pay_multisig_address = "0xCF193782f2eBC069ae05eC0Ef955E4B042D000Dd"
# contract_address = "0x42f626A1379B802902a3fEE66409edA559627306" #'0xaddress'
erc20_token_abi = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "payable": False,
        "type": "function"
    },
    # Add any other functions you need here
]


def get_w3_provider(chain_id):
    rpc_endpoint = endpoints.get(chain_id).get('url')
    w3 = Web3(Web3.HTTPProvider(rpc_endpoint))
    return w3


def create_contract_instance(contract_address, contract_abi, chain_id):
    w3 = get_w3_provider(chain_id)
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)
    return contract


def get_burner_contract_address(
        contract, payment_id, erc20_token_address,
        amount_in_that_token, merchant_scw_address, purple_pay_multisig):
    contract_bytecode = contract.functions.predictAddress(
        payment_id, erc20_token_address, amount_in_that_token,
        merchant_scw_address, purple_pay_multisig).call()
    print(f'contract_bytecode: {contract_bytecode}')
    return contract_bytecode


def get_burner_address_balance_native(burner_address, chain_id):
    w3 = get_w3_provider(chain_id)
    return w3.eth.get_balance(burner_address)


def get_burner_address_balance(burner_address, token_instance, contract_abi):
    # token_address = '0x1234567890123456789012345678901234567890'
    token_address = token_instance.token_address_on_network

    print_statement_with_line('utils', 61, 'token_address', token_address)

    # Replace 'decimals' with the actual number of decimals used by the ERC20 token
    # decimals = 18
    decimals = token_instance.decimals

    # Create a web3.py instance to interact with the Ethereum network
    chain_id = token_instance.blockchain_network.chain_id
    w3 = get_w3_provider(chain_id)
    # w3 = Web3(Web3.HTTPProvider(goerli_endpoint))

    # Instantiate the ERC20 token contract object
    token_contract = w3.eth.contract(address=token_address, abi=contract_abi)
    print_statement_with_line('utils', 72, 'token_contract', token_contract)

    # Get the balance of the ERC20 token held in the wallet
    balance = token_contract.functions.balanceOf(burner_address).call()

    # Convert the balance to a human-readable format using the number of decimals
    balance_formatted = balance / 10 ** decimals

    # Print the wallet address and ERC20 token balance
    print(f'Wallet address: {burner_address}')
    print(f'Token address: {token_address}')
    print(f'Token balance: {balance_formatted} tokens')
    return balance


# Correct contract_address and contract_abi

# Start a thread to deploy and distribute

def deploy_and_disburse(burner_address_instance, token_instance,
                        payment_instance):
    payment_burner_address_obj = PaymentBurnerAddress.objects.filter(id=burner_address_instance.get('id'))[0]
    try:
        payment_burner_address_obj.burner_contract_deploy_status = 'initiated deploy'
        payment_burner_address_obj.save()

        print_statement_with_line('utils', 111, 'payment_instance', payment_instance)
        purple_pay_contract_instance = PurplePayFactoryContract.objects.get(
            blockchain_network=token_instance.blockchain_network)

        chain_id = token_instance.blockchain_network.chain_id
        # w3 = Web3(Web3.HTTPProvider(goerli_endpoint))
        w3 = get_w3_provider(chain_id)

        # Purple Pay Private Key | Signer
        private_key = "7b9ea6629926e9eb34d6355a08b9923c9e38c37d5299444767547641123b791d"
        account = Account.from_key(private_key)

        # Create a contract instance from the address and ABI
        contract_address = purple_pay_contract_instance.address
        contract_abi = purple_pay_contract_instance.contract_abi

        contract = w3.eth.contract(address=contract_address,
                                   abi=contract_abi)

        # Arguments needed
        # args = [payment_id, ERC20_token_address, amount_in_that_token, merchant_scw_address, purple_pay_multisig]
        print_statement_with_line('utils', 131, 'payment_instance', payment_instance)
        payment_id = str(payment_instance.get('id'))
        token_address = token_instance.token_address_on_network
        amount = int(burner_address_instance.get('order_amount') * (10 ** token_instance.decimals))
        merchant_scw_address = payment_instance.get('final_address_to')

        # purplepay_multisig
        purple_pay_multisig_address_qs = PurplePayMultisigContract.objects.filter(blockchain_network=token_instance.blockchain_network.id)
        purple_pay_multisig_address = purple_pay_multisig_address_qs[0].address

        print("X" * 100)
        print(f"line 138, payment_id: {payment_id}")
        print(f"token_address: {token_address}")
        print(f"amount: {amount} {type(amount)}")
        print(f"merchant_scw_address: {merchant_scw_address}")
        print("X" * 100)

        # Encode the arguments for the deploy function
        arguments = contract.encodeABI(fn_name='deploy',
                                       args=[payment_id, token_address,
                                             amount, merchant_scw_address,
                                             purple_pay_multisig_address])

        # Create a raw transaction to send to the network
        transaction = {
            'to': contract_address,
            'data': arguments,
            'gas': w3.eth.estimate_gas({'to': contract_address, 'data': arguments}),
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account.address),
            'chainId': 5
        }

        # Sign and send the transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)
        txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

        print("*" * 100)
        print(f'payment_burner_address_serializer.data: {burner_address_instance}')
        print("*" * 50)
        print(f'token_instance: {token_instance}')
        print("*" * 50)
        print(f'payment_burner_serializer.data: {payment_instance}')
        print("*" * 50)
        print(f'purple_pay_factory_contract_obj: {purple_pay_contract_instance}')
        print("*" * 50)
        print(f'Transaction hash: {txn_hash.hex()}')
        print("*" * 100)

        payment_burner_address_obj.burner_contract_deploy_status = 'success deploy'
        payment_burner_address_obj.transfer_to_merchant_transaction_hash = txn_hash.hex()
        payment_burner_address_obj.burner_contract_deploy_failure_reason = None
        payment_burner_address_obj.save()

        return txn_hash.hex()

    except Exception as e:
        payment_burner_address_obj.burner_contract_deploy_status = 'failure deploy'
        payment_burner_address_obj.burner_contract_deploy_failure_reason = str(e)[0:500]
        payment_burner_address_obj.save()
        print(e)
        return str(e)


def start_thread_to_deploy_and_disburse(fn_name, kwarg_dict):
    print_statement_with_line('views', 187, 'kwarg_dict', kwarg_dict)
    t = threading.Thread(target=fn_name, args=(), kwargs=kwarg_dict)
    t.setDaemon(True)
    t.start()


def get_payer_address():
    return


def get_transaction_hash_payer_to_burner_address():
    return


def get_latest_block_number(chain_id):
    # w3 = Web3(Web3.HTTPProvider(goerli_endpoint))
    w3 = get_w3_provider(chain_id)
    return w3.eth.get_block('latest').number


def get_transactions(idx):
    w3 = Web3(Web3.HTTPProvider(goerli_endpoint))
    block = w3.eth.get_block(idx)
    return block.transactions


def get_transaction_details(tx_hash):
    w3 = Web3(Web3.HTTPProvider(goerli_endpoint))
    return w3.eth.get_transaction(tx_hash)


def get_transaction_details_using_block_explorer(address, chain_id,
                                                 start=0, end=99999999,
                                                 api_key=asharan_etherscan_api_key,
                                                 module='account'):

    """
    response:
    [{'blockNumber': '8860581',
  'timeStamp': '1681986240',
  'hash': '0xd903955aa77d60512d3c15bb3f1b94530bbf338395ff26d43e8afa9e15201f18',
  'nonce': '7',
  'blockHash': '0x30bb932a6b6b419371ea42f79ee62136299f056e913556ceab4b3ac8f48dbad0',
  'transactionIndex': '51',
  'from': '0x107c189b0aa1c309ba65fd6fc22be1aa513a459c',
  'to': '0x518677020cacd19ddb6b56f44aac0e395c407d0e',
  'value': '6000000000000000',
  'gas': '21000',
  'gasPrice': '29131332885',
  'isError': '0',
  'txreceipt_status': '1',
  'input': '0x',
  'contractAddress': '',
  'cumulativeGasUsed': '6893641',
  'gasUsed': '21000',
  'confirmations': '911',
  'methodId': '0x',
  'functionName': ''}]"""
    base_url = blockexplorer_urls[chain_id]['base_url']

    # Need to maintain a mapping of chain id to api_url since api_url parameters and structure will vary according to chain
    api_url = f"{base_url}?module={module}&action=txlist&address={address}&startBlock={start}&endblock={end}&page=1&offset=10&sort=asc&apikey={api_key}"
    print(api_url)
    result = []
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            response_json = json.loads(response.text)
            if response_json.get('status', '0') == '1':
                print_statement_with_line('utils', 251, 'result_tx_etherscan', result)
                return response_json.get('result', [])
        return result
    except Exception as e:
        return result


def get_transaction_details_using_block_explorer_erc20(address, contract_address, chain_id,
                                                 start=0, end=27025780,
                                                 api_key=asharan_etherscan_api_key,
                                                 module='account'):

    """
    response:
    [{'blockNumber': '8860581',
  'timeStamp': '1681986240',
  'hash': '0xd903955aa77d60512d3c15bb3f1b94530bbf338395ff26d43e8afa9e15201f18',
  'nonce': '7',
  'blockHash': '0x30bb932a6b6b419371ea42f79ee62136299f056e913556ceab4b3ac8f48dbad0',
  'transactionIndex': '51',
  'from': '0x107c189b0aa1c309ba65fd6fc22be1aa513a459c',
  'to': '0x518677020cacd19ddb6b56f44aac0e395c407d0e',
  'value': '6000000000000000',
  'gas': '21000',
  'gasPrice': '29131332885',
  'isError': '0',
  'txreceipt_status': '1',
  'input': '0x',
  'contractAddress': '',
  'cumulativeGasUsed': '6893641',
  'gasUsed': '21000',
  'confirmations': '911',
  'methodId': '0x',
  'functionName': ''}]"""
    if chain_id == '5':
        base_url = blockexplorer_urls[chain_id]['base_url']
        api_url = f"{base_url}?module={module}&action=tokentx&contractaddress={contract_address}&address={address}&startBlock={start}&endblock={end}&page=1&offset=100&sort=asc&apikey={api_key}"
        print(api_url)
    else:
        base_url = blockexplorer_urls[chain_id]['base_url']
        api_url = f"{base_url}"

    result = []
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            response_json = json.loads(response.text)
            if response_json.get('status', '0') == '1':
                print_statement_with_line('utils', 251, 'result_tx_etherscan', result)
                return response_json.get('result', [])
        return result
    except Exception as e:
        return result



