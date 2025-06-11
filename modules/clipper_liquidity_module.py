from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional
from decimal import Decimal

class MyProtocolLiquidityModule(LiquidityModule):
    def _get_lptoken_value(self, pool_state: Dict, amount: Decimal) -> Decimal:
        tvl = self.get_tvl(pool_state)
        totalSupply = Decimal(pool_state["allTokensBalance"]["totalSupply"])

        if totalSupply == 0:
            return Decimal(0)

        # Both has 18 decimals
        return tvl / totalSupply

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
        lpTokenValue = self._get_lptoken_value(pool_state, 1)

        oldAll = pool_state["allTokensBalance"]
        pool_state["allTokensBalance"] = pool_state["previousAllTokensBalance"]
        pDLpTokenValue = self._get_lptoken_value(pool_state, 1)
        pool_state["allTokensBalance"] = oldAll

        days = pool_state["days"]
        if days == 0:
            return Decimal(0)
        
        apyDaily = (lpTokenValue - pDLpTokenValue) / days
        apyCompounded = (1 + apyDaily) ** 365 - 1

        if apyCompounded < 0:
            return Decimal(0)
        return apyCompounded * 100

    def get_tvl(self, pool_state: Dict, token: Optional[Token] = None) -> Decimal:
        # From Pool.allTokensBalance()
        # Structure:
        # {
        #     "balances": list[int],
        #     "tokens": list[Token],
        #     "totalSupply": int,
        # }
        allTokensBalance = pool_state["allTokensBalance"]

        tvl = 0

        for i, token_ in enumerate(allTokensBalance["tokens"]):
            balance = Decimal(allTokensBalance["balances"][i])
            balance *= token_.reference_price
            
            d2 = token_.decimals
            balance /= 10 ** d2

            tvl += balance

        return tvl