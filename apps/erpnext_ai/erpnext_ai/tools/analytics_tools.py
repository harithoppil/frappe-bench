"""Analytics tools — SQL queries and chart data generation (Viz agent).

Only SELECT statements are allowed for run_sql_query to prevent
destructive operations via the AI.
"""

from langchain_core.tools import tool


@tool
def run_sql_query(sql: str, max_rows: int = 500) -> dict:
    """Execute a read-only SQL SELECT query on the ERPNext database.

    ONLY SELECT statements are permitted. Use this to answer analytical
    questions that require joining multiple tables or aggregations.

    Args:
        sql: A SELECT SQL query (no INSERT/UPDATE/DELETE/DROP)
        max_rows: Maximum rows to return (capped at 500)
    Returns:
        Dict with 'columns' list and 'data' list of rows
    """
    import frappe

    sql_upper = sql.strip().upper()
    if not sql_upper.startswith("SELECT"):
        raise ValueError("Only SELECT queries are allowed via run_sql_query.")

    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE", "ALTER", "CREATE"]
    for kw in forbidden:
        if kw in sql_upper:
            raise ValueError(f"Forbidden keyword '{kw}' found in query.")

    max_rows = min(max_rows, 500)
    result = frappe.db.sql(sql, as_dict=True)
    data = list(result)[:max_rows]

    columns = list(data[0].keys()) if data else []
    return {"columns": columns, "data": [list(row.values()) for row in data]}


@tool
def generate_chart_data(
    doctype: str,
    group_by_field: str,
    aggregate_field: str,
    aggregate_fn: str = "count",
    filters: dict | None = None,
    limit: int = 10,
) -> dict:
    """Generate aggregated data suitable for charting.

    Args:
        doctype: Target DocType
        group_by_field: Field to group results by
        aggregate_field: Field to aggregate (use 'name' for count)
        aggregate_fn: Aggregation function: 'count', 'sum', 'avg'
        filters: Optional filters
        limit: Max groups to return
    Returns:
        Dict with 'labels' and 'datasets' for chart rendering
    """
    import frappe

    fn_map = {"count": "COUNT", "sum": "SUM", "avg": "AVG"}
    fn = fn_map.get(aggregate_fn.lower(), "COUNT")

    table = f"`tab{doctype}`"
    where_clause = ""
    values = []

    if filters:
        conditions = [f"`{k}` = %s" for k in filters]
        where_clause = "WHERE " + " AND ".join(conditions)
        values = list(filters.values())

    sql = f"""
        SELECT `{group_by_field}` AS label,
               {fn}(`{aggregate_field}`) AS value
        FROM {table}
        {where_clause}
        GROUP BY `{group_by_field}`
        ORDER BY value DESC
        LIMIT {int(limit)}
    """
    rows = frappe.db.sql(sql, values=values, as_dict=True)

    return {
        "labels": [r.label for r in rows],
        "datasets": [{"label": f"{aggregate_fn}({aggregate_field})", "data": [r.value for r in rows]}],
    }
