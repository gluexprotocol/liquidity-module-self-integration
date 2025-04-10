import aiohttp
import asyncio
from templates.liquidity_module import Token
from typing import Dict, Tuple, Literal
from decimal import Decimal

class MarketMakerLiquidityModule:

    async def get_sell_quote(
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        input_amount: int,
        block: Literal['latest', int] = 'latest'
    ) -> Tuple[int | None, int | None]:

        market_maker_api = fixed_parameters.get("market_maker_api")
        api_key = fixed_parameters.get("api_key", None)
        chain = fixed_parameters.get("chain", "ethereum")
        user_address = fixed_parameters.get("user_address")

        # Construct the URL for the API call
        url = f"{market_maker_api}/sellQuote"
        
        body = {
            "chain": chain,
            "sell_token": input_token.address,
            "buy_token": output_token.address,
            "sell_amounts": input_amount,
            "user_address": user_address
        }


        headers = {
            "api-key": api_key,
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, json=body) as resp:
                    data = await resp.json()
                    
                    if "SUCCESS" not in data.get("status", ""):
                        return None, None
                    
                    output_amount = data.get("buy_amount")

                    return 0, amount_out

            except Exception as e:
                print(f"Error fetching sell quote: {e}")
                return None, None

    async def get_buy_quote(
        fixed_parameters: Dict,
        input_token: Token,
        output_token: Token,
        output_amount: int,
        block: Literal['latest', int] = 'latest'
    ) -> Tuple[int | None, int | None]:

        market_maker_api = fixed_parameters.get("market_maker_api")
        api_key = fixed_parameters.get("api_key", None)
        chain = fixed_parameters.get("chain", "ethereum")
        user_address = fixed_parameters.get("user_address")

        # Construct the URL for the API call
        url = f"{market_maker_api}/buyQuote"
        
        body = {
            "chain": chain,
            "buy_token": output_token.address,
            "sell_token": input_token.address,
            "buy_amount": output_amount,
            "user_address": user_address
        }

        headers = {
            "api-key": api_key,
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, json=body) as resp:
                    data = await resp.json()
                    
                    if "SUCCESS" not in data.get("status", ""):
                        return None, None
                    
                    input_amount = data.get("sell_amount")

                    return 0, input_amount

            except Exception as e:
                print(f"Error fetching buy quote: {e}")
                return None, None