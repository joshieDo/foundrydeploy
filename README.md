# foundrydeploy

Limited scripting (declarative?) language to implement a basic deployment pipeline using [foundry](https://github.com/gakonst/foundry).  Can also be used as python library.

Still WIP.


**Deployment script should be called from the foundry project with the build artifacts present at `out/`.**

**For the lexicon check both: [FD Script](#fd-script) (real-use) and [example/deploy.fd](./example/deploy.fd) (expands on available vocabulary)** 

## Table of Contents
- [foundrydeploy](#foundrydeploy)
  - [Table of Contents](#table-of-contents)
  - [Description](#description)
    - [Install](#install)
  - [Usage](#usage)
    - [FD Script](#fd-script)
      - [deploy.fd](#deployfd)
      - [output](#output)
    - [As a python library](#as-a-python-library)
      - [deploy.py](#deploypy)

## Description

* Cache deployments identified by `sha256(ETH_RPC, deployer_name)`
* Declare limited variables
* Contract labels
* Only requires the function name if the contract is declared with a path. Extracts the ABI present at `out/***.sol/***.json`
* Using labels as **arguments** requires preceeding it with "$". eg: `$LABEL1`
* Signer public keys can be used as an argument by invoking it as such: `#PUB`

### Install

```bash
pip install foundrydeploy
```

## Usage
### FD Script
```bash
$ python -m foundrydeploy deploy.fd
```

#### deploy.fd
```ruby
.id name

.declare
    EMPTY_BYTES_32 00*32 # * multiples the occorrences of the prefix string

    TADPOLE_URI "uri"

    POND_EMISSION_RATE 0.0001ether
    STREAM_EMISSION_RATE 0.0001ether
    BONUS_EMISSION_RATE 0.0001ether
    REWARD_EMISSION_RATE 0.0001ether


.contracts
    # NFTs
    HOPPER "src/Hopper.sol:HopperNFT"
    TADPOLE "src/Tadpole.sol:Tadpole"

    # Currencies
    FLY "src/Fly.sol:Fly"
    VEFLY "src/veFly.sol:veFly"

    # Adventures
    POND "src/zones/Pond.sol:Pond"
    STREAM "src/zones/Pond.sol:Pond"
    BREEDING "src/zones/Breeding.sol:Breeding"

    BALLOT "src/Ballot.sol:Ballot"

.deployer my_deployer
    network local
    signer ganache
    legacy
    # no_cache
    debug

.use my_deployer
    ###
    # Deployments
    ##

    deploy HOPPER (Hopper, hopper, 11ether)
    deploy TADPOLE (Tad, Tad)

    deploy FLY (FLY, FLY)
    deploy VEFLY ($FLY, 1, 1, 100)

    deploy POND ($FLY, $VEFLY, $HOPPER)
    deploy STREAM ($FLY, $VEFLY, $HOPPER)
    deploy BALLOT ($FLY, $VEFLY)

    deploy BREEDING ($FLY, $HOPPER, $TADPOLE, 0.1ether)

    ####
    # Setting Parameters
    ####
    send HOPPER setSaleDetails(1, @EMPTY_BYTES_32, @EMPTY_BYTES_32, 0)

    send TADPOLE setBreedingSpot ($BREEDING)
    # send TADPOLE setExchanger($EXCHANGER)
    send TADPOLE setBaseURI(@TADPOLE_URI)

    send POND setEmissionRate(@POND_EMISSION_RATE)
    send POND setBallot($BALLOT)

    send STREAM setEmissionRate(@POND_EMISSION_RATE)
    send STREAM setBallot($BALLOT)

    send FLY addZone($POND)
    send FLY addZone($STREAM)
    send FLY addZone($BALLOT)

    send BALLOT addZones([$POND,$STREAM])
    send BALLOT setBonusEmissionRate(@BONUS_EMISSION_RATE)
    send BALLOT setCountRewardRate(@REWARD_EMISSION_RATE)
    send BALLOT openBallot()

    send VEFLY addBallot($BALLOT)

    send HOPPER addZone($POND)
    send HOPPER addZone($STREAM)

    ## Test Accounts
    send HOPPER setApprovalForAll($POND, true)
    send HOPPER setApprovalForAll($STREAM, true)
    send FLY approve($VEFLY, 1000000000ether)
```
#### output
```bash
2022-02-24T18:15:43.298256+0400 | INFO | #####
2022-02-24T18:15:43.298374+0400 | INFO | # Deployer: `my_deployer`
2022-02-24T18:15:43.298401+0400 | INFO | # RPC: `--rpc-url http://127.0.0.1:8545`
2022-02-24T18:15:43.298568+0400 | INFO | # Loading cache at `cache/deploy_bace3878`
2022-02-24T18:15:43.300568+0400 | INFO | #####

2022-02-24T18:15:43.301200+0400 | INFO | Skipping $HOPPER deployment. Has address: 0xe78a0f7e598cc8b0bb87894b0f60dd2a88d6a8ab
2022-02-24T18:15:43.301345+0400 | INFO | Skipping $TADPOLE deployment. Has address: 0x5b1869d9a4c187f2eaa108f3062412ecf0526b24
2022-02-24T18:15:43.301394+0400 | INFO | Skipping $FLY deployment. Has address: 0xcfeb869f69431e42cdb54a4f4f105c19c080a601
2022-02-24T18:15:43.301424+0400 | INFO | Skipping $VEFLY deployment. Has address: 0x254dffcd3277c0b1660f6d42efbb754edababc2b
2022-02-24T18:15:43.301455+0400 | INFO | Skipping $POND deployment. Has address: 0xc89ce4735882c9f0f0fe26686c53074e09b0d550
2022-02-24T18:15:43.301487+0400 | INFO | Skipping $STREAM deployment. Has address: 0xd833215cbcc3f914bd1c9ece3ee7bf8b14f841bb
2022-02-24T18:15:43.301544+0400 | INFO | Skipping $BALLOT deployment. Has address: 0x9561c133dd8580860b6b7e504bc5aa500f0f06a7
2022-02-24T18:15:43.301659+0400 | INFO | Skipping $BREEDING deployment. Has address: 0xe982e462b094850f12af94d21d470e21be9d0e9c
2022-02-24T18:15:43.301747+0400 | INFO | my_deployer | Sending   | $HOPPER setSaleDetails(...) 
2022-02-24T18:15:43.403211+0400 | INFO | my_deployer | Sending   | $TADPOLE setBreedingSpot(...) 
2022-02-24T18:15:43.482563+0400 | INFO | my_deployer | Sending   | $TADPOLE setBaseURI(...) 
2022-02-24T18:15:43.546522+0400 | INFO | my_deployer | Sending   | $POND setEmissionRate(...) 
2022-02-24T18:15:43.580965+0400 | INFO | my_deployer | Sending   | $POND setBallot(...) 
2022-02-24T18:15:43.642924+0400 | INFO | my_deployer | Sending   | $STREAM setEmissionRate(...) 
2022-02-24T18:15:43.678821+0400 | INFO | my_deployer | Sending   | $STREAM setBallot(...) 
2022-02-24T18:15:43.737502+0400 | INFO | my_deployer | Sending   | $FLY addZone(...) 
2022-02-24T18:15:43.840611+0400 | INFO | my_deployer | Sending   | $FLY addZone(...) 
2022-02-24T18:15:43.923611+0400 | INFO | my_deployer | Sending   | $FLY addZone(...) 
2022-02-24T18:15:44.000249+0400 | INFO | my_deployer | Sending   | $BALLOT addZones(...) 
2022-02-24T18:15:44.227005+0400 | INFO | my_deployer | Sending   | $BALLOT setBonusEmissionRate(...) 
2022-02-24T18:15:44.299795+0400 | INFO | my_deployer | Sending   | $BALLOT setCountRewardRate(...) 
2022-02-24T18:15:44.358623+0400 | INFO | my_deployer | Sending   | $BALLOT openBallot(...) 
2022-02-24T18:15:44.394266+0400 | INFO | my_deployer | Sending   | $VEFLY addBallot(...) 
2022-02-24T18:15:44.425738+0400 | INFO | my_deployer | Sending   | $HOPPER addZone(...) 
2022-02-24T18:15:44.505505+0400 | INFO | my_deployer | Sending   | $HOPPER addZone(...) 
2022-02-24T18:15:44.590838+0400 | INFO | my_deployer | Sending   | $HOPPER setApprovalForAll(...) 
2022-02-24T18:15:44.655163+0400 | INFO | my_deployer | Sending   | $HOPPER setApprovalForAll(...) 
2022-02-24T18:15:44.709889+0400 | INFO | my_deployer | Sending   | $FLY approve(...) 
2022-02-24T18:15:44.744388+0400 | INFO | # Transaction Sequence
['0x5158e1649c5d6bb3f39bbce034cdc18b14377ede443ec0af67547cdad763fdd1', '0xb878d726608113ab62c4ad7017171c37f643a0ffb1ff8066b46d226ccc5f74c0', '0x4e3db8c1ebd6c47023993009ce32e9369f4c5fafe007fe16a957f7eb0b20c4fe', '4a3cb406d210afb1fea3accd096603c61375e82","transactionIndex":"0x0"}', '0x4b5711342f965a82e74f62da14a3cb406d210afb1fea3accd096603c61375e82', '3a35d08d133a32fddf499baf75bcffe1d20c4da","transactionIndex":"0x0"}', '0x879129d8fd2926276fe5234e13a35d08d133a32fddf499baf75bcffe1d20c4da', 'adbe429c87c673c64a037e2cbaec3957a8ff020","transactionIndex":"0x0"}', '0x213643b41d6254d946d6a2d39adbe429c87c673c64a037e2cbaec3957a8ff020', 'a730d070a79c76dc8a522abceb3fff913d521e9","transactionIndex":"0x0"}', '0x250e4dbffc060abfc205154e6a730d070a79c76dc8a522abceb3fff913d521e9', '0xe43c484edd4af20dcf3bcc97e02835ba20657f1ea04fa6931da79dd93d95f533', '0x09d7653fa435e2cd1ea04ad76d9ac9d6d7bd1f55c2d2254a6fa6e9dc18644593', '0x5e6be62cf65851030a166bc228b3a83d7e4c772eb93cb67d06283be4315c5fa5', '0x9514d15ef64ea6d8753a0bcfa8e2a325a8916b711553963dc5cd0a106e61102f', '0xe4c8baf6245a0cb132e0553ffa6240dab7ac222ae553a8beadcd8cb5b556b206', '0xe94f184b25815b51cef405799c15b0db30a9dfd11cfbfd538984466f452eed08', '0x86b22c37980cbd5bdb627493ad861bc9066d5a432751d30a70880fbd44041d80', '0x7253b67fffea0dcdae28ce08e881d9bc4d94c688eac85e00ebda513bcf40c305', '0xcdb9c722e090af760bbd6a75d66e7303f28656a1dde0a02ab7653801c34c556a', '0x418e25527add9a6c0720279a2f49a064c48e46864119bdda0300043f0298af25', '70aafb9641000a62409f2d1df1db272c385bb61","transactionIndex":"0x0"}', '0x681a3300421f88b47470b84ec70aafb9641000a62409f2d1df1db272c385bb61', '75ade83329e2ffab219ad43ba9c97bdd3b0093d","transactionIndex":"0x0"}', '0x518f04dc94438b206ef7dcf1975ade83329e2ffab219ad43ba9c97bdd3b0093d', 'be0a48a26053fda315d93e6c119d045dff24041","transactionIndex":"0x0"}', '0xdaa36da1e35d48723bfe09458be0a48a26053fda315d93e6c119d045dff24041']
2022-02-24T18:15:44.744659+0400 | INFO | # Addresses
{'HOPPER': '0xe78a0f7e598cc8b0bb87894b0f60dd2a88d6a8ab', 'TADPOLE': '0x5b1869d9a4c187f2eaa108f3062412ecf0526b24', 'FLY': '0xcfeb869f69431e42cdb54a4f4f105c19c080a601', 'VEFLY': '0x254dffcd3277c0b1660f6d42efbb754edababc2b', 'POND': '0xc89ce4735882c9f0f0fe26686c53074e09b0d550', 'STREAM': '0xd833215cbcc3f914bd1c9ece3ee7bf8b14f841bb', 'BALLOT': '0x9561c133dd8580860b6b7e504bc5aa500f0f06a7', 'BREEDING': '0xe982e462b094850f12af94d21d470e21be9d0e9c'}
```
### As a python library

```bash
$ python deploy.py
```
#### deploy.py
```python
from foundrydeploy import Network, Deployer, TEST_SIGNER

contracts = [
    # (Contract Label, ContractPath:ContractName, ContractAddress)
    ("LABEL1", "src/Contract1.sol:ContractName1", "0x1111111111111111111111111111111111111111"),
    ("LABEL2", "src/Contract2.sol:ContractName2"),
    ("LABEL3", "", "0x2222222222222222222222222222222222222222")
]

deployer = Deployer(
    Network.LOCAL,
    TEST_SIGNER, # deterministic key from ganache
    contracts,
    is_legacy = True, # for legacy transactions
    debug = False, # if True, prints the calling commands and raw output
)

path = [
    # Format :
    # (ACTION_TYPE, CONTRACT_LABEL, [ARG, ... ])

    # Both Deploy and Send will be skipped
    (Deployer.SKIP_START,0,0),
    (Deployer.DEPLOY, "LABEL1", ["Arg1", "Arg2", "11ether"]),
    (Deployer.SEND, "LABEL1",   ["functionName", "9999999999", "00"*32, "00"*32, "0"]),
    (Deployer.SKIP_END,0,0),

    # It will be skipped, since we passed an address above (0x11..11)
    (Deployer.DEPLOY, "LABEL1", ["Arg1", "Arg2", "11ether"]),

    # Will find out the `functionName` signature and call it to the address of LABEL1
    # (Deployer.SEND, "LABEL1",   ["functionName", "9999999999", "00"*32, "00"*32, "0"]),

    # Deploys LABEL2 and passes LABEL1 address as the first argument
    (Deployer.DEPLOY, "LABEL2", ["$LABEL1", "arg2", "1gwei"]),
    
    # Will find out the `functionName` signature and call it to the address of LABEL1
    (Deployer.SEND, "LABEL2",   ["functionName", "9999999999"]),

    # Since LABEL3 has no contract path, it's the same as calling `cast send 0x2222222222222222222222222222222222222222 1gwei` and passes LABEL1 address as the first argument
    # (Deployer.SEND, "LABEL3", ["function_name(uint256)", "1gwei"])

]

deployer.path(path)
```
