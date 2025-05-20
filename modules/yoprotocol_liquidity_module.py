from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional
from decimal import Decimal

class Constant:
    ETHER = Decimal('1e18')

class YoProtocolLiquidityModule(LiquidityModule):
    def get_amount_out(
        self, 
        pool_states: Dict, 
        fixed_parameters: Dict,
        input_token: Token, 
        output_token: Token,
        input_amount: int, 
    ) -> tuple[int | None, int | None]:
        """
        Returns the amount of underlying asset required to transfer to get output_amount shares in Ether denomination. (using OZ ERC4626 convertToAssets function)
        """

    def get_amount_in(
        self, 
        pool_state: Dict, 
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        output_amount: int
    ) -> tuple[int | None, int | None]:
        """
        Returns the amount of underlying asset received from input_amount of shares in Ether denomination. (using OZ ERC4626 convertToShares function)
        """
        pass

    def get_apy(self, pool_state: Dict) -> Decimal:
        """
        Returns the APY of the pool in decimal percentage.
        """

        currentSharePrice = Decimal(pool_state['currentSharePrice'])
        firstSharePrice = Decimal(pool_state['firstSharePrice'])
        uptimeDays = Decimal(pool_state['uptimeDays'])

        return (currentSharePrice - firstSharePrice) / Constant.ETHER / uptimeDays * Decimal(365) * Decimal(100)

    def get_tvl(self, pool_state: Dict, token: Optional[Token] = None) -> Decimal:
        """
        Returns the total value locked (TVL) in the pool in Ether denomination.
        """
        
        totalAssets = Decimal(pool_state['totalAssets'])

        if token.address != pool_state['underlyingTokenAddress']:
            raise ValueError("Token address does not match the underlying token address in the pool state.")
        
        tvl = 0
        # write access is only on Base, and yoETH uses WETH as underlying token
        if token.address == "0x4200000000000000000000000000000000000006":
            tvl = totalAssets / Constant.ETHER
        else:
            tvl = totalAssets * token.reference_price / Constant.ETHER
        return tvl