from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional
from decimal import Decimal
import math

class Constant:
    ETHER = Decimal('1e18')
    OPTIMISM_WETH = "0x4200000000000000000000000000000000000006"

class YoProtocolLiquidityModule(LiquidityModule):
    def _convert_to_assets(self, pool_state: Dict, fixed_parameters: Dict, amount: int) -> int:
        """
        Convert a given amount of shares to the equivalent amount of underlying assets using the pool state and fixed parameters.
        Formula: floor(amount * (totalAssets + 1) / (totalSupply + 10 ** decimals))
        """
        totalAssets = pool_state["totalAssets"]
        totalSupply = pool_state["totalSupply"]
        decimals = fixed_parameters["decimals"]

        return math.floor(amount * (totalAssets + 1) / (totalSupply + 10 ** decimals))

    def _convert_to_shares(self, pool_state: Dict, fixed_parameters: Dict, amount: int) -> int:
        """
        Convert a given amount of underlying assets to the equivalent amount of shares using the pool state and fixed parameters.
        Formula: floor(amount * (totalSupply + 10 ** decimals) / (totalAssets + 1))
        """
        totalAssets = pool_state["totalAssets"]
        totalSupply = pool_state["totalSupply"]
        decimals = fixed_parameters["decimals"]

        return math.floor(amount * (totalSupply + 10 ** decimals) / (totalAssets + 1))

    def _wei_to_ether(self, amount: int) -> Decimal:
        """
        Convert a value from Wei to Ether denomination using the constant ETHER.
        """
        return Decimal(amount) / Constant.ETHER  # Fix typo in Constant

    def get_amount_out(
        self, 
        pool_state: Dict, 
        fixed_parameters: Dict,
        input_token: Token, 
        output_token: Token,
        input_amount: int, 
    ) -> tuple[int | None, int | None]:
        """
        Returns the amount of underlying asset required to transfer to get output_amount shares in Ether denomination. (using OZ ERC4626 convertToAssets function)
        """

        output_amount = 0

        if input_token.address == fixed_parameters["underlyingTokenAddress"]:
            output_amount = self._convert_to_assets(pool_state, fixed_parameters, input_amount)
        elif input_token.address == fixed_parameters["sharesTokenAddress"]:
            output_amount = self._convert_to_shares(pool_state, fixed_parameters, input_amount)
        else:
            raise ValueError("Invalid token address. Must be either underlyingTokenAddress or sharesTokenAddress.")
        
        return (output_amount, None)

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
        
        output_amount = 0

        if input_token.address == fixed_parameters["underlyingTokenAddress"]:
            output_amount = self._convert_to_shares(pool_state, fixed_parameters, output_amount)
        elif input_token.address == fixed_parameters["sharesTokenAddress"]:
            output_amount = self._convert_to_assets(pool_state, fixed_parameters, output_amount)
        else:
            raise ValueError("Invalid token address. Must be either underlyingTokenAddress or sharesTokenAddress.")
        
        return (output_amount, None)

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
        if token.address == Constant.OPTIMISM_WETH:
            tvl = totalAssets / Constant.ETHER
        else:
            tvl = totalAssets * token.reference_price / Constant.ETHER
        return tvl