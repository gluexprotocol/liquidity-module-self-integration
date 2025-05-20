from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional
from decimal import Decimal

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
        # Implement APY calculation logic
        pass

    def get_tvl(self, pool_state: Dict, token: Optional[Token] = None) -> Decimal:
        # Implement TVL calculation logic
        pass