GET_PAYMENT_STATUS_SUCCESS = "Payment status returned successfully"
USER_ID_API_KEY_MISMATCH = "Supplied API Key and User Id do not match"
CREATE_PAYMENT_SUCCESS = "Payment Id created successfully"
CREATE_PAYMENT_FAIL = "Payment Id could not be created"
EXCEPTION_OCCURRED = "Exception! PLease check error"
GET_PAYMENT_LIST_SUCCESS = "Payment List for given User Id fetched successfully"
GET_PAYMENT_SESSION_LIST_SUCCESS = "Payment Session for given Payment Id fetched successfully"
CREATE_PAYMENT_SESSION_SUCCESS = "Payment Session Id created successfully"
DATE_FILTER_MISSING_FAIL = "Please add missing date filter"
PAYMENT_ID_NOT_FOUND_FAIL = "No Payment Id found for this user"
PURPLE_PAY_FACTORY_CONTRACT_UNAVAILABLE = "Purple Pay Factory Contract unavailable for this network"
CREATE_BURNER_ADDRESS_SUCCESS = "Burner Addresses Created Successfully"
CREATE_BURNER_ADDRESS_FAIL = "Error: Burner Addresses could not be created"
PAYMENT_COMPLETED_SUCCESS = "Success: Payment Completed"
BURNER_ADDRESS_UNAVAILABLE_AGAINST_PAYMENT_ID_FAIL = "No Burner Addresses available against this payment Id"
PAYMENT_STATUS_COMPLETED = "Completed"
PAYMENT_STATUS_IN_PROGRESS = "In Progress"
PAYMENT_ID_MISSING_FAIL = "Please send payment_id"
DEPLOY_STATUS_NOT_DEPLOY = 'not deploy'
DEPLOY_STATUS_FAILURE_DEPLOY = 'failure deploy'
DEPLOY_STATUS_INITIATED_DEPLOY = 'initiated deploy'
DEPLOY_STATUS_SUCCESS_DEPLOY = 'success deploy'

ASHARAN_ETHERSCAN_API_KEY = "G99IM24UWSWJT5EIWZA65NNPUE216M95QV"
ASHARAN_POLYGONSCAN_API_KEY = "Y6PDEQQNMRJTFR1WZKNC3KR3IDFB5SR7D7"

BLOCKEXPLORER_URLS = {
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

RPC_ENDPOINTS = {
    '5': {
        'name': 'goerli',
        'url': "https://rpc.ankr.com/eth_goerli"
    },
    '137': {
        'name': 'polygon mainnet',
        'url': "https://polygon-mainnet.public.blastapi.io"
    }
}

COINGECKO_EXCHANGE_RATE_1BTC_URL = "https://api.coingecko.com/api/v3/exchange_rates"
COINGECKO_EXCHANGE_RATE_VS_1USD_URL = "https://api.coingecko.com/api/v3/simple/price"
