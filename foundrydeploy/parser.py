from .const import *
from . import Signer, Network, TEST_SIGNER, KeyKind, Deployer

#####################
# Context
#####################

SIGNERS = {}
DEPLOYERS = {}

#####################
# Helpers
#####################


def _load_arguments(is_send: bool, arguments: list):
    args = []
    if is_send:
        # function name
        args.append(arguments[0])
        # function args
        arguments = arguments[1]

    if not arguments.startswith("(") or not arguments.endswith(")"):
        raise ValueError(f"arguments which should start with `(` and end with `)`")

    arguments = arguments[1:-1].split(",")

    for arg in arguments:
        arg = arg.strip()
        args.append(arg)
    return args


def _name_check(current_section: str, tokens: list, field_desc="field") -> str:
    if len(tokens) == 1:
        raise ValueError(
            f"section `{current_section}` missing {field_desc}. `{current_section} ???? "
        )
    return tokens[1]


def _remove_field(field: str, missing_fields: list):
    try:
        missing_fields.remove(field)
    except:
        pass
    return missing_fields


def tokenize(line: str):
    tokens = []
    skip = False

    token = ""
    length = len(line)
    for (index, ch) in enumerate(line):
        if ch == '"':
            skip = not skip
        elif ch == " " and not skip:
            tokens.append(token)
            token = ""
        else:
            token += ch
        if index == length - 1:
            tokens.append(token)

    # print('tokens')
    # print(tokens)
    return tokens


#####################
# Instantiators
#####################


def signer_from_details(details: dict):
    if SECTION_SIGNER_PUB in details:
        pub = details[SECTION_SIGNER_PUB]
    else:
        pub = ""

    return Signer(pub, KeyKind.PRIVATE, details[SECTION_SIGNER_PRIV])


def deployer_from_details(details: dict, contracts: list):

    signer = details[SECTION_DEPLOYER_SIGNER]

    if type(signer) == str and signer.startswith("0x"):
        signer = Signer("", KeyKind.PRIVATE, signer)
    elif "ledger" == signer:
        signer = Signer("", KeyKind.LEDGER)
    elif "trezor" == signer:
        signer = Signer("", KeyKind.TREZOR)
    elif "ganache" == signer:
        signer = TEST_SIGNER
    else:
        signer = signers[signer]

    network = details[SECTION_DEPLOYER_NETWORK]
    if network.startswith("http"):
        network = f"--rpc-url {network}"
    else:
        network = Network.networks[network]

    return Deployer(
        network,
        signer,
        contracts,
        is_legacy=SECTION_DEPLOYER_LEGACY in details,  # for legacy transactions
        # debug = SECTION_DEPLOYER_LEGACY in global, # todo if True, prints the calling commands and raw output
    )


#####################
# Parser
#####################


