def recalc(total_items, payment_made, discount_amount):
    net_amount = max(total_items - discount_amount, 0)
    if 0 < net_amount <= payment_made:
        bill_status = "PAID"
    elif payment_made > 0:
        bill_status = "PARTIAL"
    else:
        bill_status = "DUE"
    return net_amount, bill_status
test_cases = [
    (0, 0, 0),  
    (100, 50, 20),  
    (100, 100, 0),  
    (100, 150, 0),  
    (100, 0, 150),  
    (100, 50, 100),  
]
for total, payment, discount in test_cases:
    calc_net, calc_status = recalc(total, payment, discount)
    print(
        f"Total: {total}, Paid: {payment}, Discount: {discount} -> Net: {calc_net}, Status: {calc_status}"
    )  