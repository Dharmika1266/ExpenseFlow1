"""
Bill Extractor using Google Gemini API (Free)
More accurate extraction using AI
"""

import json
from typing import Dict
import os
from PIL import Image


class BillExtractorAI:
    def __init__(self, api_key: str = None):
        """
        Initialize the AI bill extractor
        
        Args:
            api_key: Google Gemini API key (or set GEMINI_API_KEY environment variable)
        """
        try:
            import google.generativeai as genai
            
            api_key = api_key or os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("Gemini API key not provided. Set GEMINI_API_KEY environment variable or pass it to the constructor.")
            
            genai.configure(api_key=api_key)
            # Using gemini-2.5-flash for image analysis
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        except ImportError:
            raise ImportError("Please install google-generativeai library: pip install google-generativeai")
    
    def extract_bill_details(self, image_path: str) -> Dict:
        """
        Extract bill details using Google Gemini Vision API
        
        Args:
            image_path: Path to the bill image
            
        Returns:
            Dictionary containing bill details
        """
        # Load image
        img = Image.open(image_path)
        
        # Prepare prompt
        prompt = """
        Analyze this bill/receipt image and extract ONLY the main details in JSON format.
        
        Please extract the following information:
        - vendor_name: Name of the store/restaurant
        - address: Full address if available
        - phone: Phone number if available
        - date: Date of purchase
        - time: Time of purchase
        - bill_number: Receipt/invoice number
        - total: Total amount paid
        
        Return ONLY a valid JSON object with these exact fields. If any field is not found, use null.
        Do not include any other information like items, tax, subtotal, etc.
        """
        
        try:
            # Generate content with image
            response = self.model.generate_content([prompt, img])
            
            # Extract JSON from response
            content = response.text
            
            # Try to parse JSON
            # Remove markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            bill_data = json.loads(content)
            return bill_data
            
        except Exception as e:
            raise Exception(f"Error extracting bill details: {str(e)}")
    
    def process_bill(self, image_path: str) -> str:
        """
        Process bill image and return JSON string
        
        Args:
            image_path: Path to the bill image
            
        Returns:
            JSON string containing bill details
        """
        bill_data = self.extract_bill_details(image_path)
        return json.dumps(bill_data, indent=2)


def main():
    """Example usage"""
    # Make sure to set your Gemini API key
    # Get free API key from: https://makersuite.google.com/app/apikey
    # You can set it as environment variable: GEMINI_API_KEY
    # or pass it directly: BillExtractorAI(api_key="your-api-key")
    
    extractor = BillExtractorAI()
    
    # Process bill image
    image_path = "D:\\Projects\\Expense\\Le.jpeg"  # Replace with your image path
    
    try:
        result_json = extractor.process_bill(image_path)
        print("Extracted Bill Details:")
        print(result_json)
        
        # Save to file
        with open("bill_details.json", "w") as f:
            f.write(result_json)
        print("\nBill details saved to bill_details.json")
        
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
