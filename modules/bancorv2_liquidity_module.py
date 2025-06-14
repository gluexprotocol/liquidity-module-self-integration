from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional
from decimal import Decimal

class MyProtocolLiquidityModule(LiquidityModule):
    NATIVE_ASSET = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE".lower()
    
    def get_amount_out(
        self, 
        pool_state: Dict, 
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

    def get_tvl(
        self, 
        pool_state: Dict, 
        pool_tokens: Dict[Token.address, Token]
    ) -> int:
        # LP Tokens are not included in the TVL calculation. Because they don't hold value.

        # Obtainable from StandardPoolConverter.reserveBalances:
        # function reserveBalances() public view returns (uint256, uint256) {
        #     return _loadReserveBalances(1, 2);
        # }
        reserve1 = pool_state.get('reserve1', 0)
        reserve2 = pool_state.get('reserve2', 0)

        # Reserve tokens 1 and 2 are btainable from StandardPoolConverter.reserveTokens()
        token1 = pool_state.get('token1').lower()
        token2 = pool_state.get('token2').lower()
        # Which can then be utilized to get their decimals.
        decimal1 = pool_state.get('decimal1', 18)
        decimal2 = pool_state.get('decimal2', 18)

        rprice1 = pool_tokens[token1].reference_price
        rprice2 = pool_tokens[token2].reference_price
        
        tvl = 0

        if self.NATIVE_ASSET == token1:
            tvl += reserve1
        else:
            tvl += reserve1 * rprice1 / (10 ** decimal1)
        if self.NATIVE_ASSET == token2:
            tvl += reserve2
        else:
            tvl += reserve2 * rprice2 / (10 ** decimal2)
        
        return tvl