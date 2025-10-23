import ast
import operator


def greet(name):
    """
    A simple function that returns a greeting message.
    
    Args:
        name (str): The name of the person to greet
        
    Returns:
        str: A greeting message
    """
    return f"Hello, {name}!"


def calculator(expression):
    """
    A simple calculator function that evaluates basic arithmetic expressions.
    
    Args:
        expression (str): A string containing a mathematical expression
                         (supports +, -, *, / operations with numbers)
        
    Returns:
        float: The result of the calculation
        
    Raises:
        ValueError: If the expression is invalid or contains unsupported operations
        ZeroDivisionError: If division by zero is attempted
    """
    # Define supported operations
    ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }
    
    def _eval(node):
        """Recursively evaluate AST nodes"""
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.Num):  # Python < 3.8 compatibility
            return node.n
        elif isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            op = ops.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operation: {type(node.op).__name__}")
            try:
                return op(left, right)
            except ZeroDivisionError:
                raise ZeroDivisionError("Division by zero is not allowed")
        elif isinstance(node, ast.UnaryOp):
            operand = _eval(node.operand)
            op = ops.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported unary operation: {type(node.op).__name__}")
            return op(operand)
        else:
            raise ValueError(f"Unsupported expression type: {type(node).__name__}")
    
    try:
        # Parse the expression into an AST
        tree = ast.parse(expression, mode='eval')
        # Evaluate the AST
        result = _eval(tree.body)
        return float(result)
    except SyntaxError:
        raise ValueError(f"Invalid mathematical expression: {expression}")
    except Exception as e:
        if isinstance(e, (ValueError, ZeroDivisionError)):
            raise
        else:
            raise ValueError(f"Error evaluating expression: {expression}")


# Example usage
if __name__ == "__main__":
    # Test the greet function
    result = greet("World")
    print(result)  # Output: Hello, World!
    
    # Test the calculator function
    print("\nCalculator examples:")
    test_expressions = [
        "2 + 3",
        "10 - 4",
        "6 * 7",
        "15 / 3",
        "2 + 3 * 4",
        "(2 + 3) * 4",
        "-5 + 3",
        "10 / 2 / 2"
    ]
    
    for expr in test_expressions:
        try:
            result = calculator(expr)
            print(f"{expr} = {result}")
        except Exception as e:
            print(f"{expr} -> Error: {e}")