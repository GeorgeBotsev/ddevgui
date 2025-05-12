## ⚙️ DDEV Manager GUI

A cross-platform desktop GUI for managing [DDEV](https://ddev.readthedocs.io/) web development environments — built with Python and Tkinter.

---

### 🧰 Project Management

- Auto-detects all DDEV projects in your `websites/` directory.
- Create:
  - New **blank** PHP projects
  - New **WordPress** projects (with auto-install + admin setup)
- Delete projects (with folder cleanup and confirmation).
- Periodically refreshes the project list automatically.

---

### 🚀 Project Controls

- One-click **Start** / **Stop** for selected projects.
- Launch project in **browser**, **Adminer**, or **Mailpit**.
- Execute project-specific commands via DDEV CLI.

---

### 🛠️ Configuration & Debugging

- GUI prompts for:
  - PHP version (5.6 to 8.4)
  - MariaDB / MySQL version
  - Webserver type (Apache-FPM, Nginx-FPM, Generic)
- Enable **Xdebug** in:
  - Debug mode
  - Profile mode
- Automatically configures `.ddev/php/php.ini`.

---

### 🗃️ Database Utilities

- **Import SQL dumps** into selected project.
- **Export database** to `.sql` file.

---

### 📦 WordPress Support

- Installs WordPress using WP-CLI with:
  - URL: `http://<project>.ddev.site`
  - Admin login: `admin / admin`
- Enables WP_DEBUG, Redis support.
- Configures `wp-config.php` automatically.
- Adds Adminer support.

---

### ➕ Addons & Services

- Add **custom vhost domains** (e.g., `sub.example.ddev.site`).
- Enable **Redis** or **Memcached** with one click:
  - Generates `docker-compose` service files
  - Automatically restarts project

---

### ✅ Cross-Platform

- Works on Windows and Linux (Python + Tkinter).
- Designed for simplicity and dev-focused workflows.

---

## 📦 Requirements

- Python 3.x
- `tkinter`
- `yaml`
- [DDEV CLI](https://ddev.readthedocs.io/en/stable/)

---

## 📸 Screenshot

> *(Insert screenshot here)*

---

## 🧪 License

MIT License
