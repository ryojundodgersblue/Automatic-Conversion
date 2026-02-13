from typing import Optional

from pydantic import BaseModel


# --- 1. 貸借対照表 (BalanceSheet) ---
class BalanceSheet(BaseModel):
    # 流動資産
    cash: Optional[int] = None  # 現金及び預金
    accounts_receivable: Optional[int] = None  # 売掛金
    materials: Optional[int] = None  # 原材料
    uncompleted_costs: Optional[int] = None  # 未成工事支出金
    advance_payments: Optional[int] = None  # 立替金
    total_current_assets: Optional[int] = None  # 流動資産合計

    # 固定資産
    buildings: Optional[int] = None  # 建物
    structures: Optional[int] = None  # 構築物
    machinery: Optional[int] = None  # 機械装置
    vehicles: Optional[int] = None  # 車両運搬具
    tools_fixtures: Optional[int] = None  # 工具器具備品
    total_tangible_assets: Optional[int] = None  # 有形固定資産合計
    software: Optional[int] = None  # ソフトウェア
    total_intangible_assets: Optional[int] = None  # 無形固定資産合計
    investments: Optional[int] = None  # 出資金
    total_investment_assets: Optional[int] = None  # 投資その他の資産合計
    total_fixed_assets: Optional[int] = None  # 固定資産合計

    # 資産合計
    total_assets: Optional[int] = None  # 資産合計

    # 流動負債
    payable_construction: Optional[int] = None  # 工事未払金
    payable_other: Optional[int] = None  # 未払金
    tax_payable: Optional[int] = None  # 未払法人税等
    consumption_tax_payable: Optional[int] = None  # 未払消費税等
    advances_received: Optional[int] = None  # 未成工事受入金
    deposits_received: Optional[int] = None  # 預り金
    total_current_liabilities: Optional[int] = None  # 流動負債合計

    # 固定負債
    long_term_loans: Optional[int] = None  # 長期借入金
    director_loans: Optional[int] = None  # 役員等借入金
    total_fixed_liabilities: Optional[int] = None  # 固定負債合計

    # 負債合計
    total_liabilities: Optional[int] = None  # 負債合計

    # 純資産
    capital: Optional[int] = None  # 資本金
    retained_earnings: Optional[int] = None  # 利益剰余金合計
    total_equity: Optional[int] = None  # 株主資本合計
    total_net_assets: Optional[int] = None  # 純資産合計
    total_liabilities_net_assets: Optional[int] = None  # 負債・純資産合計


# --- 2. 損益計算書 (ProfitAndLoss) ---
class ProfitAndLoss(BaseModel):
    sales: Optional[int] = None  # 完成工事高 (売上高)
    cost_of_sales: Optional[int] = None  # 完成工事原価
    gross_profit: Optional[int] = None  # 完成工事総利益

    # 販売費及び一般管理費
    director_salary: Optional[int] = None  # 役員報酬
    staff_salary: Optional[int] = None  # 給与手当
    misc_salary: Optional[int] = None  # 雑給
    bonuses: Optional[int] = None  # 賞与
    welfare_expense: Optional[int] = None  # 法定福利費
    outsourcing_expense: Optional[int] = None  # 外注費
    travel_expense: Optional[int] = None  # 旅費交通費
    comm_expense: Optional[int] = None  # 通信費
    ent_expense: Optional[int] = None  # 交際費
    meeting_expense: Optional[int] = None  # 会議費
    depreciation: Optional[int] = None  # 減価償却費
    rent: Optional[int] = None  # 賃借料
    lease: Optional[int] = None  # リース料
    insurance: Optional[int] = None  # 保険料
    utilities: Optional[int] = None  # 水道光熱費
    supplies: Optional[int] = None  # 消耗品費
    taxes: Optional[int] = None  # 租税公課
    office_supplies: Optional[int] = None  # 事務用品費
    advertising: Optional[int] = None  # 広告宣伝費
    fees: Optional[int] = None  # 支払手数料
    training: Optional[int] = None  # 研修諸会費
    books: Optional[int] = None  # 新聞図書費
    software_expense: Optional[int] = None  # ソフト費
    misc_expense: Optional[int] = None  # 雑費
    total_sga_expense: Optional[int] = None  # 販管費合計

    operating_income: Optional[int] = None  # 営業利益 (損失)
    interest_income: Optional[int] = None  # 受取利息
    dividend_income: Optional[int] = None  # 受取配当金
    misc_income: Optional[int] = None  # 雑収入
    interest_expense: Optional[int] = None  # 支払利息
    ordinary_income: Optional[int] = None  # 経常利益
    income_before_tax: Optional[int] = None  # 税引前当期純利益
    income_taxes: Optional[int] = None  # 法人税等
    net_income: Optional[int] = None  # 当期純利益


# --- 3. 完成工事原価報告書 (CostReport) ---
class CostReport(BaseModel):
    beginning_materials: Optional[int] = None  # 期首材料
    major_materials: Optional[int] = None  # 主要材料費
    sub_materials: Optional[int] = None  # 補助材料費
    ending_materials: Optional[int] = None  # 期末材料
    total_materials: Optional[int] = None  # 当期材料費

    wages: Optional[int] = None  # 賃金給料
    bonuses: Optional[int] = None  # 賞与
    legal_welfare: Optional[int] = None  # 法定福利費
    welfare: Optional[int] = None  # 福利厚生費
    total_labor_cost: Optional[int] = None  # 当期労務費

    subcontracting: Optional[int] = None  # 外注加工費
    total_subcontracting: Optional[int] = None  # 当期外注費

    depreciation: Optional[int] = None  # 減価償却費
    insurance: Optional[int] = None  # 保険料
    repairs: Optional[int] = None  # 修繕費
    fuel: Optional[int] = None  # 燃料費
    supplies: Optional[int] = None  # 消耗品費
    taxes: Optional[int] = None  # 租税公課
    vehicle_expense: Optional[int] = None  # 車両費
    misc_expense: Optional[int] = None  # 雑費
    total_expenses: Optional[int] = None  # 当期経費

    total_construction_cost: Optional[int] = None  # 当期総工事費用
    beginning_wip: Optional[int] = None  # 期首仕掛品
    ending_wip: Optional[int] = None  # 期末仕掛品
    transfer_out: Optional[int] = None  # 他勘定振替
    final_cost: Optional[int] = None  # 完成工事原価


# --- 4. 株主資本等変動計算書 (StatementOfAccount) ---
class StatementOfAccount(BaseModel):
    start_capital: Optional[int] = None  # 資本金 期首
    start_retained_earnings: Optional[int] = None  # 利益剰余金 期首
    start_total_equity: Optional[int] = None  # 株主資本合計 期首

    current_net_income: Optional[int] = None  # 当期純利益
    total_change: Optional[int] = None  # 当期変動額合計

    end_capital: Optional[int] = None  # 資本金 期末
    end_retained_earnings: Optional[int] = None  # 利益剰余金 期末
    end_total_equity: Optional[int] = None  # 株主資本合計 期末


# マスタ
class FinancialStatements(BaseModel):
    balance_sheet: BalanceSheet
    profit_and_loss: ProfitAndLoss
    cost_report: CostReport
    statement_of_account: StatementOfAccount
