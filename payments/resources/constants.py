EXCEPTION_OCCURRED = "Uh-oh, spaghetti-o's! Something wonky happened. Time to pull out the debugging magnifying glass. 🕵️"
GET_PAYMENT_STATUS_SUCCESS = "Woot woot! We successfully fetched your payment status. It's standing tall and proud."
USER_ID_API_KEY_MISMATCH = "Aww, snap! Your User ID and API key are not on speaking terms. They're mismatched, you see."
CREATE_PAYMENT_SUCCESS = "Super-duper! You've successfully created a payment request. Ching-ching goes the digital cash register! 💰"
CREATE_PAYMENT_FAIL = "Rats! Creating your payment request failed. Try again, will you?"
GET_PAYMENT_LIST_SUCCESS = "Yahoo! We've successfully fetched your payments list. It's a digital shopping spree!"

GET_PAYMENT_SESSION_LIST_SUCCESS = "Hooray! We've fetched your payment session list successfully. It's party time!"
CREATE_PAYMENT_SESSION_SUCCESS = "Woohoo! You've successfully created a payment session. It's like your own little digital party."

DATE_FILTER_MISSING_FAIL = "Uh-oh! We're missing a date filter here. Time isn't on our side, it seems."
PAYMENT_ID_NOT_FOUND_FAIL = "Drat! The Payment ID you're looking for is as elusive as Bigfoot."
PURPLE_PAY_FACTORY_CONTRACT_UNAVAILABLE = "Shoot! The Purple Pay Factory contract is unavailable. Maybe it's gone on a coffee break?"
CREATE_BURNER_ADDRESS_SUCCESS = "Yippee! You've successfully created a burner address. Just don't burn any bridges, okay?"
CREATE_BURNER_ADDRESS_FAIL = "Dang it! Your burner address creation failed. Should've added more sizzle!"

PAYMENT_COMPLETED_SUCCESS = "Yay! Your payment completed successfully. The digital cash register is ringing!"
BURNER_ADDRESS_UNAVAILABLE_AGAINST_PAYMENT_ID_FAIL = "Oh no! There's no burner address available for this payment ID. Maybe it's on vacation?"
PAYMENT_STATUS_COMPLETED = "Completed"
PAYMENT_STATUS_IN_PROGRESS = "In Progress"
PAYMENT_ID_MISSING_FAIL = "Oh no! We're missing a Payment ID. It's like a sandwich without the filling."
DEPLOY_STATUS_NOT_DEPLOY = 'not deploy'
DEPLOY_STATUS_FAILURE_DEPLOY = 'failure deploy'
DEPLOY_STATUS_INITIATED_DEPLOY = 'initiated deploy'
DEPLOY_STATUS_SUCCESS_DEPLOY = 'success deploy'

ASHARAN_ETHERSCAN_API_KEY = "G99IM24UWSWJT5EIWZA65NNPUE216M95QV"
ASHARAN_POLYGONSCAN_API_KEY = "Y6PDEQQNMRJTFR1WZKNC3KR3IDFB5SR7D7"
ASHARAN_SUBSCAN_API_KEY = "a34ef694af434165a4bfbef9dca812c8"
ASHARAN_BLOCKSCOUT_API_KEY = "a85e1005-1679-40c2-b17d-3c6d8dc1175b"

