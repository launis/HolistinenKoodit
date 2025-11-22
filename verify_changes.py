import os
import sys
from src.processor import AIProcessor

def test_docx_reading():
    print("Testing docx reading...")
    # Create a dummy docx file if it doesn't exist
    try:
        import docx
        doc = docx.Document()
        doc.add_paragraph("Hello world from docx")
        doc.save("test_doc.docx")
        
        processor = AIProcessor()
        content = processor._read_docx("test_doc.docx")
        print(f"Content read: {content.strip()}")
        
        if "Hello world from docx" in content:
            print("SUCCESS: Docx reading works.")
        else:
            print("FAILURE: Content mismatch.")
            
        os.remove("test_doc.docx")
    except ImportError:
        print("FAILURE: python-docx not installed.")
    except Exception as e:
        print(f"FAILURE: {str(e)}")

def test_processor_methods():
    print("\nTesting processor methods...")
    processor = AIProcessor()
    if hasattr(processor, 'run_orchestration'):
        print("SUCCESS: run_orchestration method exists.")
    else:
        print("FAILURE: run_orchestration method missing.")

if __name__ == "__main__":
    test_docx_reading()
    test_processor_methods()
