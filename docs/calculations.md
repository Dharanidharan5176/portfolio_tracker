# Local Portfolio Tracker — Calculations & Methodologies

## 1. Monetary and Numeric Precision
All monetary calculations are performed using Python's `Decimal` module:
- Currency amounts: rounded to 2 decimal places using `ROUND_HALF_UP` (or standard fiat precision).
- Quantities: stored with up to 6 decimal places (supports fractional shares/crypto).
- Unit prices and FX rates: stored with up to 6 decimal places.
No IEEE 754 binary floating-point representation (`float`) is used for persistent ledger balances or accounting calculations.

## 2. Cash and Ledger Calculations

### 2.1 BUY Transaction
- Quantity increases: `Holding.quantity += txn.quantity`
- Cash decreases by total cost:
  `Total Cost = (txn.quantity * txn.unit_price) + txn.fee + txn.tax`
  `Account.cash -= Total Cost`
- Cost Basis increases:
  `Cost Basis += Total Cost`
- Average Cost per unit is updated:
  `Average Cost = Current Total Cost / Current Total Quantity`

### 2.2 SELL Transaction
- Quantity decreases: `Holding.quantity -= txn.quantity`
- Net proceeds increase cash:
  `Net Proceeds = (txn.quantity * txn.unit_price) - txn.fee - txn.tax`
  `Account.cash += Net Proceeds`
- Cost of shares sold (Average Cost Method):
  `Sold Cost Basis = txn.quantity * Average Cost`
  `Remaining Cost Basis -= Sold Cost Basis`
- Realized Gain/Loss:
  `Realized P&L = Net Proceeds - Sold Cost Basis`

### 2.3 CASH DEPOSIT & WITHDRAWAL
- `CASH_DEPOSIT`: `Account.cash += amount` (External cash inflow)
- `CASH_WITHDRAWAL`: `Account.cash -= amount` (External cash outflow)
- These affect cash balance, but are treated as external capital movements and never as investment return or portfolio profit.

### 2.4 DIVIDEND & INTEREST
- Income received:
  `Net Income = gross_amount - fee - tax`
  `Account.cash += Net Income`
- Does not change share quantity or cost basis. Tracked under portfolio income.

### 2.5 STOCK SPLITS
- Example 2-for-1 Split (split ratio = 2.0):
  `New Quantity = Old Quantity * split_ratio`
  `Total Cost Basis remains unchanged`
  `New Average Cost per Unit = Old Cost Basis / New Quantity`

## 3. Valuation Engine

### 3.1 Market Value
For each held instrument at valuation date $T$:
$$\text{Market Value} = \text{Quantity} \times \text{Latest Price}_T \times \text{FX Rate}_T$$
If instrument currency equals portfolio base currency, $\text{FX Rate} = 1.0$.
If no price observation exists for the instrument, valuation is flagged as **INCOMPLETE / MISSING PRICE**, never silently defaulting to zero or cost.

### 3.2 Unrealized Gain/Loss
$$\text{Unrealized P\&L} = \text{Market Value} - \text{Remaining Cost Basis}$$
$$\text{Unrealized P\&L \%} = \frac{\text{Unrealized P\&L}}{\text{Remaining Cost Basis}} \times 100$$ (if Cost Basis > 0)

### 3.3 Total Portfolio Value
$$\text{Total Portfolio Value} = \sum \text{Holding Market Values} + \sum \text{Account Cash Balances}$$

## 4. Performance Metrics

### 4.1 Time-Weighted Return (TWR)
To isolate manager/investment performance from timing of deposits and withdrawals, the timeline is partitioned into sub-periods $i=1 \dots n$ bounded by external cash flows:
$$R_i = \frac{V_{end, i} - \text{Net Cash Flow}_i}{V_{start, i}} - 1$$
Compound TWR across all sub-periods:
$$\text{TWR} = \left(\prod_{i=1}^n (1 + R_i)\right) - 1$$
If valuations at cash flow events are unavailable, the system explicitly returns `insufficient_data` with an explanatory notice rather than an erroneous simple percentage change.

### 4.2 Drawdown
At any point $t$ with portfolio value $V_t$ and historical peak $M_t = \max_{s \le t} V_s$:
$$\text{Drawdown}_t = \frac{V_t - M_t}{M_t}$$
Max drawdown is the minimum value of $\text{Drawdown}_t$ across the period.

