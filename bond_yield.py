import QuantLib as ql  # Correct package name is 'QuantLib', not 'quantlib'
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Set evaluation date
evaluation_date = ql.Date(16, 10, 2025)
ql.Settings.instance().evaluationDate = evaluation_date

# Use TARGET calendar if India is not available in QuantLib
try:
    calendar = ql.India()
except AttributeError:
    calendar = ql.TARGET()

# Sample bond data (replace with real data from RBI or Bloomberg)
bonds_data = [
    {"maturity": ql.Date(16, 10, 2026), "coupon": 0.06, "price": 99.5},
    {"maturity": ql.Date(16, 10, 2028), "coupon": 0.065, "price": 98.8},
    {"maturity": ql.Date(16, 10, 2030), "coupon": 0.07, "price": 97.2},
    {"maturity": ql.Date(16, 10, 2035), "coupon": 0.072, "price": 96.5}
]

# Day count and conventions
day_count = ql.Actual365Fixed()
settlement_days = 2
compounding = ql.Compounded
frequency = ql.Annual

# Build bond objects
bonds = []
helpers = []
for bond in bonds_data:
    schedule = ql.Schedule(
        evaluation_date,
        bond["maturity"],
        ql.Period(frequency),
        calendar,
        ql.Unadjusted,
        ql.Unadjusted,
        ql.DateGeneration.Backward,
        False
    )
    bond_obj = ql.FixedRateBond(
        settlement_days,
        100.0,  # face value
        schedule,
        [bond["coupon"]],
        day_count
    )
    helpers.append(
        ql.BondHelper(ql.QuoteHandle(ql.SimpleQuote(bond["price"])), bond_obj)
    )

# Construct yield curve
curve = ql.PiecewiseLogLinearDiscount(evaluation_date, helpers, day_count)
curve.enableExtrapolation()

# Extract zero rates
dates = [evaluation_date + ql.Period(i, ql.Months) for i in range(1, 121)]
zero_rates = [curve.zeroRate(date, day_count, compounding, frequency).rate() for date in dates]
maturities = [(date - evaluation_date) / 365.0 for date in dates]

# Price a sample bond
sample_bond_schedule = ql.Schedule(
    evaluation_date,
    ql.Date(16, 10, 2032),
    ql.Period(frequency),
    calendar,
    ql.Unadjusted,
    ql.Unadjusted,
    ql.DateGeneration.Backward,
    False
)
sample_bond = ql.FixedRateBond(
    settlement_days,
    100.0,
    sample_bond_schedule,
    [0.068],
    day_count
)
sample_bond.setPricingEngine(ql.DiscountingBondEngine(ql.YieldTermStructureHandle(curve)))
bond_price = sample_bond.cleanPrice()

# Sensitivity analysis (shift yield curve by +10bps)
shifted_curve = ql.ZeroSpreadedTermStructure(
    ql.YieldTermStructureHandle(curve),
    ql.QuoteHandle(ql.SimpleQuote(0.001))  # +10bps
)
sample_bond.setPricingEngine(ql.DiscountingBondEngine(ql.YieldTermStructureHandle(shifted_curve)))
shifted_price = sample_bond.cleanPrice()
price_change = bond_price - shifted_price

# Export to DataFrame
df = pd.DataFrame({
    "Maturity_Years": maturities,
    "Zero_Rate": zero_rates
})
df.to_csv("yield_curve.csv", index=False)

# Plot yield curve
plt.plot(maturities, zero_rates, label="Zero-Coupon Yield Curve")
plt.xlabel("Maturity (Years)")
plt.ylabel("Zero Rate")
plt.title("Indian Government Bond Yield Curve")
plt.legend()
plt.savefig("yield_curve.png")
plt.close()

# Summary report
summary = f"""
Bond Yield Curve Analysis
Evaluation Date: {evaluation_date}
Sample Bond (Maturity 2032, Coupon 6.8%):
  - Clean Price: {bond_price:.2f}
  - Price Change (+10bps shift): {price_change:.4f}
Insights:
  - Curve shape indicates market expectations for interest rates.
  - Price sensitivity shows impact of rate changes on bond valuation.
"""
with open("yield_summary.txt", "w") as f:
    f.write(summary)

print("Yield curve and summary generated successfully.")