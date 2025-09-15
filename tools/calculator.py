TOOL_METADATA = {
    "name": "calculator",
    "title": "Calculator",
    "description": "Perform basic arithmetic operations"
}

def run(operation: str, a: float, b: float):
    if operation == "add":
        return {"result": a + b}
    elif operation == "sub":
        return {"result": a - b}
    elif operation == "mul":
        return {"result": a * b}
    elif operation == "div":
        return {"result": a / b if b != 0 else None}
    else:
        raise ValueError("Unsupported operation")
