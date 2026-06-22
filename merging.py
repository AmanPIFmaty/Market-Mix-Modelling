import pandas as pd


def merging(promotion_df, sales):
    sales["discount_amount"] = 0.0
    sales["promotion_intensity"] = 0.0

    def process(rows_df):
        """Run one pass over a set of promo rows, updating `sales` in place,
        and return any leftover tail segments that spilled past a week."""
        tail_rows = []
        for _, row in rows_df.iterrows():
            start = row["promo_start_date"]
            end = row["promo_end_date"]
            dept = row["dept"]
            dma = row["dma"]

            sales_row = sales[
                (sales["dma"] == dma) &
                (sales["dept"] == dept) &
                (sales["Week_Start"] <= start) &
                (sales["Week_End"] >= start) &
                (sales["Week_End"] >= end)
            ].index
            sale_row = sales[
                (sales["dma"] == dma) &
                (sales["dept"] == dept) &
                (sales["Week_Start"] <= start) &
                (sales["Week_End"] >= start) &
                (sales["Week_End"] < end)
            ].index

            if len(sales_row) > 0:
                duration = (end - start).days + 1
                sales.loc[sales_row, "discount_amount"] += row["discount_amount"]
                sales.loc[sales_row, "promotion_intensity"] += row["breadth_pct"] * row["depth_pct"] * duration

            elif len(sale_row) > 0:
                week_end = sales.loc[sale_row[0], "Week_End"]
                duration = (week_end - start).days + 1
                total_duration = (end - start).days + 1
                fraction = duration / total_duration

                sales.loc[sale_row, "discount_amount"] += row["discount_amount"] * fraction
                sales.loc[sale_row, "promotion_intensity"] += row["breadth_pct"] * row["depth_pct"] * duration

                tail_rows.append([
                    week_end + pd.Timedelta(days=1), end,
                    row["discount_amount"] * (1 - fraction),
                    dma, dept, row["breadth_pct"], row["depth_pct"],
                ])
            # else: no matching week at all -> dropped, as intended

        return pd.DataFrame(
            tail_rows,
            columns=["promo_start_date", "promo_end_date", "discount_amount", "dma", "dept", "breadth_pct", "depth_pct"]
        )

    promo_mid = process(promotion_df)
    while len(promo_mid) > 0:
        promo_mid = process(promo_mid)

    return sales
