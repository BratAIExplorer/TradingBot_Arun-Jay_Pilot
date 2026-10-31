import os
import zipfile
import shutil
from pathlib import Path

def pack_source():
    # Define source directory (project root) - assuming this script is in project root
    src_dir = os.path.dirname(os.path.abspath(__file__))
    output_filename = os.path.join(src_dir, "source_payload.zip")
    
    # Remove existing zip if it exists
    if os.path.exists(output_filename):
        os.remove(output_filename)
        print(f"Removed old {output_filename}")

    # Files/Dirs to exclude
    excludes = [
        '.venv', 'dist', 'build', '__pycache__', '.git', '.pytest_cache',
        'install.log', 'source_payload.zip', 'ARUN_Bot_Installer.spec',
        'build_installer.bat', 'installer_gui.py', '.encryption_key',
        'settings.json', 'trades.db'
    ]
    
    # Extensions to exclude
    exclude_exts = ['.pyc', '.spec', '.lnk']

    print(f"Packing source from {src_dir} to {output_filename}...")
    
    file_count = 0
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(src_dir):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in excludes]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, src_dir)
                
                # Check exclusions
                if any(rel_path.startswith(ex) for ex in excludes):
                    continue
                if any(file.endswith(ext) for ext in exclude_exts):
                    continue
                
                # Special cases
                if "installer" in file.lower() and file.endswith(".exe"):
                    continue

                print(f"Adding: {rel_path}")
                zipf.write(file_path, rel_path)
                file_count += 1
                
    print(f"Packed {file_count} files into source_payload.zip")

if __name__ == "__main__":
    pack_source()
