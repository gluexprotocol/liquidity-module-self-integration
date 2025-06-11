from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional
from decimal import Decimal

class ClipperLiquidityModule(LiquidityModule):
    def _get_lptoken_value(self, pool_state: Dict, amount: Decimal) -> Decimal:
        tvl = self.get_tvl(pool_state)
        totalSupply = Decimal(pool_state["allTokensBalance"]["totalSupply"])

        if totalSupply == 0:
            return Decimal(0)

        # Both has 18 decimals
        return tvl / totalSupply
    
    def _get_quote_for(self, output_asset: Dict, input_asset: Dict, input_token: Token, output_token: Token) -> Decimal:
        outPrice = Decimal(output_asset["price_in_usd"])
        inPrice = Decimal(input_asset["price_in_usd"])
        d1 = input_token.decimals
        d2 = output_token.decimals

        if inPrice == 0:
            return Decimal(0)
        
        priceRatio = inPrice / outPrice
        priceRatio *= Decimal(10) ** (d2 - d1)
        
        return priceRatio

    def _get_pair(self, pool: Dict, token0: Token, token1: Token) -> Optional[Dict]:
        pairs = pool["pairs"]
        for pair in pairs:
            if token0.symbol.upper() in pair["assets"] and token1.symbol.upper() in pair["assets"]:
                return pair
        
        return None
    
    def _get_amount_out(
        self,
        pair: Dict,
        input_amount: int,
        quote: Decimal
    ) -> tuple[Decimal | None, Decimal | None]:
        output_amount = Decimal(input_amount) * quote

        feePercentage = Decimal(pair["fee_in_basis_points"]) / Decimal(10000)
        fee = output_amount * feePercentage
        
        output_amount -= fee
        return fee, output_amount
    
    def _get_assets(self, pool: Dict, input_token: Token, output_token: Token) -> tuple[Optional[Dict], Optional[Dict]]:
        asset0 = None
        asset1 = None

        for asset in pool["assets"]:
            if not asset0:
                if asset["address"].lower() == input_token.address.lower():
                    asset0 = asset
            if not asset1:
                if asset["address"].lower() == output_token.address.lower():
                    asset1 = asset
            
            if asset0 and asset1:
                break
        
        if not asset0 or not asset1:
            return None, None
        return asset0, asset1

    def get_amount_out(
        self, 
        pool_states: Dict, 
        fixed_parameters: Dict,
        input_token: Token, 
        output_token: Token,
        input_amount: int, 
    ) -> tuple[int | None, int | None]:
        # https://docs.clipper.exchange/disclaimers-and-technical/integrating-with-clipper-rfq/api-reference/api-v2/pool-v2#examples
        pools = pool_states["pools"]

        for pool in pools:
            if not pool["pool"]["swaps_enabled"]:
                continue

            # asset_in = input_token, asset_out = output_token
            asset_in, asset_out = self._get_assets(pool, input_token, output_token)
            if asset_in is None or asset_out is None:
                continue

            pair = self._get_pair(pool, input_token, output_token)
            if pair is None:
                continue

            quote = self._get_quote_for(asset_out, asset_in, input_token, output_token)
            if quote == 0:
                return 0, 0

            fee, output_amount = self._get_amount_out(pair, input_amount, quote)
            return int(fee), int(output_amount)
        return None, None

    def get_amount_in(
        self, 
        pool_state: Dict, 
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        output_amount: int
    ) -> tuple[int | None, int | None]:
        # Implement logic to calculate required input amount given output amount
        pass

    def get_apy(self, pool_state: Dict) -> Decimal:
        lpTokenValue = self._get_lptoken_value(pool_state, 1)

        oldAll = pool_state["allTokensBalance"]
        pool_state["allTokensBalance"] = pool_state["previousAllTokensBalance"]
        pDLpTokenValue = self._get_lptoken_value(pool_state, 1)
        pool_state["allTokensBalance"] = oldAll

        days = pool_state["days"]
        if days == 0:
            return Decimal(0)
        
        apyDaily = (lpTokenValue - pDLpTokenValue) / days
        apyCompounded = (1 + apyDaily) ** 365 - 1

        if apyCompounded < 0:
            return Decimal(0)
        return apyCompounded * 100

    def get_tvl(self, pool_state: Dict, token: Optional[Token] = None) -> Decimal:
        # From Pool.allTokensBalance()
        # Structure:
        # {
        #     "balances": list[int],
        #     "tokens": list[Token],
        #     "totalSupply": int,
        # }
        allTokensBalance = pool_state["allTokensBalance"]

        tvl = 0

        for i, token_ in enumerate(allTokensBalance["tokens"]):
            balance = Decimal(allTokensBalance["balances"][i])
            balance *= token_.reference_price
            
            d2 = token_.decimals
            balance /= 10 ** d2

            tvl += balance

        return tvl