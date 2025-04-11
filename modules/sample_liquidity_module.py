from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional
from decimal import Decimal

from modules.amm.stable import Stable
from modules.hooks.default_hook import DefaultHook
from modules.buffer import erc4626_buffer_wrap_or_unwrap

class SampleLiquidityModule(LiquidityModule):
    def get_amount_out(
        self, 
        pool_states: Dict, 
        fixed_parameters: Dict,
        input_token: Token, 
        output_token: Token,
        input_amount: int, 
    ) -> tuple[int | None, int | None]:
        
        #Get All the pool states
        stablePoolDynamicData = pool_states["stablePoolDynamicData"]
        aggregateFeePercentages = pool_states["aggregateFeePercentages"]
        poolConfig = pool_states["poolConfig"]

        if poolConfig['isPoolRegistered'] == False or poolConfig['isPoolInitialized'] == False or poolConfig['isPoolPaused'] == True or poolConfig['isPoolInRecoveryMode'] == True:
            fee = None
            output_amount = None
            return fee, output_amount

        # Get all the fixed parameters
        pool_address = fixed_parameters["pool_address"]
        lp_token_address = fixed_parameters["lp_token_address"]
        tokens = fixed_parameters["tokens"]
        scalingFactors = fixed_parameters["decimal_scaling_factors"]
        max_invariant_ratio = fixed_parameters["max_invariant_ratio"]
        min_invariant_ratio = fixed_parameters["min_invariant_ratio"]

        # Required inputs for add_liquidity, remove_liquidity, swap
        poolType = "STABLE"
        chainId = 0
        blockNumber = 0
        poolAddress = pool_address
        tokens = tokens
        scalingFactors = [int(scalingFactor) for scalingFactor in scalingFactors]
        amp = stablePoolDynamicData['amplificationParameter']
        swapFee = stablePoolDynamicData['staticSwapFeePercentage']
        balancesLiveScaled18 = stablePoolDynamicData['balancesLiveScaled18']
        tokenRates = stablePoolDynamicData['tokenRates']
        totalSupply = stablePoolDynamicData['totalSupply']
        aggregateSwapFee = aggregateFeePercentages['aggregateSwapFeePercentage']

        pool = {
            "poolType": poolType,
            "chainId": chainId,
            "blockNumber": blockNumber,
            "poolAddress": poolAddress,
            "tokens": tokens,
            "scalingFactors": scalingFactors,
            "amp": amp,
            "swapFee": swapFee,
            "balancesLiveScaled18": balancesLiveScaled18,
            "tokenRates": tokenRates,
            "totalSupply": totalSupply,
            "aggregateSwapFee": aggregateSwapFee,
            "max_invariant_ratio": max_invariant_ratio,
            "min_invariant_ratio": min_invariant_ratio
        }

        if input_token.address == lp_token_address or output_token.address == lp_token_address:
            
            ## Some initial logic to confirm if AMM is in a valid state
            if poolConfig['disableUnbalancedLiquidity'] == True:
                fee = None
                output_amount = None
                return fee, output_amount
            # Add liquidity
            if output_token.address == lp_token_address:
                # Format required inputs
                max_amounts_in_raw = [0] * len(tokens)
                max_amounts_in_raw[tokens.index(input_token.address)] = input_amount
                add_liquidity_input = {
                    "pool": poolAddress,
                    "max_amounts_in_raw": max_amounts_in_raw,
                    "min_bpt_amount_out_raw": 0,
                    "kind": 0
                }
                output_amounts = self.add_liquidity_to_pool(add_liquidity_input, pool)
                output_amount = output_amounts["bpt_amount_out_raw"]
                fee_amount = 0
            
            # Remove liquidity
            elif input_token.address == lp_token_address:
                 # Format required inputs
                min_amounts_out_raw = [0] * len(tokens)
                min_amounts_out_raw[tokens.index(output_token.address)] = 1
                remove_liquidity_input = {
                    "pool": poolAddress,
                    "min_amounts_out_raw": min_amounts_out_raw,
                    "max_bpt_amount_in_raw": input_amount,
                    "kind": 1
                }
                # Balancer Hooks
                pool["hookType"] = None
                input_hook_state = {
                    "removeLiquidityHookFeePercentage": 0,
                    "tokens": tokens
                }
                output_amounts = self.remove_liquidity_from_pool(remove_liquidity_input, pool, input_hook_state)
                output_amount = output_amounts["amounts_out_raw"][tokens.index(output_token.address)]
                fee_amount = 0
                
        # Swap Tokens
        else:
            swap_input = {
                "amount_raw": input_amount,
                "swap_kind": 0,
                "token_in": input_token.address,
                "token_out": output_token.address
            }
            output_amount = self.swap_tokens(swap_input, pool)
            fee_amount = 0

        return fee_amount, output_amount

    def get_amount_in(
        self, 
        pool_states: Dict, 
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        output_amount: int
    ) -> tuple[int | None, int | None]:
        #Get All the pool states
        stablePoolDynamicData = pool_states["stablePoolDynamicData"]
        aggregateFeePercentages = pool_states["aggregateFeePercentages"]
        poolConfig = pool_states["poolConfig"]

        if poolConfig['isPoolRegistered'] == False or poolConfig['isPoolInitialized'] == False or poolConfig['isPoolPaused'] == True or poolConfig['isPoolInRecoveryMode'] == True:
            fee = None
            output_amount = None
            return fee, output_amount

        # Get all the fixed parameters
        pool_address = fixed_parameters["pool_address"]
        lp_token_address = fixed_parameters["lp_token_address"]
        tokens = fixed_parameters["tokens"]
        scalingFactors = fixed_parameters["decimal_scaling_factors"]
        max_invariant_ratio = fixed_parameters["max_invariant_ratio"]
        min_invariant_ratio = fixed_parameters["min_invariant_ratio"]

        # Required inputs for add_liquidity, remove_liquidity, swap
        poolType = "STABLE"
        chainId = 0
        blockNumber = 0
        poolAddress = pool_address
        tokens = tokens
        scalingFactors = [int(scalingFactor) for scalingFactor in scalingFactors]
        amp = stablePoolDynamicData['amplificationParameter']
        swapFee = stablePoolDynamicData['staticSwapFeePercentage']
        balancesLiveScaled18 = stablePoolDynamicData['balancesLiveScaled18']
        tokenRates = stablePoolDynamicData['tokenRates']
        totalSupply = stablePoolDynamicData['totalSupply']
        aggregateSwapFee = aggregateFeePercentages['aggregateSwapFeePercentage']

        pool = {
            "poolType": poolType,
            "chainId": chainId,
            "blockNumber": blockNumber,
            "poolAddress": poolAddress,
            "tokens": tokens,
            "scalingFactors": scalingFactors,
            "amp": amp,
            "swapFee": swapFee,
            "balancesLiveScaled18": balancesLiveScaled18,
            "tokenRates": tokenRates,
            "totalSupply": totalSupply,
            "aggregateSwapFee": aggregateSwapFee,
            "max_invariant_ratio": max_invariant_ratio,
            "min_invariant_ratio": min_invariant_ratio
        }

        if input_token.address == lp_token_address or output_token.address == lp_token_address:
            
            ## Some initial logic to confirm if AMM is in a valid state
            if poolConfig['disableUnbalancedLiquidity'] == True:
                fee = None
                input_amount = None
                return fee, input_amount
            # Add liquidity
            if output_token.address == lp_token_address:
                # Format required inputs
                max_amounts_in_raw = [0] * len(tokens)
                max_amounts_in_raw[tokens.index(input_token.address)] = 1
                min_bpt_amount_out_raw = output_amount
                add_liquidity_input = {
                    "pool": poolAddress,
                    "max_amounts_in_raw": max_amounts_in_raw,
                    "min_bpt_amount_out_raw": min_bpt_amount_out_raw,
                    "kind": 1
                }
                input_amounts = self.add_liquidity_to_pool(add_liquidity_input, pool)

                input_amount = input_amounts["amounts_in_raw"][tokens.index(input_token.address)]
                fee_amount = 0
            
            # Remove liquidity
            elif input_token.address == lp_token_address:
                
                # Format required inputs
                min_amounts_out_raw = [0] * len(tokens)
                min_amounts_out_raw[tokens.index(output_token.address)] = output_amount
                max_bpt_amount_in_raw = 1
                remove_liquidity_input = {
                    "pool": poolAddress,
                    "min_amounts_out_raw": min_amounts_out_raw,
                    "max_bpt_amount_in_raw": max_bpt_amount_in_raw,
                    "kind": 2
                }
                # Balancer Hooks
                pool["hookType"] = None
                input_hook_state = {
                    "removeLiquidityHookFeePercentage": 0,
                    "tokens": tokens
                }
                input_amounts = self.remove_liquidity_from_pool(remove_liquidity_input, pool, input_hook_state)

                input_amount = input_amounts["bpt_amount_in_raw"]
                fee_amount = 0
                
        # Swap Tokens
        else:
            swap_input = {
                "amount_raw": output_amount,
                "swap_kind": 1,
                "token_in": input_token.address,
                "token_out": output_token.address
            }
            input_amount = self.swap_tokens(swap_input, pool)
            fee_amount = 0

        return fee_amount, input_amount

    def get_apy(self, pool_state: Dict) -> Decimal:
        fees = pool_state.get('fees', 0)
        tvl = pool_state.get('tvl', 0)
        days_accumulated = pool_state.get('days_accumulated', 1) 

        daily_yield = (fees / days_accumulated) / tvl if tvl and days_accumulated else 0

        apy_simple = daily_yield * 365

        if daily_yield == 0:
            return Decimal(0)
        apy_compounded = (1 + daily_yield) ** 365 - 1

        return Decimal(apy_compounded)

    def get_tvl(self, pool_state: Dict, token: Optional[Token] = None) -> Decimal:
        return pool_state.get('tvl', 0)
    
    def add_liquidity_to_pool(self, add_liquidity_input: Dict, pool: Dict) -> Dict:

        pool_class = Stable(pool)
        hook_class = DefaultHook()
        return add_liquidity(
            add_liquidity_input, pool, pool_class, hook_class, None
        )
        
    def remove_liquidity_from_pool(self, remove_liquidity_input, pool: Dict) -> Dict:

        pool_class = Stable(pool)
        hook_class = DefaultHook()
        return remove_liquidity(
            remove_liquidity_input, pool, pool_class, hook_class, None
        )
        
    def swap_tokens(self, swap_input: Dict, pool: Dict)-> int:
        if swap_input["amount_raw"] == 0:
            return 0

        # buffer is handled separately than a "normal" pool
        if pool.get("totalSupply") is None:
            return erc4626_buffer_wrap_or_unwrap(swap_input, pool)
        pool_class = Stable(pool)
        hook_class = DefaultHook()
        return swap(swap_input, pool, pool_class, hook_class, None)
    