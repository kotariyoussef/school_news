import os
import argparse
import subprocess

def run_loaddata_commands(output_dir, python_path, manage_path):
    fixtures = [
        "sites.json",
        "auth_users.json",
        "allauth_email.json",
        "student_requests.json",
        "student_profiles.json",
        "categories.json",
        "tags.json",
        "news.json",
        "tagged_items.json",
        "news_media.json",
        "comments.json",
        "contact_messages.json",
    ]

    for fixture in fixtures:
        fixture_path = os.path.join(output_dir, fixture)
        command = [
            python_path,
            manage_path,
            "loaddata",
            fixture_path
        ]
        print("Running:", " ".join(command))
        subprocess.run(command, check=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run loaddata scripts with a specific Python and manage.py path.")
    parser.add_argument("output", help="Path to the directory containing JSON fixtures", default="fixtures")
    
    # Hardcoded values (you can make these args if needed)
    PYTHON_PATH = "python"
    MANAGE_PATH = "manage.py"

    run_loaddata_commands(parser.parse_args().output, PYTHON_PATH, MANAGE_PATH)
