# foundrydeploy

Basic python wrapper around `forge create` and `cast send` from [foundry](https://github.com/gakonst/foundry) for a basic deployment pipeline with caching capabilities.

**Deployment script should be called from the foundry project with the build artifacts present at `out/`.**

## Summary

Basic features:
* (deploy) Deployments map the resulting address to the given label, which can be used later on.
* (deploy) Deployments are cached (tied to the RPC) and skipped if they're run again. 
* (send) Only requires the function name. The signature is extracted from the ABI present at `out/***.sol/***.json`
* It will cache the state on error.

Helpers:
* Using labels as **arguments** requires preceeding it with "$". eg: `$LABEL1`
* Signer public keys can be used as an argument by invoking it as such: `#PUB`

Still early, so test on a local network first.

### Install

```
pip install foundrydeploy
```

## Example

### script
```
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
### result
```
> example $ python deploy.py
```

### First Time
```
#####
# RPC: `--rpc-url http://127.0.0.1:8545`
# Starting cache at `cache/deploy_a73a4677`
#####

Skipping $LABEL1 deployment. Has address: 0x1111111111111111111111111111111111111111
Deploying | $LABEL2...
Sending   | $LABEL2 functionName(...) 

##
 {'LABEL1': '0x1111111111111111111111111111111111111111', 'LABEL3': '0x2222222222222222222222222222222222222222', 'LABEL2': '0xc89ce4735882c9f0f0fe26686c53074e09b0d550'}
```

### Second Time
```
#####
# RPC: `--rpc-url http://127.0.0.1:8545`
# Loading cache at `cache/deploy_a73a4677`
#####

Skipping $LABEL1 deployment. Has address: 0x1111111111111111111111111111111111111111
Skipping $LABEL2 deployment. Has address: 0xc89ce4735882c9f0f0fe26686c53074e09b0d550
Sending   | $LABEL2 functionName(...) 

##
 {'LABEL1': '0x1111111111111111111111111111111111111111', 'LABEL3': '0x2222222222222222222222222222222222222222', 'LABEL2': '0xc89ce4735882c9f0f0fe26686c53074e09b0d550'}
```

### On error
