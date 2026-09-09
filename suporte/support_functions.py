from pyspark.sql import functions as F

def list_valid_batches(root, dbutils):
    """Return sorted list of (name, path) for YYYYMMDD_HHMM folders."""
    out = []
    try:
        for f in dbutils.fs.ls(root):
            if f.isDir():
                name = f.path.rstrip("/").split("/")[-1]
                out.append((name, f.path))
    except Exception:
        pass

    return sorted(out, key=lambda x: x[0])


def get_latest(root, dbutils):
    lst = list_valid_batches(root, dbutils)
    return lst[-1] if lst else None


def get_latest_before(root, ts_ref, dbutils):
    lst = list_valid_batches(root, dbutils)
    older = [x for x in lst if x[0] < ts_ref]
    return older[-1] if older else None

def normalize_datetime_cols(df, columns, flag_col="flag_fail_datehour_conversion"):
    if flag_col not in df.columns:
        df = df.withColumn(flag_col, F.lit(None).cast("string"))

    for c in columns:
        if c in df.columns:
            raw = F.trim(F.col(c))

            parsed = F.coalesce(
                F.to_timestamp(raw, "dd/MM/yy HH:mm"),
                F.to_timestamp(raw, "dd/MM/yyyy HH:mm"),
                F.to_timestamp(raw, "dd/MM/yyyy HH:mm:ss"),
                F.to_timestamp(raw, "dd/MM/yy"),
                F.to_timestamp(raw, "dd/MM/yyyy"),
                F.to_timestamp(raw, "dd-MM-yy HH:mm"),
                F.to_timestamp(raw, "dd-MM-yyyy HH:mm:ss"),
                F.to_timestamp(raw, "dd-MM-yy"),
                F.to_timestamp(raw, "dd-MM-yyyy"),
                F.to_timestamp(raw, "yyyy-MM-dd HH:mm:ss"),
                F.to_timestamp(raw, "yyyy-MM-dd"),
            )

            df = (
                df
                .withColumn(c, parsed)  # timestamp, keeps time
                .withColumn(
                    flag_col,
                    F.when(
                        raw.isNotNull() & parsed.isNull(),
                        F.concat_ws(";", F.col(flag_col), F.lit(c)),
                    ).otherwise(F.col(flag_col))
                )
            )
    return df

def flag_missing_mandatory_fields(df, mandatory_cols, flag_col="flag_missing_mandatory_field"):
    if flag_col not in df.columns:
        df = df.withColumn(flag_col, F.lit(None).cast("string"))

    for c in mandatory_cols:
        if c in df.columns:
            df = df.withColumn(
                flag_col,
                F.when(
                    F.col(c).isNull() | (F.trim(F.col(c)) == ""),
                    F.concat_ws(";", F.col(flag_col), F.lit(c))
                ).otherwise(F.col(flag_col))
            )

    return df

def build_fail_summary(df_clean, df_fail, batch_ts, table_name, spark):
    from pyspark.sql import functions as F

    flag_cols = [
        # "flag_fail_datehour_conversion",
        "flag_missing_mandatory_field"
    ]

    # Keep only the flag columns (or add them as NULL for clean data)
    df_clean_flags = df_clean.select(
        *[F.lit(None).cast("string").alias(c) for c in flag_cols]
    )
    df_fail_flags = df_fail.select(*flag_cols)

    # Union and aggregate in a single job
    union_df = df_clean_flags.union(df_fail_flags)

    agg_row = union_df.agg(
        F.count("*").alias("total_rows"),
        # F.count(flag_cols[0]).alias("fail_date"),
        # F.count(flag_cols[1]).alias("fail_hour"),
        F.count(flag_cols[0]).alias("fail_mandatory")
    ).collect()[0]

    total = agg_row["total_rows"]
    # fail_date = agg_row["fail_date"]
    # fail_hour = agg_row["fail_hour"]
    fail_mandatory = agg_row["fail_mandatory"]

    rows = [
        # (batch_ts, table_name, "date", total - fail_date, fail_date),
        # (batch_ts, table_name, "hour", total - fail_hour, fail_hour),
        (batch_ts, table_name, "mandatory_col", total - fail_mandatory, fail_mandatory),
    ]
    return spark.createDataFrame(rows, ["execution", "table", "flag", "valid_rows", "failed_rows"])
