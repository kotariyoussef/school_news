import os
import subprocess
from pathlib import Path

# Paths
python_exe = r'C:/Users/act08/Documents/tmp ssf/venv/Scripts/python.exe'
manage_py = r'c:/Users/act08/Documents/tmp ssf/venv/school_newsletter4/manage.py'
fixtures_folder = Path('fixtures')

# Get all .json fixture files
fixture_files = sorted(fixtures_folder.glob('*.json'))

if not fixture_files:
    print("No fixture files found.")
    exit(1)

# Show list of files with indices
print("\nAvailable fixture files:")
for idx, f in enumerate(fixture_files, start=1):
    print(f"{idx}. {f.name}")

# Ask user for the sorting method
print("\nHow would you like to order the fixture files?")
print("1. Creation time")
print("2. Modification time")
print("3. Custom order (e.g., 1 5 2 3)")

choice = input("Enter 1, 2, or 3: ").strip()

if choice == '1':
    sorted_files = sorted(fixture_files, key=lambda f: f.stat().st_ctime)
elif choice == '2':
    sorted_files = sorted(fixture_files, key=lambda f: f.stat().st_mtime)
elif choice == '3':
    custom_input = input("Enter space-separated file numbers in desired order: ").strip()
    try:
        indices = [int(i) for i in custom_input.split()]
        sorted_files = [fixture_files[i - 1] for i in indices if 1 <= i <= len(fixture_files)]
    except ValueError:
        print("Invalid input. Please enter space-separated numbers.")
        exit(1)
else:
    print("Invalid choice. Exiting.")
    exit(1)

# Run loaddata for each selected file
for fixture_file in sorted_files:
    command = [
        python_exe,
        manage_py,
        'loaddata',
        str(fixture_file)
    ]
    print(f"\nRunning: {' '.join(command)}")
    subprocess.run(command)