def parse(script: str):

    next_section = 0

    details = {}
    paths = []
    missing_fields = []

    current_section = ""
    current_section_name = ""
    current_deployer = ""
    current_path = []

    lines = script.split("\n")
    num_lines = len(lines)
    for (linenu, line) in enumerate(lines):
        try:
            line = line.strip()

            if (linenu == num_lines - 1) and current_section == SECTION_PATH:
                if type(current_deployer) != str:
                    current_deployer.path(current_path)

            # Skip if comment or line is empty
            if len(line) == 0 or line.startswith("#"):
                continue

            tokens = tokenize(line)

            # Is it the beginning of a section
            if line.startswith("."):
                if len(missing_fields) > 0:
                    raise ValueError(
                        f"section `{current_section}` missing the following fields ${missing_fields}"
                    )

                section = tokens[0]
                if section in SECTIONS:
                    if current_section == SECTION_SIGNER:
                        SIGNERS[current_section_name] = signer_from_details(
                            details[SECTION_SIGNER][current_section_name]
                        )

                    elif current_section == SECTION_DEPLOYER:
                        DEPLOYERS[current_section_name] = deployer_from_details(
                            details[SECTION_DEPLOYER][current_section_name],
                            details[SECTION_CONTRACTS],
                        )

                    elif current_section == SECTION_PATH:
                        current_deployer.path(current_path)
                        current_path = []

                    current_section = section
                else:
                    raise ValueError(
                        f"error at line({linenu}) | `.` is a reserved first character "
                    )

            # if it exists
            missing_fields = _remove_field(tokens[0], missing_fields)

            #####################
            # ID
            #####################
            if current_section == SECTION_ID:
                # ".id FILE_ID"
                details[SECTION_ID] = _name_check(current_section, tokens)

            #####################
            # CONTRACTS
            #####################

            elif current_section == SECTION_CONTRACTS:
                if SECTION_DEPLOYER in details:
                    raise ValueError(
                        "All contracts need to be declared before any deployer is declared."
                    )

                if line.startswith(SECTION_CONTRACTS):
                    if SECTION_CONTRACTS not in details:
                        details[SECTION_CONTRACTS] = []
                else:
                    num_tokens = len(tokens)
                    if num_tokens < 2 or num_tokens > 3:
                        raise ValueError(
                            "contracts have the following format: `label address` or `label contract_path` or `label contract_path address`"
                        )

                    if tokens[1].startswith('"') and tokens[1].endswith('"'):
                        tokens[1] = tokens[1][1:-1]
                    elif tokens[1].startswith("0x"):
                        if num_tokens == 2:
                            tokens.append(tokens[1])
                        tokens[1] = ""

                    details[SECTION_CONTRACTS].append(tokens)

            #####################
            # SIGNER
            #####################

            elif current_section == SECTION_SIGNER:
                # .signer
                # private 123123123
                # public 0x1123123123
                if line.startswith(SECTION_SIGNER):

                    if SECTION_SIGNER not in details:
                        details[SECTION_SIGNER] = {}

                    missing_fields = SECTION_SIGNER_REQUIRED
                    current_section_name = _name_check(current_section, tokens)
                    details[SECTION_SIGNER][current_section_name] = {}

                elif line.startswith(SECTION_SIGNER_PRIV):
                    details[SECTION_SIGNER][current_section_name][
                        SECTION_SIGNER_PRIV
                    ] = tokens[1]

                elif line.startswith(SECTION_SIGNER_PUB):
                    details[SECTION_SIGNER][current_section_name][
                        SECTION_SIGNER_PUB
                    ] = tokens[1]
                else:
                    raise ValueError(
                        f"error at line({linenu}) | section: {current_section} "
                    )

            #####################
            # DEPLOYER
            #####################

            elif current_section == SECTION_DEPLOYER:
                # .deployer
                # network local | avax | fuji | http...
                # signer local | test | trezor | ledger
                # legacy
                if SECTION_CONTRACTS not in details:
                    raise ValueError(
                        "You need to declare contracts before declaring a deployer."
                    )

                if line.startswith(SECTION_DEPLOYER):
                    if SECTION_DEPLOYER not in details:
                        details[SECTION_DEPLOYER] = {}

                    missing_fields = SECTION_DEPLOYER_REQUIRED
                    current_section_name = _name_check(current_section, tokens)
                    details[SECTION_DEPLOYER][current_section_name] = {}

                elif line.startswith(SECTION_DEPLOYER_NETWORK):
                    network = tokens[1]
                    if network in SECTION_DEPLOYER_NETWORKS or network.startswith(
                        "http"
                    ):
                        details[SECTION_DEPLOYER][current_section_name][
                            SECTION_DEPLOYER_NETWORK
                        ] = network
                    else:
                        raise ValueError(
                            f"network `{network}` not supported at deployer `{current_section_name}`"
                        )

                elif line.startswith(SECTION_DEPLOYER_SIGNER):
                    signer = tokens[1]
                    if (
                        signer in SECTION_DEPLOYER_SIGNERS
                        or signer in details[SECTION_DEPLOYER].keys()
                        or signer.startswith("0x")
                    ):
                        details[SECTION_DEPLOYER][current_section_name][
                            SECTION_DEPLOYER_SIGNER
                        ] = signer
                    else:
                        raise ValueError(
                            f"signer `{signer}` not supported or found at deployer `{current_section_name}`"
                        )

                elif line.startswith(SECTION_DEPLOYER_LEGACY):
                    details[SECTION_DEPLOYER][current_section_name][
                        SECTION_DEPLOYER_LEGACY
                    ] = True

                else:
                    raise ValueError(
                        f"error at line({linenu}) | section: {current_section} "
                    )

            #####################
            # PATH / USE
            #####################

            elif current_section == SECTION_PATH:

                if DEPLOYERS.keys() == []:
                    raise ValueError(f"you need a deployer for .use")

                if line.startswith(SECTION_PATH):
                    if SECTION_PATH not in details:
                        details[SECTION_PATH] = {}

                    deployer_name = _name_check(
                        current_section, tokens, "deployer name"
                    )
                    current_deployer = DEPLOYERS[deployer_name]
                else:
                    action = tokens[0]
                    if action == SECTION_PATH_SKIP0:
                        current_path.append((Deployer.SKIP_START, 0, 0))
                        continue
                    elif action == SECTION_PATH_SKIP1:
                        current_path.append((Deployer.SKIP_END, 0, 0))
                        continue

                    contract_label = tokens[1]

                    if line.startswith(SECTION_PATH_DEPLOY):
                        arguments = _load_arguments(False, tokens[2])
                        current_path.append(
                            (Deployer.DEPLOY, contract_label, arguments)
                        )
                    elif line.startswith(SECTION_PATH_SEND):
                        arguments = tokenize(
                            line.split(tokens[0] + " " + tokens[1])[1].strip()
                        )
                        arguments = _load_arguments(True, arguments)
                        current_path.append((Deployer.SEND, contract_label, arguments))
                    else:
                        raise ValueError(
                            f"error at line({linenu}) | section: {current_section} "
                        )
        except Exception as e:
            raise ValueError(f"##\nerror\nline:{linenu}\n{line}\n{e}")
