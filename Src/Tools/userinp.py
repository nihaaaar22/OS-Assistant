def get_user_input(prompt="Enter input: ", input_type="text"):
    """
    Get input from the user with optional type validation.
    
    Args:
        prompt (str): The message to display to the user
        input_type (str): Type of input to validate (text, number, boolean)
    
    Returns:
        The user's input, converted to the appropriate type
    """
    while True:
        try:
            user_input = input(prompt)
            
            if input_type == "text":
                return user_input
            elif input_type == "number":
                return float(user_input)
            
            else:
                raise ValueError(f"Invalid input type: {input_type}")
                
        except ValueError as e:
            print(f"Invalid input. Please try again. ({str(e)})")
            continue