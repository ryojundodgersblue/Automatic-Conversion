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
            ws1[cell] = round(bs_data[field] / 1000)

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
            ws2[cell] = round(bs_data[field] / 1000)

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
            ws3[cell] = round(bs_data[field] / 1000)


if __name__ == "__main__":
    bs_data, pl_data, cr_data = parse_pdf(PDF_PATH)
    wb = openpyxl.load_workbook(TEMPLATE_PATH)
    write_bs(wb, bs_data)
    wb.save("/Users/ryoya.fujioka/Downloads/test_output.xlsx")
    print("保存完了！")
