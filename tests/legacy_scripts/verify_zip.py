import zipfile

def check_zip():
    zip_name = "ARUN_Trading_Bot_v1_20260117.zip"
    print(f"Inspecting {zip_name}...")
    
    sensitive_files = ['settings.json', '.encryption_key', 'trades.db']
    found = []
    
    with zipfile.ZipFile(zip_name, 'r') as z:
        for name in z.namelist():
            for s in sensitive_files:
                if name.endswith(s):
                    found.append(name)
    
    if found:
        print("❌ DANGER: Found sensitive files:")
        for f in found:
            print(f"  - {f}")
    else:
        print("✅ CLEAN: No sensitive files found.")

if __name__ == "__main__":
    check_zip()
