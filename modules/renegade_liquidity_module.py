from typing_extensions import Literal

from templates.liquidity_module import Token
from typing import Dict
from enum import Enum

from renegade import AtomicMatchApiBundle, ExternalMatchClient, SignedExternalQuote
from renegade.types import OrderSide, ExternalOrder

# Constant annotating that a fee is not taken out of the input token
NO_INPUT_FEE: int = 0

class Chain(Enum):
    """Supported blockchain networks for Renegade."""
    ARBITRUM_ONE = "arbitrum_one"
    ARBITRUM_SEPOLIA = "arbitrum_sepolia"

class RenegadeLiquidityModule:
    async def get_sell_quote(
        self, 
        fixed_parameters: Dict,
        input_token: Token, 
        output_token: Token,
        input_amount: int, 
        _block: Literal['latest', int] = 'latest'
    ) -> tuple[int | None, int | None, SignedExternalQuote | None]:
        """
        Computes the amount of output token a user would receive when providing `input_amount` of `input_token`.

        :param fixed_parameters: A dictionary of fixed parameters for the liquidity module.
        :param input_token: The token being swapped in.
        :param output_token: The token being swapped out.
        :param input_amount: The amount of input_token being provided.
        :return: The fee amount (integer or None type) in terms of input token, the 
        amount of output_token (integer or None type) that would be received by the user, 
        and the signed quote which can be assembled into a bundle. 
        """
        # Validate the input pair
        valid_pair = self._validate_pair(input_token, output_token)
        if not valid_pair:
            return None, None, None

        # Fetch a quote
        client = self._get_client(fixed_parameters)
        order = self._create_order_from_input(input_token, output_token, input_amount)
        try:
            signed_quote = await client.request_quote(order)
        except Exception as e:
            print(f"Error fetching Renegade quote: {e}")
            return None, None, None
        
        # If the quote is not found, return None
        if not signed_quote:
            return None, None, None
        
        # Fees are taken out of the receive amount, so the input token fee is zero
        # The output token amount on the quote accounts for this fee
        return NO_INPUT_FEE, signed_quote.quote.receive.amount, signed_quote
    
    async def get_buy_quote(
        self, 
        fixed_parameters: Dict,
        input_token: Token, 
        output_token: Token,
        output_amount: int, 
        _block: Literal['latest', int] = 'latest'
    ) -> tuple[int | None, int | None, SignedExternalQuote | None]:
        """
        Computes the amount of input token a user would need to provide to receive `output_amount` of `output_token`.

        :param fixed_parameters: A dictionary of fixed parameters for the liquidity module.
        :param input_token: The token being swapped in.
        :param output_token: The token being swapped out.
        :param output_amount: The amount of output_token desired.
        :return: The fee amount (integer or None type) in terms of input token, the 
        amount of input_token (integer or None type) required to receive the desired 
        output amount, and the signed quote which can be assembled into a bundle.
        """
        # Validate the input pair
        valid_pair = self._validate_pair(input_token, output_token)
        if not valid_pair:
            return None, None

        client = self._get_client(fixed_parameters)
        order = self._create_order_from_output(input_token, output_token, output_amount)
        try:
            signed_quote = await client.request_quote(order)
        except Exception as e:
            print(f"Error fetching Renegade quote: {e}")
            return None, None, None

        # If the quote is not found, return None
        if not signed_quote:
            return None, None, None
        
        # Fees are taken out of the receive amount, so the input token fee is zero
        # The output token amount on the quote accounts for this fee
        return NO_INPUT_FEE, signed_quote.quote.send.amount, signed_quote

    async def assemble_quote(
        self,
        fixed_parameters: Dict,
        quote: SignedExternalQuote,
    ) -> tuple[int | None, int | None, AtomicMatchApiBundle | None]:
        """
        Assembles a quote into an AtomicMatchApiBundle.

        :param fixed_parameters: A dictionary of fixed parameters for the liquidity module.
        :param quote: The signed quote to assemble.
        :return: The fee amount (integer or None type), the amount (integer or None type),
        and the AtomicMatchApiBundle (or None type) that can be used for execution.
        """
        client = self._get_client(fixed_parameters)
        try:
            atomic_bundle = await client.assemble_quote(quote)
        except Exception as e:
            print(f"Error assembling quote: {e}")
            return None, None, None

        # If a bundle cannot be assembled, return None
        if not atomic_bundle:
            return None, None, None

        # Fees are taken out of the receive amount, so the input token fee is zero
        # The output token amount on the quote accounts for this fee
        return NO_INPUT_FEE, atomic_bundle.match_bundle.receive.amount, atomic_bundle

    # --- Private Helpers --- #

    def _get_client(self, fixed_parameters: Dict) -> ExternalMatchClient:
        """
        Gets the Renegade client for the given fixed parameters.
        """
        chain = fixed_parameters.get("chain")
        api_key = fixed_parameters.get("api_key")
        api_secret = fixed_parameters.get("api_secret")

        if chain == Chain.ARBITRUM_ONE:
            return ExternalMatchClient.new_mainnet_client(
                api_key=api_key,
                api_secret=api_secret,
            )
        elif chain == Chain.ARBITRUM_SEPOLIA:
            return ExternalMatchClient.new_sepolia_client(
                api_key=api_key,
                api_secret=api_secret,
            )
        else:
            raise ValueError(f"Invalid chain: {chain}")

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
