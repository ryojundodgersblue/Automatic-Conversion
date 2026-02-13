import pdfplumber

pdf_path = "/Users/ryoya.fujioka/Documents/doc/tests/testData/報告式決算報告書-202410-202513-260110173437.pdf"

with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):
        print(f"=== Page {i} ===")
        print(page.extract_text())
        print()
