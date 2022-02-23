
class KeyKind:
    TREZOR = "--trezor"
    LEDGER = "--ledger"
    PRIVATE = "--private-key"


class Network:
    LOCAL: str = "--rpc-url http://127.0.0.1:8545"
    AVAX_MAIN: str = "--rpc-url https://api.avax.network/ext/bc/C/rpc"
    AVAX_TEST: str = "--rpc-url https://api.avax-test.network/ext/bc/C/rpc"


class Signer:
    def __init__(
        self, pub: str = "", key_kind: str = KeyKind.PRIVATE, argument: str = ""
    ):
        self.key_kind = key_kind
        self.key_argument = argument
        self.pub = pub

    def get(self) -> str:
        return f"{self.key_kind} {self.key_argument}"

    def pub(self) -> str:
        return self.pub


TEST_SIGNER = Signer(
    "0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1",
    KeyKind.PRIVATE,
    "4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d",
)

from .deploy import *
