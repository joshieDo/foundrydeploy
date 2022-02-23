from .const import *
from . import Signer, Network, TEST_SIGNER, KeyKind, Deployer

#####################
# Context
#####################

SIGNERS = {}
DEPLOYERS = {}
CONTEXT = {}

#####################
# Helpers
#####################


def _sharing_is_caring():
    """
    Makes sure all deployers have access to all deployed addresses
    """
    addresses = {}

    for deployer in DEPLOYERS.keys():
        addresses.update(DEPLOYERS[deployer].addresses)

    for deployer in DEPLOYERS.keys():
        DEPLOYERS[deployer].addresses.update(addresses)


def _load_arguments(is_send: bool, arguments: list):
    args = []
    if is_send:

        if len(arguments) == 1 and is_send:
            tokens = arguments[0].split("(")
            function_name = tokens[0]
            arguments = "(" + tokens[1]
        else:
            function_name = arguments[0]
            arguments = arguments[1]

        args.append(function_name)

    if not arguments.startswith("(") or not arguments.endswith(")"):
        raise ValueError(f"arguments which should start with `(` and end with `)`")

    arguments = arguments[1:-1].split(",")

    for arg in arguments:
        arg = arg.strip()

        # check if * is present
        # 00*2 -> 0000
        str_repetition = arg.split("*")
        if len(str_repetition) > 1:
            arg = str_repetition[0].strip() * int(str_repetition[1].strip())

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

    NO_SKIP = ""
    close_skip = NO_SKIP

    token = ""
    length = len(line)
    for (index, ch) in enumerate(line):

        if close_skip == NO_SKIP and ch == '"':
            close_skip = ch
        if close_skip == NO_SKIP and ch == "(":
            close_skip = ")"
        elif ch == close_skip:
            close_skip = NO_SKIP

        if ch == " " and close_skip == NO_SKIP:
            tokens.append(token)
            token = ""
        else:
            token += ch

        if index == length - 1:
            tokens.append(token)

    return tokens


#####################
# Instantiators
#####################


def signer_from_context(context: dict):
    if SECTION_SIGNER_PUB in context:
        pub = context[SECTION_SIGNER_PUB]
    else:
        pub = ""

    return Signer(pub, KeyKind.PRIVATE, context[SECTION_SIGNER_PRIV])


def deployer_from_context(context: dict, contracts: list, name: str):

    signer = context[SECTION_DEPLOYER_SIGNER]

    if type(signer) == str and signer.startswith("0x"):
        signer = Signer("", KeyKind.PRIVATE, signer)
    elif "ledger" == signer:
        signer = Signer("", KeyKind.LEDGER)
    elif "trezor" == signer:
        signer = Signer("", KeyKind.TREZOR)
    elif "ganache" == signer:
        signer = TEST_SIGNER
    else:
        signer = SIGNERS[signer]

    network = context[SECTION_DEPLOYER_NETWORK]
    if network.startswith("http"):
        network = f"--rpc-url {network}"
    else:
        network = Network.networks[network]

    return Deployer(
        network,
        signer,
        contracts,
        is_legacy=(SECTION_DEPLOYER_LEGACY in context),  # for legacy transactions
        debug=(
            SECTION_DEPLOYER_DEBUG in context
        ),  # todo if True, prints the calling commands and raw output
        no_cache=(
            SECTION_DEPLOYER_NO_CACHE in context
        ),  # todo if True, prints the calling commands and raw output
        name=name,
    )


#####################
# Parser
#####################


