import openpyxl
from pdf_parser import parse_pdf

TEMPLATE_PATH = (
    "/Users/ryoya.fujioka/Documents/doc/backend/public/0_愛知県テンプレ.xlsx"
)
PDF_PATH = "/Users/ryoya.fujioka/Documents/doc/tests/testData/報告式決算報告書-202410-202513-260110173437.pdf"


def write_bs(wb, bs_data):
    ws1 = wb["１５ (１)"]
    ws2 = wb["１５（２）"]
    ws3 = wb["１５（３）"]

    # --- シート1: 流動資産・固定資産 ---
    MAPPING_1 = {
        "cash": "AE12",
        "accounts_receivable": "AE14",
        "uncompleted_costs": "AE16",
        "materials": "AE17",
        "advance_payments": "AE21",
        "total_current_assets": "AG23",
        "software": "AE46",
        "total_intangible_assets": "AE47",
    }
    for field, cell in MAPPING_1.items():
        if field in bs_data:
            ws1[cell] = bs_data[field] // 1000

    # --- シート2: 投資資産・負債 ---
    MAPPING_2 = {
        "investments": "AR8",
        "total_investment_assets": "AR10",
        "total_fixed_assets": "BE11",
        "total_assets": "BE19",
        "payable_construction": "AR24",
        "payable_other": "AR27",
        "tax_payable": "AR29",
        "consumption_tax_payable": "AR30",
        "advances_received": "AR31",
        "deposits_received": "AR32",
        "total_current_liabilities": "BE36",
        "long_term_loans": "AR39",
        "director_loans": "AR44",
        "total_fixed_liabilities": "BE45",
        "total_liabilities": "BE46",
    }
    for field, cell in MAPPING_2.items():
        if field in bs_data:
            ws2[cell] = bs_data[field] // 1000

    # --- シート3: 純資産 ---
    MAPPING_3 = {
        "capital": "AW4",
        "retained_earnings": "AY16",
        "total_equity": "BK19",
        "total_net_assets": "BK26",
        "total_liabilities_net_assets": "BI28",
    }
    for field, cell in MAPPING_3.items():
        if field in bs_data:
            ws3[cell] = bs_data[field] // 1000


def write_pl(wb, pl_data):
    ws4 = wb["１６（４）"]
    ws5 = wb["１６（５）"]

    # --- シート4: 売上・販管費 ---
    MAPPING_4 = {
        "sales": "AV9",
        "cost_of_sales": "AV12",
        "gross_profit": "AX15",
        "director_salary": "AI18",
        "welfare_expense": "AI21",
        # AI24 は supplies + office_supplies の合算で別途計算
        "utilities": "AI26",
        "lease": "AI27",
        "advertising": "AI28",
        "training": "AI30",
        "ent_expense": "AI31",
        "outsourcing_expense": "AI32",
        "rent": "AI33",
        "depreciation": "AI34",
        "meeting_expense": "AI35",
        "taxes": "AI36",
        "insurance": "AI37",
        "misc_expense": "AI38",
    }
    for field, cell in MAPPING_4.items():
        if field in pl_data:
            ws4[cell] = pl_data[field] // 1000

    # 合算が必要な項目
    ws4["AI19"] = (
        pl_data.get("staff_salary", 0)
        + pl_data.get("misc_salary", 0)
        + pl_data.get("bonuses", 0)
    ) // 1000
    ws4["AI24"] = (
        pl_data.get("supplies", 0) + pl_data.get("office_supplies", 0)
    ) // 1000
    ws4["AI25"] = (
        pl_data.get("travel_expense", 0) + pl_data.get("comm_expense", 0)
    ) // 1000

    # 売上・原価・利益の小計（兼業事業分はゼロのため、完成工事分がそのまま合計）
    ws4["BI10"] = pl_data.get("sales", 0) // 1000
    ws4["BI13"] = pl_data.get("cost_of_sales", 0) // 1000
    ws4["BK16"] = pl_data.get("gross_profit", 0) // 1000

    # 販管費合計を計算してセットする
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
    total_sga = sum(pl_data.get(f, 0) for f in sga_fields)
    ws4["AV38"] = total_sga // 1000
    ws4["BK39"] = (pl_data.get("gross_profit", 0) - total_sga) // 1000

    # --- シート5: 営業外・純利益 ---
    MAPPING_5 = {
        "misc_income": "AI5",
        "interest_expense": "AI7",
        "ordinary_income": "BK11",
        "income_before_tax": "BK20",
        "income_taxes": "AI21",
        "net_income": "BK23",
    }
    for field, cell in MAPPING_5.items():
        if field in pl_data:
            ws5[cell] = pl_data[field] // 1000

    # 受取利息及び配当金（合算）→ AI4
    ws5["AI4"] = (
        pl_data.get("interest_income", 0) + pl_data.get("dividend_income", 0)
    ) // 1000

    # 各カテゴリの小計（すでに千円単位のセル値を合算）
    ws5["AV5"] = (ws5["AI4"].value or 0) + (ws5["AI5"].value or 0)  # 営業外収益合計
    ws5["AV10"] = (
        (ws5["AI7"].value or 0)
        + (ws5["AI8"].value or 0)
        + (ws5["AI9"].value or 0)
        + (ws5["AI10"].value or 0)
    )  # 営業外費用合計
    ws5["AV15"] = (ws5["AI14"].value or 0) + (ws5["AI15"].value or 0)  # 特別利益合計
    ws5["AV18"] = (ws5["AI17"].value or 0) + (ws5["AI18"].value or 0)  # 特別損失合計


def write_cr(wb, cr_data):
    ws5 = wb["１６（５）"]

    A = cr_data.get("final_cost", 0)
    F = cr_data.get("total_construction_cost", 0)
    ratio = A / F if F != 0 else 0

    # B' = B * (A/F) を千円単位で
    ws5["BI31"] = int(cr_data.get("total_materials", 0) * ratio) // 1000
    ws5["BI32"] = int(cr_data.get("total_labor_cost", 0) * ratio) // 1000
    ws5["BI34"] = int(cr_data.get("total_subcontracting", 0) * ratio) // 1000
    ws5["BI35"] = int(cr_data.get("total_expenses", 0) * ratio) // 1000
    ws5["BI37"] = A // 1000


if __name__ == "__main__":
    bs_data, pl_data, cr_data = parse_pdf(PDF_PATH)
    wb = openpyxl.load_workbook(TEMPLATE_PATH)
    write_bs(wb, bs_data)
    write_pl(wb, pl_data)
    wb.save("/Users/ryoya.fujioka/Downloads/test_output.xlsx")
    print("保存完了！")
