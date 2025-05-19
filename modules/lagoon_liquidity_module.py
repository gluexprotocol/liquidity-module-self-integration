from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional
from decimal import Decimal

ETHER = Decimal("1e18")

class MyProtocolLiquidityModule(LiquidityModule):
    def get_amount_out(
        self, 
        pool_states: Dict, 
        fixed_parameters: Dict,
        input_token: Token, 
        output_token: Token,
        input_amount: int, 
    ) -> tuple[int | None, int | None]:
        # Implement logic to calculate output amount given input amount
        pass

    def get_amount_in(
        self, 
        pool_state: Dict, 
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        output_amount: int
    ) -> tuple[int | None, int | None]:
        # Implement logic to calculate required input amount given output amount
        pass

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