from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional, List
from decimal import Decimal

from requests import post
from eth_abi import encode

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

# { CrossChainSwap function ABI
#   "inputs": [
#     {
#       "internalType": "address",
#       "name": "recipient",
#       "type": "address"
#     },
#     {
#       "internalType": "address",
#       "name": "sourceToken",
#       "type": "address"
#     },
#     {
#       "internalType": "uint256",
#       "name": "amount",
#       "type": "uint256"
#     },
#     {
#       "internalType": "uint32",
#       "name": "targetEndpointId",
#       "type": "uint32"
#     },
#     {
#       "internalType": "address",
#       "name": "targetToken",
#       "type": "address"
#     },
#     {
#       "internalType": "uint128",
#       "name": "nativeDrop",
#       "type": "uint128"
#     },
#     {
#       "internalType": "bytes",
#       "name": "sourceSwapPath",
#       "type": "bytes"
#     },
#     {
#       "internalType": "bytes",
#       "name": "targetSwapPath",
#       "type": "bytes"
#     },
#     {
#       "internalType": "uint128",
#       "name": "bridgeGasLimit",
#       "type": "uint128"
#     }
#   ],
#   "name": "quoteCrossChainSwap",
#   "outputs": [
#     {
#       "internalType": "uint256",
#       "name": "messageFee",
#       "type": "uint256"
#     },
#     {
#       "internalType": "address",
#       "name": "bridgeToken",
#       "type": "address"
#     },
#     {
#       "internalType": "uint256",
#       "name": "beforeBridgeAmountOut",
#       "type": "uint256"
#     },
#     {
#       "internalType": "uint256",
#       "name": "afterBridgeAmountOut",
#       "type": "uint256"
#     }
#   ],
#   "stateMutability": "nonpayable",
#   "type": "function"
# }

