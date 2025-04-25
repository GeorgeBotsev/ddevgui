import os
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from pathlib import Path
import platform

# Constants
PROJECTS_DIR = Path(__file__).resolve().parent / "websites"
REFRESH_INTERVAL = 5000  # in milliseconds
DDEV_COMMAND = "ddev"
if platform.system() == "Windows":
    DDEV_COMMAND = "C:\\Program Files\\ddev\\ddev.exe"  # Adjust this path if needed

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
        if self.selected_project:
            self.run_ddev_command(self.selected_project, ["xdebug", "on"])
            config_file = PROJECTS_DIR / self.selected_project / ".ddev" / "php" / "php.ini"
            config_file.parent.mkdir(parents=True, exist_ok=True)
            output_dir = "/var/www/html/.ddev/"
            mode_line = (
                f"[PHP]\n"
                f"xdebug.mode={mode}\n"
                f"xdebug.start_with_request=yes\n"
                f"xdebug.use_compression=false"
                f"xdebug.profiler_output_name=trace.%c%p%r%u.out\n"
                f"xdebug.output_dir=\"{output_dir}\"\n"
            )
            try:
                with open(config_file, "w") as f:
                    f.write(mode_line)
                self.run_ddev_command(self.selected_project, ["restart"])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to write xdebug config: {e}")

    def create_new_project(self):
        name = simpledialog.askstring("New Project", "Enter project name:")
        if name:
            path = PROJECTS_DIR / name
            path.mkdir(parents=True, exist_ok=True)
            subprocess.run([DDEV_COMMAND, "config", "--project-name", name, "--docroot", "public", "--create-docroot", "--project-type", "php"], cwd=path)
            self.refresh_projects()

    def create_wordpress_project(self):
        name = simpledialog.askstring("New WordPress Project", "Enter project name:")
        if name:
            path = PROJECTS_DIR / name
            path.mkdir(parents=True, exist_ok=True)
            subprocess.run([DDEV_COMMAND, "config", "--project-name", name, "--project-type", "wordpress", "--docroot", "web", "--create-docroot"], cwd=path)
            subprocess.run([DDEV_COMMAND, "start"], cwd=path)
            subprocess.run([DDEV_COMMAND, "wp", "--path=web" , "core", "download"], cwd=path)
            subprocess.run([DDEV_COMMAND, "wp", "--path=web" , "core", "install", "--url=http://{}".format(name + ".ddev.site"),
                            "--title=WordPress Site", "--admin_user=admin", "--admin_password=admin", "--admin_email=admin@example.com"], cwd=path)
            wp_config = path / "web" / "wp-config.php"
            try:
                with open(wp_config, "a") as f:
                    f.write("define('WP_DEBUG_LOG', true);\n")
                messagebox.showinfo("Success", "WordPress project created and configured.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to modify wp-config.php: {e}")
            self.refresh_projects()

if __name__ == "__main__":
    PROJECTS_DIR.mkdir(exist_ok=True)
    root = tk.Tk()
    app = DDEVManagerGUI(root)
    root.mainloop()
