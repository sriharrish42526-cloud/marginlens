import unittest
import pandas as pd
from engine import validate_and_process_data, compute_summary_kpis, generate_deterministic_insights

class TestMarginLensEngine(unittest.TestCase):

    def setUp(self):
        self.raw_data = pd.DataFrame({
            "Date": ["2025-05-01", "2025-05-02", "invalid_date", "2025-06-10"],
            "Item": ["Rice", "Oil", "Sugar", "Rice"],
            "Qty": [2, 5, 1, -3],
            "Revenue": ["₹1,000", "500", "200", "300"],
            "Cost": [700, 400, 150, 200],
            "Exp": [50, 20, 10, 10]
        })
        self.mapping = {
            "date": "Date",
            "product": "Item",
            "quantity": "Qty",
            "sales": "Revenue",
            "cost": "Cost",
            "expenses": "Exp"
        }

    def test_validation_and_cleaning(self):
        processed = validate_and_process_data(self.raw_data, self.mapping)
        self.assertEqual(len(processed), 2)
        self.assertEqual(processed.attrs['dropped_rows'], 2)

    def test_financial_calculations(self):
        processed = validate_and_process_data(self.raw_data, self.mapping)
        kpis = compute_summary_kpis(processed)
        self.assertEqual(kpis["total_revenue"], 1500.0)
        self.assertEqual(kpis["total_cost"], 1100.0)
        self.assertEqual(kpis["total_gross_profit"], 400.0)
        self.assertEqual(kpis["total_expenses"], 70.0)
        self.assertEqual(kpis["total_net_profit"], 330.0)

    def test_insights_generation(self):
        processed = validate_and_process_data(self.raw_data, self.mapping)
        kpis = compute_summary_kpis(processed)
        insights = generate_deterministic_insights(processed, kpis)
        self.assertTrue(len(insights) >= 2)

if __name__ == "__main__":
    unittest.main()
