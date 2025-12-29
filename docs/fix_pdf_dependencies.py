"""
Fix PDF Generation Dependencies for Windows

This script helps install the necessary GTK libraries for WeasyPrint on Windows.
WeasyPrint requires GTK libraries which are not automatically installed on Windows.
"""

import subprocess
import sys
import os

def install_gtk_dependencies():
    """Install GTK dependencies for WeasyPrint on Windows."""
    print("🔧 Installing GTK dependencies for PDF generation...")
    
    try:
        # Try installing GTK via conda if available
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "weasyprint[all]", "--upgrade", "--force-reinstall"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ WeasyPrint dependencies updated")
        else:
            print(f"⚠ WeasyPrint install warning: {result.stderr}")
        
        # Alternative: Install GTK manually
        print("\n📋 Manual GTK Installation Instructions:")
        print("1. Download GTK for Windows from: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer")
        print("2. Run the installer as administrator")
        print("3. Restart your terminal/IDE")
        print("4. Test PDF generation again")
        
        return True
        
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def test_pdf_generation():
    """Test if PDF generation is working."""
    try:
        import weasyprint
        
        # Create simple test HTML
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body><h1>PDF Test</h1><p>This is a test PDF.</p></body>
        </html>
        """
        
        # Try to create PDF
        doc = weasyprint.HTML(string=html_content)
        pdf_bytes = doc.write_pdf()
        
        if pdf_bytes:
            print("✅ PDF generation test successful!")
            return True
        else:
            print("❌ PDF generation test failed")
            return False
            
    except Exception as e:
        print(f"❌ PDF generation test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("PDF GENERATION DEPENDENCY FIXER")
    print("=" * 60)
    
    # Test current status
    if test_pdf_generation():
        print("🎉 PDF generation is already working!")
    else:
        print("🔧 PDF generation needs fixing...")
        install_gtk_dependencies()
        
        print("\n🔄 Testing again...")
        if test_pdf_generation():
            print("🎉 Fixed! PDF generation now working!")
        else:
            print("⚠ Manual installation may be required. See instructions above.")