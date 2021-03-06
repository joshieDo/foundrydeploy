import pickle, json, subprocess, hashlib
from loguru import logger
from . import Signer
from .log import _info, _debug, _error


class Deployer:

    DEPLOY = 0
    SEND = 1
    SKIP_START = 2
    SKIP_END = 3

    def __init__(
        self,
        rpc: str,
        signer: Signer,
        contracts: list,
        is_legacy: bool,
        debug=False,
        cache_path="cache",
        no_cache=False,
        name="",
    ):
        _info("#####")
        self.name = name
        if len(name) > 0:
            _info(f"# Deployer: `{name}`")

        _info(f"# RPC: `{rpc}`")

        self.rpc = rpc
        self.contracts = {}
        self.addresses = {}
        self.contract_signatures = {}
        self.transactions = []
        self.context = {}

        # Load from cache if it exists
        self.cache_path = (
            cache_path
            + "/deploy_"
            + hashlib.sha256((name + rpc).encode()).hexdigest()[:8]
        )
        if not no_cache:
            self.load_from_cache(self.cache_path)

        # Add/Replace cached values
        self.add_contracts(contracts)
        self.signer = signer
        self.debug = debug

        self.is_legacy = ""
        if is_legacy:
            self.is_legacy = "--legacy"

        _info("#####\n")

    ###########################
    # Helpers
    ###########################

    def print_details(self, sigs: bool = False):
        _info(
            f"""# Transaction Sequence
{self.transactions}"""
        )
        _info(
            f"""# Addresses
{self.addresses}"""
        )

        if sigs:
            _info(self.contracts)
            _info(self.contract_signatures)

    def _handle_arg(self, arg: str) -> str:
        if arg.startswith("[") and arg.endswith("]"):
            args = []
            for _arg in arg[1:-1].split(","):
                args.append(self._handle_arg(_arg))
            arg = "[" + ",".join(args) + "]"

        elif arg.startswith("$"):
            contract_label = arg[1:]
            arg = f"{self.addresses[contract_label]}"

        elif arg.startswith("#PUB"):
            arg = f"{self.signer.public_key()}"

        return arg

    ###########################
    # Cache
    ###########################

    def load_from_cache(self, cache_path):
        try:
            deployer = Deployer.load(cache_path)
            _info(f"# Loading cache at `{cache_path}`")
            self.contracts = deployer.contracts
            self.addresses = deployer.addresses
            self.contract_signatures = deployer.contract_signatures

        except FileNotFoundError:
            _info(f"# Starting cache at `{cache_path}`")
            pass

    def load(cache_path):
        with open(cache_path, "rb") as f:
            return pickle.load(f)

    def save(self):
        with open(self.cache_path, "wb") as f:
            pickle.dump(self, f)

    ###########################
    # Contract loading
    ###########################

    def load_contract_signatures(self, contract_label: str, contract_path: str):
        """
        Reads ABI from out/ folder generated by foundry and loads out function names and signatures
        """
        contract_file_path, contract_name = contract_path.split(":")

        out = {}
        for chunk in contract_file_path.split("/"):
            if chunk.endswith(".sol"):
                with open(f"out/" + chunk + "/" + contract_name + ".json") as f:
                    out = json.load(f)
                    break

        abi = out["abi"]

        signatures = {}
        for obj in abi:
            if obj["type"] == "function":

                # Get inputs
                inputs = []
                for inp in obj["inputs"]:
                    inputs.append(inp["type"])
                inputs = ",".join(inputs)

                # Get Name
                func_name = obj["name"]
                signature = "{}({})".format(func_name, inputs)

                if contract_path not in self.contract_signatures:
                    self.contract_signatures[contract_path] = {}

                self.contract_signatures[contract_path][func_name] = signature

    def add_contracts(self, contracts: [tuple]):
        """
        Example:
            contracts = [
                ("CONTRACT_1_LABEL", "src/Contract1.sol:ContractName1", "0x1111111111111111111111111111111111111111"),
                ("CONTRACT_2_LABEL", "src/Contract2.sol:ContractName2")
            ]
        """
        for contract in contracts:
            if contract[1] != "":
                self.contracts[contract[0]] = contract[1]
                self.load_contract_signatures(contract[0], contract[1])

            if len(contract) == 3:
                self.addresses[contract[0]] = contract[2]

    ###########################
    # OS execution
    ###########################

    def run(self, cmd: str):
        proc = subprocess.Popen(
            cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )
        result = (proc.stdout.read()).decode()
        err = (proc.stderr.read()).decode()

        proc.wait()

        if not proc.returncode == 0:
            self.save()
            proc.wait()

            _error(f"command:\n{cmd}")
            _error(f"result:\n{err}\n\r")
            self.print_details()
            exit(1)
        elif self.debug:
            _debug(f"command:\n{cmd}")
            _debug(f"result:\n{result}\n\r")

        return result

    ###########################
    # Foundry Calls
    ###########################

    def _store_transaction_details(self, contract_label: str, output: str):
        # Store deployed address
        address = ""
        for line in output.splitlines():
            if "Deployed to: " in line:
                address = line[-42:]
                self.addresses[contract_label] = address

            if "Transaction hash: " in line:
                tx = line[-66:]
                self.transactions.append(tx)

            if "transactionHash" in line:
                tx = line[-67:][:-1]
                self.transactions.append(tx)

    def deploy(self, contract_label: str, args: str) -> str:
        """
        Calls `$ forge create`
        """

        # Skips deployment if there's an address cached for this contract label
        if contract_label in self.addresses:
            _info(
                f"Skipping ${contract_label} deployment. Has address: {self.addresses[contract_label]}"
            )
            return self.addresses[contract_label]

        contract_path = self.contracts[contract_label]

        # Stringify arguments
        const = ""
        for arg in args:
            arg = self._handle_arg(arg)
            if arg.startswith("[") and arg.endswith("]"):
                arg = f'"{arg}"'
            const += f"--constructor-args {arg} "

        _info(f"{self.name} | Deploying | ${contract_label}...")

        # Call `forge create`
        result = self.run(
            f"forge create {self.rpc} {self.is_legacy} {self.signer.get()} {contract_path} {const}"
        )

        self._store_transaction_details(contract_label, result)

    def send(self, contract_label: str, address: str, _args: str) -> str:
        """
        Calls `$ cast send`
        """

        function_name = _args[0]

        # Get function signature if not given
        if "(" not in function_name:

            if contract_label not in self.contracts:
                raise ValueError(
                    f"{contract_label} has no contract specified, so you need to specify the function signature"
                )

            contract_path = self.contracts[contract_label]

            if function_name not in self.contract_signatures[contract_path]:
                raise ValueError(f"{function_name} does not exist in {contract_path}")

            _args[0] = (
                '"' + self.contract_signatures[contract_path][function_name] + '"'
            )
        else:
            _args[0] = '"' + function_name + '"'

        _info(f"{self.name} | Sending   | ${contract_label} {function_name}(...) ")

        # Stringify arguments
        args = ""
        for index, arg in enumerate(_args):
            arg = self._handle_arg(arg)
            if arg.startswith("[") and arg.endswith("]"):
                arg = f'"{arg}"'
            args += f" {arg} "

        result = self.run(
            f"cast send {address} {self.rpc} {self.is_legacy} {self.signer.get()} {args}"
        )

        self._store_transaction_details(contract_label, result)

    ###########################
    # Action Flow
    ###########################

    def path(self, path: list):
        """
        Example:

            path = [
                (Deployer.SKIP_START,0,0),
                (Deployer.DEPLOY, "CONTRACT_0_LABEL", ["Arg1", "Arg2", "1ether"]),
                (Deployer.DEPLOY, "CONTRACT_1_LABEL", ["Arg1", "Arg2", "1ether"]),
                (Deployer.SKIP_END,0,0),

                (Deployer.SEND, "CONTRACT_1_LABEL",   ["ContractMethodName", "9999999999", "00"*32, "00"*32, "0"]),

                (Deployer.DEPLOY, "CONTRACT_2_LABEL", ["Arg1", "Arg2", "12ether"])
            ]

        Will skip the first Deploy and execute the rest, one after the other.
        """
        skipping = False
        for (action, contract_contract_label, arguments) in path:

            if action == Deployer.SKIP_START:
                skipping = True
            elif action == Deployer.SKIP_END:
                skipping = False
                continue

            if skipping:
                continue
            elif action == Deployer.SEND:

                if contract_contract_label not in self.addresses:
                    raise ValueError(
                        f"{contract_contract_label} has not been deployed."
                    )

                self.send(
                    contract_contract_label,
                    self.addresses[contract_contract_label],
                    arguments,
                )
            elif action == Deployer.DEPLOY:
                self.deploy(contract_contract_label, arguments)

        self.save()
        self.print_details()
