#####################
# Sections
#####################

SECTION_ID = ".id"
SECTION_CONTRACTS = ".contracts"
SECTION_SIGNER = ".signer"
SECTION_DEPLOYER = ".deployer"
SECTION_PATH = ".use"

SECTIONS = [
    SECTION_ID,
    SECTION_CONTRACTS,
    SECTION_SIGNER,
    SECTION_DEPLOYER,
    SECTION_PATH,
]

#####################
# Signer
#####################

SECTION_SIGNER_PRIV = "private"
SECTION_SIGNER_PUB = "public"
SECTION_SIGNER_REQUIRED = [SECTION_SIGNER_PRIV]

#####################
# Deployer
#####################

SECTION_DEPLOYER_SIGNERS = ["trezor", "ledger", "ganache"]
SECTION_DEPLOYER_NETWORKS = ["ava", "fuji", "local"]
SECTION_DEPLOYER_NETWORK = "network"
SECTION_DEPLOYER_SIGNER = "signer"
SECTION_DEPLOYER_LEGACY = "legacy"
SECTION_DEPLOYER_NO_CACHE = "no_cache"
SECTION_DEPLOYER_DEBUG = "debug"
SECTION_DEPLOYER_REQUIRED = [SECTION_DEPLOYER_SIGNER, SECTION_DEPLOYER_NETWORK]

#####################
# USE
#####################
SECTION_PATH_DEPLOY = "deploy"
SECTION_PATH_SEND = "send"
SECTION_PATH_SKIP0 = "skip_start"
SECTION_PATH_SKIP1 = "skip_end"
SECTION_PATH_ACTIONS = [
    SECTION_PATH_DEPLOY,
    SECTION_PATH_SEND,
    SECTION_PATH_SKIP0,
    SECTION_PATH_SKIP1,
]
