"""
Generate ~12 fake tax document PDFs for the cadence-intake-agent demo.
Also writes tests/ground_truth.csv with the expected classification answers.

All data is fictional. TFNs shown as XXX XXX XXX.
Run:  python scripts/make_samples.py
"""

import csv
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

INBOX = Path("inbox")
TESTS = Path("tests")

PAGE_W, PAGE_H = A4
STYLES = getSampleStyleSheet()

# ── Shared style helpers ──────────────────────────────────────────────────────

def _doc(filename: str):
    return SimpleDocTemplate(
        str(INBOX / filename),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )


def _h1(text: str) -> Paragraph:
    s = ParagraphStyle("h1", fontSize=14, fontName="Helvetica-Bold", spaceAfter=4)
    return Paragraph(text, s)


def _h2(text: str) -> Paragraph:
    s = ParagraphStyle("h2", fontSize=11, fontName="Helvetica-Bold", spaceAfter=2)
    return Paragraph(text, s)


def _body(text: str) -> Paragraph:
    s = ParagraphStyle("body", fontSize=9, fontName="Helvetica", spaceAfter=2)
    return Paragraph(text, s)


def _small(text: str) -> Paragraph:
    s = ParagraphStyle("small", fontSize=7, fontName="Helvetica", textColor=colors.grey)
    return Paragraph(text, s)


def _sample_banner() -> Paragraph:
    s = ParagraphStyle(
        "banner",
        fontSize=7,
        fontName="Helvetica-Oblique",
        textColor=colors.red,
        alignment=TA_RIGHT,
    )
    return Paragraph("SAMPLE DATA — NOT A REAL DOCUMENT", s)


def _hr() -> HRFlowable:
    return HRFlowable(width="100%", thickness=0.5, color=colors.grey, spaceAfter=6)


def _money_table(rows: list[tuple[str, str]]) -> Table:
    """Two-column label/amount table."""
    data = [[_body(label), Paragraph(amount, ParagraphStyle("r", fontSize=9, alignment=TA_RIGHT))]
            for label, amount in rows]
    t = Table(data, colWidths=[12 * cm, 4 * cm])
    t.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


# ── Document generators ───────────────────────────────────────────────────────

def make_payg(filename, client_name, employer_name, employer_abn,
              gross_income, tax_withheld, fy="2024-25"):
    story = [
        _sample_banner(),
        Spacer(1, 0.3 * cm),
        _h1("PAYG PAYMENT SUMMARY"),
        _body(f"Financial Year: 1 July 20{fy[:2]} to 30 June 20{fy[3:]}"),
        Spacer(1, 0.4 * cm),
        _h2("Payer (Employer)"),
        _body(employer_name),
        _body(f"ABN: {employer_abn}"),
        Spacer(1, 0.3 * cm),
        _h2("Payee (Employee)"),
        _body(client_name),
        _body("TFN: XXX XXX XXX"),
        Spacer(1, 0.4 * cm),
        _hr(),
        _money_table([
            ("Gross payments", f"${gross_income:,.2f}"),
            ("Total tax withheld", f"${tax_withheld:,.2f}"),
            ("Allowances", "$0.00"),
            ("Reportable fringe benefits", "$0.00"),
        ]),
        _hr(),
        Spacer(1, 0.4 * cm),
        _small("This is a payment summary for the period stated above. Keep this document for your tax records."),
        _small("Issued under s16-155 of Schedule 1, Taxation Administration Act 1953."),
    ]
    _doc(filename).build(story)
    print(f"  Created {filename}")


def make_bank_interest(filename, client_name, bank_name, bsb,
                       total_interest, account_last4, fy="2024-25"):
    story = [
        _sample_banner(),
        Spacer(1, 0.3 * cm),
        _h1("ANNUAL TAX STATEMENT — INTEREST INCOME"),
        _body(f"{bank_name}  |  BSB: {bsb}"),
        _body(f"Statement Period: 1 July 20{fy[:2]} to 30 June 20{fy[3:]}"),
        Spacer(1, 0.4 * cm),
        _h2("Account Holder"),
        _body(client_name),
        _body("TFN: XXX XXX XXX"),
        _body(f"Account ending: **** {account_last4}"),
        Spacer(1, 0.4 * cm),
        _hr(),
        _money_table([
            ("Total interest earned", f"${total_interest:,.2f}"),
            ("TFN withholding tax deducted", "$0.00"),
            ("Net interest credited", f"${total_interest:,.2f}"),
        ]),
        _hr(),
        Spacer(1, 0.4 * cm),
        _small("Please include this interest income in your income tax return."),
        _small(f"Report code: S6B  |  {bank_name} ABN: 44 XXX XXX XXX"),
    ]
    _doc(filename).build(story)
    print(f"  Created {filename}")


