import os
import zipfile
import datetime

def create_founder_zip():
    timestamp = datetime.datetime.now().strftime("%Y%m%d")
    zip_name = f"ARUN_Trading_Bot_v1_{timestamp}.zip"
    
    # Exclude these
    excludes = [
        '.venv', 'dist', 'build', '__pycache__', '.git', '.pytest_cache',
        'install.log', 'source_payload.zip', 'ARUN_Bot_Installer.spec',
        'build_installer.bat', 'installer_gui.py', '.encryption_key',
        'settings.json', 'trades.db', 'test_installer_gui.bat', 'tests'
    ]
    
    print(f"Creating {zip_name}...")
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("."):
            # Exclude dirs
            dirs[:] = [d for d in dirs if d not in excludes]
            
            for file in files:
                if file == zip_name: continue
                if file.endswith(('.pyc', '.spec', '.lnk', '.log')): continue
                if file.endswith('.zip'): continue  # ERROR: Do not include other zips (like the old tainted one)
                if file in excludes: continue       # ERROR: Explicitly skip files in the excludes list
                
                path = os.path.join(root, file)
                print(f"Adding {path}")
                zipf.write(path)
                
    print(f"\n✅ Created {zip_name}")
    print("You can send this file directly to the founder!")

if __name__ == "__main__":
    create_founder_zip()
