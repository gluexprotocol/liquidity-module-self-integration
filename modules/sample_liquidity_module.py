from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional
from decimal import Decimal

from utils.lp_token_swap import LPTokenSwap

class MyProtocolLiquidityModule(LiquidityModule):

    # The uniswap_v2 amm logic is replicated for representation purposes

    # Calculates the output amount given an input amount for a swap. This handles token-to-token swaps,
    # LP token minting (adding liquidity), and LP token burning (removing liquidity).
    def get_amount_out(
        self, 
        pool_state: Dict, 
        fixed_parameters: Dict,
        input_token: Token, 
        output_token: Token,
        input_amount: int, 
    ) -> tuple[int | None, int | None]:

        # Implement logic to calculate output amount given input amount

        is_lp_token_swap, is_lp_token_in = self.is_lp_token_swap(
            token_in = input_token,
            token_out = output_token
        )

        if is_lp_token_swap:
            # LP_token swap

            if is_lp_token_in:
                # burn
                fee_amount, amount_out = self.lp_token_burn_wrapper(
                    pool_state=pool_state,
                    token0_out = output_token.address.lower() == fixed_parameters['tokens_address0'].lower(),
                    lp_token_amount = input_amount
                )
            else:
                # mint        
                fee_amount, amount_out = self.lp_token_mint_wrapper(
                    pool_state=pool_state,
                    amount0 = input_amount if input_token.address.lower() == fixed_parameters['tokens_address0'].lower() else 0,
                    amount1 = input_amount if input_token.address.lower() == fixed_parameters['tokens_address1'].lower() else 0
                )

        else:
            # token to token swap
            if input_token.address == fixed_parameters['token0']:
                reserve_in = pool_state['reserve0']
                reserve_out = pool_state['reserve1']
            else:
                reserve_in = pool_state['reserve1']
                reserve_out = pool_state['reserve0']

            if not reserve_in or not reserve_out:
                fee = None
                amount = None

                return fee, amount

            fee_amount, amount_out = self.swap(reserve_in=reserve_in, reserve_out=reserve_out, amount_in=input_amount)

        fee = fee_amount
        amount = amount_out

        return fee, amount

    # Calculates the input amount needed to get a specific output amount for a swap.
    # Returns (None, None) for LP token swaps as they're not supported for this direction.
    def get_amount_in(
        self, 
        pool_state: Dict, 
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        output_amount: int
    ) -> tuple[int | None, int | None]:

        is_lp_token_swap, _ = self.is_lp_token_swap(
            token_in = input_token,
            token_out = output_token
        )

        if is_lp_token_swap:
            # return None if lp_tokens are involved in swap
            fee = None
            amount = None

            return fee, amount

        if input_token.address == fixed_parameters['token0']:
            reserve_in = pool_state['reserve0']
            reserve_out = pool_state['reserve1']
        else:
            reserve_in = pool_state['reserve1']
            reserve_out = pool_state['reserve0']

        fee_amount, amount_in = self.swap(reserve_in=reserve_in, reserve_out=reserve_out, amount_out=output_amount)

        fee = fee_amount
        amount = amount_in

        return fee, amount
    def get_tvl(
        self, 
        pool_state: Dict, 
        pool_tokens: Dict[Token.address, Token]
    ) -> int:
            '''
            Method to obtain the TVL at an arbitrary liquidity pool in the 
            protocol. 
            
            Inputs:
            - pool_state -> Dictionary of liquidity pool data attainable via 
                            RPC calls that are required to compute the pool's TVL.
            - pool_tokens -> Dictionary of tokens relevant to the liquidity pool.
            
            NOTE: pool_tokens also contains the LP token.
            NOTE: token.reference_price can be assumed to be the exchange
                    rate between token.address and the native token of the 
                    blockchain in which this liquidity pool exists.
            
            Returns:
            TVL of the pool denominated in the lowest denomination of 
            the native token.
            '''
            # Implement TVL calculation logic
            reserve0 = pool_state.get('reserve0', 0)
            reserve1 = pool_state.get('reserve1', 0)
            
            # Get tokens from pool_tokens dictionary
            tokens = list(pool_tokens.values())
            token0 = tokens[0]  
            token1 = tokens[1]  
            
            rprice0 = token0.reference_price
            rprice1 = token1.reference_price
                
                # Translate reserves into reference token amounts
            rreserve0 = reserve0 * rprice0
            rreserve1 = reserve1 * rprice1
                
                # Get TVL in refrence token
            rtvl = rreserve0 + rreserve1
            
            return int(rtvl)

