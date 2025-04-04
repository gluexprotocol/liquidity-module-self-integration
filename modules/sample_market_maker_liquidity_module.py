from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional
from decimal import Decimal

class MarketMakerLiquidityModule(LiquidityModule):
    def get_amount_out(
        self, 
        pool_states: Dict, 
        fixed_parameters: Dict,
        input_token: Token, 
        output_token: Token,
        input_amount: int, 
    ) -> tuple[int | None, int | None]:
        # Implement logic to calculate output amount given input amount
        ## a list of token pairs supported by market maker
        token_pairs: list[str] = pool_states.get("token_pairs", [])
        
        desired_pair: str = input_token.address + "_" + output_token.address
        
        ## If the desired pair is not in the list of token pairs, return None
        if desired_pair not in token_pairs:
            return None, None
        
        ## Get the price levels for the desired pair made available by the market maker
        ## The price levels are a dictionary where the key is the token pair and the value is a list of tuples of amount and price
        pricelevels: dict[str, list[tuple[int, int]]] = pool_states.get("pricelevels", {})
        
        ## If the desired pair is not in the price levels, return None
        if desired_pair not in pricelevels:
            return None, None
        
        ## Get the price levels for the desired pair
        levels: list[tuple[int, int]] = pricelevels[desired_pair]
        ## If the levels are empty, return None
        if len(levels) == 0:
            return None, None

        if input_amount < levels[0][0]:
            return None, None
        
        ## Iterate through the levels and find the amount and price
        remaining_amount: int = input_amount
        output_amount: int = 0
        for l in levels:
            vol_in_level: int = l[0]
            price_in_level: int = l[1]
            if remaining_amount <= vol_in_level:
                output_amount += remaining_amount * price_in_level
                remaining_amount = 0
            else:
                output_amount += vol_in_level * price_in_level
                remaining_amount -= vol_in_level
                
            if remaining_amount == 0:
                break
            
        if remaining_amount > 0:
            return None, None
        
        return 0, int(output_amount)
            
        

    def get_amount_in(
        self, 
        pool_state: Dict, 
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        output_amount: int
    ) -> tuple[int | None, int | None]:

        pass

    def get_apy(self, pool_state: Dict) -> Decimal:

        pass

    def get_tvl(self, pool_state: Dict, token: Optional[Token] = None) -> Decimal:

        pass