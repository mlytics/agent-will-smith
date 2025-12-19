"""Test script to verify prompt loading from Databricks.

Run this after creating the prompt in Databricks UI to verify setup.
"""

from core.prompts.loader import load_prompt_from_registry
from core.config import config
import sys

def test_prompt_loading():
    """Test that the prompt can be loaded successfully."""
    print("="*80)
    print("TESTING PROMPT LOADING")
    print("="*80)
    print()
    print(f"Prompt path: {config.prompt_name}")
    print(f"Databricks host: {config.databricks_host}")
    print()
    
    # Validate format
    if not config.prompt_name.startswith("prompts:/"):
        print("❌ ERROR: PROMPT_NAME must start with 'prompts:/' (single slash)")
        print(f"   Current value: {config.prompt_name}")
        print()
        print("Fix: Update your .env file:")
        print("PROMPT_NAME=prompts:/aigc_uat.intent_engine.product_recommendation_prompt/1")
        return False
    
    print("Attempting to load prompt...")
    print()
    
    try:
        prompt = load_prompt_from_registry()
        
        print("✅ SUCCESS! Prompt loaded successfully")
        print("="*80)
        print(f"Prompt length: {len(prompt)} characters")
        print()
        print("First 200 characters:")
        print("-"*80)
        print(prompt[:200])
        print("...")
        print("-"*80)
        print()
        print("✅ Your prompt is configured correctly!")
        print()
        print("Next steps:")
        print("1. Start the application: ./run_local.sh")
        print("2. Test the API: ./test_api.sh")
        print()
        return True
        
    except ValueError as e:
        print(f"❌ ERROR: {e}")
        print()
        print("This usually means the prompt path format is wrong.")
        print("Expected format: prompts://catalog.schema.name/version")
        return False
        
    except Exception as e:
        print(f"❌ ERROR: Failed to load prompt")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print()
        print("Troubleshooting:")
        print("1. Make sure you created the prompt in Databricks UI")
        print("2. Check the prompt name matches exactly:")
        print("   aigc_uat.intent_engine.product_recommendation_prompt")
        print("3. Verify your DATABRICKS_TOKEN has read access")
        print("4. See docs/PROMPT_SETUP.md for detailed instructions")
        print()
        return False


if __name__ == "__main__":
    success = test_prompt_loading()
    sys.exit(0 if success else 1)

