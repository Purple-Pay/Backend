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

PAYMENT_COMPLETED_SUCCESS = "Success: Payment Completed"
BURNER_ADDRESS_UNAVAILABLE_AGAINST_PAYMENT_ID_FAIL = "No Burner Addresses available against this payment Id"
PAYMENT_STATUS_COMPLETED = "Completed"
PAYMENT_STATUS_IN_PROGRESS = "In Progress"
PAYMENT_ID_MISSING_FAIL = "Oh no! We're missing a Payment ID. It's like a sandwich without the filling."
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
