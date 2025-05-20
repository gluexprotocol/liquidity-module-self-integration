from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional, Tuple
from decimal import Decimal
import math

class Constants:
    ETHER = Decimal("1e18")

class LagoonLiquidityModule(LiquidityModule):
    def _convert_to_assets(self, pool_state: Dict, shareToken: Token, amount: int) -> int:
        """
        Convert a given amount of shares to the equivalent amount of underlying assets using the pool state and fixed parameters.
        Formula: floor(amount * (totalAssets + 1) / (totalSupply + 10 ** decimals))
        """
        totalAssets = pool_state["totalAssets"]
        totalSupply = pool_state["totalSupply"]
        decimals = shareToken.decimals
        
        return math.floor(amount * (totalAssets + 1) / (totalSupply + 10 ** decimals))

    def _convert_to_shares(self, pool_state: Dict, shareToken: Token, amount: int) -> int:
        """
        Convert a given amount of underlying assets to the equivalent amount of shares using the pool state and fixed parameters.
        Formula: floor(amount * (totalSupply + 10 ** decimals) / (totalAssets + 1))
        """
        totalAssets = pool_state["totalAssets"]
        totalSupply = pool_state["totalSupply"]
        decimals = shareToken.decimals
        
        return math.floor(amount * (totalSupply + 10 ** decimals) / (totalAssets + 1))

    def _wei_to_ether(self, amount: int) -> Decimal:
        """
        Convert a value from Wei to Ether denomination using the constant ETHER.
        """
        return Decimal(amount) / Constants.ETHER

    def get_amount_out(
        self,
        pool_state: Dict,
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        output_amount: int
    ) -> Tuple[None, int]:
        """
        Given an output amount (in shares or assets), calculate the required input amount (in the other token),
        depending on the input token address. Returns a tuple (fee, amount in Ether denomination).
        """
        # Input validation
        if (
            pool_state["totalAssets"] == 0 or
            pool_state["totalSupply"] == 0 or
            pool_state["daysStarted"] == 0 or
            output_amount < 0
        ):
            raise Exception("Invalid pool state or output amount")
        
        output_amount = 0
        if input_token.address == fixed_parameters["shareTokenAddress"]:
            output_amount = self._convert_to_assets(pool_state, fixed_parameters, output_amount)
        elif input_token.address == fixed_parameters["underlyingTokenAddress"]:
            output_amount = self._convert_to_shares(pool_state, fixed_parameters, output_amount)
        else:
            raise Exception("Invalid input token address")
        
        return (None, self._wei_to_ether(output_amount))

    def get_amount_in(
        self,
        pool_state: Dict,
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        input_amount: int
    ) -> Tuple[None, Decimal]:
        """
        Given an input amount (in shares or assets), calculate the output amount (in the other token),
        depending on the input token address. Returns a tuple (fee, amount in Ether denomination).
        """
        if (
            pool_state["totalAssets"] == 0 or
            pool_state["totalSupply"] == 0 or
            pool_state["daysStarted"] == 0 or
            input_amount < 0
        ):
            raise Exception("Invalid pool state or input amount")
        output_amount = 0

        if input_token.address == fixed_parameters["shareTokenAddress"]:
            output_amount = self._convert_to_assets(pool_state, fixed_parameters, input_amount)
        elif input_token.address == fixed_parameters["underlyingTokenAddress"]:
            output_amount = self._convert_to_shares(pool_state, fixed_parameters, input_amount)
        else:
            raise Exception("Invalid input token address")

        return (None, self._wei_to_ether(output_amount))

    def get_apy(self, pool_state: Dict) -> Decimal:
        """
        Calculate APY (Annual Percentage Yield) as a percentage using the formula:
        (sharePrice / totalSupply) / ETHER * (365 / daysStarted) * 100
        """
        sharePrice = Decimal(pool_state["sharePrice"])
        totalSupply = Decimal(pool_state["totalSupply"])
        daysStarted = Decimal(pool_state["daysStarted"])
        if daysStarted == 0 or totalSupply == 0:
            raise Exception("Invalid pool state for APY calculation")
        # APY formula: (sharePrice / totalSupply) / ETHER * (365 / daysStarted) * 100
        return (sharePrice / totalSupply) / Constants.ETHER * (Decimal(365) / daysStarted) * Decimal(100)

    def get_tvl(self, pool_state: Dict, token: Optional[Token] = None) -> Decimal:
        """
        Calculate TVL (Total Value Locked) as totalSupply multiplied by the underlying asset token's
        reference price in terms of native gas token.
        """
        totalSupply = pool_state["totalSupply"]
        if totalSupply == 0 or (token and token.reference_price <= 0):
            raise Exception("Invalid pool state or token for TVL calculation")
        if token is None:
            raise Exception("Token must be provided for TVL calculation")
        return Decimal(totalSupply) * Decimal(token.reference_price)