# Calculates the Annual Percentage Yield (APY) for providing liquidity to the pool.
# Uses a compound interest formula based on 24-hour fees and total value locked (TVL).
    def get_apy(
            self, 
            pool_state: Dict, 
            underlying_amount: int,
            underlying_token: Token, 
            pool_tokens: Dict[Token.address, Token]
    ) -> int:
            '''
                    Method to obtain the diluted APY of an arbitrary liquidity pool in the 
                    protocol. 
                    
                    Inputs:
                    - pool_state -> Dictionary of liquidity pool data attainable via 
                                    RPC calls that are required to compute the pool's diluted APY..
                    - pool_tokens -> Dictionary of tokens relevant to the liquidity pool.
                    
                    NOTE: pool_tokens also contains the LP token.
                    NOTE: token.reference_price can be assumed to be the exchange
                        rate between token.address and the native token of the 
                        blockchain in which this liquidity pool exists.
                    
                    Returns:
                    Diluted APY of the pool in basis points (10,000).
            '''
            
        # Get current reserves of the pool
            reserve0 = pool_state.get('reserve0', 0)
            reserve1 = pool_state.get('reserve1', 0)
                
            token0_address = pool_state.get("token0_address")
            token1_address = pool_state.get("token1_address")
                
            # Add the underlying amount into the pool
            if underlying_token.address == token0_address:
                reserve0 += underlying_amount
            elif underlying_token.address == token1_address:
                reserve1 += underlying_amount
            
            token0_decimals = pool_tokens[token0_address].decimals
            token1_decimals = pool_tokens[token1_address].decimals
            
            rprice0 = pool_tokens[token0_address].reference_price
            rprice1 = pool_tokens[token1_address].reference_price
            
            # Adjust for the difference in reference price scaling
            d1 = 18 - token0_decimals
            d2 = 18 - token1_decimals
            
            # Normalize prices based on decimals
            price0 = Decimal(rprice0) / (Decimal(10) ** d1) if rprice0 else Decimal(0)
            price1 = Decimal(rprice1) / (Decimal(10) ** d2) if rprice1 else Decimal(0)
            
            # If price data is missing, return 0 APY
            if price0 == 0 or price1 == 0:
                return 0
                
            # Adjust reserves for decimals
            adjusted_reserve0 = Decimal(reserve0) / (Decimal(10) ** token0_decimals)
            adjusted_reserve1 = Decimal(reserve1) / (Decimal(10) ** token1_decimals)
            
            # Convert token reserves into value terms using price
            reserve0_value = adjusted_reserve0 * price0
            reserve1_value = adjusted_reserve1 * price1
            tvl = reserve0_value + reserve1_value
            
            fee_data = pool_state.get('fees_over_period', {})
            fee_amount0 = fee_data.get('amount0', 0)
            fee_amount1 = fee_data.get('amount1', 0)
            days = fee_data.get('days', 0)
            
            fee_amount0 = (Decimal(fee_amount0) / (Decimal(10) ** token0_decimals)) * price0
            fee_amount1 = (Decimal(fee_amount1) / (Decimal(10) ** token1_decimals)) * price1
            
            # Assume 0.3% fee portion goes to LPs (Uniswap v2-style)
            total_fees_value = (fee_amount0 + fee_amount1) * Decimal("0.003")
            
            if tvl == 0 or days == 0:
                return 0
                
            # Calculate daily yield from total fees
            daily_fees = total_fees_value / Decimal(days)
            daily_rate = daily_fees / tvl
            
            # Annualize the return using simple compounding approximation
            apy = daily_rate * Decimal(365) * Decimal(100)
                
            # Get apy in bps
            apy_bps = apy * Decimal(100)  # Convert percentage to basis points
                
            return int(apy_bps)

    # Core AMM swap function that implements the constant product formula (x * y = k).
    # Can calculate either output amount given input, or input needed for desired output.
    # Applies a 0.3% fee on swaps.
    def swap(
        self,
        reserve_in:int,
        reserve_out:int,
        amount_out: int = None,
        amount_in:int = None
    ) -> tuple[int | None, int | None]:

        '''
        Calculation for amount out or amount_in of constant-product pools given reserves.
        Source sample:
        https://etherscan.io/address/0x7a250d5630b4cf539739df2c5dacb4c659f2488d#code 
        '''

        if amount_out is None:

            if not (reserve_in > 0 and reserve_out > 0):
                return None, None
            amount_in_with_fee = amount_in * 997
            fee_amount = int(amount_in * 0.003)
            numerator = amount_in_with_fee * reserve_out
            denominator = reserve_in * 1000 + amount_in_with_fee
            amount = int(numerator//denominator) 

        else:

            if not (reserve_in > 0 and reserve_out > 0):
                return 0, 0
            amount_out = int(amount_out)
            numerator = reserve_in * amount_out * 1000
            denominator = (reserve_out - amount_out) * 997
            amount =  int(numerator // denominator) + 1

            if amount < 0:
                return None, None

            fee_amount = int(amount * 0.003)


        return int(fee_amount), int(amount)

    '''
    LP Token swap Methods
    '''

    # Helper function that determines if an LP token is involved in the swap and, if so,
    # which direction (whether LP token is the input or output token).
    def is_lp_token_swap(
        self,
        token_in: Token,
        token_out: Token
    ):
        if (token_in.address.lower() == self.lp_token_address.lower() \
                or token_out.address.lower() == self.lp_token_address.lower()):

            return (True, token_in.address.lower() == self.lp_token_address.lower())

        return (False, None)

    # Handles adding liquidity to the pool by providing a single token.
    # Internally swaps half of the provided token for the other token, then mints LP tokens.
    # Returns the fee and the amount of LP tokens minted, with a 5% discount applied.
    def lp_token_mint_wrapper(
        self,
        pool_state: Dict,
        amount0: int,
        amount1: int
    ):

        '''
        Interactions in mint:
        - Swap 50% of token1 for token2
        - Mint lp tokens using 50% of token1 and token2  recevied from swap        
        '''

        # Use pool_state for reserves
        reserve0 = int(pool_state['reserve0'])
        reserve1 = int(pool_state['reserve1'])

        # Get LP swap states from pool_state
        feeTo = pool_state.get('feeTo', '')
        _kLast = int(pool_state.get('kLast', 0))
        totalSupply = int(pool_state.get('totalSupply', 0))
        MINIMUM_LIQUIDITY = int(pool_state.get('MINIMUM_LIQUIDITY', 1000))

        _, _, _, lp_amount = self._lp_mint(
            pool_state=pool_state,
            amount0=amount0,
            amount1=amount1,
            reserve0=reserve0,
            reserve1=reserve1,
            feeTo=feeTo,
            _kLast=_kLast,
            totalSupply=totalSupply,
            MINIMUM_LIQUIDITY=MINIMUM_LIQUIDITY
        )        
        fee_amount = 0

        # Note: Apply 5% discount on the lp_amount
        # We add this discount as there are some tokens that charge a fee which we cant replicate in the AMM
        # On gluex router, we use simualtion amount out to send in the response

        if lp_amount is not None:
            lp_amount = int(lp_amount * 0.95)

        return fee_amount, lp_amount   

    # Handles removing liquidity from the pool by burning LP tokens.
    # Burns LP tokens to get both underlying tokens, then swaps one token for the other if needed.
    # Returns the fee and the amount of tokens received after the complete operation.
    def lp_token_burn_wrapper(
        self,
        pool_state: Dict,
        token0_out: bool,
        lp_token_amount: int
    ):

        '''
        Interactions in burn:
        - Call burn - returns both token0 and token1
        - swap received token1 for token0 if token_out is token0, vice-versa      
        '''

        # Use pool_state for reserves
        reserve0 = int(pool_state['reserve0'])
        reserve1 = int(pool_state['reserve1'])

        # Get LP swap states from pool_state
        feeTo = pool_state.get('feeTo', '')
        _kLast = int(pool_state.get('kLast', 0))
        totalSupply = int(pool_state.get('totalSupply', 0))
        liquidity = int(pool_state.get('liquidity', 0)) + lp_token_amount

        _, _, _, amount_received = self._lp_burn(
            pool_state=pool_state,
            token0_out=token0_out,
            lp_token_amount=lp_token_amount,
            reserve0=reserve0,
            reserve1=reserve1,
            feeTo=feeTo,
            _kLast=_kLast,
            totalSupply=totalSupply,
            liquidity=liquidity
        )

        fee_amount = 0
        return fee_amount, amount_received

    # Internal method that implements the LP token minting process.
    # Handles swapping half of the input token for the other token, then mints LP tokens.
    # Returns detailed information about all intermediate steps in the process.
    def _lp_mint(
        self,
        pool_state: Dict,
        amount0: int,
        amount1: int,
        reserve0: int,
        reserve1: int,
        feeTo: str,
        _kLast: int,
        totalSupply: int,
        MINIMUM_LIQUIDITY: int
    ):
        # swap 50% of tokenIn
        if amount0 == 0:
            amount1_half = amount1 // 2
            amount1 = amount1 - amount1_half # to handle cases where amount1 is odd

            _, amount0_received = self.swap(
                reserve_in = reserve1,
                reserve_out = reserve0,
                amount_in = amount1_half,
                amount_out  =  None
            )

            if amount0_received is None or reserve1 <= amount1_half:
                # swap failed. return None
                return None, None, None, None

            # update reserves
            reserve0 -= amount0_received
            reserve1 += amount1_half

            try:
                lp_amount = LPTokenSwap.mint(
                    _reserve0 = reserve0,
                    _reserve1 = reserve1,
                    balance0 =  reserve0 + amount0_received,
                    balance1 = reserve1 + amount1,
                    feeTo = feeTo,
                    _kLast = _kLast,
                    totalSupply = totalSupply,
                    MINIMUM_LIQUIDITY = MINIMUM_LIQUIDITY
                )

                lp_amount = int(lp_amount) if lp_amount is not None else lp_amount
            except Exception as e:
                lp_amount = None

            return int(amount1), int(amount1_half), int(amount0_received), lp_amount
        else:
            amount0_half = amount0 // 2
            amount0 = amount0 - amount0_half # to handle cases where amount0 is odd

            _, amount1_received = self.swap(
                reserve_in = reserve0,
                reserve_out = reserve1,
                amount_in = amount0_half,
                amount_out  = None
            )

            if amount1_received is None or reserve0 <= amount0_half:
                # swap failed. return None
                return None, None, None, None

            # update reserves
            reserve1 -= amount1_received
            reserve0 += amount0_half

            try:
                lp_amount = LPTokenSwap.mint(
                    _reserve0 = reserve0,
                    _reserve1 = reserve1,
                    balance0 =  reserve0 + amount0,
                    balance1 = reserve1 + amount1_received,
                    feeTo = feeTo,
                    _kLast = _kLast,
                    totalSupply = totalSupply,
                    MINIMUM_LIQUIDITY = MINIMUM_LIQUIDITY
                )

                lp_amount = int(lp_amount) if lp_amount is not None else lp_amount
            except Exception as e:
                lp_amount = None

            return int(amount0), int(amount0_half), int(amount1_received), lp_amount

    # Internal method that implements the LP token burning process.
    # Burns LP tokens to receive both tokens, then swaps one token for the other if needed.
    # Returns detailed information about all intermediate steps in the process.
    def _lp_burn(
        self,
        pool_state: Dict,
        token0_out: bool,
        lp_token_amount: int,
        reserve0: int,
        reserve1: int,
        feeTo: str,
        _kLast: int,
        totalSupply: int,
        liquidity: int
    ):

        '''
        BURN
        '''

        try:
            (amount0_received, amount1_received) = LPTokenSwap.burn(
                _reserve0 = reserve0,
                _reserve1 = reserve1,
                balance0 = reserve0,
                balance1 = reserve1,
                liquidity = liquidity,
                feeTo = feeTo,
                _kLast = _kLast,
                totalSupply = totalSupply
            )

            # update pool reserves after swap
            reserve0 -= amount0_received
            reserve1 -= amount1_received

            if reserve0 <= 0 or reserve1 <= 0:
                return None, None, None, None

            if token0_out: # only token0 should be received from the swap
                if amount1_received > 0:
                    # Need to swap token1 for token0

                    _, amount0_received_from_token_swap = self.swap(
                        reserve_in = reserve1,
                        reserve_out = reserve0,
                        amount_in = amount1_received,
                        amount_out = None
                    )

                    if amount0_received_from_token_swap is None:
                        return None, None, None, None

                    total_amount0_received = amount0_received + amount0_received_from_token_swap

                return int(amount1_received), int(amount0_received), int(amount0_received_from_token_swap), int(total_amount0_received)

            else: # only token1 should be received from the swap
                if amount0_received > 0:
                    # Need to swap token0 for token1

                    _, amount1_received_from_token_swap = self.swap(
                        reserve_in = reserve0,
                        reserve_out = reserve1,
                        amount_in = amount0_received,
                        amount_out = None
                    )

                    if amount1_received_from_token_swap is None:
                        return None, None, None, None

                    total_amount1_received = amount1_received + amount1_received_from_token_swap

                return int(amount0_received), int(amount1_received), int(amount1_received_from_token_swap), int(total_amount1_received)

        except Exception as e:
            return None, None, None, None