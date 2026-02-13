import re

import pdfplumber

pdf_path = "/Users/ryoya.fujioka/Documents/doc/tests/testData/報告式決算報告書-202410-202513-260110173437.pdf"


# --- 1. 貸借対照表 (BalanceSheet) ---
BALANCE_SHEET_KEYS = {
    "cash": ["現金及び預金", "現金及預金", "現金預金", "現預金", "現金"],
    "accounts_receivable": [
        "売掛金",
        "完成工事未収入金",
        "完成工事未収金",
        "工事未収金",
    ],
    "materials": ["原材料", "材料", "貯蔵品"],
    "uncompleted_costs": ["未成工事支出金", "未成工事支出", "建設仮勘定", "仕掛品"],
    "advance_payments": ["立替金", "従業員立替金"],
    "total_current_assets": ["流動資産合計", "流動資産計"],
    "buildings": ["建物", "附属設備"],
    "structures": ["構築物", "土木構築物"],
    "machinery": ["機械装置", "機械及び装置", "重機"],
    "vehicles": ["車両運搬具", "車両", "自動車"],
    "tools_fixtures": ["工具器具備品", "器具備品", "什器備品", "工具"],
    "total_tangible_assets": ["有形固定資産合計", "有形固定資産計"],
    "software": ["ソフトウェア", "ソフトウエア"],
    "total_intangible_assets": ["無形固定資産合計", "無形固定資産計"],
    "investments": ["出資金", "投資有価証券", "長期投資"],
    "total_investment_assets": ["投資その他の資産合計", "投資合計"],
    "total_fixed_assets": ["固定資産合計", "固定資産計"],
    "total_assets": ["資産合計", "資産計"],
    "payable_construction": ["工事未払金", "未払金（工事）", "下請未払金"],
    "payable_other": ["未払金", "未払費用"],
    "tax_payable": ["未払法人税等", "未払法人税", "法人税等未払金"],
    "consumption_tax_payable": ["未払消費税等", "未払消費税", "消費税等未払金"],
    "advances_received": ["未成工事受入金", "前受金", "工事前受金", "受入金"],
    "deposits_received": ["預り金", "従業員預り金", "源泉所得税預り金"],
    "total_current_liabilities": ["流動負債合計", "流動負債計"],
    "long_term_loans": ["長期借入金", "証券借入金", "長期ローン"],
    "director_loans": ["役員等借入金", "役員借入金", "役員長期借入金"],
    "total_fixed_liabilities": ["固定負債合計", "固定負債計"],
    "total_liabilities": ["負債合計", "負債計"],
    "capital": ["資本金", "元入金"],
    "retained_earnings": ["利益剰余金合計", "利益剰余金", "利益剰余"],
    "total_equity": ["株主資本合計", "株主資本計"],
    "total_net_assets": ["純資産合計", "純資産計"],
    "total_liabilities_net_assets": [
        "負債・純資産合計",
        "負債純資産合計",
        "負債及び純資産合計",
    ],
}

# --- 2. 損益計算書 (ProfitAndLoss) ---
PROFIT_AND_LOSS_KEYS = {
    "sales": ["売上高", "完成工事高", "完成工事収入"],
    "cost_of_sales": ["完成工事原価", "売上原価"],
    "gross_profit": ["完成工事総利益", "完成工事総利益金額", "売上総利益"],
    "director_salary": ["役員報酬", "役員給与"],
    "staff_salary": ["給与手当", "給料手当", "給料", "従業員給料"],
    "misc_salary": ["雑給", "賃金"],
    "bonuses": ["賞与", "ボーナス", "賞与引当金繰入"],
    "welfare_expense": ["法定福利費", "社会保険料"],
    "outsourcing_expense": ["外注費", "支払外注費", "外注加工費"],
    "travel_expense": ["旅費交通費", "旅費", "交通費"],
    "comm_expense": ["通信費", "通信運搬費"],
    "ent_expense": ["交際費", "接待交際費"],
    "meeting_expense": ["会議費", "福利厚生費（会議）"],
    "depreciation": ["減価償却費", "減価償却"],
    "rent": ["賃借料", "地代家賃", "事務所家賃"],
    "lease": ["リース料", "リース代"],
    "insurance": ["保険料", "損害保険料", "火災保険料"],
    "utilities": ["水道光熱費", "光熱水費", "電気代"],
    "supplies": ["消耗品費", "消耗品"],
    "taxes": ["租税公課", "公租公課"],
    "office_supplies": ["事務用品費", "文房具代"],
    "advertising": ["広告宣伝費", "宣伝費"],
    "fees": ["支払手数料", "振込手数料", "手数料"],
    "training": ["研修諸会費", "教育研修費", "諸会費"],
    "books": ["新聞図書費", "図書費"],
    "software_expense": ["ソフト費", "情報システム費"],
    "misc_expense": ["雑費", "諸費"],
    "total_sga_expense": ["販売費及び一般管理費合計", "販管費合計", "販管費計"],
    "operating_income": ["営業利益", "営業利益金額", "営業損失", "営業損失金額"],
    "interest_income": ["受取利息", "受取配当金利息"],
    "dividend_income": ["受取配当金"],
    "misc_income": ["雑収入", "営業外収益"],
    "interest_expense": ["支払利息", "支払利息割引料"],
    "ordinary_income": ["経常利益", "経常利益金額", "経常損失"],
    "income_before_tax": ["税引前当期純利益", "税引前当期純利益金額", "税前利益"],
    "income_taxes": ["法人税、住民税及び事業税", "法人税等", "法人税住民税"],
    "net_income": ["当期純利益", "当期純利益金額", "当期純損失"],
}

