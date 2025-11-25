# tests/test_analysis_small_unit.py
import unittest
from datetime import datetime

from src import (
    Transaction,
    avg_order_value,
    cancellation_rate,
    cancellation_summary,
    monthly_revenue,
    revenue_by_country,
    returns_view,
    sales_by_weekday,
    top_n_customers_by_revenue,
    top_n_products_by_revenue,
    total_revenue,
    units_sold_per_product,
    valid_transactions,
)


class AnalysisSmallUnitTests(unittest.TestCase):
    """
    Unit tests validating core analytical functions using a small, handcrafted dataset.

    Covers:
        - Filtering views (valid_transactions, returns_view)
        - Revenue aggregations
        - Ranking (top N products/customers)
        - AOV, weekday sales, cancellation metrics
        - Product and customer grouping rules
    """

    def setUp(self) -> None:
        """
        Prepare a representative in-memory dataset for repeated use.

        Dataset consists of:
            - Two valid sale rows for invoice 540001
            - One cancellation row (C540050)
            - One valid sale for invoice 540010
        """
        self.raw = [
            Transaction(
                invoice_no="540001",
                stock_code="A111",
                description="VINTAGE MUG",
                quantity=10,
                invoice_date=datetime(2011, 3, 5, 10, 15),
                unit_price=1.99,
                customer_id="10001",
                country="United Kingdom",
            ),
            Transaction(
                invoice_no="540001",
                stock_code="B222",
                description="RETRO CLOCK",
                quantity=3,
                invoice_date=datetime(2011, 3, 5, 10, 15),
                unit_price=9.50,
                customer_id="10001",
                country="United Kingdom",
            ),
            # Cancellation row
            Transaction(
                invoice_no="C540050",
                stock_code="A111",
                description="VINTAGE MUG",
                quantity=-10,
                invoice_date=datetime(2011, 3, 5, 10, 45),
                unit_price=1.99,
                customer_id="10001",
                country="United Kingdom",
            ),
            Transaction(
                invoice_no="540010",
                stock_code="C333",
                description="GLASS VASE",
                quantity=2,
                invoice_date=datetime(2011, 3, 5, 11, 0),
                unit_price=15.00,
                customer_id="20002",
                country="Germany",
            ),
        ]

        # Pre-filter valid transactions.
        self.records = list(valid_transactions(self.raw))

        # Ensure test assumptions hold.
        self.assertEqual(len(self.records), 3)

    # ------------------------------------------------------------------
    # valid_transactions
    # ------------------------------------------------------------------
    def test_valid_transactions_filters_cancellations(self) -> None:
        """Ensure cancellation invoices and invalid quantities/prices are removed."""
        self.assertTrue(all(not t.is_cancellation for t in self.records))
        self.assertTrue(all(t.quantity > 0 and t.unit_price > 0 for t in self.records))

    def test_valid_transactions_filters_zero_quantity_and_price(self) -> None:
        """Rows with zero quantity or zero price should be excluded."""
        zero_cases = [
            Transaction(
                invoice_no="540020",
                stock_code="ZQ0",
                description="Zero qty",
                quantity=0,
                invoice_date=datetime(2011, 3, 5, 12, 0),
                unit_price=7.5,
                customer_id="99990",
                country="United Kingdom",
            ),
            Transaction(
                invoice_no="540021",
                stock_code="ZP0",
                description="Zero price",
                quantity=4,
                invoice_date=datetime(2011, 3, 5, 12, 5),
                unit_price=0.0,
                customer_id="99991",
                country="United Kingdom",
            ),
        ]
        filtered = list(valid_transactions(zero_cases))
        self.assertEqual(filtered, [])

    def test_valid_transactions_all_cancellations(self) -> None:
        """If every row is a cancellation, valid view should be empty."""
        cancelled_only = [
            Transaction(
                invoice_no="C90001",
                stock_code="X1",
                description="Cancelled A",
                quantity=-1,
                invoice_date=datetime(2011, 3, 6, 9, 0),
                unit_price=12.0,
                customer_id="11111",
                country="United Kingdom",
            ),
            Transaction(
                invoice_no="C90002",
                stock_code="X2",
                description="Cancelled B",
                quantity=-5,
                invoice_date=datetime(2011, 3, 6, 9, 5),
                unit_price=3.5,
                customer_id="22222",
                country="Germany",
            ),
        ]
        filtered = list(valid_transactions(cancelled_only))
        self.assertEqual(filtered, [])

    # ------------------------------------------------------------------
    # returns_view
    # ------------------------------------------------------------------
    def test_returns_view_only_cancellations_and_non_positive(self) -> None:
        """returns_view must yield only cancellation or nonpositive-quantity rows."""
        returns = list(returns_view(self.raw))
        self.assertEqual(len(returns), 1)
        self.assertTrue(all(t.is_cancellation or t.quantity <= 0 for t in returns))
        self.assertEqual(returns[0].invoice_no, "C540050")

    def test_returns_view_no_cancellations(self) -> None:
        """If all records are valid, returns view is empty."""
        returns = list(returns_view(self.records))
        self.assertEqual(returns, [])

    # ------------------------------------------------------------------
    # total_revenue
    # ------------------------------------------------------------------
    def test_total_revenue(self) -> None:
        """Total revenue should equal the sum of all valid line totals."""
        self.assertAlmostEqual(total_revenue(self.records), 78.40, places=2)

    def test_total_revenue_empty(self) -> None:
        """Empty input should return zero revenue."""
        self.assertEqual(total_revenue([]), 0.0)

    # ------------------------------------------------------------------
    # revenue_by_country
    # ------------------------------------------------------------------
    def test_revenue_by_country(self) -> None:
        """Revenue should accumulate per country and sum to total revenue."""
        result = revenue_by_country(self.records)
        self.assertAlmostEqual(result["United Kingdom"], 48.40, places=2)
        self.assertAlmostEqual(result["Germany"], 30.00, places=2)
        self.assertAlmostEqual(sum(result.values()), 78.40, places=2)

    def test_revenue_by_country_empty(self) -> None:
        """Empty input should return an empty mapping."""
        self.assertEqual(revenue_by_country([]), {})

    # ------------------------------------------------------------------
    # monthly_revenue
    # ------------------------------------------------------------------
    def test_monthly_revenue(self) -> None:
        """Monthly revenue should group using YYYY-MM keys."""
        result = monthly_revenue(self.records)
        self.assertIn("2011-03", result)
        self.assertAlmostEqual(result["2011-03"], 78.40, places=2)

    def test_monthly_revenue_empty(self) -> None:
        """Empty input should produce an empty dictionary."""
        self.assertEqual(monthly_revenue([]), {})

    # ------------------------------------------------------------------
    # top_n_products_by_revenue
    # ------------------------------------------------------------------
    def test_top_n_products_by_revenue(self) -> None:
        """Products should be ranked by revenue descending."""
        result = top_n_products_by_revenue(self.records, n=3)
        names = [name for name, _ in result]
        self.assertEqual(names, ["GLASS VASE", "RETRO CLOCK", "VINTAGE MUG"])

    def test_top_n_products_with_less_than_n_items(self) -> None:
        """If fewer than n items exist, all products should be returned."""
        result = top_n_products_by_revenue(self.records, n=10)
        self.assertEqual(len(result), 3)

    def test_top_n_products_with_zero_n(self) -> None:
        """n = 0 should always return an empty list."""
        result = top_n_products_by_revenue(self.records, n=0)
        self.assertEqual(result, [])

    # ------------------------------------------------------------------
    # top_n_customers_by_revenue
    # ------------------------------------------------------------------
    def test_top_n_customers_by_revenue(self) -> None:
        """Top customers must be ranked by total revenue."""
        result = top_n_customers_by_revenue(self.records, n=2)
        self.assertEqual(result[0][0], "10001")  # highest spender
        self.assertEqual(len(result), 2)

    def test_top_n_customers_with_less_than_n_customers(self) -> None:
        """If fewer customers exist, return the available ones."""
        result = top_n_customers_by_revenue(self.records, n=10)
        self.assertEqual(len(result), 2)

    def test_top_n_customers_with_zero_n(self) -> None:
        """n = 0 yields empty list."""
        result = top_n_customers_by_revenue(self.records, n=0)
        self.assertEqual(result, [])

    # ------------------------------------------------------------------
    # avg_order_value
    # ------------------------------------------------------------------
    def test_avg_order_value(self) -> None:
        """AOV should average invoice-level totals."""
        self.assertAlmostEqual(avg_order_value(self.records), 39.20, places=2)

    def test_avg_order_value_empty(self) -> None:
        """Empty input yields zero."""
        self.assertEqual(avg_order_value([]), 0.0)

    # ------------------------------------------------------------------
    # units_sold_per_product
    # ------------------------------------------------------------------
    def test_units_sold_per_product(self) -> None:
        """Units should aggregate per product description (fallback to stock code)."""
        result = units_sold_per_product(self.records)
        self.assertEqual(result["VINTAGE MUG"], 10)
        self.assertEqual(result["RETRO CLOCK"], 3)
        self.assertEqual(result["GLASS VASE"], 2)

    def test_units_sold_per_product_no_description_still_counts(self) -> None:
        """If description is missing, product should be grouped by stock code."""
        anon = Transaction(
            invoice_no="540100",
            stock_code="NCODE",
            description=None,
            quantity=7,
            invoice_date=datetime(2011, 3, 7, 10, 0),
            unit_price=2.0,
            customer_id="99999",
            country="Testland",
        )
        result = units_sold_per_product([anon])
        self.assertIn("NCODE", result)
        self.assertEqual(result["NCODE"], 7)

    # ------------------------------------------------------------------
    # sales_by_weekday
    # ------------------------------------------------------------------
    def test_sales_by_weekday_single_day_totals(self) -> None:
        """Weekday aggregation should place all revenue into correct day bucket."""
        result = sales_by_weekday(self.raw)
        self.assertAlmostEqual(result["Saturday"], 78.40, places=2)

        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Sunday"]:
            self.assertEqual(result[day], 0.0)

    def test_sales_by_weekday_empty(self) -> None:
        """Empty input should include all days with zero revenue."""
        result = sales_by_weekday([])
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            self.assertEqual(result[day], 0.0)

    # ------------------------------------------------------------------
    # cancellation_rate
    # ------------------------------------------------------------------
    def test_cancellation_rate(self) -> None:
        """Cancellation rate should be based on absolute values of cancelled vs gross."""
        self.assertAlmostEqual(cancellation_rate(self.raw), 20.2, places=1)

    def test_cancellation_rate_no_data(self) -> None:
        """Empty dataset yields cancellation rate of 0."""
        self.assertEqual(cancellation_rate([]), 0.0)

    def test_cancellation_rate_all_cancellations(self) -> None:
        """If everything is cancelled, rate must be 100 percent."""
        cancelled_only = [
            Transaction(
                invoice_no="C30001",
                stock_code="Y1",
                description="Cancelled A",
                quantity=-3,
                invoice_date=datetime(2011, 3, 8, 9, 0),
                unit_price=4.0,
                customer_id="11111",
                country="United Kingdom",
            ),
            Transaction(
                invoice_no="C30002",
                stock_code="Y2",
                description="Cancelled B",
                quantity=-2,
                invoice_date=datetime(2011, 3, 8, 9, 5),
                unit_price=6.0,
                customer_id="22222",
                country="Germany",
            ),
        ]
        self.assertEqual(cancellation_rate(cancelled_only), 100.0)

    # ------------------------------------------------------------------
    # cancellation_summary
    # ------------------------------------------------------------------
    def test_cancellation_summary_basic(self) -> None:
        """Verify summary counts, cancellation rate, and amounts."""
        summary = cancellation_summary(self.raw)
        self.assertEqual(summary["TotalCancellations"], 1)
        self.assertAlmostEqual(summary["CancellationRate"], 33.33, places=2)
        self.assertAlmostEqual(summary["CancelledNetAmount"], -19.90, places=2)
        self.assertAlmostEqual(summary["CancelledAbsAmount"], 19.90, places=2)

    def test_cancellation_summary_empty(self) -> None:
        """Empty dataset should yield zeros in all summary fields."""
        summary = cancellation_summary([])
        self.assertEqual(summary["TotalCancellations"], 0)
        self.assertEqual(summary["CancellationRate"], 0.0)
        self.assertEqual(summary["CancelledNetAmount"], 0.0)
        self.assertEqual(summary["CancelledAbsAmount"], 0.0)


if __name__ == "__main__":
    unittest.main()
