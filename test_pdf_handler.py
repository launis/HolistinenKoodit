
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    import PyPDF2
    print("✅ PyPDF2 imported successfully.")
except ImportError as e:
    print(f"❌ Failed to import PyPDF2: {e}")
    sys.exit(1)

try:
    from src.data_handler import DataHandler, TextUpload
    print("✅ DataHandler imported successfully.")
    
    # Test instantiation
    handler = DataHandler()
    print("✅ DataHandler instantiated.")
    
except Exception as e:
    print(f"❌ Failed to import/instantiate DataHandler: {e}")
    sys.exit(1)
