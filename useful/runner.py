import subprocess
from pathlib import Path

# Set the folder containing the scripts
scripts_folder = Path('useful')  # Change to your folder name if different

# Get all .py files in the folder, sorted by name
script_files = sorted(scripts_folder.glob('*.py'))

if not script_files:
    print(f"No Python scripts found in: {scripts_folder.resolve()}")
    exit(1)

# Run each script
for script in script_files[:3]:
    print(f"\nRunning {script.name}...")
    result = subprocess.run(['C:/Users/act08/Documents/tmp ssf/venv/Scripts/python.exe', str(script)])
    if result.returncode != 0:
        print(f"{script.name} failed with exit code {result.returncode}")
        break
else:
    print("\nAll scripts completed successfully.")
