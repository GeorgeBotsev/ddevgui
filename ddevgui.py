import os
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog, ttk
from pathlib import Path
import platform
import yaml

# Constants
PROJECTS_DIR = Path(__file__).resolve().parent / "websites"
REFRESH_INTERVAL = 5000  # in milliseconds
DDEV_COMMAND = "ddev"
if platform.system() == "Windows":
    DDEV_COMMAND = "C:\\Program Files\\ddev\\ddev.exe"  # Adjust this path if needed

PHP_VERSIONS = ["5.6", "7.0", "7.1", "7.2", "7.3", "7.4", "8.0", "8.1", "8.2", "8.3", "8.4"]
DB_VERSIONS = ["mariadb:5.5", "mariadb:10.0", "mariadb:10.1", "mariadb:10.2", "mariadb:10.3", "mariadb:10.4", "mariadb:10.5", "mariadb:10.6", "mariadb:10.8", "mariadb:10.11", "mariadb:11.4", "mysql:5.5", "mysql:5.6", "mysql:5.7", "mysql:8.0", "mysql:8.1", "mysql:8.2", "mysql:8.3", "mysql:8.4"]
WEBSERVERS = ["apache-fpm", "nginx-fpm", "generic"]

class DDEVManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DDEV Project Manager")
        self.projects = []
        self.selected_project = None

        self.setup_ui()
        self.refresh_projects_periodically()

    def setup_ui(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.sidebar = tk.Frame(self.main_frame, width=200)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        self.project_listbox = tk.Listbox(self.sidebar)
        self.project_listbox.pack(fill=tk.BOTH, expand=True)
        self.project_listbox.bind('<<ListboxSelect>>', self.on_project_select)

        self.refresh_button = tk.Button(self.sidebar, text="Refresh", command=self.refresh_projects)
        self.refresh_button.pack(fill=tk.X)

        self.new_project_button = tk.Button(self.sidebar, text="New Blank Project", command=self.create_new_project)
        self.new_project_button.pack(fill=tk.X)

        self.new_wp_project_button = tk.Button(self.sidebar, text="New WordPress Project", command=self.create_wordpress_project)
        self.new_wp_project_button.pack(fill=tk.X)

        self.controls = tk.Frame(self.main_frame)
        self.controls.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        buttons = [
            ("Start", self.start_project),
            ("Stop", self.stop_project),
            ("Delete", self.delete_project),
            ("Import DB", self.import_db),
            ("Export DB", self.export_db),
            ("Enable Xdebug (Debug)", lambda: self.enable_xdebug("debug")),
            ("Enable Xdebug (Profile)", lambda: self.enable_xdebug("profile")),
        ]

        for text, command in buttons:
            btn = tk.Button(self.controls, text=text, command=command)
            btn.pack(fill=tk.X, pady=2)

    def run_ddev_command(self, project, command):
        project_path = PROJECTS_DIR / project
        try:
            result = subprocess.run([DDEV_COMMAND] + command, cwd=project_path, capture_output=True, text=True)
            if result.returncode != 0:
                messagebox.showerror("Error", result.stderr)
            else:
                messagebox.showinfo("Success", result.stdout)
        except Exception as e:
            messagebox.showerror("Exception", str(e))

    def refresh_projects(self):
        self.projects = [d.name for d in PROJECTS_DIR.iterdir() if (d / ".ddev").exists()]
        self.project_listbox.delete(0, tk.END)
        for project in self.projects:
            self.project_listbox.insert(tk.END, project)

    def refresh_projects_periodically(self):
        self.refresh_projects()
        self.root.after(REFRESH_INTERVAL, self.refresh_projects_periodically)

    def on_project_select(self, event):
        try:
            selection = event.widget.curselection()
            if selection:
                index = selection[0]
                self.selected_project = self.projects[index]
        except IndexError:
            self.selected_project = None

    def start_project(self):
        if self.selected_project:
            self.run_ddev_command(self.selected_project, ["start"])

    def stop_project(self):
        if self.selected_project:
            self.run_ddev_command(self.selected_project, ["stop"])

    def delete_project(self):
        if self.selected_project:
            confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {self.selected_project}?")
            if confirm:
                self.run_ddev_command(self.selected_project, ["delete", "-Oy"])
                project_path = PROJECTS_DIR / self.selected_project
                try:
                    if project_path.exists():
                        for root, dirs, files in os.walk(project_path, topdown=False):
                            for name in files:
                                os.remove(os.path.join(root, name))
                            for name in dirs:
                                os.rmdir(os.path.join(root, name))
                        os.rmdir(project_path)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to remove project folder: {e}")
                self.refresh_projects()

    def import_db(self):
        if self.selected_project:
            db_file = filedialog.askopenfilename(title="Select SQL file to import")
            if db_file:
                self.run_ddev_command(self.selected_project, ["import-db", "--src", db_file])

    def export_db(self):
        if self.selected_project:
            export_path = filedialog.asksaveasfilename(title="Save exported SQL as", defaultextension=".sql")
            if export_path:
                self.run_ddev_command(self.selected_project, ["export-db", "--file", export_path])

    def enable_xdebug(self, mode):
        if not self.selected_project:
            messagebox.showerror("Error", "No project selected.")
            return

        project_path = PROJECTS_DIR / self.selected_project
        php_config_dir = project_path / ".ddev" / "php"
        php_ini_file = php_config_dir / "php.ini"

        try:
            php_config_dir.mkdir(parents=True, exist_ok=True)

            output_dir = "/var/www/html/.ddev/"
            if mode not in ["debug", "profile"]:
                messagebox.showerror("Error", "Unsupported Xdebug mode. Choose 'debug' or 'profile'.")
                return

            php_ini_content = (
                "[PHP]\n"
                f"xdebug.mode={mode}\n"
                "xdebug.start_with_request=yes\n"
                "xdebug.use_compression=false\n"
                "xdebug.profiler_output_name=trace.%c%p%r%u.out\n"
                f"xdebug.output_dir=\"{output_dir}\"\n"
            )

            with open(php_ini_file, "w") as f:
                f.write(php_ini_content)

            restart_result = subprocess.run([DDEV_COMMAND, "restart"], cwd=project_path, capture_output=True, text=True)
            if restart_result.returncode != 0:
                raise RuntimeError(restart_result.stderr)

            enable_result = subprocess.run([DDEV_COMMAND, "xdebug", "enable"], cwd=project_path, capture_output=True, text=True)
            if enable_result.returncode != 0:
                raise RuntimeError(enable_result.stderr)

            messagebox.showinfo("Success", f"Xdebug {mode} mode enabled (php.ini written, container restarted, xdebug activated).")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to enable Xdebug: {e}")

    def ask_project_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Project Settings")
        settings_win.grab_set()

        tk.Label(settings_win, text="PHP Version:").pack()
        php_version_var = tk.StringVar(value=PHP_VERSIONS[0])
        php_dropdown = ttk.Combobox(settings_win, textvariable=php_version_var, values=PHP_VERSIONS)
        php_dropdown.pack()

        tk.Label(settings_win, text="Database:").pack()
        db_version_var = tk.StringVar(value=DB_VERSIONS[0])
        db_dropdown = ttk.Combobox(settings_win, textvariable=db_version_var,     values=DB_VERSIONS)
        db_dropdown.pack()
        tk.Label(settings_win, text="Webserver:").pack()
        webserver_var = tk.StringVar(value=WEBSERVERS[0])
        web_dropdown = ttk.Combobox(settings_win, textvariable=webserver_var, values=WEBSERVERS)
        web_dropdown.pack()

        def submit():
            settings_win.destroy()

        submit_btn = tk.Button(settings_win, text="OK", command=submit)
        submit_btn.pack(pady=10)

        self.root.wait_window(settings_win)
    
        return php_version_var.get(), db_version_var.get(), webserver_var.get()

    def create_new_project(self):
        name = simpledialog.askstring("New Project", "Enter project name:")
        if name:
            php_version, db_version, webserver_type = self.ask_project_settings()
            path = PROJECTS_DIR / name
            path.mkdir(parents=True, exist_ok=True)
            subprocess.run([DDEV_COMMAND, "config", "--project-name", name, "--docroot", "public", "--create-docroot",
                            "--project-type", "php", "--php-version", php_version, "--webserver-type", webserver_type], cwd=path)
            config_file = path / ".ddev" / "config.yaml"
            if config_file.exists():
                with open(config_file, "r") as f:
                    config = yaml.safe_load(f)
                config["dbimage"] = db_version
                with open(config_file, "w") as f:
                    yaml.safe_dump(config, f)
            self.refresh_projects()

    def create_wordpress_project(self):
        name = simpledialog.askstring("New WordPress Project", "Enter project name:")
        if name:
            php_version, db_version, webserver_type = self.ask_project_settings()
            path = PROJECTS_DIR / name
            path.mkdir(parents=True, exist_ok=True)
            subprocess.run([DDEV_COMMAND, "config", "--project-name", name, "--project-type", "wordpress",
                            "--docroot", "web", "--create-docroot", "--php-version", php_version,
                            "--webserver-type", webserver_type], cwd=path)
            config_file = path / ".ddev" / "config.yaml"
            if config_file.exists():
                with open(config_file, "r") as f:
                    config = yaml.safe_load(f)
                config["dbimage"] = db_version
                with open(config_file, "w") as f:
                    yaml.safe_dump(config, f)

            subprocess.run([DDEV_COMMAND, "start"], cwd=path)
            subprocess.run([DDEV_COMMAND, "wp", "--path=web", "core", "download"], cwd=path)
            subprocess.run([
                DDEV_COMMAND, "wp", "--path=web", "core", "install",
                "--url=http://{}.ddev.site".format(name),
                "--title=WordPress Site",
                "--admin_user=admin",
                "--admin_password=admin",
                "--admin_email=admin@example.com"
            ], cwd=path)

            wp_config = path / "web" / "wp-config.php"
            try:
                with open(wp_config, "a") as f:
                    f.write("\ndefine('WP_DEBUG', true);\n")
                    f.write("define('WP_DEBUG_LOG', true);\n")
                messagebox.showinfo("Success", "WordPress project created and configured.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to modify wp-config.php: {e}")

            self.refresh_projects()

        def submit():
            settings_win.destroy()

        submit_btn = tk.Button(settings_win, text="OK", command=submit)
        submit_btn.pack(pady=10)

        self.root.wait_window(settings_win)

        return php_version_var.get(), db_version_var.get(), webserver_var.get()

if __name__ == "__main__":
    PROJECTS_DIR.mkdir(exist_ok=True)
    root = tk.Tk()
    app = DDEVManagerGUI(root)
    root.mainloop()
