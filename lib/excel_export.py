import io
from datetime import datetime
import pandas as pd


def generate_excel_report(receipts: list) -> bytes:
    if not receipts:
        return None

    try:
        df = pd.DataFrame(receipts)

        columns = {
            "merchant_name": "Merchant",
            "receipt_date": "Date",
            "total_amount": "Total (HKD)",
            "tax_amount": "Tax (HKD)",
            "receipt_type": "Type",
            "status": "Status",
            "notes": "Notes",
        }

        available = {k: v for k, v in columns.items() if k in df.columns}
        df_export = df[list(available.keys())].rename(columns=available)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_export.to_excel(writer, sheet_name="Receipts", index=False)

            if "Total (HKD)" in df_export.columns:
                summary_data = {
                    "Metric": ["Total Receipts", "Total Amount (HKD)", "Total Tax (HKD)"],
                    "Value": [
                        len(df_export),
                        df_export["Total (HKD)"].sum(),
                        df_export["Tax (HKD)"].sum() if "Tax (HKD)" in df_export.columns else 0,
                    ],
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)

            if "Type" in df_export.columns:
                type_summary = df_export.groupby("Type").agg(
                    Count=("Type", "size"),
                    Total_Amount=("Total (HKD)", "sum"),
                ).reset_index()
                type_summary.to_excel(writer, sheet_name="By Category", index=False)

        return output.getvalue()
    except Exception as e:
        return None