class LatchLiquidityModule(LiquidityModule):
    __addressMap = {
        "0xc4af68Dd5b96f0A544c4417407773fEFDc97F58d": True,  # ATUSD Gravity
        "0xc314b8637B05A294Ae9D9C29300d5f667c748baD": True,  # ATETH Gravity
        "0x0725fBB2CE5603340c06A4eCe4D68170C5464854": True,  # VaultNavViewUpgradeable Ethereum
        "0xca11bde05977b3631167028862be2a173976ca11": True,  # Multicall3 Ethereum
        "0x754D6827A57334143eD5fB58C5b1A4aAe4396ba5": True,  # VerifiedTldHub Ethereum
        "": False,
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": True,  # USDC Ethereum
        "0xdAC17F958D2ee523a2206206994597C13D831ec7": True,  # USDT Ethereum
        "0xaf88d065e77c8cC2239327C5EDb3A432268e5831": True,  # USDC Arbitrum
        "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9": True,  # USDT Arbitrum
        "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d": True,  # USDC BSC
        "0x55d398326f99059fF775485246999027B3197955": True,  # USDT BSC
        "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359": True,  # USDC Polygon
        "0xc2132d05d31c914a87c6611c10748aeb04b58e8f": True,  # USDT Polygon
        "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913": True,  # USDC Base
        "0x0000000000000000000000000000000000000000": True,  # ETH Placeholder
        "0xFbDa5F676cB37624f28265A144A48B0d6e87d3b6": True,  # USDC.e Stargate on Gravity
        "0x816E810f9F787d669FB71932DeabF6c83781Cd48": True,  # USDT Gravity
        "0x4200000000000000000000000000000000000006": True,  # WETH Optimism and Base
        "0x2D2a6A33CA360B66B82250901Aa9EdAb63Db21E3": True,  # LSDSwapWithBaseUniswapV2 on Base
        "0x41d5538015C61EEFC92cE64A41c18fDa327334AA": True,  # LSDSwapWithCamelotswapV2 on Gravity
    }
    __wethMap = {
        "1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # Ethereum Mainnet
        "56": "0x2170Ed0880ac9A755fd29B2688956BD959F933F8",  # Binance Smart Chain
        "137": "0x7ceb23fd6bc0add59e62ac25578270cff1b9f619",  # Polygon
        "1625": "0xf6f832466Cd6C21967E0D954109403f36Bc8ceaA",  # Stargate bridged WETH
        "8453": "0x4200000000000000000000000000000000000006",  # Base
        "42161": "0x82af49447d8a07e3bd95bd0d56f35241523fbab1",  # Arbitrum
    }
    __usdtMap = {
        "1": "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # Ethereum Mainnet
        "56": "0x55d398326f99059fF775485246999027B3197955",  # Binance Smart Chain
        "137": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",  # Polygon
        "1625": "0x816E810f9F787d669FB71932DeabF6c83781Cd48",  # Stargate bridged USDT
        "42161": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",  # Arbitrum
    }

    __usdcMap = {
        "1": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # Ethereum Mainnet
        "1625": "0xFbDa5F676cB37624f28265A144A48B0d6e87d3b6",  # Stargate bridged USDC
        "8453": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",  # Base
    }

    __chainIdMap = {
        "1": "Eth",
        "56": "Bsc",
        "137": "Polygon",
        "1625": "Gravity",
        "8453": "Base",
        "42161": "Arb",
    }

    __reverseChainIdMap = {v: k for k, v in __chainIdMap.items()}

    def __get_pool_fee(self, input_token: Token) -> Decimal:
        """
        Fetches the pool fee for a given pool state.
        Args:
            input_token (Token): The token being swapped in.
        Returns:
            int: The pool fee in basis points. 100 = 0.01%.
        """
        if input_token.chain_id in ["Polygon", "Base"]:
            return Decimal(500)  # 5.00% fee for Polygon and Base chains
        else:
            return Decimal(100)  # 1.00% fee for other chains
    
    def __map_addresses(self, input_token: Token) -> str:
        """
        Maps the input token address to the corresponding address in the Latch liquidity module.
        Args:
            input_token (Token): The token being swapped in.
        Returns:
            str: The mapped address for the input token.
        """
        if input_token.address in self.__addressMap and self.__addressMap[input_token.address]:
            return input_token.address
        else:
            return "0x0000000000000000000000000000000000000000"
    
    def __get_pool_address(self, vaultName: str) -> str:
        if vaultName == "USDT":
            poolAddress = "0xc4af68Dd5b96f0A544c4417407773fEFDc97F58d"
        elif vaultName == "ETH":
            poolAddress = "0xc314b8637B05A294Ae9D9C29300d5f667c748baD"
        
        return poolAddress

    def __get_weth_address(self, chain_id: str) -> str:
        """
        Fetches the WETH address for a given chain ID.
        Args:
            chain_id (str): The chain ID to fetch the WETH address for.
        Returns:
            str: The WETH address for the given chain ID.
        """
        if chain_id in self.__wethMap:
            return self.__wethMap[chain_id]
        else:
            raise ValueError(f"Unsupported chain ID: {chain_id}")
    
    def __get_usdt_address(self, chain_id: str) -> str:
        """
        Fetches the USDT address for a given chain ID.
        Args:
            chain_id (str): The chain ID to fetch the USDT address for.
        Returns:
            str: The USDT address for the given chain ID.
        """
        if chain_id in self.__usdtMap:
            return self.__usdtMap[chain_id]
        else:
            raise ValueError(f"Unsupported chain ID: {chain_id}")

    def __get_usdc_address(self, chain_id: str) -> str:
        """
        Fetches the USDC address for a given chain ID.
        Args:
            chain_id (str): The chain ID to fetch the USDC address for.
        Returns:
            str: The USDC address for the given chain ID.
        """
        if chain_id in self.__usdcMap:
            return self.__usdcMap[chain_id]
        else:
            raise ValueError(f"Unsupported chain ID: {chain_id}")
    
    def __get_chain_id(self, chain_name: str) -> str:
        """
        Fetches the chain ID for a given chain name.
        Args:
            chain_name (str): The name of the chain to fetch the ID for.
        Returns:
            str: The chain ID for the given chain name.
        """
        if chain_name in self.__reverseChainIdMap:
            return self.__reverseChainIdMap[chain_name]
        else:
            raise ValueError(f"Unsupported chain name: {chain_name}")

    def __get_chain_name(self, chain_id: str) -> str:
        """
        Fetches the chain name for a given chain ID.
        Args:
            chain_id (str): The chain ID to fetch the name for.
        Returns:
            str: The chain name for the given chain ID.
        """
        if chain_id in self.__chainIdMap:
            return self.__chainIdMap[chain_id]
        else:
            raise ValueError(f"Unsupported chain ID: {chain_id}")
        
    def __encode_swap_path(self, chain_id: str, token1: str, token2_or_fee: Decimal, token3_if_v3: Optional[str] = None) -> bytes:
        """
        Encodes the swap path based on the chain ID and token details.
        Args:
            chain_id (str): The chain ID to determine the encoding style.
            token1 (str): The first token in the swap path.
            token2_or_fee (Decimal): The second token or fee in the swap path.
            token3_if_v3 (Optional[str]): The third token if using uni V3 style path.
        Returns:
            bytes: The encoded swap path.
        """
        if chain_id == self.__get_chain_id("Gravity"):
            # V2 style path: [token1, token2_or_fee (which is token2 here)]
            return encode(['address', 'address'], [token1, token2_or_fee])
        else:
            # V3 style path: [token1, token2_or_fee (which is fee here), token3_if_v3 (which is token2 here)]
            if token3_if_v3 is None:
                raise ValueError("token3_if_v3 must be provided for V3 style path")
            return encode(['address', 'uint24', 'address'], [token1, int(token2_or_fee), token3_if_v3])
    
    def __get_swap_path(self, pool_states: Dict, input_token: Token, output_token: Token) -> bytes:
        """
        Generates the swap path for a given input and output token.
        Args:
            pool_states (Dict): The pool states containing information about the tokens.
            input_token (Token): The token being swapped in.
            output_token (Token): The token being swapped out.
        Returns:
            bytes: The encoded swap path.
        """
        sourceChainId = input_token.chain_id
        sourceAddress = self.__map_addresses(input_token)
        targetChainId = output_token.chain_id
        targetAddress = self.__map_addresses(output_token)

        vaultName = pool_states["VaultName"]
        poolAddress = self.__get_pool_address(vaultName)

        if vaultName == "ETH":
            wethSource = self.__get_weth_address(sourceChainId)
            wethTarget = self.__get_weth_address(targetChainId)
        elif vaultName == "USDT":
            if self.__get_chain_id("Base") != sourceChainId and self.__get_chain_id("Base") != targetChainId:
                sourceTokenAddress = self.__get_usdt_address(sourceChainId)
                targetTokenAddress = self.__get_usdt_address(targetChainId)
                if sourceChainId == self.__get_chain_id("Base") and targetChainId == self.__get_chain_id("Gravity"):
                    sourceTokenAddress = self.__get_usdc_address(sourceChainId)
                    targetTokenAddress = self.__get_usdc_address(targetChainId)
                    targetSwapPath = encode(
                        ['address', 'address', 'address'],
                        [targetTokenAddress, self.__get_usdt_address(targetChainId), targetAddress]
                    )
            elif sourceChainId == self.__get_chain_id("Gravity") and targetChainId == self.__get_chain_id("Base"):
                sourceTokenAddress = self.__get_usdc_address(sourceChainId)
                targetTokenAddress = self.__get_usdc_address(targetChainId)
                sourceSwapPath = encode(
                    ['address', 'address', 'address'],
                    [sourceAddress, self.__get_usdt_address(sourceChainId), sourceTokenAddress]
                )
        else:
            raise ValueError(f"Unsupported vault name: {vaultName}")

        # Encode the swap path
        if sourceSwapPath is None:
            sourceSwapPath = self.__encode_swap_path(
                sourceChainId,
                sourceAddress,
                self.__get_usdt_address(sourceChainId) if sourceChainId == self.__get_chain_id("Gravity") else self.__get_pool_fee(input_token),
                self.__get_usdt_address(sourceChainId) if sourceChainId != self.__get_chain_id("Gravity") else None
            )

        if targetSwapPath is None:
            targetSwapPath = self.__encode_swap_path(
                targetChainId,
                targetAddress,
                self.__get_usdt_address(targetChainId) if targetChainId == self.__get_chain_id("Gravity") else self.__get_pool_fee(output_token),
                self.__get_usdt_address(targetChainId) if targetChainId != self.__get_chain_id("Gravity") else None
            )

        return {
            "bridgeTokenOnSourceChain": sourceTokenAddress,
            "bridgeTokenOnTargetChain": targetTokenAddress,
            "sourceSwapPath": sourceSwapPath,
            "targetSwapPath": targetSwapPath,
        }

    def get_deposit_quote(
        self, 
        pool_states: Dict,
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        input_amount: int,
    ) -> tuple[Decimal | None, Decimal | None]:
        # Implement logic to calculate output amount given input amount
        pass

    def get_withdraw_quote(
        self, 
        pool_state: Dict, 
        fixed_parameters: Dict,
        input_token: Token,
        input_amount: int,
        output_token: Token,
    ) -> tuple[Decimal | None, Decimal | None]:
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
        poolAddress = self.__get_pool_address(vaultName)
        
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

