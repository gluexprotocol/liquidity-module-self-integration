from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional, Tuple
from decimal import Decimal
import math

class Constants:
    ETHER = Decimal("1e18")

class LagoonLiquidityModule(LiquidityModule):
    def _convert_to_assets(self, pool_state: Dict, fixed_parameters: Dict, amount: int) -> int:
        """
        Convert a given amount of shares to the equivalent amount of underlying assets.
        Uses the pool state and share token decimals.
        Formula: floor(amount * (totalAssets + 1) / (totalSupply + 10 ** decimals))
        Args:
            pool_state (Dict): The current state of the pool.
            shareToken (Token): The share token object (with decimals).
            amount (int): The amount of shares to convert.
        Returns:
            int: The equivalent amount of underlying assets.
        """
        totalAssets = pool_state["totalAssets"]
        totalSupply = pool_state["totalSupply"]
        decimals = fixed_parameters["shareTokenDecimals"]
        
        return math.floor(amount * (totalAssets + 1) / (totalSupply + 10 ** decimals))

    def _convert_to_shares(self, pool_state: Dict, fixed_parameters: Dict, amount: int) -> int:
        """
        Convert a given amount of underlying assets to the equivalent amount of shares.
        Uses the pool state and share token decimals.
        Formula: floor(amount * (totalSupply + 10 ** decimals) / (totalAssets + 1))
        Args:
            pool_state (Dict): The current state of the pool.
            shareToken (Token): The share token object (with decimals).
            amount (int): The amount of assets to convert.
        Returns:
            int: The equivalent amount of shares.
        """
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
        """
        Calculate the required input amount for a given output amount.
        Depending on the input token address, converts between shares and assets.
        Args:
            pool_state (Dict): The current state of the pool.
            fixed_parameters (Dict): Fixed parameters including token addresses.
            input_token (Token): The input token object.
            output_token (Token): The output token object.
            output_amount (int): The desired output amount.
        Returns:
            Tuple[None, int]: Tuple of (fee, input amount in lowest denomination).
        Raises:
            Exception: If pool state or output amount is invalid, or token address is invalid.
        """
        if (
            pool_state["totalAssets"] == 0 or
            pool_state["totalSupply"] == 0 or
            pool_state["days"] == 0 or
            output_amount < 0
        ):
            raise Exception("Invalid pool state or output amount")
        
        input_amount = 0
        if input_token.address == fixed_parameters["vaultContractAddress"]:
            input_amount = self._convert_to_assets(pool_state, fixed_parameters, output_amount)
        elif input_token.address == fixed_parameters["underlyingTokenAddress"]:
            input_amount = self._convert_to_shares(pool_state, fixed_parameters, output_amount)
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
        """
        Calculate the output amount for a given input amount.
        Depending on the input token address, converts between shares and assets.
        Args:
            pool_state (Dict): The current state of the pool.
            fixed_parameters (Dict): Fixed parameters including token addresses.
            input_token (Token): The input token object.
            output_token (Token): The output token object.
            input_amount (int): The input amount.
        Returns:
            Tuple[None, Decimal]: Tuple of (fee, output amount in lowest denomination).
        Raises:
            Exception: If pool state or input amount is invalid, or token address is invalid.
        """
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
        """
        Calculate the APY (Annual Percentage Yield) as a percentage.
        Formula: (currentSharePrice - originSharePrice) / days * 100
        Args:
            pool_state (Dict): The current state of the pool.
        Returns:
            Decimal: The APY as a percentage.
        Raises:
            Exception: If days is zero.
        """
        
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
        
        if days == 0:
            return Decimal(0)
        
        apyDaily = (sharePrice - sharePriceBefore) / sharePriceBefore / days
        apyCompounded = (1 + apyDaily) ** 365 - 1
        
        return apyCompounded * 100

    def get_tvl(self, pool_state: Dict, token: Optional[Token] = None) -> Decimal:
        """
        Get the TVL (Total Value Locked) for the pool.
        Returns the value from the pool state, or 0 if not present.
        In terms of the network native asset in its lowest denomination.
        Args:
            pool_state (Dict): The current state of the pool.
            token (Optional[Token]): The underlying token of the Lagoon vault.
        Returns:
            Decimal: The TVL value.
        """
        
        totalAssets = pool_state.get("totalAssets", 0)

        if token.symbol == "ETH" or token.symbol == "WETH":
            return Decimal(totalAssets)
        else:
            return Decimal(totalAssets * token.reference_price)