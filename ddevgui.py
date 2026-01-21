import os
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog, ttk
from pathlib import Path
import platform
import yaml
import base64
import json
import shutil
import tempfile
import re

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".ddevgui.json")
DEFAULTS = {
    "php_version": "8.3",
    "db_version": "mysql:8.0",
    "webserver": "apache-fpm"
}
PROJECTS_DIR = Path(__file__).resolve().parent / "websites"
REFRESH_INTERVAL = 5000
DDEV_COMMAND = "ddev"
if platform.system() == "Windows":
    DDEV_COMMAND = "C:\\Program Files\\ddev\\ddev.exe"

PHP_VERSIONS = ["5.6", "7.0", "7.1", "7.2", "7.3", "7.4", "8.0", "8.1", "8.2", "8.3", "8.4"]
DB_VERSIONS = [
    "mariadb:5.5", "mariadb:10.0", "mariadb:10.1", "mariadb:10.2", "mariadb:10.3", "mariadb:10.4", "mariadb:10.5", "mariadb:10.6", "mariadb:10.8", "mariadb:10.11", "mariadb:11.4",
    "mysql:5.5", "mysql:5.6", "mysql:5.7", "mysql:8.0", "mysql:8.1", "mysql:8.2", "mysql:8.3", "mysql:8.4"
]
WEBSERVERS = ["apache-fpm", "nginx-fpm", "generic"]

def extract_table_prefix(wp_config_path, docroot, project_path):
    try:
        content = Path(wp_config_path).read_text()
        match = re.search(r"""\$table_prefix\s*=\s*(['"])(.*?)\1""", content)
        if match:
            prefix = match.group(2)
            return prefix
    except Exception as e:
        print(f"[ERROR] Reading wp-config.php: {e}")

    try:
        result = subprocess.run(
            [
                DDEV_COMMAND, "exec", "bash", "-c",
                f"wp --path={docroot} db prefix"
            ],
            cwd=project_path,
            encoding="utf-8",
            capture_output=True,
            text=True,
            check=True
        )
        fallback_prefix = result.stdout.strip()
        return fallback_prefix
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] wp db prefix failed: {e.stderr}")
    except Exception as e:
        print(f"[ERROR] Unexpected error running wp db prefix: {e}")

    return "wp_"

class DDEVManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DDEV Project Manager")
        self.projects = []
        self.selected_project = None
        icon_png_base64 = """
iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAAAxHpUWHRSYXcgcHJvZmlsZSB0eXBlIGV4aWYAAHjabVBbDsMgDPvnFDsCxOF1HLp20m6w489AqNpplgjGpm6IOz7vl3t0SFCnMZdUU/KEVq3SSIqfaKMGr6MOLIvnm+5OQyiBO+yDZPeXHs6AuTWyeA16mrHdjaqWX36C7EfoHQnJbkHVgiDTCBbQ5rN8qiVfn7Ad/o4yl+sFeWSfIb9nzZzeHilC5ECAZwXSbAB9RYdGElkDIi8GZHJBHcrqhAP5N6cF9wXxLlkrViIf9AAAAYNpQ0NQSUNDIHByb2ZpbGUAAHicfZE9SMNAHMVfU4si1Q52EOmQoTrZRaU41ioUoUKoFVp1MLn0C5q0JCkujoJrwcGPxaqDi7OuDq6CIPgB4i44KbpIif9LCi1iPDjux7t7j7t3gNCqMs3sSwCabhmZVFLM5VfF/lcEEMIwIojLzKzPSVIanuPrHj6+3sV4lve5P8eQWjAZ4BOJE6xuWMQbxPFNq855nzjMyrJKfE48adAFiR+5rrj8xrnksMAzw0Y2M08cJhZLPaz0MCsbGvEMcVTVdMoXci6rnLc4a9UG69yTvzBY0FeWuU4zghQWsQQJIhQ0UEEVFmK06qSYyNB+0sM/5vglcinkqoCRYwE1aJAdP/gf/O7WLE5PuUnBJBB4se2PcaB/F2g3bfv72LbbJ4D/GbjSu/5aC5j9JL3Z1aJHQGgbuLjuasoecLkDjD7VZUN2JD9NoVgE3s/om/LAyC0wuOb21tnH6QOQpa7SN8DBITBRoux1j3cP9Pb275lOfz/ByHLGxZE/pwAADltpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADw/eHBhY2tldCBiZWdpbj0i77u/IiBpZD0iVzVNME1wQ2VoaUh6cmVTek5UY3prYzlkIj8+Cjx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IlhNUCBDb3JlIDQuNC4wLUV4aXYyIj4KIDxyZGY6UkRGIHhtbG5zOnJkZj0iaHR0cDovL3d3dy53My5vcmcvMTk5OS8wMi8yMi1yZGYtc3ludGF4LW5zIyI+CiAgPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIKICAgIHhtbG5zOnhtcE1NPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvbW0vIgogICAgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIKICAgIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIKICAgIHhtbG5zOkdJTVA9Imh0dHA6Ly93d3cuZ2ltcC5vcmcveG1wLyIKICAgIHhtbG5zOnRpZmY9Imh0dHA6Ly9ucy5hZG9iZS5jb20vdGlmZi8xLjAvIgogICAgeG1sbnM6eG1wPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvIgogICB4bXBNTTpEb2N1bWVudElEPSJnaW1wOmRvY2lkOmdpbXA6MzEwODE4MTctZDc4Ny00MzdiLWI5MDItODViODRlZDVhYjNmIgogICB4bXBNTTpJbnN0YW5jZUlEPSJ4bXAuaWlkOjc4MDdmNzI3LWRhNzQtNDA2NC1hNjFjLWZjODg4NTdkYmU0MSIKICAgeG1wTU06T3JpZ2luYWxEb2N1bWVudElEPSJ4bXAuZGlkOjgwYTE0ZDBiLTQ5ODItNDUzMC05ZTEyLTExMTJlYjdmYzE3NSIKICAgZGM6Rm9ybWF0PSJpbWFnZS9wbmciCiAgIEdJTVA6QVBJPSIyLjAiCiAgIEdJTVA6UGxhdGZvcm09IkxpbnV4IgogICBHSU1QOlRpbWVTdGFtcD0iMTc0NzMxOTM1NTkwMTY2NyIKICAgR0lNUDpWZXJzaW9uPSIyLjEwLjM2IgogICB0aWZmOk9yaWVudGF0aW9uPSIxIgogICB4bXA6Q3JlYXRvclRvb2w9IkdJTVAgMi4xMCIKICAgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyNTowNToxNVQxNzoyOToxNCswMzowMCIKICAgeG1wOk1vZGlmeURhdGU9IjIwMjU6MDU6MTVUMTc6Mjk6MTQrMDM6MDAiPgogICA8eG1wTU06SGlzdG9yeT4KICAgIDxyZGY6U2VxPgogICAgIDxyZGY6bGkKICAgICAgc3RFdnQ6YWN0aW9uPSJzYXZlZCIKICAgICAgc3RFdnQ6Y2hhbmdlZD0iLyIKICAgICAgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDphMmEwMDQ3Zi1lNGEzLTQ5ZjYtODg5Zi1mY2EyZmNiYWY2OTUiCiAgICAgIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkdpbXAgMi4xMCAoTGludXgpIgogICAgICBzdEV2dDp3aGVuPSIyMDI1LTA1LTE1VDE3OjI4OjA3KzAzOjAwIi8+CiAgICAgPHJkZjpsaQogICAgICBzdEV2dDphY3Rpb249InNhdmVkIgogICAgICBzdEV2dDpjaGFuZ2VkPSIvIgogICAgICBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOjQ2NmFmMzIyLTk1ODktNGRlYi04N2U0LThkZDdkOWRmYTk3NCIKICAgICAgc3RFdnQ6c29mdHdhcmVBZ2VudD0iR2ltcCAyLjEwIChMaW51eCkiCiAgICAgIHN0RXZ0OndoZW49IjIwMjUtMDUtMTVUMTc6Mjk6MTUrMDM6MDAiLz4KICAgIDwvcmRmOlNlcT4KICAgPC94bXBNTTpIaXN0b3J5PgogIDwvcmRmOkRlc2NyaXB0aW9uPgogPC9yZGY6UkRGPgo8L3g6eG1wbWV0YT4KICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgIAo8P3hwYWNrZXQgZW5kPSJ3Ij8+k40fMAAAAAZiS0dEAP8A/wD/oL2nkwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB+kFDw4dDwhRI0sAACAASURBVHja7X13mBzVle/vVPfkPKPRSJqRNKOchUZIAgsBEsYIA16SA2/BsGCMbRwWr/2WXT+/5+f17nqDwYFHWDAYbGMWDAaTJIJIyjmOwowmaUbS5NHkmQ7n/VHV3VU3VFVLve+P9839PlBPd9Wt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
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

        self.new_wp_project_button = tk.Button(self.sidebar, text="Install WordPress Core", command=self.install_wordpress_core)
        self.new_wp_project_button.pack(fill=tk.X)

        self.controls = tk.Frame(self.main_frame)
        self.controls.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        buttons = [
            ("Start", self.start_project),
            ("Stop", self.stop_project),
            ("Restart", self.restart_project),
            ("Open Browser", self.open_browser),
            ("Open Adminer", self.open_adminer),
            ("Open Folder", self.open_project_folder),
            ("Open Terminal (ddev ssh)", self.open_terminal_ssh),
            ("Open Mailpit", self.open_mailpit),
            ("Delete", self.delete_project),
            ("Import DB", self.import_db),
            ("Export DB", self.export_db),
            ("Enable Xdebug (Debug)", lambda: self.enable_xdebug("debug")),
            ("Enable Xdebug (Profile)", lambda: self.enable_xdebug("profile")),
            ("Add Vhost", self.add_vhost),
            ("Enable Redis", lambda: self.enable_service("redis")),
            ("Enable Memcached", lambda: self.enable_service("memcached")),
            ("Reset WP Admin Users", self.reset_admin_users),
            ("Prepare dev environment", self.setup_environment),
        ]

        for text, command in buttons:
            btn = tk.Button(self.controls, text=text, command=command)
            btn.pack(fill=tk.X, pady=2)

    def run_ddev_command(self, project, command):
        def worker():
            project_path = PROJECTS_DIR / project
            try:
                result = subprocess.run(
                    [DDEV_COMMAND] + command,
                    cwd=project_path,
                    encoding="utf-8",
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    self.show_error("Error", result.stderr)
            except Exception as e:
                self.show_error("Exception", str(e))

        threading.Thread(target=worker, daemon=True).start()

    def show_error(self, title, message):
        self.root.after(0, lambda: messagebox.showerror(title, message))

    def refresh_projects(self):
        # Remember current selection (by project name)
        current_selection = self.project_listbox.curselection()
        selected_project_name = None
        if current_selection:
            label = self.project_listbox.get(current_selection[0])
            # label is like: "[running] nest"
            selected_project_name = label.split(' ', 1)[1]

        # Clear listbox
        self.project_listbox.delete(0, tk.END)

        # Get ddev data
        ddev_entries = self.get_ddev_raw_entries()

        # Map absolute approot → status
        status_by_path = {
            str(Path(entry["approot"]).resolve()): entry["status"]
            for entry in ddev_entries
        }

        # Custom order: running → paused → stopped → unknown/other
        status_priority = {
            "running": 0,
            "paused": 1,
            "stopped": 2,
            "unknown": 3,
        }

        # Collect all projects first
        projects = []
        for d in PROJECTS_DIR.iterdir():
            if not (d / ".ddev").exists():
                continue

            resolved_path = str(d.resolve())
            raw_status = status_by_path.get(resolved_path, "unknown")
            status = (raw_status or "unknown").lower()

            projects.append({
                "name": d.name,
                "status": status,
                "resolved_path": resolved_path,
            })

        # Sort projects by status, then by name
        projects.sort(
            key=lambda p: (
                status_priority.get(p["status"], 99),
                p["name"].lower()
            )
        )

        # Rebuild listbox in sorted order
        new_index_to_select = None

        for idx, proj in enumerate(projects):
            # If you prefer capitalised labels, use proj["status"].capitalize()
            label = f"[{proj['status']}] {proj['name']}"
            self.project_listbox.insert(tk.END, label)

            if proj["name"] == selected_project_name:
                new_index_to_select = idx

           # Restore selection if possible
        if new_index_to_select is not None:
            self.project_listbox.select_set(new_index_to_select)
            self.project_listbox.event_generate("<<ListboxSelect>>")


    def open_project_folder(self):
        if self.selected_project:
            project_path = PROJECTS_DIR / self.selected_project
            self.open_directory(str(project_path))

    @staticmethod
    def open_directory(path):
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", path])
        else:  # Assume Linux/Unix
            subprocess.run(["xdg-open", path])

    def get_ddev_raw_entries(self):
        try:
            result = subprocess.run(
                ["ddev", "list", "-j"],
                capture_output=True,
                encoding="utf-8",
                check=True,
                text=True
            )
            data = json.loads(result.stdout)
            return data.get("raw", [])
        except Exception as e:
            print("Error running ddev list:", e)
            return []

    def refresh_projects_periodically(self):
        self.refresh_projects()
        self.root.after(REFRESH_INTERVAL, self.refresh_projects_periodically)

    def on_project_select(self, event):
        try:
            selection = event.widget.curselection()
            if selection:
                index = selection[0]
                label = self.project_listbox.get(index)
                self.selected_project = label.split(' ', 1)[1]  # Skip symbol
        except Exception:
            self.selected_project = None

    def start_project(self):
        if self.selected_project:
            self.run_ddev_command(self.selected_project, ["start"])

    def stop_project(self):
        if self.selected_project:
            self.run_ddev_command(self.selected_project, ["stop"])

    def restart_project(self):
        if self.selected_project:
            self.run_ddev_command(self.selected_project, ["restart"])

    WP_CORE_PHP = {
        "index.php", "wp-activate.php", "wp-blog-header.php", "wp-comments-post.php",
        "wp-config.php", "wp-cron.php", "wp-links-opml.php", "wp-load.php",
        "wp-login.php", "wp-mail.php", "wp-settings.php", "xmlrpc.php"
    }

    def _read_docroot(self,project_path: Path, default="public") -> str:
        cfg = project_path / ".ddev" / "config.yaml"
        if not cfg.is_file():
            return default
        try:
            with cfg.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return str(data.get("docroot", default)).strip() or default
        except Exception as e:
            print(f"Error reading config.yaml: {e}")
            return default

    def _wp_is_installed(self,project_path: Path) -> bool:
        try:
            force = subprocess.run(
                ["ddev", "config", "--project-type=wordpress"],
                cwd=project_path,
                check=True,
            )
            res = subprocess.run(
                ["ddev", "wp", "core", "is-installed"],
                cwd=project_path,
                check=True,
            )
            return res.returncode == 0
        except Exception as e:
            print(f"WP install check failed: {e}")
            return False

    def open_browser(self):
        if not self.selected_project:
            return

        project_path = PROJECTS_DIR / self.selected_project
        docroot = self._read_docroot(project_path)
        root = project_path / docroot

        if not root.exists():
            return self.run_ddev_command(self.selected_project, ["launch"])

        if self._wp_is_installed(project_path):
            wp_admin = root / "wp-admin"
            if wp_admin.is_dir():
                return self.run_ddev_command(self.selected_project, ["launch", "/wp-admin"])
            return self.run_ddev_command(self.selected_project, ["launch"])

        installer = root / "installer.php"
        if installer.is_file():
            return self.run_ddev_command(self.selected_project, ["launch", "/installer.php"])

        try:
            candidates = sorted(p for p in root.glob("*.php") if p.name not in self.WP_CORE_PHP)
        except Exception as e:
            print(f"Error scanning docroot: {e}")
            candidates = []

        if candidates:
            rel = "/" + candidates[0].name
            return self.run_ddev_command(self.selected_project, ["launch", rel])

        if (root / "wp-admin").is_dir():
            return self.run_ddev_command(self.selected_project, ["launch", "/wp-admin"])

        return self.run_ddev_command(self.selected_project, ["launch"])

    def open_adminer(self):
        if self.selected_project:
            self.run_ddev_command(self.selected_project, ["adminer"])

    def open_mailpit(self):
        if self.selected_project:
            self.run_ddev_command(self.selected_project, ["mailpit"])

    def reset_admin_users(self):
        if not self.selected_project:
            messagebox.showerror("Error", "No project selected.")
            return

        try:
            project_path = PROJECTS_DIR / self.selected_project
            config_path = project_path / ".ddev" / "config.yaml"
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
                docroot = config.get("docroot", "public")

                wp_config = Path(config_path).parent.parent / docroot / "wp-config.php"

                prefix = extract_table_prefix(wp_config, docroot, project_path)

                get_admins_sql = (
                    f"SELECT user_id FROM {prefix}usermeta "
                    f"WHERE meta_key = '{prefix}capabilities' AND meta_value LIKE '%administrator%';"
                )

            result = subprocess.run(
                [DDEV_COMMAND, "exec", "bash", "-c",
                 f'wp --path={docroot} db query "{get_admins_sql}" --skip-column-names'],
                cwd=project_path,
                encoding="utf-8",
                capture_output=True,
                text=True,
                check=True
            )

            user_ids = [line.strip() for line in result.stdout.splitlines() if line.strip().isdigit()]

            if not user_ids:
                messagebox.showinfo("Info", "No administrator users found.")
                return

            for idx, uid in enumerate(user_ids):
                login = "admin" if idx == 0 else f"admin{idx}"
                self.update_admin_user_sql(uid, login)

            messagebox.showinfo("Success", f"Updated {len(user_ids)} admin users.")

        except Exception as e:
            messagebox.showerror("Error", str(e))


    def update_admin_user_sql(self, uid, login):
        if not self.selected_project:
            messagebox.showerror("Error", "No project selected.")
            return

        try:
            project_path = PROJECTS_DIR / self.selected_project
            config_path = project_path / ".ddev" / "config.yaml"

            if not config_path.exists():
                raise FileNotFoundError(f"{config_path} not found")

            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            docroot = config.get("docroot", "public")

            wp_config = Path(config_path).parent.parent / docroot / "wp-config.php"

            prefix = extract_table_prefix(wp_config, docroot, project_path)

            password_hash = "$P$Bk60b9sSLvYMTmfLn0njbnRavY8.6U0"

            with tempfile.NamedTemporaryFile(
                mode='w', delete=False, suffix=".sql", dir=project_path
            ) as sql_file:
                sql_file.write(
                    f"UPDATE {prefix}users SET user_login = '{login}', "
                    f"user_pass = '{password_hash}' WHERE ID = {uid};"
                )
                sql_filename = sql_file.name

            filename_in_container = f"/var/www/html/{Path(sql_filename).name}"

            bash_command = f"wp --path={docroot} db query < {filename_in_container}"

            subprocess.run(
                [DDEV_COMMAND, "exec", "bash", "-c", bash_command],
                cwd=project_path,
                check=True
            )

            Path(sql_filename).unlink()

            print(f"Updated user ID {uid} to {login}")

        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Command failed:\n{e.stderr}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def setup_environment(self):
        if not self.selected_project:
            messagebox.showerror("Error", "No project selected.")
            return

        project_path = PROJECTS_DIR / self.selected_project
        config_path = project_path / ".ddev" / "config.yaml"
        with open(config_path, "r") as f:
             config = yaml.safe_load(f)
             docroot = config.get("docroot", "public")
        container_docroot = f"/var/www/html/{docroot}"

        smtp_plugins = [
            "wp-mail-smtp", "wp-mail-smtp-pro" , "post-smtp", "easy-wp-smtp", "smtp-mailer", "gmail-smtp",
            "sendinblue", "mailgun", "pepipost-smtp", "mailjet", "smtp-settings"
        ]

        other_plugins = [
            "akismet", "hello-dolly", "hello"
        ]

        migration_plugin = "all-in-one-wp-migration"
        setup_lines = []

        for plugin in smtp_plugins:
            setup_lines.append(f'''
            cd {container_docroot} || exit 1
            if wp plugin is-installed {plugin}; then
                if wp plugin is-active {plugin}; then
                    wp plugin deactivate {plugin};
                fi
                wp plugin delete {plugin};
            fi
            ''')

        for plugin in other_plugins:
            setup_lines.append(f'''
            wp plugin delete {plugin};
            ''')

        setup_lines.append(f'''
        if ! wp plugin is-installed {migration_plugin}; then
            wp plugin install {migration_plugin} --activate;
        elif ! wp plugin is-active {migration_plugin}; then
            wp plugin activate {migration_plugin};
        fi
        wp rewrite flush --hard;
        ''')

        setup_script = "\n".join(setup_lines)

        try:
            subprocess.run(
                ["ddev", "exec", "bash", "-c", setup_script],
                cwd=project_path,
                check=True
            )
            messagebox.showinfo("Setup Complete", f"Environment setup completed for {self.selected_project}.")

        except subprocess.CalledProcessError as e:
            messagebox.showerror("Setup Failed", f"Error setting up environment: {e}")

    def open_terminal_ssh(self):
        if not self.selected_project:
            messagebox.showerror("Error", "No project selected.")
            return

        project_path = PROJECTS_DIR / self.selected_project

        if platform.system() == "Windows":
            command = f'start cmd.exe /K "cd /d {project_path} && ddev ssh"'
            os.system(command)

        elif platform.system() == "Darwin":
            script = f'''
            tell application "Terminal"
                do script "cd {project_path} && ddev ssh"
                activate
            end tell
            '''
            subprocess.run(["osascript", "-e", script])

        else:
            terminals = ["gnome-terminal", "konsole", "x-terminal-emulator", "xterm", "xfce4-terminal"]
            for term in terminals:
                if shutil.which(term):
                    subprocess.Popen([term, "-e", f'bash -c "cd \\"{project_path}\\" && ddev ssh; exec bash"'])
                    return
            messagebox.showerror("Error", "No supported terminal emulator found.")

    def delete_project(self):
        if self.selected_project:
            confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {self.selected_project}?")
            if confirm:
                project_path = PROJECTS_DIR / self.selected_project
                subprocess.run(
                    ["ddev", "delete", "-Oy"],
                    cwd=project_path,
                    encoding="utf-8",
                    capture_output=True,
                    text=True
                )
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
            db_file = filedialog.askopenfilename(
                title="Select a SQL Dump File",
                filetypes=[
                    ("SQL files", "*.sql"),
                    ("GZipped SQL files", "*.sql.gz"),
                    ("Gzipped SQL (alt)", "*.sql.gzip"),
                    ("ZIP archives", "*.zip"),
                    ("All supported", ("*.sql", "*.sql.gz", "*.sql.gzip", "*.zip")),
                    ("All files", "*.*")
                ]
            )
            if db_file:
                self.run_ddev_command(self.selected_project, ["import-db", "--file", db_file])

    def export_db(self):
        if self.selected_project:
            export_path = filedialog.asksaveasfilename(title="Save exported SQL as", defaultextension=".sql")
            if export_path:
                self.run_ddev_command(self.selected_project, ["export-db", "--file", export_path])

    def enable_xdebug(self, mode):

        if not self.selected_project:
            messagebox.showerror("Error", "No project selected.")
            return

        try:
            project_path = PROJECTS_DIR / self.selected_project
            php_config_dir = project_path / ".ddev" / "php"
            php_ini_file = php_config_dir / "php.ini"
            ini_exists = os.path.isfile(php_ini_file)
            needs_restart = False

            if ini_exists:
                with open(php_ini_file, "r") as file:
                    lines = file.readlines()

                found_mode_line = False
                updated_lines = []

                for line in lines:
                    if line.strip().startswith("xdebug.mode"):
                        found_mode_line = True
                        current_mode = line.strip().split("=")[1].strip()
                        if current_mode != mode:
                            updated_lines.append(f"xdebug.mode={mode}\n")
                            needs_restart = True
                        else:
                            updated_lines.append(line)
                    else:
                        updated_lines.append(line)

                if not found_mode_line:
                    updated_lines.append(f"xdebug.mode={mode}\n")
                    needs_restart = True

                with open(php_ini_file, "w") as file:
                    file.writelines(updated_lines)

            else:
                os.makedirs(os.path.dirname(php_ini_file), exist_ok=True)
                with open(php_ini_file, "w") as file:
                    file.write(f"xdebug.mode={mode}\n")
                needs_restart = True

            if needs_restart:
                subprocess.run([DDEV_COMMAND, "restart", self.selected_project], cwd=project_path, check=True)

            subprocess.run([DDEV_COMMAND, "xdebug", "on"], cwd=project_path, check=True)

            messagebox.showinfo("Success", f"Xdebug '{mode}' mode set and enabled.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to set Xdebug mode: {e}")

    def ask_project_settings(self):
        settings = load_defaults()

        result = {"php": None, "db": None, "web": None}

        settings_win = tk.Toplevel(self.root)
        settings_win.title("Project Settings")
        settings_win.grab_set()

        php_version_var = tk.StringVar(value=settings.get("php_version", PHP_VERSIONS[0]))
        db_version_var = tk.StringVar(value=settings.get("db_version", DB_VERSIONS[0]))
        webserver_var = tk.StringVar(value=settings.get("webserver", WEBSERVERS[0]))

        tk.Label(settings_win, text="PHP Version:").pack()
        ttk.Combobox(settings_win, textvariable=php_version_var, values=PHP_VERSIONS).pack()

        tk.Label(settings_win, text="Database:").pack()
        ttk.Combobox(settings_win, textvariable=db_version_var, values=DB_VERSIONS).pack()

        tk.Label(settings_win, text="Webserver:").pack()
        ttk.Combobox(settings_win, textvariable=webserver_var, values=WEBSERVERS).pack()

        def on_submit():
            result["php"] = php_version_var.get()
            result["db"] = db_version_var.get()
            result["web"] = webserver_var.get()
            save_defaults(result["php"], result["db"], result["web"])
            settings_win.destroy()

        submit_btn = tk.Button(settings_win, text="OK", command=on_submit)
        submit_btn.pack(pady=10)

        self.root.wait_window(settings_win)

        if None in result.values():
            return None  # User closed the window or didn't submit

        return result["php"], result["db"], result["web"]

    def create_new_project(self):
        name = simpledialog.askstring("New Project", "Enter project name:")
        if name:
            php_version, db_version, webserver_type = self.ask_project_settings()
            path = PROJECTS_DIR / name
            path.mkdir(parents=True, exist_ok=True)
            subprocess.run([DDEV_COMMAND, "config", "--project-name", name, "--docroot", "public",
                            "--project-type", "php", "--php-version", php_version, "--database", db_version, "--webserver-type", webserver_type], cwd=path)
            config_file = path / ".ddev" / "config.yaml"
            subprocess.run([
                    DDEV_COMMAND, "add-on", "get", "ddev/ddev-adminer"
            ], cwd=path)
            if config_file.exists():
                with open(config_file, "r") as f:
                    config = yaml.safe_load(f)
                config["disable_settings_management"] = True
                with open(config_file, "w") as f:
                    yaml.safe_dump(config, f)

        project_path = path
        php_config_dir = project_path / ".ddev" / "php"
        php_ini_file = php_config_dir / "php.ini"
        profiler_dir = project_path / "profiler"
        profiler_dir.mkdir(parents=True, exist_ok=True)

        try:
            php_config_dir.mkdir(parents=True, exist_ok=True)
            output_dir = "/var/www/html/profiler/"
            php_ini_content = (
                "[PHP]\n"
                "upload_max_filesize = 4084M\n"
                "post_max_size = 4084M\n"
                "memory_limit = 256M\n"
                f"xdebug.mode=debug\n"
                "xdebug.start_with_request=yes\n"
                "xdebug.use_compression=false\n"
                "xdebug.profiler_output_name=profiler.%H.%R.%t.out\n"
                f"xdebug.output_dir=\"{output_dir}\"\n"
            )

            with open(php_ini_file, "w") as f:
                f.write(php_ini_content)

            subprocess.run([DDEV_COMMAND, "start"], cwd=path)
            self.refresh_projects()
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {e}")
            self.refresh_projects()

        import base64

        transparent_png_base64 = (
            b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAKbNPioAAAAASUVORK5CYII='
        )

        try:
            placeholder_path = path / "public" / "placeholder.png"
            placeholder_path.parent.mkdir(parents=True, exist_ok=True)
            with open(placeholder_path, "wb") as img_file:
                img_file.write(base64.b64decode(transparent_png_base64))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create placeholder.png: {e}")

        htaccess_path = path / "public" / ".htaccess"

        custom_rules = (
            "<IfModule mod_rewrite.c>\n"
            "RewriteEngine On\n"
            "RewriteCond %{REQUEST_FILENAME} !-f\n"
            "RewriteRule \\.(jpe?g|png|gif|webp|bmp|svg|ico)$ /placeholder.png [L]\n"
            "</IfModule>\n\n"
            "# BEGIN WordPress\n\n"
            "<IfModule mod_rewrite.c>\n"
            "RewriteEngine On\n"
            "RewriteRule .* - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]\n"
            "RewriteBase /\n"
            "RewriteRule ^index\.php$ - [L]\n"
            "RewriteCond %{REQUEST_FILENAME} !-f\n"
            "RewriteCond %{REQUEST_FILENAME} !-d\n"
            "RewriteRule . /index.php [L]\n"
            "</IfModule>\n\n"
            "# END WordPress\n"
        )

        try:
            if htaccess_path.exists():
                with open(htaccess_path, "r") as f:
                    original_contents = f.read()
            else:
                original_contents = ""

            with open(htaccess_path, "w") as f:
                f.write(custom_rules + original_contents)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to modify .htaccess: {e}")

    def create_wordpress_project(self):
        name = simpledialog.askstring("New WordPress Project", "Enter project name:")
        if name:
            php_version, db_version, webserver_type = self.ask_project_settings()
            path = PROJECTS_DIR / name
            path.mkdir(parents=True, exist_ok=True)
            subprocess.run([DDEV_COMMAND, "config", "--project-name", name, "--project-type", "wordpress", "--docroot", "web",
                            "--php-version", php_version, "--database", db_version, "--webserver-type", webserver_type], cwd=path)
            config_file = path / ".ddev" / "config.yaml"
            subprocess.run([
                    DDEV_COMMAND, "add-on", "get", "ddev/ddev-adminer"
            ], cwd=path)
            if config_file.exists():
                with open(config_file, "r") as f:
                    config = yaml.safe_load(f)
                config["disable_settings_management"] = True
                with open(config_file, "w") as f:
                    yaml.safe_dump(config, f)
                    project_path = path
        php_config_dir = project_path / ".ddev" / "php"
        php_ini_file = php_config_dir / "php.ini"
        profiler_dir = project_path / "profiler"
        profiler_dir.mkdir(parents=True, exist_ok=True)

        try:
            php_config_dir.mkdir(parents=True, exist_ok=True)
            output_dir = "/var/www/html/profiler/"
            php_ini_content = (
                "[PHP]\n"
                "upload_max_filesize = 4084M\n"
                "post_max_size = 4084M\n"
                "memory_limit = 256M\n"
                f"xdebug.mode=debug\n"
                "xdebug.start_with_request=yes\n"
                "xdebug.use_compression=false\n"
                "xdebug.profiler_output_name=profiler.%H.%R.%t.out\n"
                f"xdebug.output_dir=\"{output_dir}\"\n"
            )

            with open(php_ini_file, "w") as f:
                f.write(php_ini_content)

            subprocess.run([DDEV_COMMAND, "start"], cwd=path)
            subprocess.run([DDEV_COMMAND, "wp", "--path=web", "core", "download"], cwd=path)
            subprocess.run([DDEV_COMMAND, "wp", "--path=web", "core", "install", "--url=http://{}.ddev.site".format(name),
                            "--title=WordPress Site", "--admin_user=admin", "--admin_password=admin", "--admin_email=admin@example.com"], cwd=path)
            wp_config = path / "web" / "wp-config.php"

        except Exception as e:
            messagebox.showerror("Error", f"Failed: {e}")


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

        import base64

        transparent_png_base64 = (
            b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAKbNPioAAAAASUVORK5CYII='
        )

        try:
            placeholder_path = path / "web" / "placeholder.png"
            placeholder_path.parent.mkdir(parents=True, exist_ok=True)
            with open(placeholder_path, "wb") as img_file:
                img_file.write(base64.b64decode(transparent_png_base64))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create placeholder.png: {e}")

        htaccess_path = path / "web" / ".htaccess"

        custom_rules = (
            "<IfModule mod_rewrite.c>\n"
            "RewriteEngine On\n"
            "RewriteCond %{REQUEST_FILENAME} !-f\n"
            "RewriteRule \\.(jpe?g|png|gif|webp|bmp|svg|ico)$ /placeholder.png [L]\n"
            "</IfModule>\n\n"
            "# BEGIN WordPress\n\n"
            "<IfModule mod_rewrite.c>\n"
            "RewriteEngine On\n"
            "RewriteRule .* - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]\n"
            "RewriteBase /\n"
            "RewriteRule ^index\.php$ - [L]\n"
            "RewriteCond %{REQUEST_FILENAME} !-f\n"
            "RewriteCond %{REQUEST_FILENAME} !-d\n"
            "RewriteRule . /index.php [L]\n"
            "</IfModule>\n\n"
            "# END WordPress\n"
        )

        try:
            if htaccess_path.exists():
                with open(htaccess_path, "r") as f:
                    original_contents = f.read()
            else:
                original_contents = ""

            with open(htaccess_path, "w") as f:
                f.write(custom_rules + original_contents)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to modify .htaccess: {e}")

        self.refresh_projects()

    def install_wordpress_core(self):
        if not self.selected_project:
            messagebox.showerror("Error", "No project selected.")
            return

        try:
            project_path = PROJECTS_DIR / self.selected_project
            config_path = project_path / ".ddev" / "config.yaml"

            if not config_path.exists():
                raise FileNotFoundError(f"{config_path} not found")

            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            docroot = config.get("docroot", "web")
            wp_path = project_path / docroot

            subprocess.run(
                [DDEV_COMMAND, "exec", "bash", "-c",
                 f"wp --path={docroot} core download"],
                cwd=project_path, check=True
            )

            subprocess.run(
                [DDEV_COMMAND, "exec", "bash", "-c",
                 f"wp --path={docroot} core config --dbhost=db --dbname=db --dbuser=db --dbpass=db"],
                cwd=project_path, check=True
            )

            subprocess.run(
                [DDEV_COMMAND, "exec", "bash", "-c",
                 f"wp --path={docroot} core install --url=https://{self.selected_project}.ddev.site "
                 "--title='Installed WordPress' --admin_user=admin --admin_password=admin --admin_email=admin@admin.com"],
                cwd=project_path, check=True
            )

            messagebox.showinfo("Success", "WordPress installed successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to install WordPress: {e}")

    def add_vhost(self):
        import json, re, subprocess, tkinter as tk
        from tkinter import messagebox, ttk

        if not self.selected_project:
            messagebox.showerror("Error", "No project selected.")
            return

        DDEV_DOMAIN_SUFFIX = ".ddev.site"
        VALID = re.compile(r"^[a-z0-9][a-z0-9\-\.]*[a-z0-9]$", re.IGNORECASE)

        def normalize_one(h):
            h = (h or "").strip().lower()
            if not h:
                return None
            if h.endswith(DDEV_DOMAIN_SUFFIX):
                h = h[: -len(DDEV_DOMAIN_SUFFIX)]
            if "/" in h or " " in h:
                return None
            if h.startswith("."):
                h = h[1:]
            if h.endswith("."):
                h = h[:-1]
            return h if h and VALID.match(h) else None

        def normalize_many(items):
            out, seen, errs = [], set(), []
            for it in items:
                v = normalize_one(it)
                if v is None:
                    errs.append(f"Invalid: {it!r}")
                elif v not in seen:
                    out.append(v); seen.add(v)
            return out, errs

        def split_multi(s):
            return [p.strip() for p in s.replace(",", "\n").splitlines() if p.strip()]

        project_path = PROJECTS_DIR / self.selected_project

        # Read current hostnames from `ddev describe -j`
        try:
            p = subprocess.run(
                [DDEV_COMMAND, "describe", "-j"],
                cwd=str(project_path),
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=True,
            )
            out = (p.stdout or "") + "\n" + (p.stderr or "")
            j = json.loads(out)
            r = j.get("raw") or {}

            # FQDNs from ddev. First is primary; also available as r["hostname"].
            fqdn_list = r.get("hostnames") or []
            if not fqdn_list and r.get("hostname"):
                fqdn_list = [r["hostname"]]
            if not fqdn_list:
                raise RuntimeError("No hostnames found in ddev JSON.")

            # Normalize to base names (strip .ddev.site etc.)
            primary = normalize_one(r.get("hostname") or fqdn_list[0])
            bases = [normalize_one(x) for x in fqdn_list if normalize_one(x)]

            # Additional only (exclude primary). Use `current` downstream for the listbox.
            current, _errs = normalize_many([b for b in bases if b != primary])

        except Exception as e:
            messagebox.showerror("Error", f"Failed to read hostnames via `ddev describe -j`: {e}")
            return

        # Modal dialog
        parent = getattr(self, "root", None) or tk._get_default_root()
        dlg = tk.Toplevel(parent)
        dlg.title("Edit ddev vhosts")
        dlg.transient(parent)
        dlg.grab_set()

        ttk.Label(dlg, text="Configured vhosts (without .ddev.site):").grid(row=0, column=0, columnspan=3, sticky="w", padx=8, pady=(8,4))

        lb = tk.Listbox(dlg, selectmode=tk.EXTENDED, height=12)
        lb.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=8)
        for h in sorted(set(current)):
            lb.insert(tk.END, h)

        ttk.Label(dlg, text="Add hostnames (comma or newline separated):").grid(row=2, column=0, columnspan=2, sticky="w", padx=8, pady=(10,2))
        add_text = tk.Text(dlg, height=3, width=40)
        add_text.grid(row=3, column=0, columnspan=2, sticky="ew", padx=8)

        def on_add():
            raw = add_text.get("1.0", "end").strip()
            if not raw:
                return
            cleaned, errs = normalize_many(split_multi(raw))
            if errs:
                messagebox.showerror("Invalid entries", "\n".join(errs), parent=dlg); return
            existing = {lb.get(i) for i in range(lb.size())}
            for h in cleaned:
                if h not in existing:
                    lb.insert(tk.END, h)
            add_text.delete("1.0", "end")

        def on_remove():
            sel = list(lb.curselection())
            for idx in reversed(sel):
                lb.delete(idx)

        ttk.Button(dlg, text="Add", command=on_add).grid(row=3, column=2, sticky="e", padx=(0,8))
        ttk.Button(dlg, text="Remove selected", command=on_remove).grid(row=4, column=2, sticky="e", padx=(0,8), pady=(8,0))

        btns = ttk.Frame(dlg); btns.grid(row=5, column=0, columnspan=3, sticky="e", padx=8, pady=8)
        result = {"ok": False}
        def on_ok():
            items = [lb.get(i) for i in range(lb.size())]
            cleaned, errs = normalize_many(items)
            if errs:
                messagebox.showerror("Invalid entries", "\n".join(errs), parent=dlg); return
            result["list"] = cleaned; result["ok"] = True
            dlg.destroy()
        def on_cancel():
            dlg.destroy()
        ttk.Button(btns, text="Cancel", command=on_cancel).pack(side="right", padx=(0,6))
        ttk.Button(btns, text="OK", command=on_ok).pack(side="right")

        dlg.columnconfigure(0, weight=1); dlg.columnconfigure(1, weight=1)
        dlg.rowconfigure(1, weight=1)
        dlg.wait_window()

        if not result.get("ok"):
            return

        new_hosts = result.get("list", [])
        if sorted(new_hosts) == sorted(current):
            messagebox.showinfo("No changes", "No updates to additional_hostnames.")
            return

        try:
            args = [
                DDEV_COMMAND, "config", "--auto",
                "--additional-hostnames", ",".join(new_hosts) if new_hosts else "",
            ]
            subprocess.run(args, cwd=project_path, check=True)
            subprocess.run([DDEV_COMMAND, "restart"], cwd=project_path, check=True)
            shown = "\n".join(f"- {h}{DDEV_DOMAIN_SUFFIX}" for h in new_hosts)
            messagebox.showinfo("Success", f"Updated additional_hostnames:\n{shown}")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"ddev failed: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update vhosts: {e}")

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

def load_defaults():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULTS.copy()

def save_defaults(php_version, db_version, webserver):
    data = {
        "php_version": php_version,
        "db_version": db_version,
        "webserver": webserver
    }
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        print(f"Error saving config: {e}")

if __name__ == "__main__":
    PROJECTS_DIR.mkdir(exist_ok=True)
    root = tk.Tk()
    app = DDEVManagerGUI(root)
    root.mainloop()

