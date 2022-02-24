.id whatever

.declare
    random_param 99
    callme functionName(uint256)

.contracts
    LABEL1 "src/Contract1.sol:ContractName1" 0x1111111111111111111111111111111111111111
    LABEL2 "src/Contract2.sol:ContractName2"
    LABEL3 0xeea2fc1d255fd28aa15c6c2324ad40b03267f9c5

.signer mySigner1
    private 4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d
    # pub 0x3333333333333333333333333333333333333333

.signer mySigner2
    private 4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d
    # pub 0x3333333333333333333333333333333333333333

.deployer myDeployer1
    legacy
    signer mySigner2
    network http://127.0.0.1:8545

.deployer myDeployer2
    legacy
    # debug
    # no_cache

    network local
    # network fuji
    # network ava

    signer ganache
    # signer ledger
    # signer trezor

.use myDeployer1

    # Skips deploy and send
    skip_start
    deploy LABEL1 (Arg1, Arg2, 11ether)
    send LABEL1 functionName (9999999999, 00 * 32, 00 * 32, 0)
    skip_end

    deploy LABEL2 ($LABEL1, arg2, 1gwei)
    deploy LABEL2 (#PUB, arg2, 1gwei)

    # Valid
    send LABEL2 functionName(99999)

.use myDeployer2
    send LABEL2 functionName (99999)
    send LABEL2 functionName(uint256) (99999)
    send LABEL2 @callme (@random_param)

    # seeded before
    send LABEL3 functionName(uint256) (@random_param)
    send LABEL3 @callme (@random_param)

    # Address-only variables need to have full function signature
    # send LABEL3 functionName(uint256) (@random_param)

    # Invalid
    # send LABEL2 functionName(uint256)(99999)
