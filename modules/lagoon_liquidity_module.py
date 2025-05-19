from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional
from decimal import Decimal
import math

ETHER = Decimal("1e18")

class LagoonLiquidityModule(LiquidityModule):
    def _convert_to_assets(self, pool_state: Dict, fixed_parameters: Dict, amount: int) -> int:
        totalAssets = pool_state["totalAssets"]
        totalSupply = pool_state["totalSupply"]
        decimals = fixed_parameters["decimals"]

        return math.floor(amount * (totalAssets + 1) / (totalSupply + 10 ** decimals))

    def _convert_to_shares(self, pool_state: Dict, fixed_parameters: Dict, amount: int) -> int: 
        totalAssets = pool_state["totalAssets"]
        totalSupply = pool_state["totalSupply"]
        decimals = fixed_parameters["decimals"]

        return math.floor(amount * (totalSupply + 10 ** decimals) / (totalAssets + 1))

    def _wei_to_ether(self, amount: int) -> Decimal:
        return Decimal(amount) / ETHER

    def get_deposit_amount(
        self, 
        pool_states: Dict, 
        fixed_parameters: Dict,
        input_token: Token, 
        output_token: Token,
        input_amount: int, 
    ) -> Decimal:
        """
        Deposit underlying asset into the pool and receive shares in return.
        Returns the amount of shares received in Ether denomination.
        """
        # amount of underlying asset to deposit in wei
        amountIn = input_amount

        # amount of shares to receive
        sharesToMint = self._convert_to_shares(pool_states, fixed_parameters, amountIn)

        return sharesToMint

    def get_redeem_amount(
        self, 
        pool_state: Dict, 
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        input_amount: int
    ) -> Decimal:
        """
        Redeem shares from the pool and receive underlying asset in return.
        Returns the amount of underlying asset received in Ether denomination.
        """
        # amount of shares to redeem in wei
        sharesToRedeem = input_amount

        # amount of underlying asset to receive
        amountOut = self._convert_to_assets(pool_state, fixed_parameters, sharesToRedeem)

        return self._wei_to_ether(amountOut)

    def get_apy(self, pool_state: Dict) -> Decimal:
        """
        APY is in percentage
        """
        
        # Retrieved from convertToAssets(uint256) of 1 ether
        sharePrice = pool_state["sharePrice"]
        # total underlying asset supply
        totalSupply = pool_state["totalSupply"]
        # days since the start of the pool
        daysStarted = pool_state["daysStarted"]

        return (sharePrice / totalSupply) / ETHER * (365 / daysStarted) * 100

    def get_tvl(self, pool_state: Dict, token: Optional[Token] = None) -> Decimal:
        """
        TVL is in native chain currency
        """

        # total underlying asset supply
        totalSupply = pool_state["totalSupply"]

        return totalSupply * token.reference_price