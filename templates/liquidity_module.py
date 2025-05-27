from abc import ABC, abstractmethod
from typing import Dict, Optional
from decimal import Decimal


class Token:
    """ A representation of a token within the liquidity module. """
    def __init__(self, address: str, symbol: str, decimals: int, reference_price: Decimal):
        """
        :param address: The blockchain address of the token.
        :param symbol: The symbol of the token (e.g., "USDC", "ETH").
        :param decimals: The number of decimal places the token uses.
        :param reference_price: The price of the token relative to the native blockchain token.
        """
        self.address = address
        self.symbol = symbol
        self.decimals = decimals
        self.reference_price = reference_price


class LiquidityModule(ABC):
    """
    Abstract base class that all GlueX liquidity modules must inherit from.
    Ensures that modules correctly implement liquidity-related computations.
    """

    @abstractmethod
    def get_amount_out(
        self, 
        pool_state: Dict, 
        fixed_parameters: Dict,
        input_token: Token, 
        output_token: Token,
        input_amount: int, 
    ) -> tuple[int | None, int | None]:
        """
        Computes the amount of output token a user would receive when providing `input_amount` of `input_token`.

        :param pool_state: A dictionary representing the state of the liquidity pool.
        :param fixed_parameters: A dictionary of fixed parameters for the liquidity module.
        :param input_token: The token being swapped in.
        :param output_token: The token being swapped out.
        :param input_amount: The amount of input_token being provided.
        :return: The fee amount (integer or None type) in terms of input token and the amount of output_token (integer or None type) that would be received by the user. 
        """
        pass

    @abstractmethod
    def get_amount_in(
        self, 
        pool_state: Dict, 
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        output_amount: int
    ) -> tuple[int | None, int | None]:
        """
        Computes the amount of input token required to receive `output_amount` of `output_token`.

        :param pool_state: A dictionary representing the state of the liquidity pool.
        :param fixed_parameters: A dictionary of fixed parameters for the liquidity module.
        :param input_token: The token being swapped in.
        :param output_token: The token being swapped out.
        :param output_amount: The amount of output_token desired.
        :return: The fee amount (integer or None type) in terms of input token and the amount of input_token (integer or None type) required to receive the desired output amount.
        """
        pass

    @abstractmethod
    def get_apy(
        self, 
        pool_state: Dict, 
        input_token: Token, 
        output_token: Token, 
        input_amount: int
    ) -> Decimal:
        """
        Computes the annual percentage yield (APY) for liquidity providers, lenders, or other actors in the protocol.
        
        :param pool_state: A dictionary representing the state of the liquidity pool.
        :param input_token: The token being swapped in.
        :param output_token: The token being swapped out.
        :param input_amount: The amount of input_token being provided.
        :return: The APY as a decimal value (e.g., 0.05 for 5% APY).
        """
        pass

    @abstractmethod
    def get_tvl(self, pool_state: Dict, token: Optional[Token] = None) -> Decimal:
        """
        Computes the total value locked (TVL) in a liquidity pool.

        :param pool_state: A dictionary representing the state of the liquidity pool.
        :param token: If provided, returns TVL for the specific token. Otherwise, returns total TVL.
        :return: The total value locked in the pool, denominated in the blockchain's native token.
        """
        pass