BLOCKEXPLORER_URLS = {
    '5': {
        'name': 'goerli',
        'block_explorer': 'etherscan',
        'base_url': 'https://api-goerli.etherscan.io/api',
        'api_key': ASHARAN_ETHERSCAN_API_KEY
    },
    '137': {
        'name': 'polygon mainnet',
        'block_explorer': 'blastapi',
        'base_url': 'https://api.polygonscan.com/api',
        'api_key': ASHARAN_POLYGONSCAN_API_KEY
    },
    '80001': {
        'name': 'polygon mumbai',
        'block_explorer': 'polygonscan',
        'base_url': 'https://api-testnet.polygonscan.com/api',
        'api_key': ASHARAN_POLYGONSCAN_API_KEY
    },
    '592': {
        'name': 'astar mainnet',
        'block_explorer': 'blockscout',
        'base_url': 'https://blockscout.com/astar/api',
        'api_key': ASHARAN_BLOCKSCOUT_API_KEY
    },
    '5001': {
        'name': 'mantle testnet',
        'block_explorer': 'blockscout',
        'base_url': 'https://explorer.testnet.mantle.xyz/api',
        'api_key': ASHARAN_BLOCKSCOUT_API_KEY
    },
'5000': {
        'name': 'mantle mainnet',
        'block_explorer': 'mantle explorer',
        'base_url': 'https://explorer.mantle.xyz/api',
        'api_key': ASHARAN_BLOCKSCOUT_API_KEY
    },
'59144': {
        'name': 'linea mainnet',
        'block_explorer': 'blockscout',
        'base_url': 'https://blockscout.com/astar/api',
        'api_key': ASHARAN_BLOCKSCOUT_API_KEY
    },
'59140': {
        'name': 'linea testnet',
        'block_explorer': 'blockscout',
        'base_url': 'https://blockscout.com/astar/api',
        'api_key': ASHARAN_BLOCKSCOUT_API_KEY
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
    },
    '80001': {
        'name': 'polygon mumbai',
        'url': "https://polygon-testnet.public.blastapi.io"
    },
    '592': {
        'name': 'astar mainnet',
        'url': "https://astar.public.blastapi.io"
    },
    '81': {
        'name': 'shibuya',
        'url': "https://evm.shibuya.astar.network"
    },
'5000': {
        'name': 'mantle mainnet',
        'url': "https://mantle-mainnet.public.blastapi.io"
    },
'5001': {
        'name': 'mantle testnet',
        'url': "https://rpc.testnet.mantle.xyz"
    },
'59144': {
        'name': 'linea mainnet',
        'url': "https://linea.blockpi.network/v1/rpc/public"
    },
'59140': {
        'name': 'linea testnet',
        'url': "https://rpc.goerli.linea.build"
    }
}

COINGECKO_EXCHANGE_RATE_1BTC_URL = "https://api.coingecko.com/api/v3/exchange_rates"
COINGECKO_EXCHANGE_RATE_VS_1USD_URL = "https://api.coingecko.com/api/v3/simple/price"
MAINNET = 'mainnet'
TESTNET = 'testnet'


ECOMMERCE = 'ECOMMERCE'
ONE_TIME_PAYMENT = 'ONE_TIME_PAYMENT'
SCAN_AND_PAY = 'SCAN_AND_PAY'
P2P = 'P2P'
NA = 'NA'

PAYMENT_TYPES = ['ecommerce', 'one time payment', 'scan and pay', 'p2p']
PAYMENT_TYPES_V2 = [ECOMMERCE, ONE_TIME_PAYMENT, SCAN_AND_PAY, P2P]
DEVICE_TYPES = ["APP", "WEB", "WAP", "OTHERS"]
OS_TYPES = ['ANDROID', 'IOS', 'WINDOWS', 'LINUX', 'OTHERS']
USDOLLAR = 'USD'
PAYMENT_TYPES_MAPPING = {
    'ecommerce': 'merchant ecommerce',
    'one time payment': 'one time',
    'scan and pay': 'merchant pos',
    'p2p': 'p2p',
    'na': 'na'
}

PAYMENT_TYPES_MAPPING_V2 = {
    ECOMMERCE: 'merchant ecommerce',
    ONE_TIME_PAYMENT: 'one time',
    SCAN_AND_PAY: 'merchant pos',
    P2P: 'p2p',
    NA: 'na'
}

PAYMENT_TYPES_DB_TO_ENUM_MAPPING = {
    'merchant ecommerce': 'ecommerce',
    'one time': 'one time payment',
    'merchant pos': 'scan and pay',
    'p2p': 'p2p',
    'na': 'na'
}

PAYMENT_TYPES_DB_TO_ENUM_MAPPING_V2 = {
    'merchant ecommerce': ECOMMERCE,
    'one time': ONE_TIME_PAYMENT,
    'merchant pos': SCAN_AND_PAY,
    'p2p': P2P,
    'na': NA
}

CHAIN_IDS = ['80001', '81', '137', '592', '5001', '5000', '59144', '59140']
