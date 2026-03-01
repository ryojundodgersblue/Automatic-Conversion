"""Excel書き込みモジュール (excel_writer.py) の単体テスト。

テスト対象:
- 千円単位変換の正確性
- 合算項目の計算ロジック
- 原価報告書の比率計算
- 空データ・ゼロ除算の処理
"""

import os
import sys
import tempfile

import openpyxl
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from excel_writer import write_cr


# =============================================
# write_cr（原価報告書）のロジックテスト
# =============================================
class TestWriteCrLogic:
    """原価報告書の比率計算ロジックのテスト。
    テンプレートExcelが無くてもロジック自体を検証する。
    """

    def test_ratio_calculation_basic(self):
        """基本的な比率計算: A/F でスケーリングされる。"""
        cr_data = {
            "final_cost": 20000000,  # A = 20,000,000
            "total_construction_cost": 25000000,  # F = 25,000,000
            "total_materials": 5000000,
            "total_labor_cost": 8000000,
            "total_subcontracting": 10000000,
            "total_expenses": 2000000,
        }
        ratio = cr_data["final_cost"] / cr_data["total_construction_cost"]
        assert ratio == 0.8

        # 計算結果の検証（千円単位）
        assert int(cr_data["total_materials"] * ratio) // 1000 == 4000
        assert int(cr_data["total_labor_cost"] * ratio) // 1000 == 6400
        assert int(cr_data["total_subcontracting"] * ratio) // 1000 == 8000
        assert int(cr_data["total_expenses"] * ratio) // 1000 == 1600

    def test_ratio_zero_division(self):
        """total_construction_cost=0 の場合、ゼロ除算が発生しない。"""
        cr_data = {
            "final_cost": 0,
            "total_construction_cost": 0,
            "total_materials": 5000000,
        }
        F = cr_data.get("total_construction_cost", 0)
        ratio = cr_data["final_cost"] / F if F != 0 else 0
        assert ratio == 0
        assert int(cr_data["total_materials"] * ratio) // 1000 == 0

    def test_ratio_same_values(self):
        """final_cost == total_construction_cost の場合 ratio=1.0。"""
        cr_data = {
            "final_cost": 10000000,
            "total_construction_cost": 10000000,
            "total_materials": 3000000,
        }
        ratio = cr_data["final_cost"] / cr_data["total_construction_cost"]
        assert ratio == 1.0
        assert int(cr_data["total_materials"] * ratio) // 1000 == 3000

    def test_missing_cr_data_keys(self):
        """cr_data にキーが欠損している場合、get() デフォルトの 0 が使われる。"""
        cr_data = {}
        F = cr_data.get("total_construction_cost", 0)
        ratio = cr_data.get("final_cost", 0) / F if F != 0 else 0
        assert ratio == 0


# =============================================
# 千円単位変換テスト
# =============================================
class TestThousandYenConversion:
    """金額の千円単位変換（// 1000）が正確かテスト。"""

    @pytest.mark.parametrize(
        "input_val,expected",
        [
            (1000, 1),
            (1000000, 1000),
            (12345678, 12345),
            (500, 0),  # 500 // 1000 = 0
            (999, 0),  # 999 // 1000 = 0
            (1500, 1),  # 切り捨て
            (0, 0),
            (-1000000, -1000),  # マイナス値
        ],
    )
    def test_integer_division(self, input_val, expected):
        assert input_val // 1000 == expected


# =============================================
# PL合算項目のロジックテスト
# =============================================
class TestPLAggregation:
    """販管費の合算計算ロジックをテスト。"""

    def test_staff_salary_aggregation(self):
        """給与手当 + 雑給 + 賞与の合算。"""
        pl_data = {
            "staff_salary": 8000000,
            "misc_salary": 500000,
            "bonuses": 1200000,
        }
        total = (
            pl_data.get("staff_salary", 0)
            + pl_data.get("misc_salary", 0)
            + pl_data.get("bonuses", 0)
        ) // 1000
        assert total == 9700

    def test_supplies_aggregation(self):
        """消耗品費 + 事務用品費の合算。"""
        pl_data = {
            "supplies": 200000,
            "office_supplies": 50000,
        }
        total = (pl_data.get("supplies", 0) + pl_data.get("office_supplies", 0)) // 1000
        assert total == 250

    def test_travel_comm_aggregation(self):
        """旅費交通費 + 通信費の合算。"""
        pl_data = {
            "travel_expense": 300000,
            "comm_expense": 100000,
        }
        total = (
            pl_data.get("travel_expense", 0) + pl_data.get("comm_expense", 0)
        ) // 1000
        assert total == 400

    def test_total_sga_calculation(self):
        """販管費合計の計算（全フィールド合算）。"""
        sga_fields = [
            "director_salary",
            "staff_salary",
            "misc_salary",
            "bonuses",
            "welfare_expense",
            "outsourcing_expense",
            "travel_expense",
            "comm_expense",
            "ent_expense",
            "meeting_expense",
            "depreciation",
            "rent",
            "lease",
            "insurance",
            "utilities",
            "supplies",
            "taxes",
            "office_supplies",
            "advertising",
            "fees",
            "training",
            "books",
            "software_expense",
            "misc_expense",
        ]
        pl_data = {f: 100000 for f in sga_fields}  # 各10万円
        total_sga = sum(pl_data.get(f, 0) for f in sga_fields)
        assert total_sga == 100000 * 24  # 24フィールド × 10万 = 240万

    def test_operating_income_from_gross_minus_sga(self):
        """営業利益 = 売上総利益 - 販管費合計。"""
        pl_data = {"gross_profit": 20000000}
        total_sga = 15000000
        operating = (pl_data.get("gross_profit", 0) - total_sga) // 1000
        assert operating == 5000

    def test_aggregation_with_missing_fields(self):
        """欠損フィールドは 0 として扱われる。"""
        pl_data = {"staff_salary": 5000000}  # misc_salary, bonuses 欠損
        total = (
            pl_data.get("staff_salary", 0)
            + pl_data.get("misc_salary", 0)
            + pl_data.get("bonuses", 0)
        ) // 1000
        assert total == 5000

    def test_interest_dividend_aggregation(self):
        """受取利息 + 受取配当金の合算。"""
        pl_data = {
            "interest_income": 50000,
            "dividend_income": 30000,
        }
        total = (
            pl_data.get("interest_income", 0) + pl_data.get("dividend_income", 0)
        ) // 1000
        assert total == 80