def parse(script: str):

    next_section = 0

    context = {}
    paths = []
    missing_fields = []

    current_section = ""
    current_section_name = ""
    current_deployer = ""
    current_path = []

    lines = script.split("\n")
    num_lines = len(lines)
    for (linenu, line) in enumerate(lines):
        linenu += 1
        try:
            line = line.strip()

            _sharing_is_caring()

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
                        SIGNERS[current_section_name] = signer_from_context(
                            context[SECTION_SIGNER][current_section_name]
                        )

                    elif current_section == SECTION_DEPLOYER:
                        DEPLOYERS[current_section_name] = deployer_from_context(
                            context[SECTION_DEPLOYER][current_section_name],
                            context[SECTION_CONTRACTS],
                            current_section_name,
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
                context[SECTION_ID] = _name_check(current_section, tokens)

            #####################
            # CONTRACTS
            #####################

            elif current_section == SECTION_CONTRACTS:
                if SECTION_DEPLOYER in context:
                    raise ValueError(
                        "All contracts need to be declared before any deployer is declared."
                    )

                if line.startswith(SECTION_CONTRACTS):
                    if SECTION_CONTRACTS not in context:
                        context[SECTION_CONTRACTS] = []
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

                    context[SECTION_CONTRACTS].append(tokens)

            #####################
            # SIGNER
            #####################

            elif current_section == SECTION_SIGNER:
                # .signer
                # private 123123123
                # public 0x1123123123
                if line.startswith(SECTION_SIGNER):

                    if SECTION_SIGNER not in context:
                        context[SECTION_SIGNER] = {}

                    missing_fields = SECTION_SIGNER_REQUIRED
                    current_section_name = _name_check(current_section, tokens)
                    context[SECTION_SIGNER][current_section_name] = {}

                elif line.startswith(SECTION_SIGNER_PRIV):
                    context[SECTION_SIGNER][current_section_name][
                        SECTION_SIGNER_PRIV
                    ] = tokens[1]

                elif line.startswith(SECTION_SIGNER_PUB):
                    context[SECTION_SIGNER][current_section_name][
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
                if SECTION_CONTRACTS not in context:
                    raise ValueError(
                        "You need to declare contracts before declaring a deployer."
                    )

                if line.startswith(SECTION_DEPLOYER):
                    if SECTION_DEPLOYER not in context:
                        context[SECTION_DEPLOYER] = {}

                    missing_fields = SECTION_DEPLOYER_REQUIRED
                    current_section_name = _name_check(current_section, tokens)
                    context[SECTION_DEPLOYER][current_section_name] = {}
                elif line.startswith(SECTION_DEPLOYER_NO_CACHE):
                    context[SECTION_DEPLOYER][current_section_name][
                        SECTION_DEPLOYER_NO_CACHE
                    ] = True
                elif line.startswith(SECTION_DEPLOYER_DEBUG):
                    context[SECTION_DEPLOYER][current_section_name][
                        SECTION_DEPLOYER_DEBUG
                    ] = True
                elif line.startswith(SECTION_DEPLOYER_NETWORK):
                    network = tokens[1]
                    if network in SECTION_DEPLOYER_NETWORKS or network.startswith(
                        "http"
                    ):
                        context[SECTION_DEPLOYER][current_section_name][
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
                        or signer in SIGNERS
                        or signer.startswith("0x")
                    ):
                        context[SECTION_DEPLOYER][current_section_name][
                            SECTION_DEPLOYER_SIGNER
                        ] = signer
                    else:
                        raise ValueError(
                            f"signer `{signer}` not supported or found at deployer `{current_section_name}`"
                        )

                elif line.startswith(SECTION_DEPLOYER_LEGACY):
                    context[SECTION_DEPLOYER][current_section_name][
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
                    if SECTION_PATH not in context:
                        context[SECTION_PATH] = {}

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
            if linenu != num_lines:
                raise ValueError(f"##\nerror:\nline:{linenu}\n{line}\n{e}")
            raise ValueError(f"##\nerror:\n{e}")

    try:
        if current_section == SECTION_PATH:
            if type(current_deployer) != str and len(current_path) > 0:
                current_deployer.path(current_path)
    except Exception as e:
        print(current_path)
        raise ValueError(f"##\nerror:\n{e}")
