from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional
from decimal import Decimal

class ClipperLiquidityModule(LiquidityModule):
    def _get_lptoken_value(self, pool_state: Dict, amount: Decimal) -> Decimal:
        tvl = self.get_tvl(pool_state)
        total_supply = Decimal(pool_state["allTokensBalance"]["totalSupply"])

        if total_supply == 0:
            return Decimal("0")

        # Both have 18 decimals
        return tvl / total_supply

    def _get_quote_for(self, output_asset: Dict, input_asset: Dict, input_token: Token, output_token: Token) -> Decimal:
        out_price = Decimal(output_asset["price_in_usd"])
        in_price = Decimal(input_asset["price_in_usd"])
        d1 = input_token.decimals
        d2 = output_token.decimals

        if in_price == 0:
            return Decimal("0")
        
        price_ratio = in_price / out_price
        price_ratio *= Decimal(10) ** (d2 - d1)
        
        return price_ratio

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

        fee_percentage = Decimal(pair["fee_in_basis_points"]) / Decimal(10000)
        fee = output_amount * fee_percentage
        
        output_amount -= fee
        return fee, output_amount
    
    def _get_amount_in(
        self,
        pair: Dict,
        output_amount: int,
        quote: Decimal
    ) -> tuple[Decimal | None, Decimal | None]:
        fee_percentage = Decimal(pair["fee_in_basis_points"]) / Decimal(10000)
        
        pre_fee_output = Decimal(output_amount) / (Decimal(1) - fee_percentage)
        
        total_input_amount = pre_fee_output / quote
        
        input_for_net_output = Decimal(output_amount) / quote
        fee = total_input_amount - input_for_net_output
        
        return fee, total_input_amount

    def _get_assets(self, pool: Dict, input_token: Token, output_token: Token) -> tuple[Optional[Dict], Optional[Dict]]:
        asset0 = None
        asset1 = None

        for asset in pool["assets"]:
            if not asset0 and asset["address"].lower() == input_token.address.lower():
                asset0 = asset
            if not asset1 and asset["address"].lower() == output_token.address.lower():
                asset1 = asset
            
            if asset0 and asset1:
                break
        
        if not asset0 or not asset1:
            return None, None
        return asset0, asset1
    
    # Unused
    def _get_lp_token_amount_minted(
        self,
        pool_state: Dict,
        fixed_parameters: Dict,
        input_token: Token,
        input_amount: int
    ) -> Decimal:
        pass

    # Unused
    def _get_single_underlying_by_lp_burn(
        self,
        pool_state: Dict,
        fixed_parameters: Dict,
        output_token: Token,
        input_amount: int
    ) -> Decimal:
        pass

    # Unused
    def _process_liquidity_provisioning(
        self,
        pool_state: Dict,
        fixed_parameters: Dict,

        input_token: Token,
        output_token: Token,
        amount: int,
        is_add: bool
    ) -> tuple[int | None, int | None]:
        fee = None
        result_amount = None

        if is_add:
            pass
        else:
            pass
            
        return fee, result_amount

    def get_amount_out(
        self,
        pool_states: Dict,
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        input_amount: int,
    ) -> tuple[int | None, int | None]:
        # https://docs.clipper.exchange/disclaimers-and-technical/integrating-with-clipper-rfq/api-reference/api-v2/pool-v2#examples
        is_input_lp = input_token.address.lower() == fixed_parameters["lpTokenAddress"]
        is_output_lp = output_token.address.lower() == fixed_parameters["lpTokenAddress"]
        
        if is_input_lp or is_output_lp:
            fee, output_amount = self._process_liquidity_provisioning(
                pool_states, fixed_parameters,
                input_token, output_token, input_amount, is_add=is_input_lp
            )
            return fee, output_amount
        else:
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
        pool_states: Dict, # Renamed from pool_state to match usage
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        output_amount: int
    ) -> tuple[int | None, int | None]:
        # https://docs.clipper.exchange/disclaimers-and-technical/integrating-with-clipper-rfq/api-reference/api-v2/pool-v2#examples
        is_input_lp = input_token.address.lower() == fixed_parameters["lpTokenAddress"]
        is_output_lp = output_token.address.lower() == fixed_parameters["lpTokenAddress"]
        
        if is_input_lp or is_output_lp:
            fee, output_amount = self._process_liquidity_provisioning(
                pool_states, fixed_parameters,
                input_token, output_token, output_amount, is_add=is_input_lp
            )
            return fee, output_amount
        else:
            pools = pool_states["pools"]
            for pool in pools:
                if not pool["pool"]["swaps_enabled"]:
                    continue
                
                asset_in, asset_out = self._get_assets(pool, input_token, output_token)
                if asset_in is None or asset_out is None:
                    continue
                    
                pair = self._get_pair(pool, input_token, output_token)
                if pair is None:
                    continue
                
                quote = self._get_quote_for(asset_out, asset_in, input_token, output_token)
                if quote == 0:
                    return None, None
                
                fee, output_amount = self._get_amount_in(pair, output_amount, quote)
                return int(fee), int(output_amount)
            
        return None, None

    def get_apy(self, pool_state: Dict) -> Decimal:
        lp_token_value = self._get_lptoken_value(pool_state, 1)

        old_all = pool_state["allTokensBalance"]
        pool_state["allTokensBalance"] = pool_state["previousAllTokensBalance"]
        pd_lp_token_value = self._get_lptoken_value(pool_state, 1)
        pool_state["allTokensBalance"] = old_all

        days = pool_state["days"]
        if days == 0:
            return Decimal("0")
        
        apy_daily = (lp_token_value - pd_lp_token_value) / days
        apy_compounded = (1 + apy_daily) ** 365 - 1

        if apy_compounded < 0:
            return Decimal("0")
        return apy_compounded * 100

    def get_tvl(self, pool_state: Dict, token: Optional[Token] = None) -> Decimal:
        # From Pool.allTokensBalance()
        # Structure:
        # {
        #     "balances": list[int],
        #     "tokens": list[Token],
        #     "totalSupply": int,
        # }
        all_tokens_balance = pool_state["allTokensBalance"]

        tvl = Decimal(0)

        for i, token_ in enumerate(all_tokens_balance["tokens"]):
            balance = Decimal(all_tokens_balance["balances"][i])
            balance *= token_.reference_price
            
            d2 = token_.decimals
            balance /= 10 ** d2

            tvl += balance

        return tvl