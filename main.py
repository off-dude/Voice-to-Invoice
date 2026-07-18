def parse_indian_voice_text(text):
    text = text.lower().strip()
    
    # Remove common filler words and clean multiple spaces
    text = re.sub(r'\b(rs|rupees|rupee|inr)\b', '', text)
    text = re.sub(r'\s+', ' ', text)
    
    # 1. Advanced Data Science Extraction Pattern:
    # Captures item descriptions followed by numbers and potential unit names (lakh/crore/thousand)
    pattern = r"([a-z\s]+)\s+(\d+(?:\.\d+)?)\s*(lakh|lakhs|crore|crores|thousand|thousands|k)?"
    match = re.search(pattern, text)
    
    if match:
        item_name = match.group(1).strip().capitalize()
        base_value = float(match.group(2))
        unit = match.group(3)
        
        # Apply standard numerical conversion multipliers
        if unit in ['lakh', 'lakhs']:
            base_value *= 100000
        elif unit in ['crore', 'crores']:
            base_value *= 10000000
        elif unit in ['thousand', 'thousands', 'k']:
            base_value *= 1000
            
        if not item_name:
            item_name = "⚠️ ERROR: Incomplete Input"
            
        return {"Item Name": item_name, "Price (Rs)": base_value}
        
    # 2. Failsafe Alternative: Fallback calculation logic if text ordering changes
    # Extract the full numerical string from the text
    numbers = re.findall(r"\b\d+(?:\.\d+)?\b", text)
    if numbers:
        # Use the first complete match found on the line
        price = float(numbers[0])
        
        # Check if text context contains multiplier keywords elsewhere
        if "lakh" in text:
            price *= 100000
        elif "crore" in text:
            price *= 10000000
        elif "thousand" in text or " k " in text:
            price *= 1000
            
        # Strip numbers out to isolate item descriptions
        item_name = re.sub(r'\d+(?:\.\d+)?', '', text).strip().capitalize()
        if not item_name:
            item_name = "⚠️ ERROR: Incomplete Input"
            
        return {"Item Name": item_name, "Price (Rs)": price}
        
    return None
