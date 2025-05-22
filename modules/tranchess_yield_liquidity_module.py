from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional
from decimal import Decimal

class TranchessYieldLiquidityModule(LiquidityModule):
    def get_amount_out(
        self, 
        pool_states: Dict, 
        fixed_parameters: Dict,
        input_token: Token, 
        output_token: Token,
        input_amount: int, 
    ) -> tuple[int | None, int | None]:
        """
        Calculate the amount of output token received for a given input amount.
        """
        pass

    def get_amount_in(
        self, 
        pool_state: Dict, 
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        output_amount: int
    ) -> tuple[int | None, int | None]:
        """
        Calculate the amount of input token required to receive a given output amount.
        """
        pass

    def get_apy(self, pool_state: Dict) -> Decimal:
        """
        Calculate the annual percentage yield (APY) for a yield farm pool.
        """
        pass

    def get_tvl(self, pool_state: Dict, token: Optional[Token] = None) -> Decimal:
        """
        Calculate the total value locked (TVL) in a yield farm pool.
        """
        pass