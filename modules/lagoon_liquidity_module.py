from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional, Tuple
from decimal import Decimal
import math

class Constants:
    ETHER = Decimal("1e18")

class LagoonLiquidityModule(LiquidityModule):
    def _convert_to_assets(self, pool_state: Dict, fixed_parameters: Dict, amount: int) -> int:
        totalAssets = pool_state["totalAssets"]
        totalSupply = pool_state["totalSupply"]
        decimals = fixed_parameters["shareTokenDecimals"]
        
        return math.floor(amount * (totalAssets + 1) / (totalSupply + 10 ** decimals))

    def _convert_to_shares(self, pool_state: Dict, fixed_parameters: Dict, amount: int) -> int:
        totalAssets = pool_state["totalAssets"]
        totalSupply = pool_state["totalSupply"]
        decimals = fixed_parameters["shareTokenDecimals"]
        
        return math.floor(amount * (totalSupply + 10 ** decimals) / (totalAssets + 1))

    def _get_share_price(self, totalAssets: Decimal, totalSupply: Decimal, decimals: Decimal) -> Decimal:
        return Decimal(totalAssets) / Decimal(totalSupply + 10 ** decimals)

    def get_amount_in(
        self,
        pool_state: Dict,
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        output_amount: int
    ) -> Tuple[None, int]:
        if (
            pool_state["totalAssets"] == 0 or
            pool_state["totalSupply"] == 0 or
            pool_state["days"] == 0 or
            output_amount < 0
        ):
            raise Exception("Invalid pool state or output amount")
        
        input_amount = 0
        if input_token.address == fixed_parameters["vaultContractAddress"]:
            input_amount = self._convert_to_shares(pool_state, fixed_parameters, output_amount)
        elif input_token.address == fixed_parameters["underlyingTokenAddress"]:
            input_amount = self._convert_to_assets(pool_state, fixed_parameters, output_amount)
        else:
            raise Exception("Invalid input token address")
        
        return (None, input_amount)

    def get_amount_out(
        self,
        pool_state: Dict,
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        input_amount: int
    ) -> Tuple[None, Decimal]:
        if (
            pool_state["totalAssets"] == 0 or
            pool_state["totalSupply"] == 0 or
            pool_state["days"] == 0 or
            input_amount < 0
        ):
            raise Exception("Invalid pool state or input amount")
        output_amount = 0

        if input_token.address == fixed_parameters["vaultContractAddress"]:
            output_amount = self._convert_to_assets(pool_state, fixed_parameters, input_amount)
        elif input_token.address == fixed_parameters["underlyingTokenAddress"]:
            output_amount = self._convert_to_shares(pool_state, fixed_parameters, input_amount)
        else:
            raise Exception("Invalid input token address")

        return (None, output_amount)

    def get_apy(self, pool_state: Dict) -> Decimal:
        days = Decimal(pool_state["days"])
        totalAssetsBefore = Decimal(pool_state["totalAssetsBefore"])
        totalAssets = Decimal(pool_state["totalAssets"])
        totalSupplyBefore = Decimal(pool_state["totalSupplyBefore"])
        totalSupply = Decimal(pool_state["totalSupply"])
        underlyingTokenDecimals = Decimal(pool_state["underlyingTokenDecimals"])

        sharePriceBefore = self._get_share_price(
            totalAssetsBefore, totalSupplyBefore, underlyingTokenDecimals
        )
        sharePrice = self._get_share_price(
            totalAssets, totalSupply, underlyingTokenDecimals
        )
        
        if days == 0 or sharePriceBefore == 0:
            return Decimal(0)
        
        apyDaily = (sharePrice - sharePriceBefore) / sharePriceBefore / days
        apyCompounded = (1 + apyDaily) ** 365 - 1
        
        return apyCompounded * 100

    def get_tvl(self, pool_state: Dict, token: Optional[Token] = None) -> Decimal:
        totalAssets = Decimal(pool_state.get("totalAssets", 0))

        if token.symbol == "ETH" or token.symbol == "WETH":
            return Decimal(totalAssets)
        else:
            tokenDecimals = token.decimals
            tokenPrice = token.reference_price

            tvl = totalAssets * tokenPrice
            tvl /= Decimal(10 ** tokenDecimals)

            return tvl