def make_health_insurance(filename, client_name, fund_name, policy_number,
                          premium_paid, gov_rebate, days_covered=365, fy="2024-25"):
    story = [
        _sample_banner(),
        Spacer(1, 0.3 * cm),
        _h1("PRIVATE HEALTH INSURANCE STATEMENT"),
        _body(f"{fund_name}  |  ABN: 77 XXX XXX XXX"),
        _body(f"Financial Year: 20{fy[:2]}–{fy[3:]}"),
        Spacer(1, 0.4 * cm),
        _h2("Policy Details"),
        _body(f"Policy Holder: {client_name}"),
        _body(f"Policy Number: {policy_number}"),
        _body("TFN: XXX XXX XXX"),
        Spacer(1, 0.4 * cm),
        _hr(),
        _money_table([
            ("Premiums paid by you", f"${premium_paid:,.2f}"),
            ("Government rebate applied", f"${gov_rebate:,.2f}"),
            ("Total premium (gross)", f"${premium_paid + gov_rebate:,.2f}"),
            ("Days with hospital cover", str(days_covered)),
        ]),
        _hr(),
        Spacer(1, 0.4 * cm),
        _small("This statement is provided for your income tax return. You may be entitled to claim a private health insurance rebate."),
        _small("Rebate tier is based on your income. See ato.gov.au for current thresholds."),
    ]
    _doc(filename).build(story)
    print(f"  Created {filename}")


def make_rental_property(filename, client_name, agent_name,
                          property_address, gross_rent, management_fee,
                          maintenance, council_rates, insurance, water, fy="2024-25"):
    total_expenses = management_fee + maintenance + council_rates + insurance + water
    net_income = gross_rent - total_expenses
    story = [
        _sample_banner(),
        Spacer(1, 0.3 * cm),
        _h1("ANNUAL RENTAL INCOME & EXPENSE STATEMENT"),
        _body(f"{agent_name}  |  ABN: 33 XXX XXX XXX"),
        _body(f"Financial Year: 1 July 20{fy[:2]} to 30 June 20{fy[3:]}"),
        Spacer(1, 0.4 * cm),
        _h2("Client Details"),
        _body(f"Owner: {client_name}"),
        _body(f"Property: {property_address}"),
        Spacer(1, 0.4 * cm),
        _h2("Income"),
        _money_table([("Gross rent received", f"${gross_rent:,.2f}")]),
        Spacer(1, 0.3 * cm),
        _h2("Expenses"),
        _money_table([
            (f"Management fees", f"${management_fee:,.2f}"),
            ("Maintenance & repairs", f"${maintenance:,.2f}"),
            ("Council rates", f"${council_rates:,.2f}"),
            ("Building insurance", f"${insurance:,.2f}"),
            ("Water & sewerage", f"${water:,.2f}"),
            ("Total expenses", f"${total_expenses:,.2f}"),
        ]),
        _hr(),
        _money_table([("NET RENTAL INCOME", f"${net_income:,.2f}")]),
        _hr(),
        Spacer(1, 0.4 * cm),
        _small("Please include this statement with your tax return. Retain all original receipts for five years."),
    ]
    _doc(filename).build(story)
    print(f"  Created {filename}")


def make_work_expense(filename, client_name, supplier_name, supplier_abn,
                       supplier_address, description, amount_excl_gst, date_str):
    gst = round(amount_excl_gst * 0.1, 2)
    total = round(amount_excl_gst + gst, 2)
    story = [
        _sample_banner(),
        Spacer(1, 0.3 * cm),
        _h1("TAX INVOICE / RECEIPT"),
        _body(f"{supplier_name}"),
        _body(f"ABN: {supplier_abn}"),
        _body(supplier_address),
        Spacer(1, 0.4 * cm),
        _h2("Sold To"),
        _body(client_name),
        _body(f"Date: {date_str}"),
        Spacer(1, 0.4 * cm),
        _hr(),
        _money_table([
            ("Item / Description", ""),
        ]),
        _body(f"  {description}"),
        Spacer(1, 0.2 * cm),
        _money_table([
            ("Subtotal (ex. GST)", f"${amount_excl_gst:,.2f}"),
            ("GST (10%)", f"${gst:,.2f}"),
            ("TOTAL", f"${total:,.2f}"),
        ]),
        _hr(),
        _body("Payment: Visa **** 4421"),
        Spacer(1, 0.4 * cm),
        _small("This item is used exclusively for work purposes. Retain this receipt for tax records."),
    ]
    _doc(filename).build(story)
    print(f"  Created {filename}")


