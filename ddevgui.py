import os
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog, ttk
from pathlib import Path
import platform
import yaml
import base64

# Constants
PROJECTS_DIR = Path(__file__).resolve().parent / "websites"
REFRESH_INTERVAL = 5000  # in milliseconds
DDEV_COMMAND = "ddev"
if platform.system() == "Windows":
    DDEV_COMMAND = "C:\\Program Files\\ddev\\ddev.exe"

PHP_VERSIONS = ["5.6", "7.0", "7.1", "7.2", "7.3", "7.4", "8.0", "8.1", "8.2", "8.3", "8.4"]
DB_VERSIONS = [
    "mariadb:5.5", "mariadb:10.0", "mariadb:10.1", "mariadb:10.2", "mariadb:10.3", "mariadb:10.4", "mariadb:10.5", "mariadb:10.6", "mariadb:10.8", "mariadb:10.11", "mariadb:11.4",
    "mysql:5.5", "mysql:5.6", "mysql:5.7", "mysql:8.0", "mysql:8.1", "mysql:8.2", "mysql:8.3", "mysql:8.4"
]
WEBSERVERS = ["apache-fpm", "nginx-fpm", "generic"]

class DDEVManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DDEV Project Manager")
        self.projects = []
        self.selected_project = None
        icon_png_base64 = """
        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
        """
        icon = tk.PhotoImage(data=icon_png_base64)
        root.iconphoto(False, icon)
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
            ("Open Browser", self.open_browser),
            ("Open Adminer", self.open_adminer),
            ("Delete", self.delete_project),
            ("Import DB", self.import_db),
            ("Export DB", self.export_db),
            ("Enable Xdebug (Debug)", lambda: self.enable_xdebug("debug")),
            ("Enable Xdebug (Profile)", lambda: self.enable_xdebug("profile")),
            ("Add Vhost", self.add_vhost),
            ("Enable Redis", lambda: self.enable_service("redis")),
            ("Enable Memcached", lambda: self.enable_service("memcached"))
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

    def open_browser(self):
        if self.selected_project:
            self.run_ddev_command(self.selected_project, ["launch"])

    def open_adminer(self):
        if self.selected_project:
            self.run_ddev_command(self.selected_project, ["adminer"])

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
            php_ini_content = (
                "[PHP]\n"
                f"xdebug.mode={mode}\n"
                "xdebug.start_with_request=yes\n"
                "xdebug.use_compression=false\n"
                "xdebug.profiler_output_name=profiler.%H.%R.%t.out\n"
                f"xdebug.output_dir=\"{output_dir}\"\n"
            )

            with open(php_ini_file, "w") as f:
                f.write(php_ini_content)

            subprocess.run([DDEV_COMMAND, "restart"], cwd=project_path)
            subprocess.run([DDEV_COMMAND, "xdebug", "enable"], cwd=project_path)

            messagebox.showinfo("Success", f"Xdebug {mode} mode enabled.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to enable Xdebug: {e}")

    def ask_project_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Project Settings")
        settings_win.grab_set()

        php_version_var = tk.StringVar(value=PHP_VERSIONS[0])
        db_version_var = tk.StringVar(value=DB_VERSIONS[0])
        webserver_var = tk.StringVar(value=WEBSERVERS[0])

        tk.Label(settings_win, text="PHP Version:").pack()
        ttk.Combobox(settings_win, textvariable=php_version_var, values=PHP_VERSIONS).pack()

        tk.Label(settings_win, text="Database:").pack()
        ttk.Combobox(settings_win, textvariable=db_version_var, values=DB_VERSIONS).pack()

        tk.Label(settings_win, text="Webserver:").pack()
        ttk.Combobox(settings_win, textvariable=webserver_var, values=WEBSERVERS).pack()

        submit_btn = tk.Button(settings_win, text="OK", command=settings_win.destroy)
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
            subprocess.run([
                    DDEV_COMMAND, "get", "ddev/ddev-adminer"
            ], cwd=path)
            if config_file.exists():
                with open(config_file, "r") as f:
                    config = yaml.safe_load(f)
                config["dbimage"] = db_version
                config["disable_settings_management"] = True
                with open(config_file, "w") as f:
                    yaml.safe_dump(config, f)
            subprocess.run([DDEV_COMMAND, "start"], cwd=path)
            self.refresh_projects()

    def create_wordpress_project(self):
        name = simpledialog.askstring("New WordPress Project", "Enter project name:")
        if name:
            php_version, db_version, webserver_type = self.ask_project_settings()
            path = PROJECTS_DIR / name
            path.mkdir(parents=True, exist_ok=True)
            subprocess.run([DDEV_COMMAND, "config", "--project-name", name, "--project-type", "wordpress", "--docroot", "web", "--create-docroot",
                            "--php-version", php_version, "--webserver-type", webserver_type], cwd=path)
            config_file = path / ".ddev" / "config.yaml"
            subprocess.run([
                    DDEV_COMMAND, "get", "ddev/ddev-adminer"
            ], cwd=path)            
            if config_file.exists():
                with open(config_file, "r") as f:
                    config = yaml.safe_load(f)
                config["dbimage"] = db_version
                config["disable_settings_management"] = True
                with open(config_file, "w") as f:
                    yaml.safe_dump(config, f)
            subprocess.run([DDEV_COMMAND, "start"], cwd=path)
            subprocess.run([DDEV_COMMAND, "wp", "--path=web", "core", "download"], cwd=path)
            subprocess.run([DDEV_COMMAND, "wp", "--path=web", "core", "install", "--url=http://{}.ddev.site".format(name),
                            "--title=WordPress Site", "--admin_user=admin", "--admin_password=admin", "--admin_email=admin@example.com"], cwd=path)
            wp_config = path / "web" / "wp-config.php"
            try:
                with open(wp_config, "r") as f:
                    lines = f.readlines()
            
                insert_index = next((i for i, line in enumerate(lines) if "/* That's all, stop editing!" in line), len(lines))

                debug_config = [
                    "define('WP_DEBUG', true);\n",
                    "define('WP_DEBUG_LOG', true);\n",
                    "define('WP_REDIS_HOST', 'redis');\n",
                    "define('WP_REDIS_PORT', 6379);\n",
                    "define('WP_REDIS_TIMEOUT', 1);\n",
                    "define('WP_REDIS_READ_TIMEOUT', 1);\n",
                    "define('WP_REDIS_DATABASE', 0);\n"
                ]

                existing_content = ''.join(lines)
                to_insert = ["\n"] + [line for line in debug_config if line not in existing_content]
            
                if len(to_insert) > 1:  # If anything is new (more than just the "\n")
                    lines[insert_index:insert_index] = to_insert
                    with open(wp_config, "w") as f:
                        f.writelines(lines)
            
                messagebox.showinfo("Success", "WordPress project created and configured.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to modify wp-config.php: {e}")
            self.refresh_projects()
            
    def add_vhost(self):
        if not self.selected_project:
            messagebox.showerror("Error", "No project selected.")
            return

        hostname = simpledialog.askstring("Add Vhost", "Enter hostname (example: sub.mysite.ddev.site):")
        if not hostname:
            return

        project_path = PROJECTS_DIR / self.selected_project

        try:
        
            subprocess.run([DDEV_COMMAND, "config", "--auto", "--additional-hostnames", hostname], cwd=project_path, check=True)
            subprocess.run([DDEV_COMMAND, "restart"], cwd=project_path)
            messagebox.showinfo("Success", f"Hostname {hostname} added")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add vhost: {e}")
        
    def enable_service(self, service):
        if not self.selected_project:
            messagebox.showerror("Error", "No project selected.")
            return
        project_path = PROJECTS_DIR / self.selected_project
        service_files = {
        "redis": ("docker-compose.redis.yaml", """
version: '3.6'
services:
  redis:
    image: redis:7
    container_name: ddev-${DDEV_SITENAME}-redis
    restart: always
    ports:
      - "6379"
    """),
            "memcached": ("docker-compose.memcached.yaml", """
version: '3.6'
services:
  memcached:
    image: memcached:latest
    container_name: ddev-${DDEV_SITENAME}-memcached
    restart: always
    ports:
      - "11211"
    """)
        }
        filename, content = service_files.get(service, (None, None))
        if not filename:
            messagebox.showerror("Error", f"Unknown service {service}")
            return
        service_file = project_path / ".ddev" / filename
        with open(service_file, "w") as f:
            f.write(content.strip())
        subprocess.run([DDEV_COMMAND, "restart"], cwd=project_path)
        messagebox.showinfo("Success", f"{service.capitalize()} enabled and project restarted.")


if __name__ == "__main__":
    PROJECTS_DIR.mkdir(exist_ok=True)
    root = tk.Tk()
    app = DDEVManagerGUI(root)
    root.mainloop()
