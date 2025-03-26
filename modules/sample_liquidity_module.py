from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional
from decimal import Decimal

from utils.lp_token_swap import LPTokenSwap

class MyProtocolLiquidityModule(LiquidityModule):

    # The uniswap_v2 amm logic is replicated for representation purposes
    
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
                    token0_out = output_token.address.lower() == self.tokens_addresses[0].lower(),
                    lp_token_amount = input_amount
                )
            else:
                # mint        
                fee_amount, amount_out = self.lp_token_mint_wrapper(
                    amount0 = input_amount if input_token.address.lower() == self.tokens_addresses[0].lower() else 0,
                    amount1 = input_amount if input_token.address.lower() == self.tokens_addresses[1].lower() else 0
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
            
            fee_amount, amount_out = self.swap(reserve_in=reserve_in, reserve_out = reserve_out, amount_in = input_amount)

        fee = fee_amount
        amount = amount_out

        return fee, amount

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

        fee_amount, amount_in = self.swap(reserve_in = reserve_in, reserve_out = reserve_out, amount_out = output_amount)

        # NOTE: 
        # Uniswap v2 fees are denominated in token_in. 
        # Hence, it's not necessary to map fee_amount to token_in.
        # If fee_amount would be denominated in token_out, then
        # a mapping from token_out to token_in would be required.

        fee = fee_amount
        amount = amount_in

        return fee, amount
    
    def get_apy(self, pool_state: Dict) -> Decimal:
        
        # Implement APY calculation logic
        fees_24h = pool_state['fees_24h']
        tvl = pool_state['tvl']
        fee_tier = pool_state['fee_tier']

        daily_yield = fees_24h / tvl

        apy_simple = daily_yield * 365

        apy_compounded = (1 + daily_yield) ** 365 - 1

        return apy_compounded

    def get_tvl(self, pool_state: Dict, token: Optional[Token] = None) -> Decimal:
        
        # Implement TVL calculation logic
        return pool_state['tvl']

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

    # helper function that returns if lp_tokens are involved in swap along with direction of swap, if an lp_token is involved
    def is_lp_token_swap(
        self,
        token_in: Token,
        token_out: Token
    ):
        if (token_in.address.lower() == self.lp_token_address.lower() \
                or token_out.address.lower() == self.lp_token_address.lower()):
            
            return (True, token_in.address.lower() == self.lp_token_address.lower())
        
        return (False, None)
    
    
    # lp swap function
    def lp_token_mint_wrapper(
        self,
        amount0: int,
        amount1: int
    ):
        
        '''
            Interactions in mint:
            - Swap 50% of token1 for token2
            - Mint lp tokens using 50% of token1 and token2  recevied from swap        
        '''

        _, _, _, lp_amount = self._lp_mint(
            amount0 = amount0,
            amount1 = amount1
        )        
        fee_amount = 0

        # Note: Apply 5% discount on the lp_amount
        # We add this discount as there are some tokens that charge a fee which we cant replicate in the AMM
        # On gluex router, we use simualtion amount out to send in the response

        if lp_amount is not None:
            lp_amount = int(lp_amount * 0.95)

        return fee_amount, lp_amount   
    

    # lp swap function
    def lp_token_burn_wrapper(
        self,
        token0_out: bool,
        lp_token_amount: int
    ):
        
        '''
            Interactions in burn:
            - Call burn - returns both token0 and token1
            - swap received token1 for token0 if token_out is token0, vice-versa      
        '''

        _, _, _, amount_received = self._lp_burn(
            token0_out = token0_out,
            lp_token_amount = lp_token_amount
        )

        fee_amount = 0
        return fee_amount, amount_received
  

    # This function gives the intermediate amounts at all interactions with minting lp tokens
    # This method will be used by the executors
    # Returns:
    # amount of token0 used in token-swap, amount of token0 used in mint, amount of token1 received from swap, amount of lp token recevied from mint
    def _lp_mint(
        self,
        amount0: int,
        amount1: int
    ):
        reserve0 = int(self.states.Reserves.value['reserve0'])
        reserve1 = int(self.states.Reserves.value['reserve1'])
        
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

            # Get states need for LP_token_swap
            feeTo: str = self.states.FeeTo.value
            _kLast: int = int(self.states.KLast.value)
            totalSupply: int = int(self.states.TotalSupply.value)
            MINIMUM_LIQUIDITY: int = int(self.states.MINIMUM_LIQUIDITY.value)

            # for lp_token_swap, we will transfer tokens to the pool and then call mint
            
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
                if self.enableDebugLogs:
                    print(e)
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

            # Get states need for LP_token_in swap
            feeTo: str = self.states.FeeTo.value
            _kLast: int = int(self.states.KLast.value)
            totalSupply: int = int(self.states.TotalSupply.value)
            MINIMUM_LIQUIDITY: int = int(self.states.MINIMUM_LIQUIDITY.value)

            # for lp_token_swap, we will transfer tokens to the pool and then call mint
            
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
                if self.enableDebugLogs:
                    print(e)
                lp_amount = None
            

            return int(amount0), int(amount0_half), int(amount1_received), lp_amount
    

    # This function gives the intermediate amounts at all interactions with burning lp tokens
    # This method will be used by the executors
    # Returns:
    # amount of token1 recevied from burn, amount of token0 recevied from burn, amount of token0 recevied from token-swap, total amount of token0 received
    def _lp_burn(
        self,
        token0_out: bool,
        lp_token_amount: int
    ):
        
        '''
            BURN
        '''

        reserve0 = int(self.states.Reserves.value['reserve0'])
        reserve1 = int(self.states.Reserves.value['reserve1'])
        
        # Get states need for LP_token_in swap
        feeTo: str = self.states.FeeTo.value
        _kLast: int = int(self.states.KLast.value)
        totalSupply: int = int(self.states.TotalSupply.value)
        liquidity: int = int(self.states.Liquidity.value) + lp_token_amount

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

            if reserve0 <=0 or reserve1 <= 0:
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

            if self.enableDebugLogs:
                print(e)

            return None, None, None, None