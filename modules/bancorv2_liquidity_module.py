from templates.liquidity_module import LiquidityModule, Token
from typing import Dict, Optional
from decimal import Decimal

class BancorV2LiquidityModule(LiquidityModule):
    NATIVE_ASSET = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE".lower()
    
    def get_amount_out(
        self, 
        pool_state: Dict, 
        fixed_parameters: Dict,
        input_token: Token, 
        output_token: Token,
        input_amount: int, 
    ) -> tuple[int | None, int | None]:
        # Implement logic to calculate output amount given input amount
        pass

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

    def get_apy(
		self, 
		pool_state: Dict, 
		underlying_amount:int,
		underlying_token:Token, 
		pool_tokens: Dict[Token.address, Token]
    ) -> int:
        token1_address = pool_state.get('token1').lower()
        token2_address = pool_state.get('token2').lower()

        rprice1 = pool_tokens[token1_address].reference_price
        rprice2 = pool_tokens[token2_address].reference_price

        token1_decimals = pool_tokens[token1_address].decimals
        token2_decimals = pool_tokens[token2_address].decimals

        if rprice1 == 0 or rprice2 == 0:
            return 0


        reserve1 = pool_state.get('reserve1', 0)
        reserve2 = pool_state.get('reserve2', 0)

        if underlying_token.address == token1_address:
            reserve1 += underlying_amount
        elif underlying_token.address == token2_address:
            reserve2 += underlying_amount

        aux_pool_state = {
            'reserve1': reserve1,
            'reserve2': reserve2,
            'token1': token1_address,
            'token2': token2_address,
        }
        tvl = self.get_tvl(aux_pool_state, pool_tokens)
        if tvl == 0:
            return 0
        

        # Fees in a pool can be obtained from `conversionFee` in this event in StandardPoolConverter contract:
        # event Conversion(
        #     IReserveToken indexed sourceToken,
        #     IReserveToken indexed targetToken,
        #     address indexed trader,
        #     uint256 sourceAmount,
        #     uint256 targetAmount,
        #     int256 conversionFee
        # );
        fee_data = pool_state.get("fees_over_period", {})
        fee_amount1 = fee_data.get("amount1", 0)
        fee_amount2 = fee_data.get("amount2", 0)
        days = fee_data.get("days", 0)

        if days == 0:
            return 0
        
        # Normalize fee to native currency
        fee_normalized1 = fee_amount1 * rprice1 / (10 ** token1_decimals)
        fee_normalized2 = fee_amount2 * rprice2 / (10 ** token2_decimals)
        total_fees = fee_normalized1 + fee_normalized2

        daily_fees = total_fees / days
        daily_rate = daily_fees / tvl

        apy = daily_rate * 365 * 100
        apy_bps = int(apy * 10_000)

        return apy_bps

    def get_tvl(
        self, 
        pool_state: Dict, 
        pool_tokens: Dict[Token.address, Token]
    ) -> int:
        # LP Tokens are not included in the TVL calculation. Because they don't hold value.

        # Obtainable from StandardPoolConverter.reserveBalances:
        # function reserveBalances() public view returns (uint256, uint256) {
        #     return _loadReserveBalances(1, 2);
        # }
        reserve1 = pool_state.get('reserve1', 0)
        reserve2 = pool_state.get('reserve2', 0)

        # Reserve tokens 1 and 2 are btainable from StandardPoolConverter.reserveTokens()
        token1_address = pool_state.get('token1').lower()
        token2_address = pool_state.get('token2').lower()
        
        token1_decimals = pool_tokens[token1_address].decimals
        token2_decimals = pool_tokens[token2_address].decimals

        rprice1 = pool_tokens[token1_address].reference_price
        rprice2 = pool_tokens[token2_address].reference_price
        
        tvl = 0

        if token1_address == self.NATIVE_ASSET:
            tvl += reserve1
        else:
            tvl += reserve1 * rprice1 / (10 ** token1_decimals)
        if token2_address == self.NATIVE_ASSET:
            tvl += reserve2
        else:
            tvl += reserve2 * rprice2 / (10 ** token2_decimals)
        
        return tvl