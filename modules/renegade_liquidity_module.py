import httpx
import json

from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional
from decimal import Decimal
from enum import Enum

from renegade import ExternalMatchClient
from renegade.types import OrderSide, ExternalOrder

# Constant annotating that a fee is not taken out of the input token
NO_INPUT_FEE: int = 0

class Chain(Enum):
    """Supported blockchain networks for Renegade."""
    ARBITRUM_ONE = "arbitrum_one"
    ARBITRUM_SEPOLIA = "arbitrum_sepolia"

class RenegadeLiquidityModule(LiquidityModule):
    def __init__(self, renegade_api_key: str, renegade_api_secret: str, chain: Chain = Chain.ARBITRUM_ONE):
        """
        Initialize the Renegade liquidity module.
        
        :param renegade_api_key: The API key for Renegade
        :param renegade_api_secret: The API secret for Renegade
        :param chain: The blockchain to configure the client for
        """
        super().__init__()
        if chain == Chain.ARBITRUM_ONE:
            self._renegade_client = ExternalMatchClient.new_mainnet_client(
                api_key=renegade_api_key,
                api_secret=renegade_api_secret,
            )
        elif chain == Chain.ARBITRUM_SEPOLIA:
            self._renegade_client = ExternalMatchClient.new_sepolia_client(
                api_key=renegade_api_key,
                api_secret=renegade_api_secret,
            )

    def get_amount_out(
        self, 
        pool_states: Dict, 
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
        if not self._validate_pair(input_token, output_token):
            return None, None

        # Fetch a quote
        order = self._create_order_from_input(input_token, output_token, input_amount)
        signed_quote = self._renegade_client.request_quote_sync(order)
        if not signed_quote:
            return None, None
        
        # Fees are taken out of the receive amount, so the input token fee is zero
        # The output token amount on the quote accounts for this fee
        return NO_INPUT_FEE, signed_quote.quote.receive.amount

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
        if not self._validate_pair(input_token, output_token):
            return None, None

        # Fetch a quote
        order = self._create_order_from_output(input_token, output_token, output_amount)
        signed_quote = self._renegade_client.request_quote_sync(order)
        if not signed_quote:
            return None, None
        
        # Fees are taken out of the receive amount, so the input token fee is zero
        # The output token amount on the quote accounts for this fee
        return NO_INPUT_FEE, signed_quote.quote.send.amount

    def get_apy(self, _pool_state: Dict) -> Decimal:
        # Renegade has no APY
        return Decimal(0)

    def get_tvl(self, pool_state: Dict, token: Optional[Token] = None) -> Decimal:
        """
        Gets the total value locked (TVL) in the protocol.

        :param pool_state: A dictionary representing the state of the liquidity pool.
        :param token: Optional token to get TVL for. If None, returns total TVL.
        :return: The TVL amount in USD.
        """
        try:
            response = httpx.get("https://trade.renegade.fi/api/stats/tvl/usd")
            response.raise_for_status()
            data = response.json()
            return Decimal(str(data["tvl"]))
        except (httpx.RequestError, json.JSONDecodeError, KeyError) as e:
            # Log error and return 0 if we can't fetch TVL
            print(f"Error fetching Renegade TVL: {e}")
            return Decimal("0")

    # --- Private Helpers --- #

    def _create_order_from_input(self, input_token: Token, output_token: Token, input_amount: int) -> ExternalOrder:
        """
        Creates an order for the pair of tokens, constraining the input amount.
        """
        if self._check_usdc(input_token):
            # Buy side
            return ExternalOrder(
                quote_mint=input_token.address, # USDC
                base_mint=output_token.address,
                side=OrderSide.BUY,
                quote_amount=input_amount,
            )
        else:
            # Sell side
            return ExternalOrder(
                quote_mint=output_token.address, # USDC
                base_mint=input_token.address,
                side=OrderSide.SELL,
                base_amount=input_amount,
            )
    
    def _create_order_from_output(self, input_token: Token, output_token: Token, output_amount: int) -> ExternalOrder:
        """
        Creates an order for the pair of tokens, constraining the output amount.
        """
        if self._check_usdc(input_token):
            # Buy side
            return ExternalOrder(
                quote_mint=input_token.address, # USDC
                base_mint=output_token.address,
                side=OrderSide.BUY,
                exact_base_output=output_amount,
            )
        else: 
            # Sell side
            return ExternalOrder(
                quote_mint=output_token.address, # USDC
                base_mint=input_token.address,
                side=OrderSide.SELL,
                exact_quote_output=output_amount,
            )

    def _validate_pair(self, input_token: Token, output_token: Token) -> bool:
        """
        Validates the pair of tokens.

        :param input_token: The token being swapped in.
        :param output_token: The token being swapped out.
        :return: True if the pair is valid, False otherwise.
        """
        usdc_in = self._check_usdc(input_token)
        usdc_out = self._check_usdc(output_token)

        # Currently, all pairs are USDC quoted in Renegade
        if not (usdc_in or usdc_out):
            return False
        
        # No USDC -> USDC pairs
        if usdc_in and usdc_out:
            return False

        return True

    def _check_usdc(self, token: Token) -> bool:
        """
        Checks if the token is USDC.

        :param token: The token to check.
        :return: True if the token is USDC, False otherwise.
        """
        return token.symbol.upper() == "USDC"
