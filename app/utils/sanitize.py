from decimal import Decimal

def sanitize_value(value):
    if value is None:
        return "NULL"
    return str(value)

def sanitize_row(row, headers=None):
    if isinstance(row, list):
        if headers:
            return {headers[i]: sanitize_value(val) for i, val in enumerate(row) if i < len(headers)}
        return {f"column_{i}": sanitize_value(val) for i, val in enumerate(row)}
    elif isinstance(row, dict):
        return {k: sanitize_value(v) for k, v in row.items()}
    else:
        return {"value": sanitize_value(row)}

def sanitize_rows(rows, headers=None):
    if not rows:
        return []

    if headers is None and len(rows) > 0 and isinstance(rows[0], list):
        headers = rows[0]
        rows = rows[1:]
    
    return [sanitize_row(row, headers) for row in rows]