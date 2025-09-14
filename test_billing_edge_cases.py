#!/usr/bin/env python3
"""
Custom script to test edge cases in billing calculations.
"""


def recalc(total_items, payment_made, discount_amount):
    """Recalculate net amount and status after discount and payment."""
    net_amount = max(total_items - discount_amount, 0)
    if 0 < net_amount <= payment_made:
        bill_status = "PAID"
    elif payment_made > 0:
        bill_status = "PARTIAL"
    else:
        bill_status = "DUE"
    return net_amount, bill_status


# Edge cases
test_cases = [
    (0, 0, 0),  # All zero
    (100, 50, 20),  # Partial payment
    (100, 100, 0),  # Exact payment
    (100, 150, 0),  # Over payment
    (100, 0, 150),  # Discount more than total
    (100, 50, 100),  # Discount equals total
]

for total, payment, discount in test_cases:
    calc_net, calc_status = recalc(total, payment, discount)
    print(
        f"Total: {total}, Paid: {payment}, Discount: {discount} -> Net: {calc_net}, Status: {calc_status}"
    )  # noqa: E501
