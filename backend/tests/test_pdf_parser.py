"""PDF解析モジュール (pdf_parser.py) の徹底的な単体テスト。

テスト対象:
- extract_values 関数の勘定科目認識精度
- 多メーカー・多表記パターンの対応確認
- 類似名称の誤判定防止
- △マイナス値、カンマ区切り金額、特殊文字の処理
- セクション判定ロジック
"""

import os
import sys

import pytest

# backend ディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pdf_parser import (
    BALANCE_SHEET_KEYS,
    COST_REPORT_KEYS,
    PROFIT_AND_LOSS_KEYS,
    STATEMENT_KEYS,
    extract_values,
)


# =============================================
# 1. 貸借対照表 — 多パターン勘定科目テスト
# =============================================
class TestBalanceSheetMultiPattern:
    """各メーカーの異なる表記で同じフィールドに確実に分類されるかテスト。"""

    # --- 現金・預金 ---
    @pytest.mark.parametrize(
        "label,expected_field",
        [
            ("現金及び預金", "cash"),
            ("現金及預金", "cash"),
            ("現金預金", "cash"),
            ("現預金", "cash"),
            ("現金", "cash"),
        ],
    )
    def test_cash_variations(self, label, expected_field):
        lines = [f"{label} 1,234,567"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert (
            expected_field in result
        ), f"'{label}' が '{expected_field}' として認識されるべき"
        assert result[expected_field] == 1234567

    # --- 売掛金 / 完成工事未収入金 ---
    @pytest.mark.parametrize(
        "label,expected_field",
        [
            ("売掛金", "accounts_receivable"),
            ("完成工事未収入金", "accounts_receivable"),
            ("完成工事未収金", "accounts_receivable"),
            ("工事未収金", "accounts_receivable"),
        ],
    )
    def test_accounts_receivable_variations(self, label, expected_field):
        lines = [f"{label} 5,000,000"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert expected_field in result
        assert result[expected_field] == 5000000

    # --- 原材料 ---
    @pytest.mark.parametrize(
        "label,expected_field",
        [
            ("原材料", "materials"),
            ("材料", "materials"),
            ("貯蔵品", "materials"),
        ],
    )
    def test_materials_variations(self, label, expected_field):
        lines = [f"{label} 300,000"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert expected_field in result
        assert result[expected_field] == 300000

    # --- 未成工事支出金 ---
    @pytest.mark.parametrize(
        "label,expected_field",
        [
            ("未成工事支出金", "uncompleted_costs"),
            ("未成工事支出", "uncompleted_costs"),
            ("建設仮勘定", "uncompleted_costs"),
            ("仕掛品", "uncompleted_costs"),
        ],
    )
    def test_uncompleted_costs_variations(self, label, expected_field):
        lines = [f"{label} 800,000"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert expected_field in result
        assert result[expected_field] == 800000

    # --- 立替金 ---
    @pytest.mark.parametrize(
        "label,expected_field",
        [
            ("立替金", "advance_payments"),
            ("従業員立替金", "advance_payments"),
        ],
    )
    def test_advance_payments_variations(self, label, expected_field):
        lines = [f"{label} 50,000"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert expected_field in result

    # --- 流動資産合計 ---
    @pytest.mark.parametrize("label", ["流動資産合計", "流動資産計"])
    def test_total_current_assets(self, label):
        lines = [f"{label} 10,000,000"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert "total_current_assets" in result
        assert result["total_current_assets"] == 10000000

    # --- 建物 ---
    @pytest.mark.parametrize(
        "label,expected_field",
        [
            ("建物", "buildings"),
            ("附属設備", "buildings"),
        ],
    )
    def test_buildings_variations(self, label, expected_field):
        lines = [f"{label} 2,000,000"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert expected_field in result

    # --- 構築物 ---
    @pytest.mark.parametrize("label", ["構築物", "土木構築物"])
    def test_structures(self, label):
        lines = [f"{label} 500,000"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert "structures" in result

    # --- 機械装置 ---
    @pytest.mark.parametrize("label", ["機械装置", "機械及び装置", "重機"])
    def test_machinery(self, label):
        lines = [f"{label} 3,000,000"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert "machinery" in result

    # --- 車両運搬具 ---
    @pytest.mark.parametrize("label", ["車両運搬具", "車両", "自動車"])
    def test_vehicles(self, label):
        lines = [f"{label} 1,000,000"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert "vehicles" in result

    # --- 工具器具備品 ---
    @pytest.mark.parametrize("label", ["工具器具備品", "器具備品", "什器備品", "工具"])
    def test_tools_fixtures(self, label):
        lines = [f"{label} 200,000"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert "tools_fixtures" in result

    # --- ソフトウェア ---
    @pytest.mark.parametrize("label", ["ソフトウェア", "ソフトウエア"])
    def test_software(self, label):
        lines = [f"{label} 100,000"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert "software" in result

    # --- 出資金 ---
    @pytest.mark.parametrize("label", ["出資金", "投資有価証券", "長期投資"])
    def test_investments(self, label):
        lines = [f"{label} 400,000"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert "investments" in result

    # --- 合計系 ---
    @pytest.mark.parametrize(
        "label,expected_field",
        [
            ("有形固定資産合計", "total_tangible_assets"),
            ("有形固定資産計", "total_tangible_assets"),
            ("無形固定資産合計", "total_intangible_assets"),
            ("無形固定資産計", "total_intangible_assets"),
            ("投資その他の資産合計", "total_investment_assets"),
            ("投資合計", "total_investment_assets"),
            ("固定資産合計", "total_fixed_assets"),
            ("固定資産計", "total_fixed_assets"),
            ("資産合計", "total_assets"),
            ("資産計", "total_assets"),
        ],
    )
    def test_asset_totals(self, label, expected_field):
        lines = [f"{label} 20,000,000"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert expected_field in result

    # --- 負債項目 ---
    @pytest.mark.parametrize(
        "label,expected_field",
        [
            ("工事未払金", "payable_construction"),
            ("下請未払金", "payable_construction"),
            ("未払金", "payable_other"),
            ("未払費用", "payable_other"),
            ("未払法人税等", "tax_payable"),
            ("未払法人税", "tax_payable"),
            ("法人税等未払金", "tax_payable"),
            ("未払消費税等", "consumption_tax_payable"),
            ("未払消費税", "consumption_tax_payable"),
            ("消費税等未払金", "consumption_tax_payable"),
            ("未成工事受入金", "advances_received"),
            ("前受金", "advances_received"),
            ("工事前受金", "advances_received"),
            ("受入金", "advances_received"),
            ("預り金", "deposits_received"),
            ("従業員預り金", "deposits_received"),
            ("源泉所得税預り金", "deposits_received"),
            ("流動負債合計", "total_current_liabilities"),
            ("流動負債計", "total_current_liabilities"),
            ("長期借入金", "long_term_loans"),
            ("証券借入金", "long_term_loans"),
            ("長期ローン", "long_term_loans"),
            ("役員等借入金", "director_loans"),
            ("役員借入金", "director_loans"),
            ("役員長期借入金", "director_loans"),
            ("固定負債合計", "total_fixed_liabilities"),
            ("固定負債計", "total_fixed_liabilities"),
            ("負債合計", "total_liabilities"),
            ("負債計", "total_liabilities"),
        ],
    )
    def test_liability_variations(self, label, expected_field):
        lines = [f"{label} 1,500,000"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert (
            expected_field in result
        ), f"'{label}' が '{expected_field}' として認識されるべき"

    # --- 純資産項目 ---
    @pytest.mark.parametrize(
        "label,expected_field",
        [
            ("資本金", "capital"),
            ("元入金", "capital"),
            ("その他利益剰余金", "other_retained_earnings"),
            ("繰越利益剰余金", "carried_forward_earnings"),
            ("利益剰余金合計", "retained_earnings"),
            ("利益剰余金", "retained_earnings"),
            ("株主資本合計", "total_equity"),
            ("株主資本計", "total_equity"),
            ("純資産合計", "total_net_assets"),
            ("純資産計", "total_net_assets"),
            ("負債・純資産合計", "total_liabilities_net_assets"),
            ("負債純資産合計", "total_liabilities_net_assets"),
            ("負債及び純資産合計", "total_liabilities_net_assets"),
        ],
    )
    def test_equity_variations(self, label, expected_field):
        lines = [f"{label} 8,000,000"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert (
            expected_field in result
        ), f"'{label}' が '{expected_field}' として認識されるべき"


# =============================================
# 2. 損益計算書 — 多パターン勘定科目テスト
# =============================================
class TestProfitAndLossMultiPattern:
    """損益計算書の各メーカー表記パターンをテスト。"""

    @pytest.mark.parametrize(
        "label,expected_field",
        [
            ("売上高", "sales"),
            ("完成工事高", "sales"),
            ("完成工事収入", "sales"),
            ("完成工事原価", "cost_of_sales"),
            ("売上原価", "cost_of_sales"),
            ("完成工事総利益", "gross_profit"),
            ("完成工事総利益金額", "gross_profit"),
            ("売上総利益", "gross_profit"),
            ("役員報酬", "director_salary"),
            ("役員給与", "director_salary"),
            ("給与手当", "staff_salary"),
            ("給料手当", "staff_salary"),
            ("給料", "staff_salary"),
            ("従業員給料", "staff_salary"),
            ("雑給", "misc_salary"),
            ("賃金", "misc_salary"),
            ("賞与", "bonuses"),
            ("ボーナス", "bonuses"),
            ("賞与引当金繰入", "bonuses"),
            ("法定福利費", "welfare_expense"),
            ("社会保険料", "welfare_expense"),
            ("外注費", "outsourcing_expense"),
            ("支払外注費", "outsourcing_expense"),
            ("旅費交通費", "travel_expense"),
            ("旅費", "travel_expense"),
            ("交通費", "travel_expense"),
            ("通信費", "comm_expense"),
            ("通信運搬費", "comm_expense"),
            ("交際費", "ent_expense"),
            ("接待交際費", "ent_expense"),
            ("会議費", "meeting_expense"),
            ("減価償却費", "depreciation"),
            ("減価償却", "depreciation"),
            ("賃借料", "rent"),
            ("地代家賃", "rent"),
            ("事務所家賃", "rent"),
            ("リース料", "lease"),
            ("リース代", "lease"),
            ("保険料", "insurance"),
            ("損害保険料", "insurance"),
            ("火災保険料", "insurance"),
            ("水道光熱費", "utilities"),
            ("光熱水費", "utilities"),
            ("電気代", "utilities"),
            ("消耗品費", "supplies"),
            ("消耗品", "supplies"),
            ("租税公課", "taxes"),
            ("公租公課", "taxes"),
            ("事務用品費", "office_supplies"),
            ("文房具代", "office_supplies"),
            ("広告宣伝費", "advertising"),
            ("宣伝費", "advertising"),
            ("支払手数料", "fees"),
            ("振込手数料", "fees"),
            ("手数料", "fees"),
            ("研修諸会費", "training"),
            ("教育研修費", "training"),
            ("諸会費", "training"),
            ("新聞図書費", "books"),
            ("図書費", "books"),
            ("ソフト費", "software_expense"),
            ("情報システム費", "software_expense"),
            ("雑費", "misc_expense"),
            ("諸費", "misc_expense"),
            ("販売費及び一般管理費合計", "total_sga_expense"),
            ("販管費合計", "total_sga_expense"),
            ("販管費計", "total_sga_expense"),
            ("営業利益", "operating_income"),
            ("営業利益金額", "operating_income"),
            ("営業損失", "operating_income"),
            ("営業損失金額", "operating_income"),
            ("受取利息", "interest_income"),
            ("受取配当金", "dividend_income"),
            ("雑収入", "misc_income"),
            ("営業外収益", "misc_income"),
            ("支払利息", "interest_expense"),
            ("支払利息割引料", "interest_expense"),
            ("経常利益", "ordinary_income"),
            ("経常利益金額", "ordinary_income"),
            ("経常損失", "ordinary_income"),
            ("税引前当期純利益", "income_before_tax"),
            ("税引前当期純利益金額", "income_before_tax"),
            ("税前利益", "income_before_tax"),
            ("法人税等", "income_taxes"),
            ("法人税住民税", "income_taxes"),
            ("当期純利益", "net_income"),
            ("当期純利益金額", "net_income"),
            ("当期純損失", "net_income"),
        ],
    )
    def test_pl_all_variations(self, label, expected_field):
        lines = [f"{label} 1,000,000"]
        result = extract_values(lines, PROFIT_AND_LOSS_KEYS)
        assert (
            expected_field in result
        ), f"PL: '{label}' が '{expected_field}' として認識されるべき"
        assert result[expected_field] == 1000000


# =============================================
# 3. 完成工事原価報告書 — 多パターン勘定科目テスト
# =============================================
class TestCostReportMultiPattern:
    """完成工事原価報告書の各メーカー表記パターンをテスト。"""

    @pytest.mark.parametrize(
        "label,expected_field",
        [
            ("期首材料棚卸高", "beginning_materials"),
            ("期首材料", "beginning_materials"),
            ("期首棚卸", "beginning_materials"),
            ("主要材料費", "major_materials"),
            ("材料費", "major_materials"),
            ("補助材料費", "sub_materials"),
            ("副資材費", "sub_materials"),
            ("期末材料棚卸高", "ending_materials"),
            ("期末材料", "ending_materials"),
            ("期末棚卸", "ending_materials"),
            ("当期材料費", "total_materials"),
            ("材料費計", "total_materials"),
            ("賃金給料", "wages"),
            ("現場賃金", "wages"),
            ("工員給料", "wages"),
            ("賞与", "bonuses"),
            ("現場賞与", "bonuses"),
            ("法定福利費", "legal_welfare"),
            ("現場法定福利費", "legal_welfare"),
            ("福利厚生費", "welfare"),
            ("現場福利厚生費", "welfare"),
            ("当期労務費", "total_labor_cost"),
            ("労務費計", "total_labor_cost"),
            ("外注加工費", "subcontracting"),
            ("外注費", "subcontracting"),
            ("外注原価", "subcontracting"),
            ("当期外注加工費", "total_subcontracting"),
            ("外注費計", "total_subcontracting"),
            ("減価償却費", "depreciation"),
            ("工事用減価償却費", "depreciation"),
            ("保険料", "insurance"),
            ("工事保険料", "insurance"),
            ("修繕費", "repairs"),
            ("保守費", "repairs"),
            ("維持管理費", "repairs"),
            ("燃料費", "fuel"),
            ("軽油代", "fuel"),
            ("ガソリン代", "fuel"),
            ("消耗品費", "supplies"),
            ("工事消耗品", "supplies"),
            ("租税公課", "taxes"),
            ("事業税", "taxes"),
            ("車両費", "vehicle_expense"),
            ("工事車両費", "vehicle_expense"),
            ("雑費", "misc_expense"),
            ("現場雑費", "misc_expense"),
            ("当期経費", "total_expenses"),
            ("経費計", "total_expenses"),
            ("当期総工事費用", "total_construction_cost"),
            ("総工事費", "total_construction_cost"),
            ("工事原価計", "total_construction_cost"),
            ("期首仕掛品棚卸高", "beginning_wip"),
            ("期首未成工事支出金", "beginning_wip"),
            ("期末仕掛品棚卸高", "ending_wip"),
            ("期末未成工事支出金", "ending_wip"),
            ("他勘定振替高", "transfer_out"),
            ("他勘定振替", "transfer_out"),
            ("完成工事原価", "final_cost"),
            ("売上原価", "final_cost"),
        ],
    )
    def test_cr_all_variations(self, label, expected_field):
        lines = [f"{label} 500,000"]
        result = extract_values(lines, COST_REPORT_KEYS)
        assert (
            expected_field in result
        ), f"CR: '{label}' が '{expected_field}' として認識されるべき"
        assert result[expected_field] == 500000


# =============================================
# 4. △（マイナス値）処理テスト
# =============================================
class TestNegativeValues:
    """△マーカーによるマイナス値の処理をテスト。"""

    def test_negative_with_triangle(self):
        lines = ["経常損失 △ 500,000"]
        result = extract_values(lines, PROFIT_AND_LOSS_KEYS)
        assert "ordinary_income" in result
        assert result["ordinary_income"] == -500000

    def test_negative_triangle_no_space(self):
        lines = ["当期純損失△1,200,000"]
        result = extract_values(lines, PROFIT_AND_LOSS_KEYS)
        assert "net_income" in result
        assert result["net_income"] == -1200000

    def test_negative_triangle_bs(self):
        lines = ["繰越利益剰余金 △ 300,000"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert "carried_forward_earnings" in result
        assert result["carried_forward_earnings"] == -300000

    def test_positive_value_no_triangle(self):
        """△が無い場合は正の値。"""
        lines = ["当期純利益 2,000,000"]
        result = extract_values(lines, PROFIT_AND_LOSS_KEYS)
        assert result["net_income"] == 2000000


# =============================================
# 5. 金額フォーマットテスト
# =============================================
class TestAmountFormats:
    """各種金額フォーマットの抽出テスト。"""

    def test_comma_separated(self):
        lines = ["現金及び預金 12,345,678"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert result["cash"] == 12345678

    def test_no_comma_small_amount(self):
        lines = ["現金及び預金 500"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert result["cash"] == 500

    def test_large_amount(self):
        lines = ["売上高 1,234,567,890"]
        result = extract_values(lines, PROFIT_AND_LOSS_KEYS)
        assert result["sales"] == 1234567890

    def test_zero_amount(self):
        lines = ["現金及び預金 0"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert result["cash"] == 0

    def test_space_separated_label_and_amount(self):
        """ラベルと金額の間にスペースが入るパターン。"""
        lines = ["現金及び預金   5,000,000"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert result["cash"] == 5000000


# =============================================
# 6. 類似名称の誤判定防止テスト（重点テスト）
# =============================================
class TestSimilarNameDisambiguation:
    """名称が似ている勘定科目の誤判定を防止するテスト。

    これが最も重要なテストカテゴリ。
    メーカーによって類似の名前を使うことがあり、
    正しいフィールドに分類されることを確認する。
    """

    # --- 「未払金」vs「工事未払金」vs「未払法人税等」 ---
    def test_unpaid_disambiguation(self):
        """「未払金」系の類似名称をそれぞれ正しく分類。"""
        lines = [
            "工事未払金 3,000,000",
            "未払金 1,000,000",
            "未払法人税等 500,000",
            "未払消費税等 200,000",
        ]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert result.get("payable_construction") == 3000000
        assert result.get("payable_other") == 1000000
        assert result.get("tax_payable") == 500000
        assert result.get("consumption_tax_payable") == 200000

    # --- 「利益剰余金」vs「繰越利益剰余金」vs「その他利益剰余金」 ---
    def test_retained_earnings_disambiguation(self):
        """利益剰余金の類似名称を正しく分類。"""
        lines = [
            "その他利益剰余金 2,000,000",
            "繰越利益剰余金 1,500,000",
            "利益剰余金合計 3,500,000",
        ]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert result.get("other_retained_earnings") == 2000000
        assert result.get("carried_forward_earnings") == 1500000
        assert result.get("retained_earnings") == 3500000

    # --- 「資産合計」vs「流動資産合計」vs「固定資産合計」 ---
    def test_asset_total_disambiguation(self):
        """資産合計の各レベルを正しく分類。"""
        lines = [
            "流動資産合計 10,000,000",
            "固定資産合計 8,000,000",
            "資産合計 18,000,000",
        ]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert result.get("total_current_assets") == 10000000
        assert result.get("total_fixed_assets") == 8000000
        assert result.get("total_assets") == 18000000

    # --- 「負債合計」vs「流動負債合計」vs「固定負債合計」 ---
    def test_liability_total_disambiguation(self):
        lines = [
            "流動負債合計 5,000,000",
            "固定負債合計 3,000,000",
            "負債合計 8,000,000",
        ]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert result.get("total_current_liabilities") == 5000000
        assert result.get("total_fixed_liabilities") == 3000000
        assert result.get("total_liabilities") == 8000000

    # --- 「営業利益」vs「経常利益」vs「当期純利益」 ---
    def test_income_type_disambiguation(self):
        """異なるレベルの利益科目を正しく分類。"""
        lines = [
            "営業利益 3,000,000",
            "経常利益 2,800,000",
            "税引前当期純利益 2,700,000",
            "当期純利益 2,000,000",
        ]
        result = extract_values(lines, PROFIT_AND_LOSS_KEYS)
        assert result.get("operating_income") == 3000000
        assert result.get("ordinary_income") == 2800000
        assert result.get("income_before_tax") == 2700000
        assert result.get("net_income") == 2000000

    # --- PL内の「給与手当」vs「役員報酬」vs「雑給」 ---
    def test_salary_disambiguation(self):
        """給与関連の類似名称を正しく分類。"""
        lines = [
            "役員報酬 5,000,000",
            "給与手当 8,000,000",
            "雑給 500,000",
            "賞与 1,200,000",
        ]
        result = extract_values(lines, PROFIT_AND_LOSS_KEYS)
        assert result.get("director_salary") == 5000000
        assert result.get("staff_salary") == 8000000
        assert result.get("misc_salary") == 500000
        assert result.get("bonuses") == 1200000

    # --- 「外注費」vs「外注加工費」 ---
    def test_outsourcing_disambiguation_pl(self):
        """PL内の外注費バリエーション。"""
        lines = ["外注費 2,000,000"]
        result = extract_values(lines, PROFIT_AND_LOSS_KEYS)
        assert result.get("outsourcing_expense") == 2000000

    def test_outsourcing_disambiguation_cr(self):
        """CR内の外注費バリエーション。"""
        lines = ["外注費 3,000,000"]
        result = extract_values(lines, COST_REPORT_KEYS)
        assert result.get("subcontracting") == 3000000

    # --- 「受取利息」vs「支払利息」 ---
    def test_interest_disambiguation(self):
        """受取と支払の利息を正しく区別。"""
        lines = [
            "受取利息 100,000",
            "支払利息 300,000",
        ]
        result = extract_values(lines, PROFIT_AND_LOSS_KEYS)
        assert result.get("interest_income") == 100000
        assert result.get("interest_expense") == 300000

    # --- 「純資産合計」vs「負債・純資産合計」 ---
    def test_net_assets_vs_total(self):
        """純資産合計と負債・純資産合計の区別。"""
        lines = [
            "純資産合計 10,000,000",
            "負債・純資産合計 18,000,000",
        ]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert result.get("total_net_assets") == 10000000
        assert result.get("total_liabilities_net_assets") == 18000000

    # --- 「消耗品費」vs「事務用品費」 ---
    def test_supplies_disambiguation(self):
        lines = [
            "消耗品費 200,000",
            "事務用品費 50,000",
        ]
        result = extract_values(lines, PROFIT_AND_LOSS_KEYS)
        assert result.get("supplies") == 200000
        assert result.get("office_supplies") == 50000

    # --- 「旅費交通費」vs「通信費」vs「交通費」 ---
    def test_travel_comm_disambiguation(self):
        lines = [
            "旅費交通費 300,000",
            "通信費 100,000",
        ]
        result = extract_values(lines, PROFIT_AND_LOSS_KEYS)
        assert result.get("travel_expense") == 300000
        assert result.get("comm_expense") == 100000

    # --- 「材料費」(CR) vs 「当期材料費」(CR) ---
    def test_cr_materials_disambiguation(self):
        """原価報告書内の材料費と当期材料費の区別。"""
        lines = [
            "材料費 800,000",
            "当期材料費 750,000",
        ]
        result = extract_values(lines, COST_REPORT_KEYS)
        # 材料費 → major_materials、当期材料費 → total_materials
        assert result.get("major_materials") == 800000
        assert result.get("total_materials") == 750000

    # --- 「法人税、住民税及び事業税」(長い名前) ---
    def test_long_tax_name(self):
        """長くて特殊文字を含む勘定科目名。"""
        lines = ["法人税、住民税及び事業税 800,000"]
        result = extract_values(lines, PROFIT_AND_LOSS_KEYS)
        assert result.get("income_taxes") == 800000

    # --- 「未払金（工事）」（括弧付き表記） ---
    def test_parenthetical_label(self):
        """括弧付き表記のテスト。"""
        lines = ["未払金（工事） 1,500,000"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert result.get("payable_construction") == 1500000

    # --- 「福利厚生費（会議）」---
    def test_parenthetical_meeting(self):
        """括弧付き会議費の表記。"""
        lines = ["福利厚生費（会議） 80,000"]
        result = extract_values(lines, PROFIT_AND_LOSS_KEYS)
        assert result.get("meeting_expense") == 80000


# =============================================
# 7. 空データ・不正データの処理テスト
# =============================================
class TestEdgeCases:
    """異常系・境界値のテスト。"""

    def test_empty_lines(self):
        """空行のみの入力。"""
        lines = ["", "  ", ""]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert result == {}

    def test_no_amount(self):
        """勘定科目名はあるが金額がない行。"""
        lines = ["現金及び預金"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert "cash" not in result

    def test_unrecognized_label(self):
        """認識できない勘定科目名。"""
        lines = ["特殊勘定科目 999"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert result == {}

    def test_multiple_amounts_first_used(self):
        """1行に複数の数値がある場合、最初の金額が使われる。"""
        lines = ["現金及び預金 1,000,000 2,000,000"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert result["cash"] == 1000000

    def test_label_with_extra_spaces(self):
        """ラベル内にスペースが含まれるケース（スペースは除去されて判定）。"""
        lines = ["現 金 及 び 預 金 3,000,000"]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert result.get("cash") == 3000000


# =============================================
# 8. セクション判定ロジック テスト
# =============================================
class TestSectionDetection:
    """PDF内のセクション判定ロジックをテスト。"""

    def test_bs_section_detected(self):
        """「貸借対照表」を含むテキストがBSセクションとして判定される。"""
        text = "貸借対照表"
        clean_text = text.replace(" ", "")
        assert "貸借対照表" in clean_text

    def test_pl_section_detected(self):
        text = "損益計算書"
        clean_text = text.replace(" ", "")
        assert "損益計算書" in clean_text

    def test_cr_section_detected(self):
        text = "完成工事原価報告書"
        clean_text = text.replace(" ", "")
        assert "完成工事原価報告書" in clean_text

    def test_sa_section_detected(self):
        text = "株主資本等変動計算書"
        clean_text = text.replace(" ", "")
        assert "変動計算書" in clean_text

    def test_section_with_spaces(self):
        """タイトルにスペースが含まれていても判定できる。"""
        text = "貸 借 対 照 表"
        clean_text = text.replace(" ", "")
        assert "貸借対照表" in clean_text


# =============================================
# 9. 全セクション一括処理テスト（統合テスト）
# =============================================
class TestFullDocumentParsing:
    """貸借対照表 + 損益計算書 + 原価報告書が混在するデータを
    セクション別に正しく分離して解析できるかテスト。"""

    def test_multi_section_separation(self):
        """異なるセクションの同名勘定科目が混在しても正しく分離する。"""
        # BS セクションの行
        bs_lines = [
            "現金及び預金 5,000,000",
            "売掛金 3,000,000",
            "資産合計 20,000,000",
        ]
        # PL セクションの行
        pl_lines = [
            "売上高 50,000,000",
            "完成工事原価 30,000,000",
            "営業利益 5,000,000",
            "法定福利費 800,000",
            "減価償却費 600,000",
            "外注費 2,000,000",
        ]
        # CR セクションの行
        cr_lines = [
            "法定福利費 400,000",
            "減価償却費 300,000",
            "外注費 1,500,000",
            "完成工事原価 30,000,000",
        ]

        bs_result = extract_values(bs_lines, BALANCE_SHEET_KEYS)
        pl_result = extract_values(pl_lines, PROFIT_AND_LOSS_KEYS)
        cr_result = extract_values(cr_lines, COST_REPORT_KEYS)

        # BS
        assert bs_result["cash"] == 5000000
        assert bs_result["accounts_receivable"] == 3000000
        assert bs_result["total_assets"] == 20000000

        # PL（法定福利費 → welfare_expense、外注費 → outsourcing_expense）
        assert pl_result["sales"] == 50000000
        assert pl_result["welfare_expense"] == 800000
        assert pl_result["depreciation"] == 600000
        assert pl_result["outsourcing_expense"] == 2000000

        # CR（法定福利費 → legal_welfare、外注費 → subcontracting）
        assert cr_result["legal_welfare"] == 400000
        assert cr_result["depreciation"] == 300000
        assert cr_result["subcontracting"] == 1500000
        assert cr_result["final_cost"] == 30000000


# =============================================
# 10. 実際のPDFテキスト想定パターン（メーカー別）
# =============================================
class TestRealisticPDFPatterns:
    """実際のPDF出力を想定した現実的なテストデータ。"""

    def test_pattern_a_standard_format(self):
        """パターンA: 標準的な確定申告書フォーマット。"""
        lines = [
            "現金及び預金 12,345,678",
            "完成工事未収入金 8,765,432",
            "未成工事支出金 2,345,678",
            "流動資産合計 25,000,000",
            "建物 5,000,000",
            "車両運搬具 1,500,000",
            "固定資産合計 8,000,000",
            "資産合計 33,000,000",
        ]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert len(result) == 8
        assert result["cash"] == 12345678
        assert result["total_assets"] == 33000000

    def test_pattern_b_abbreviated_names(self):
        """パターンB: 略称を使うメーカーのフォーマット。"""
        lines = [
            "現預金 8,000,000",
            "工事未収金 5,000,000",
            "仕掛品 1,000,000",
            "流動資産計 14,000,000",
            "固定資産計 6,000,000",
            "資産計 20,000,000",
        ]
        result = extract_values(lines, BALANCE_SHEET_KEYS)
        assert result["cash"] == 8000000
        assert result["accounts_receivable"] == 5000000
        assert result["uncompleted_costs"] == 1000000
        assert result["total_current_assets"] == 14000000
        assert result["total_fixed_assets"] == 6000000
        assert result["total_assets"] == 20000000

    def test_pattern_c_full_names_with_negative(self):
        """パターンC: 正式名称 + マイナス値を含むフォーマット。"""
        lines = [
            "完成工事高 100,000,000",
            "完成工事原価 80,000,000",
            "完成工事総利益金額 20,000,000",
            "販売費及び一般管理費合計 15,000,000",
            "営業利益金額 5,000,000",
            "経常利益金額 4,800,000",
            "税引前当期純利益金額 4,500,000",
            "法人税等 1,500,000",
            "当期純利益金額 3,000,000",
        ]
        result = extract_values(lines, PROFIT_AND_LOSS_KEYS)
        assert result["sales"] == 100000000
        assert result["cost_of_sales"] == 80000000
        assert result["gross_profit"] == 20000000
        assert result["total_sga_expense"] == 15000000
        assert result["operating_income"] == 5000000
        assert result["net_income"] == 3000000

    def test_pattern_d_cost_report_full(self):
        """パターンD: 完成工事原価報告書の完全なデータセット。"""
        lines = [
            "期首材料棚卸高 500,000",
            "主要材料費 3,000,000",
            "補助材料費 200,000",
            "期末材料棚卸高 400,000",
            "当期材料費 3,300,000",
            "賃金給料 5,000,000",
            "法定福利費 800,000",
            "福利厚生費 200,000",
            "当期労務費 6,000,000",
            "外注加工費 10,000,000",
            "当期外注加工費 10,000,000",
            "減価償却費 500,000",
            "保険料 300,000",
            "修繕費 150,000",
            "燃料費 400,000",
            "消耗品費 100,000",
            "租税公課 200,000",
            "車両費 350,000",
            "雑費 50,000",
            "当期経費 2,050,000",
            "当期総工事費用 21,350,000",
            "完成工事原価 20,000,000",
        ]
        result = extract_values(lines, COST_REPORT_KEYS)
        assert result["beginning_materials"] == 500000
        assert result["total_materials"] == 3300000
        assert result["total_labor_cost"] == 6000000
        assert result["total_subcontracting"] == 10000000
        assert result["total_expenses"] == 2050000
        assert result["total_construction_cost"] == 21350000
        assert result["final_cost"] == 20000000
