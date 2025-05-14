from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional
from decimal import Decimal

from requests import post

class LatchLiquidityModule(LiquidityModule):
    def get_sell_quote(
        self, 
        pool_states: Dict, 
        fixed_parameters: Dict,
        input_token: Token, 
        output_token: Token,
        input_amount: int, 
    ) -> tuple[int | None, int | None]:
        # Implement logic to calculate output amount given input amount
        pass

    def get_buy_quote(
        self, 
        pool_state: Dict, 
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        output_amount: int
    ) -> tuple[int | None, int | None]:
        # Implement logic to calculate required input amount given output amount
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
        

    def get_tvl(self, pool_state: Dict, token: Optional[Token] = None) -> Decimal:
        # Implement TVL calculation logic
        pass