from modules.amm.utils import is_same_address
from modules.buffer.buffer_math import calculate_buffer_amounts
from modules.buffer.enums import WrappingDirection

_MINIMUM_WRAP_AMOUNT = 1000


def erc4626_buffer_wrap_or_unwrap(swap_input, pool_state):
    if swap_input["amount_raw"] < _MINIMUM_WRAP_AMOUNT:
        # If amount given is too small, rounding issues can be introduced that favors the user and can drain
        # the buffer. _MINIMUM_WRAP_AMOUNT prevents it. Most tokens have protections against it already, this
        # is just an extra layer of security.
        raise ValueError("wrapAmountTooSmall")

    wrapping_direction = (
        WrappingDirection.UNWRAP
        if is_same_address(swap_input["token_in"], pool_state["poolAddress"]) is True
        else WrappingDirection.WRAP
    )

    return calculate_buffer_amounts(
        wrapping_direction,
        swap_input["swap_kind"],
        swap_input["amount_raw"],
        pool_state["rate"],
    )