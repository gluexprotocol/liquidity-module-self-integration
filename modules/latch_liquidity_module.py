from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional, List
from decimal import Decimal

from requests import post

# [
#     [
#         "0xc4af68Dd5b96f0A544c4417407773fEFDc97F58d", true // ATUSD Gravity
#     ],
#     [
#         "0xc314b8637B05A294Ae9D9C29300d5f667c748baD", true // ATETH Gravity
#     ],
#     [
#         "0x0725fBB2CE5603340c06A4eCe4D68170C5464854", true // VaultNavViewUpgradeable Ethereum
#     ],
#     [
#         "0xca11bde05977b3631167028862be2a173976ca11", true // Multicall3 Ethereum
#     ],
#     [
#         "0x754D6827A57334143eD5fB58C5b1A4aAe4396ba5", true // VerifiedTldHub Ethereum
#     ],
#     [
#         "0x77777775c2F5C30868Cf6419392bc667DdD207EC", true // User address
#     ],
#     [
#         "", false
#     ],
#     [
#         "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", true // USDC Ethereum
#     ],
#     [
#         "0xdAC17F958D2ee523a2206206994597C13D831ec7", true // USDT Ethereum
#     ],
#     [
#         "0xaf88d065e77c8cC2239327C5EDb3A432268e5831", true // USDC Arbitrum
#     ],
#     [
#         "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9", true // USDT Arbitrum
#     ],
#     [
#         "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d", true // USDC BSC
#     ],
#     [
#         "0x55d398326f99059fF775485246999027B3197955", true // USDT BSC
#     ],
#     [
#         "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359", true // USDC Polygon
#     ],
#     [
#         "0xc2132d05d31c914a87c6611c10748aeb04b58e8f", true // USDT Polygon
#     ],
#     [
#         "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913", true // USDC Base
#     ],
#     [
#         "0x0000000000000000000000000000000000000000", true // ETH Placeholder
#     ],
#     [
#         "0xFbDa5F676cB37624f28265A144A48B0d6e87d3b6", true // USDC.e Stargate on Gravity
#     ],
#     [
#         "0x816E810f9F787d669FB71932DeabF6c83781Cd48", true // USDT Gravity
#     ],
#     [
#         "0x4200000000000000000000000000000000000006", true // WETH Optimism and Base
#     ],
#     [
#         "0x2D2a6A33CA360B66B82250901Aa9EdAb63Db21E3", true // LSDSwapWithBaseUniswapV2 on Base
#     ],
#     [
#         "0x41d5538015C61EEFC92cE64A41c18fDa327334AA", true // LSDSwapWithCamelotswapV2 on Gravity
#     ]
# ]

# { chainid => native wrapped tokens
#   "1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
#   "56": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
#   "137": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
#   "1625": "0xBB859E225ac8Fb6BE1C7e38D87b767e95Fef0EbD",
#   "8453": "0x4200000000000000000000000000000000000006",
#   "42161": "0x82af49447d8a07e3bd95bd0d56f35241523fbab1"
# }

# { chainid => USDT or its equivalent
#   "1": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
#   "56": "0x55d398326f99059fF775485246999027B3197955",
#   "137": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
#   "1625": "0x816E810f9F787d669FB71932DeabF6c83781Cd48",
#   "42161": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9"
# }

# { chainid => USDC or its equivalent
#   "1": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
#   "1625": "0xFbDa5F676cB37624f28265A144A48B0d6e87d3b6",
#   "8453": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
# }

# { for atETH, WETH for each chain
#   "1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
#   "56": "0x2170Ed0880ac9A755fd29B2688956BD959F933F8",
#   "137": "0x7ceb23fd6bc0add59e62ac25578270cff1b9f619",
#   "1625": "0xf6f832466Cd6C21967E0D954109403f36Bc8ceaA", // stargate bridged weth
#   "8453": "0x4200000000000000000000000000000000000006",
#   "42161": "0x82af49447d8a07e3bd95bd0d56f35241523fbab1"
# }

class LatchLiquidityModule(LiquidityModule):
    def get_deposit_quote(
        self, 
        pool_states: Dict,
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        input_amount: int,
    ) -> tuple[int | None, int | None]:
        # Implement logic to calculate output amount given input amount
        pass

    def get_withdraw_quote(
        self, 
        pool_state: Dict, 
        fixed_parameters: Dict,
        input_token: Token,
        input_amount: int,
        output_token: Token,
    ) -> tuple[int | None, int | None]:
        # Implement logic to calculate output amount given input amount
        pass

    def __get_apy(self, poolAddress: str) -> Decimal:
        """
        Fetches the APY for a given pool address from the Latch API.
        Args:
            poolAddress (str): The address of the pool to fetch the APY for.
        Returns:
            Decimal: The APY for the given pool address in decimal. 0.01 = 1%.
        """

        url = "https://savings-graphigo.prd.latch.io/query"

        headers = {
            "Content-Type": "application/json",
        }

        payload = {
            "operationName": "GetAPYs",
            "variables": {
                "lsdToken": poolAddress
            },
            "query": "query GetAPYs($lsdToken: String!) {\n  GetAPYs(lsdToken: $lsdToken)\n}"
        }

        response = post(url, headers=headers, json=payload)

        return Decimal(response.json()["data"]["GetAPYs"])
    
    def get_apy(self, pool_state: Dict) -> Decimal:
        """
        Fetches the APY for a given pool state from the Latch API.
        Args:
            pool_state["VaultName"] (str): The name of the vault to fetch the APY for. Either "USDT" or "ETH".
        Returns:
            Decimal: The APY for the given pool state in decimal. 0.01 = 1%.
        """

        vaultName = pool_state["VaultName"]
        if vaultName == "USDT":
            poolAddress = "0xc4af68Dd5b96f0A544c4417407773fEFDc97F58d"
        elif vaultName == "ETH":
            poolAddress = "0xc314b8637B05A294Ae9D9C29300d5f667c748baD"
        
        try:
            return self.__get_apy(poolAddress)
        except Exception as e:
            print(f"Error fetching APY for {vaultName} Latch Vault: {e}")
            return Decimal(0)
        

    def get_tvl(self, pool_state: Dict) -> Decimal:
        """
        Fetches the Tvl for a given pool state from the Latch API.
        Args:
            pool_state["atUSDSupply"] (int): The total supply of the atUSD token.
            pool_state["atETHSupply"] (int): The total supply of the atETH token.
            pool_state["ETHPrice"] (int): The current price of ETH in USD.
        Returns:
            Decimal: The Tvl for the given pool state in USD.
        """

        atUSDSupply = pool_state["atUSDSupply"]
        atETHSupply = pool_state["atETHSupply"]
        ETHPrice = pool_state["ETHPrice"]

        try:
            return Decimal(atUSDSupply) + (Decimal(atETHSupply) * Decimal(ETHPrice))
        except Exception as e:
            print(f"Error fetching Tvl for Latch Vault: {e}")
            return Decimal(0)