def make_ambiguous(filename):
    """Intentionally ambiguous / messy document to test low-confidence routing."""
    story = [
        _sample_banner(),
        Spacer(1, 0.3 * cm),
        _h1("CONSOLIDATED FINANCIAL SUMMARY"),
        _body("(Combined Income & Interest Statement — DRAFT)"),
        Spacer(1, 0.4 * cm),
        _body("Account Reference: JNT-VANCE-NG-2024"),
        _body("Prepared by: Automated Reporting System"),
        Spacer(1, 0.3 * cm),
        _hr(),
        _body("Primary account holder:  J. Vance-Ng"),
        _body("Secondary account holder: —"),
        _body("TFN on file: XXX XXX XXX"),
        Spacer(1, 0.3 * cm),
        _small("NOTE: Some figures in this statement may relate to FY 2023-24 OR FY 2024-25."),
        _small("Verify all amounts against primary source documents before lodging."),
        Spacer(1, 0.3 * cm),
        _h2("Employment Income"),
        _body("Employer: [REDACTED — see attached schedule]"),
        _money_table([
            ("Gross wages (approximate)", "$???,???.??"),
            ("Tax withheld (approximate)", "$  ??,???.??"),
        ]),
        Spacer(1, 0.3 * cm),
        _h2("Interest Income"),
        _money_table([
            ("Total interest (all accounts)", "$4,567.00"),
            ("(includes accounts at multiple institutions)", ""),
        ]),
        _hr(),
        _money_table([("COMBINED TOTAL INCOME (DRAFT)", "$???,???.??")]),
        _hr(),
        Spacer(1, 0.4 * cm),
        _small("This is a DRAFT combined statement and has NOT been finalised."),
        _small("Do not use this document for tax lodgement without verification."),
        _small("Contact your accountant if any figures appear incorrect."),
    ]
    _doc(filename).build(story)
    print(f"  Created {filename}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    INBOX.mkdir(exist_ok=True)
    TESTS.mkdir(exist_ok=True)

    ground_truth = []

    print("Generating sample PDFs...\n")

    # ── Eleanor Vance (missing: work_expense_receipt → will trigger reminder email)
    make_payg(
        "eleanor_vance_payg.pdf",
        "Eleanor Vance",
        employer_name="Sunrise Media Pty Ltd",
        employer_abn="11 XXX XXX XXX",
        gross_income=85_000.00,
        tax_withheld=19_200.00,
    )
    ground_truth.append([
        "eleanor_vance_payg.pdf", "Eleanor Vance",
        "payg_income_statement", "gross_income=85000.00,tax_withheld=19200.00",
    ])

    make_bank_interest(
        "eleanor_vance_bank_interest.pdf",
        "Eleanor Vance",
        bank_name="Cornfield Bank",
        bsb="062-XXX",
        total_interest=1_250.50,
        account_last4="7823",
    )
    ground_truth.append([
        "eleanor_vance_bank_interest.pdf", "Eleanor Vance",
        "bank_interest_statement", "total_interest=1250.50",
    ])

    make_health_insurance(
        "eleanor_vance_health_insurance.pdf",
        "Eleanor Vance",
        fund_name="Bluegum Health Fund",
        policy_number="BHF-29847-E",
        premium_paid=2_400.00,
        gov_rebate=720.00,
        days_covered=365,
    )
    ground_truth.append([
        "eleanor_vance_health_insurance.pdf", "Eleanor Vance",
        "private_health_insurance_statement", "premium_paid=2400.00,days_covered=365",
    ])

    make_rental_property(
        "eleanor_vance_rental_property.pdf",
        "Eleanor Vance",
        agent_name="Sandstone Property Management",
        property_address="14 Banksia Close, Riverton WA 6148",
        gross_rent=24_000.00,
        management_fee=2_112.00,
        maintenance=3_250.00,
        council_rates=1_800.00,
        insurance=850.00,
        water=488.00,
    )
    ground_truth.append([
        "eleanor_vance_rental_property.pdf", "Eleanor Vance",
        "rental_property_statement", "gross_rent=24000.00,net_income=15500.00",
    ])

    # ── Thomas Nguyen (all required docs present)
    make_payg(
        "thomas_nguyen_payg.pdf",
        "Thomas Nguyen",
        employer_name="Clearwater Consulting Group",
        employer_abn="22 XXX XXX XXX",
        gross_income=120_000.00,
        tax_withheld=35_000.00,
    )
    ground_truth.append([
        "thomas_nguyen_payg.pdf", "Thomas Nguyen",
        "payg_income_statement", "gross_income=120000.00,tax_withheld=35000.00",
    ])

    make_bank_interest(
        "thomas_nguyen_bank_interest.pdf",
        "Thomas Nguyen",
        bank_name="Ridgeline Savings Bank",
        bsb="031-XXX",
        total_interest=3_200.75,
        account_last4="5512",
    )
    ground_truth.append([
        "thomas_nguyen_bank_interest.pdf", "Thomas Nguyen",
        "bank_interest_statement", "total_interest=3200.75",
    ])

    make_work_expense(
        "thomas_nguyen_work_expense.pdf",
        "Thomas Nguyen",
        supplier_name="TechSupplies Direct Pty Ltd",
        supplier_abn="55 XXX XXX XXX",
        supplier_address="17 Innovation Way, Osborne Park WA 6017",
        description="Standing desk ergonomic keyboard — work from home equipment",
        amount_excl_gst=772.73,
        date_str="15 March 2025",
    )
    ground_truth.append([
        "thomas_nguyen_work_expense.pdf", "Thomas Nguyen",
        "work_expense_receipt", "amount=850.00",
    ])

    # ── Priya Kapoor (all required docs present)
    make_payg(
        "priya_kapoor_payg.pdf",
        "Priya Kapoor",
        employer_name="Ferndale Community Health",
        employer_abn="88 XXX XXX XXX",
        gross_income=65_000.00,
        tax_withheld=12_800.00,
    )
    ground_truth.append([
        "priya_kapoor_payg.pdf", "Priya Kapoor",
        "payg_income_statement", "gross_income=65000.00,tax_withheld=12800.00",
    ])

    make_health_insurance(
        "priya_kapoor_health_insurance.pdf",
        "Priya Kapoor",
        fund_name="Ironbark Health",
        policy_number="IH-00341-PK",
        premium_paid=1_950.00,
        gov_rebate=585.00,
        days_covered=365,
    )
    ground_truth.append([
        "priya_kapoor_health_insurance.pdf", "Priya Kapoor",
        "private_health_insurance_statement", "premium_paid=1950.00,days_covered=365",
    ])

    make_rental_property(
        "priya_kapoor_rental_property.pdf",
        "Priya Kapoor",
        agent_name="Riverview Realty",
        property_address="7 Waratah Street, Subiaco WA 6008",
        gross_rent=18_000.00,
        management_fee=1_584.00,
        maintenance=1_900.00,
        council_rates=1_400.00,
        insurance=680.00,
        water=436.00,
    )
    ground_truth.append([
        "priya_kapoor_rental_property.pdf", "Priya Kapoor",
        "rental_property_statement", "gross_rent=18000.00,net_income=12000.00",
    ])

    make_work_expense(
        "priya_kapoor_work_expense.pdf",
        "Priya Kapoor",
        supplier_name="MedEquip Supplies Pty Ltd",
        supplier_abn="66 XXX XXX XXX",
        supplier_address="22 Hospital Drive, Nedlands WA 6009",
        description="Stethoscope Littmann Classic III — clinical work equipment",
        amount_excl_gst=1_136.36,
        date_str="3 February 2025",
    )
    ground_truth.append([
        "priya_kapoor_work_expense.pdf", "Priya Kapoor",
        "work_expense_receipt", "amount=1250.00",
    ])

    # ── Ambiguous / messy document
    make_ambiguous("ambiguous_doc.pdf")
    ground_truth.append([
        "ambiguous_doc.pdf", "unknown",
        "unknown", "",
    ])

    # ── Write ground truth CSV
    gt_path = TESTS / "ground_truth.csv"
    with gt_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "client", "doc_type", "key_amounts"])
        writer.writerows(ground_truth)

    print(f"\nGenerated {len(ground_truth)} PDFs in {INBOX}/")
    print(f"Ground truth written to {gt_path}")


if __name__ == "__main__":
    main()