# --- 3. 完成工事原価報告書 (CostReport) ---
COST_REPORT_KEYS = {
    "beginning_materials": ["期首材料棚卸高", "期首材料", "期首棚卸"],
    "major_materials": ["主要材料費", "材料費"],
    "sub_materials": ["補助材料費", "副資材費"],
    "ending_materials": ["期末材料棚卸高", "期末材料", "期末棚卸"],
    "total_materials": ["当期材料費", "材料費計"],
    "wages": ["賃金給料", "現場賃金", "工員給料"],
    "bonuses": ["賞与", "現場賞与"],
    "legal_welfare": ["法定福利費", "現場法定福利費"],
    "welfare": ["福利厚生費", "現場福利厚生費"],
    "total_labor_cost": ["当期労務費", "労務費計"],
    "subcontracting": ["外注加工費", "外注費", "外注原価"],
    "total_subcontracting": ["当期外注加工費", "外注費計"],
    "depreciation": ["減価償却費", "工事用減価償却費"],
    "insurance": ["保険料", "工事保険料"],
    "repairs": ["修繕費", "保守費", "維持管理費"],
    "fuel": ["燃料費", "軽油代", "ガソリン代"],
    "supplies": ["消耗品費", "工事消耗品"],
    "taxes": ["租税公課", "事業税"],
    "vehicle_expense": ["車両費", "工事車両費"],
    "misc_expense": ["雑費", "現場雑費"],
    "total_expenses": ["当期経費", "経費計"],
    "total_construction_cost": ["当期総工事費用", "総工事費", "工事原価計"],
    "beginning_wip": ["期首仕掛品棚卸高", "期首未成工事支出金"],
    "ending_wip": ["期末仕掛品棚卸高", "期末未成工事支出金"],
    "transfer_out": ["他勘定振替高", "他勘定振替"],
    "final_cost": ["完成工事原価", "売上原価"],
}

# --- 4. 株主資本等変動計算書 (StatementOfAccount) ---
STATEMENT_KEYS = {
    "start_capital": ["当期首残高", "前期末残高", "資本金期首"],
    "start_retained_earnings": ["利益剰余金当期首残高", "繰越利益剰余金期首"],
    "start_total_equity": ["株主資本合計当期首残高", "純資産期首合計"],
    "current_net_income": ["当期純利益", "当期純損失", "純利益"],
    "total_change": ["当期変動額合計", "変動額計"],
    "end_capital": ["当期末残高", "次期繰越残高", "資本金期末"],
    "end_retained_earnings": ["利益剰余金当期末残高", "繰越利益剰余金期末"],
    "end_total_equity": ["株主資本合計当期末残高", "純資産期末合計"],
}

with pdfplumber.open(pdf_path) as pdf:
    current_section = None
    sections = {"bs": "", "pl": "", "cr": "", "sa": ""}

    for page in pdf.pages:
        text = page.extract_text()
        clean_text = text.replace(" ", "")

        # タイトルでセクション判定
        if "貸借対照表" in clean_text:
            current_section = "bs"
        elif "損益計算書" in clean_text:
            current_section = "pl"
        elif "完成工事原価報告書" in clean_text:
            current_section = "cr"
        elif "変動計算書" in clean_text:
            current_section = "sa"

        if current_section:
            sections[current_section] += text + "\n"


def extract_values(lines, keys_dict):
    result = {}
    for line in lines:
        clean = line.replace(" ", "")
        item_name = re.sub(r"[\d,]+", "", clean)
        for field, keywords in keys_dict.items():
            for keyword in keywords:
                if keyword == item_name:
                    amounts = re.findall(r"[\d,]+", line)
                    if amounts:
                        result[field] = int(amounts[0].replace(",", ""))
    return result


bs_result = extract_values(sections["bs"].split("\n"), BALANCE_SHEET_KEYS)
pl_result = extract_values(sections["pl"].split("\n"), PROFIT_AND_LOSS_KEYS)
cr_result = extract_values(sections["cr"].split("\n"), COST_REPORT_KEYS)

print("=== BalanceSheet ===")
print(bs_result)
print("=== ProfitAndLoss ===")
print(pl_result)
print("=== CostReport ===")
print(cr_result)
