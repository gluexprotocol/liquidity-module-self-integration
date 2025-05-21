# gluex-liquidity-module-self-integration

## Welcome to the GlueX Liquidity Module Self-Integration Repository

This repository provides the official framework for DeFi protocols to self-integrate into GlueX by submitting their own liquidity modules in Python.

By integrating, your protocol will be natively accessible to GlueX-connected chains, dApps, and solvers, enabling seamless execution abstraction without requiring custom infrastructure or manual onboarding.

---

## What is a GlueX Liquidity Module?

A GlueX Liquidity Module is a standardized Python-based integration that allows GlueX to:

- Retrieve liquidity from your protocol and expose it to DeFi dApps and execution optimizers.
- Embed your protocol into multi-step transactions spanning chains and liquidity sources.
- Standardize interaction formats for efficient routing and settlement.

Each liquidity module follows a strict interface, ensuring GlueX can efficiently interact with all integrated protocols.

---

## **Glueing Queue – Automatic & Community-Powered Integration**
Protocols that do not wish to self-integrate can be picked up by the GlueX's Gluers Community or the GlueX Labs team through the Glueing Queue.

**What is the Glueing Queue?**

The Glueing Queue is the official order in which liquidity modules are integrated. The queue prioritizes integrations based on the Glueing Score. However, Gluers can be incentivized to integrate liquidity modules that are not at the top of the Glueing Queue via Glueing Bounties. Read more about the Glueing Queue, the Glueing Score and Glueing Bounties [here](https://github.com/gluexprotocol/glueing-queue/tree/main).

---

## Directory Descriptions
- **`modules/`** → Contains individual liquidity module implementations for each protocol.
- **`templates/`** → Holds the base `LiquidityModule` class, which should not be modified.
- **`tests/`** → Contains test cases to validate the implementation of liquidity modules.
- **`docs/`** → Includes specifications, guidelines, and PR submission templates.
- **`README.md`** → The main guide for self-integration.
- **`requirements.txt`** → Lists dependencies required for running the module.
- **`pytest.ini`** → Configuration file for running test cases.

Make sure to place your implementation inside the `modules/` directory following the naming convention:


---

> **NOTE**  
> Before you start working on your liquidity module integration, please ensure your liquidity module has not already been glued to GlueX.  
>
> The latest list of integrated protocols is available here: [GlueX Integrated Liquidity](https://router.gluex.xyz/liquidity/staging).

## How to Submit a Liquidity Module

### 1. Fork This Repository

Click the "Fork" button at the top of this repo to create your own copy.



### 2. Implement the Required Python Interfaces

- **Do not modify** `templates/liquidity_module.py`. This file contains the abstract base class that your implementation should inherit from.
- Navigate to the `modules/` directory.
- Create a new file named `<protocol_name>_liquidity_module.py`.
- Implement your protocol’s integration by inheriting from `LiquidityModule`.

Your implementation **must** inherit from `LiquidityModule` and implement all required methods.

Example (`modules/myprotocol_liquidity_module.py`):

```python
from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional
from decimal import Decimal

class MyProtocolLiquidityModule(LiquidityModule):
    def get_amount_out(
        self, 
        pool_state: Dict, 
        input_token: Token, 
        input_amount: int, 
        output_token: Token, 
        output_amount: Optional[int] = None
    ) -> int:
        # Implement logic to calculate output amount
        pass

    def get_amount_in(
        self, 
        pool_state: Dict, 
        input_token: Token, 
        input_amount: Optional[int] = None, 
        output_token: Token, 
        output_amount: int
    ) -> int:
        # Implement logic to calculate required input amount
        pass

    def get_apy(self, pool_state: Dict) -> Decimal:
        # Implement APY calculation logic
        pass

    def get_tvl(self, pool_state: Dict, token: Optional[Token] = None) -> Decimal:
        # Implement TVL calculation logic
        pass
```




### 3. Test Your Integration

- Run the provided test suite (`tests/test_liquidity_module.py`) to ensure compatibility.

```bash
pytest tests/
```



### 4. Submit a Pull Request (PR)

Once your module is complete and tested, submit a PR following the required format.

Your PR must include:
- Protocol name and details
- Deployed chains
- Relevant smart contract addresses for indexing (e.g. factories)
- Relevant pool states and pool state retrieval instructions

Follow the PR template in `/docs/PR-template.md`.

To submit a PR:
1. Push your implementation to your forked repository.
2. Open a Pull Request (PR) to this repository.
3. In the PR description, include:
   - Protocol overview
   - A summary of your liquidity module implementation
   - Test results and relevant logs
   - Any special considerations for execution or integration
4. Wait for a GlueX reviewer to assess your submission.

Right after the PR is submitted, a Gluer will review the submission. If any modifications are required, you will receive feedback for adjustments. If approved, your protocol will be integrated into GlueX’s execution network.



## Checklist  
Before submitting, ensure you have completed the following:  

- [ ] Forked this repository  
- [ ] Implemented a new liquidity module in `modules/<protocol_name>_liquidity_module.py`  
- [ ] Passed all test cases (`pytest tests/`)  
- [ ] Provided clear documentation in this PR  
- [ ] Included test logs and results in this PR  
- [ ] Listed all dependencies and external data sources (if any)  
- [ ] Listed all chains in which your liquidity module is available
- [ ] Listed all smart contracts that are relevant to index your liquidity pools (e.g. factories)



## Relevant Links
- **Telegram:** https://t.me/+yf_US2ACNrgyNzY0
- **GlueX Website:** https://gluex.xyz
- **GlueX dApp:** https://dapp.gluex.xyz
- **GlueX Docs:** https://docs.gluex.xyz
