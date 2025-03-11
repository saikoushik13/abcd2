import os
import subprocess
import time

class ProjectSetupNode:
    """
    Sets up the Angular project based on folder_structure.txt.
    1. Initializes the Angular project (if not already created).
    2. Creates base folders in src/app (components, pages, services).
    3. Reads folder_structure.txt, finds lines with CMP:, PAGE:, SRV:,
       and runs 'ng generate component' or 'ng generate service' in subfolders:
         - 'CMP: dashboard.component' -> subfolder 'dashboard' in components/
         - 'PAGE: pods.page' -> subfolder 'pods' in pages/
         - 'SRV: pods.service' -> subfolder 'pods' in services/
    4. Installs dependencies and serves the app.
    """

    def __init__(self):
        current_directory = os.getcwd()
        self.base_path = current_directory
        self.folder_structure_file = os.path.join(self.base_path, "folder_structure.txt")
        # Get project root from the first "DIR:" line
        self.project_root = self.get_project_root()
        self.angular_project_path = os.path.join(self.base_path, self.project_root)
        print(f"✅ Project root: {self.project_root}")

    def run_command(self, command, cwd=None):
        """Runs a shell command and prints output."""
        if cwd:
            print(f"🛠 Running: {command} in {cwd}")
        else:
            print(f"🛠 Running: {command}")
        result = subprocess.run(command, shell=True, text=True, capture_output=True, cwd=cwd)
        if result.returncode != 0:
            print(f"❌ Error: {result.stderr}")
        else:
            print(result.stdout)

    def get_project_root(self):
        """
        Finds the first line starting with 'DIR:' in folder_structure.txt
        and returns whatever is after 'DIR:' as the project root name.
        """
        if not os.path.exists(self.folder_structure_file):
            raise FileNotFoundError(f"❌ folder_structure.txt not found in {self.folder_structure_file}")

        with open(self.folder_structure_file, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("DIR:"):
                    return stripped[4:].strip()

        raise ValueError("❌ No 'DIR:' line found in folder_structure.txt for project root.")

    def initialize_angular_project(self):
        """
        Initializes the Angular project if it doesn't exist yet.
        """
        angular_json_path = os.path.join(self.angular_project_path, "angular.json")
        if not os.path.exists(self.angular_project_path) or not os.path.exists(angular_json_path):
            print("🚀 Initializing Angular project...")
            init_cmd = f"ng new {self.project_root} --routing --style scss --skip-install"
            self.run_command(init_cmd, cwd=self.base_path)
            time.sleep(5)
            if not os.path.exists(angular_json_path):
                print("❌ Angular project initialization did not complete successfully.")
            else:
                print("✅ Angular project initialized.")
        else:
            print("✅ Angular project already exists, skipping initialization.")

    def create_base_folders(self):
        """
        Creates base folders in src/app: components, pages, services.
        Adjust as needed.
        """
        app_path = os.path.join(self.angular_project_path, "src", "app")
        if not os.path.exists(app_path):
            raise FileNotFoundError(f"❌ src/app folder not found in {self.angular_project_path}.")

        folders = ["components", "pages", "services"]
        for folder in folders:
            full_path = os.path.join(app_path, folder)
            os.makedirs(full_path, exist_ok=True)
            print(f"📂 Created folder: {full_path}")

    def generate_files_from_structure(self):
        """
        Reads folder_structure.txt line by line.
        For 'CMP:' or 'PAGE:', runs 'ng generate component' in subfolders under components/ or pages/.
          e.g. 'DIR: CMP: dashboard.component' -> subfolder 'dashboard' in 'components/'
        For 'SRV:', runs 'ng generate service' in subfolders under services/.
          e.g. 'DIR: SRV: pods.service' -> subfolder 'pods' in 'services/'
        """
        if not os.path.exists(self.folder_structure_file):
            raise FileNotFoundError(f"❌ folder_structure.txt not found at {self.folder_structure_file}")

        with open(self.folder_structure_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:
            stripped = line.strip()

            # 1) COMPONENTS
            # 'DIR: CMP: dashboard.component'
            if "CMP:" in stripped:
                idx = stripped.find("CMP:")
                name = stripped[idx + len("CMP:"):].strip()
                # name might be 'dashboard.component'
                # remove the '.component' suffix to get 'dashboard'
                folder_name = name.replace(".component", "")
                # We'll generate in "components/<folder_name>"
                # e.g. "ng generate component components/dashboard --skip-tests"
                command = f"ng generate component components/{folder_name} --skip-tests"
                self.run_command(command, cwd=self.angular_project_path)

            # 2) PAGES
            # 'DIR: PAGE: pods.page'
            elif "PAGE:" in stripped:
                idx = stripped.find("PAGE:")
                name = stripped[idx + len("PAGE:"):].strip()
                # remove '.page' suffix if present
                folder_name = name.replace(".page", "")
                # We'll generate in "pages/<folder_name>"
                command = f"ng generate component pages/{folder_name} --skip-tests"
                self.run_command(command, cwd=self.angular_project_path)

            # 3) SERVICES
            # 'DIR: SRV: pods.service'
            elif "SRV:" in stripped:
                idx = stripped.find("SRV:")
                name = stripped[idx + len("SRV:"):].strip()
                # remove '.service' suffix if present
                folder_name = name.replace(".service", "")
                # We'll generate in "services/<folder_name>"
                # e.g. "ng generate service services/pods --skip-tests"
                command = f"ng generate service services/{folder_name} --skip-tests"
                self.run_command(command, cwd=self.angular_project_path)

            # Optionally handle other markers (ST:, FILE:, etc.) as needed.

    def install_dependencies(self):
        """Install Angular dependencies in the workspace."""
        print("\n🔹 Installing required dependencies...")
        dependencies = [
            "rxjs"
        ]
        for package in dependencies:
            self.run_command(f"ng add {package} --skip-confirmation", cwd=self.angular_project_path)

    def start_angular_project(self):
        """Runs `ng serve` to start the Angular application."""
        print("\n🚀 Starting Angular application...")
        os.chdir(self.angular_project_path)
        self.run_command("ng serve")
        print("✅ Angular application is running.")

    def run(self):
        """Executes the project setup process."""
        print("\n🔹 Step 1: Initializing Angular Project...")
        self.initialize_angular_project()

        print("\n🔹 Step 2: Creating Base Folders in src/app...")
        self.create_base_folders()

        print("\n🔹 Step 3: Generating Components/Services from folder_structure.txt...")
        self.generate_files_from_structure()

        

if __name__ == "__main__":
    project_setup_node = ProjectSetupNode()
    project_setup_node.run()
