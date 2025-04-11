import unittest
from unittest.mock import patch, AsyncMock
import sys
from os import listdir, path, walk

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
sys.path.append(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))
sys.path.append(path.dirname(path.dirname(path.dirname(path.dirname(path.abspath(__file__))))))
sys.path.append(path.dirname(path.dirname(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))))
sys.path.append(path.dirname(path.dirname(path.dirname(path.dirname(path.dirname(path.dirname(path.abspath(__file__))))))))
from decimal import Decimal
from templates.liquidity_module import Token
from modules.sample_market_maker_liquidity_module import MarketMakerLiquidityModule  # Replace with the actual module name

class TestMarketMakerLiquidityModule(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.fixed_parameters = {
            "market_maker_api": "https://mock.api",
            "api_key": "test-api-key",
            "chain": "ethereum",
            "user_address": "0xuser"
        }
        self.input_token = Token(address="0xinput", symbol="InputToken", decimals=18, reference_price=Decimal("0.0001"))
        self.output_token = Token(address="0xoutput", symbol="OutputToken", decimals=18, reference_price=Decimal("0.0002"))

    @patch("aiohttp.ClientSession.post")
    async def test_get_sell_quote_success(self, mock_post):
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={
            "status": "SUCCESS",
            "buy_amount": 1000
        })
        mock_post.return_value.__aenter__.return_value = mock_response

        fee, amount = await MarketMakerLiquidityModule.get_sell_quote(
            self.fixed_parameters, self.input_token, self.output_token, 500
        )

        self.assertEqual(fee, 0)
        self.assertEqual(amount, 1000)

    @patch("aiohttp.ClientSession.post")
    async def test_get_sell_quote_failure(self, mock_post):
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={"status": "FAILED"})
        mock_post.return_value.__aenter__.return_value = mock_response

        fee, amount = await MarketMakerLiquidityModule.get_sell_quote(
            self.fixed_parameters, self.input_token, self.output_token, 500
        )
        self.assertIsNone(fee)
        self.assertIsNone(amount)

    @patch("aiohttp.ClientSession.post")
    async def test_get_buy_quote_success(self, mock_post):
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={
            "status": "SUCCESS",
            "sell_amount": 800
        })
        mock_post.return_value.__aenter__.return_value = mock_response

        fee, amount = await MarketMakerLiquidityModule.get_buy_quote(
            self.fixed_parameters, self.input_token, self.output_token, 1000
        )
        self.assertEqual(fee, 0)
        self.assertEqual(amount, 800)

    @patch("aiohttp.ClientSession.post")
    async def test_get_buy_quote_failure(self, mock_post):
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={"status": "ERROR"})
        mock_post.return_value.__aenter__.return_value = mock_response

        fee, amount = await MarketMakerLiquidityModule.get_buy_quote(
            self.fixed_parameters, self.input_token, self.output_token, 1000
        )
        self.assertIsNone(fee)
        self.assertIsNone(amount)

unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(TestMarketMakerLiquidityModule))
