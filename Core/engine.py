import os
import json
import time
import shutil
import hashlib
import subprocess
import tempfile

from .state import ProjectState


class ProjectCreationEngine:
    DEFAULT_PROJECT_FOLDERS = [
        "src",
        "src/manifests",
        "assets",
        "assets/source",
        "assets/images",
        "assets/references",
        "logs",
        "logs/events",
        "logs/processing",
        "output",
        "output/ocr",
        "output/corrected",
        "output/exports",
    ]

    REQUIRED_TEMPLATE_FILES = [
        "ViewController/0-MainUI/HelpSystem.py",
        "ViewController/0-MainUI/SessionManager.py",
    ]

    def __init__(self, base_path, event_bus, folder_list_path=None):
        self.base_path = base_path
        self.event_bus = event_bus
        self.folder_list_path = folder_list_path
        self.state = ProjectState.INIT
        self.context = {}
        self.ris = None

    # -----------------------
    def emit(self, name, meta=None):
        event = {
            "event": name,
            "timestamp": time.time(),
            "state": self.state.value,
            "project_name": self.context.get("project_name"),
            "metadata": meta or {}
        }

        self.event_bus.emit(event)
        return event

    # -----------------------
    def create_project(self, payload):
        try:
            self.context = payload
            self.validate()
            self.capture_provenance()
            self.generate_ris()
            self.write()
            self.register_project()

            self.state = ProjectState.COMPLETE
            self.emit("project_created")

            return {
                "status": "ok",
                "project": self.context.get("project_name"),
                "path": os.path.join(self.base_path, self.context.get("project_name")),
            }

        except Exception as e:
            self.rollback()
            self.state = ProjectState.FAILED
            self.emit("project_failed", {"error": str(e)})
            return {"status": "error", "error": str(e)}

    # -----------------------
    def validate(self):
        self.state = ProjectState.VALIDATE

        name = self.context["project_name"]
        path = os.path.join(self.base_path, name)
        overwrite_existing = bool(self.context.get("overwrite_existing"))

        if os.path.exists(path):
            if overwrite_existing:
                shutil.rmtree(path)
                self.emit("existing_project_removed", {"path": path})
            else:
                raise ValueError("Project exists")

        self.emit("validation_passed")

    # -----------------------
    def capture_provenance(self):
        self.state = ProjectState.PROVENANCE

        required = [
            "project_name",
            "project_purpose",
            "creation_trigger",
            "source_context",
            "user_intent_summary"
        ]

        for r in required:
            if r not in self.context:
                raise ValueError(f"Missing {r}")

        self.ris = self.context.copy()
        self.ris["_locked"] = True

        self.emit("provenance_captured")

    # -----------------------
    def generate_ris(self):
        self.state = ProjectState.RIS

        self.ris["ris_version"] = "1.1"
        self.ris["timestamp"] = time.time()

        self.ris["_hash"] = hashlib.sha256(
            json.dumps(self.ris, sort_keys=True).encode()
        ).hexdigest()

        self.emit("ris_generated")

    # -----------------------
    def write(self):
        self.state = ProjectState.WRITE

        name = self.context["project_name"]
        path = os.path.join(self.base_path, name)
        tmp = tempfile.mkdtemp(prefix=f"{name}_tmp_", dir=self.base_path)
        self.context["_tmp_path"] = tmp

        os.makedirs(self.base_path, exist_ok=True)

        with open(os.path.join(tmp, "project.ris.json"), "w", encoding="utf-8") as f:
            json.dump(self.ris, f, indent=2)

        self._create_project_structure(tmp)
        self._write_git_support_files(tmp)

        os.rename(tmp, path)
        self._initialize_git_repository(path)

        self.emit("filesystem_written")

    # -----------------------
    def register_project(self):
        registry_path = os.path.join(self.base_path, "_registry.json")
        registry = []

        if os.path.exists(registry_path):
            with open(registry_path, "r", encoding="utf-8-sig") as f:
                registry = json.load(f)
            if isinstance(registry, dict):
                registry = [registry]
            elif not isinstance(registry, list):
                registry = []

        project_name = self.context["project_name"]
        project_path = os.path.join(self.base_path, project_name)
        registry = [
            item for item in registry
            if item.get("project_name") != project_name
        ]
        registry.append({
            "project_name": project_name,
            "timestamp": time.time(),
            "path": project_path,
            "git_repository": True,
        })

        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2)

        self.emit("project_registered", {"registry_path": registry_path})

    # -----------------------
    def rollback(self):
        project_name = self.context.get("project_name")
        if not project_name:
            return

        project_path = os.path.join(self.base_path, project_name)
        tmp_path = self.context.get("_tmp_path") or (project_path + "_tmp")
        removed = []
        removal_errors = []
        for path in (tmp_path, project_path):
            if os.path.exists(path):
                try:
                    shutil.rmtree(path)
                    removed.append(path)
                except OSError as exc:
                    removal_errors.append({"path": path, "error": str(exc)})

        if removed:
            self.emit("rollback_complete", {"removed": removed})
        if removal_errors:
            self.emit("rollback_cleanup_failed", {"errors": removal_errors})

    # -----------------------
    def _create_project_structure(self, project_path):
        folders = set(self.DEFAULT_PROJECT_FOLDERS)
        files = set(self.REQUIRED_TEMPLATE_FILES)
        folder_list_path = self._resolve_folder_list_path()
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

        if folder_list_path:
            for entry in self._read_folder_list_entries(folder_list_path):
                normalized = self._normalize_structure_entry(entry, folder_list_path)
                if normalized:
                    if self._is_file_structure_entry(normalized, folder_list_path):
                        files.add(normalized)
                    else:
                        folders.add(normalized)

        sorted_folders = sorted(folders)
        sorted_files = sorted(files)
        total_file_bytes = self._calculate_total_structure_bytes(repo_root, sorted_files)
        copied_file_bytes = 0
        total_steps = len(sorted_folders) + len(sorted_files) + 1
        if folder_list_path:
            total_steps += 1
        completed_steps = 0

        self._emit_structure_progress(
            stage="starting",
            completed=completed_steps,
            total=total_steps,
        )

        for folder in sorted_folders:
            _source_folder, destination_folder = self._split_structure_copy_entry(folder)
            folder_path = destination_folder or folder
            os.makedirs(os.path.join(project_path, *folder_path.split("/")), exist_ok=True)
            completed_steps += 1
            self._emit_structure_progress(
                stage="folders",
                completed=completed_steps,
                total=total_steps,
                path=folder_path,
            )

        for file_path in sorted_files:
            file_size = self._create_file_from_template(

                project_path,
                file_path,
                copied_file_bytes,
                total_file_bytes,
            )
            copied_file_bytes += file_size
            completed_steps += 1
            self._emit_structure_progress(
                stage="files",
                completed=completed_steps,
                total=total_steps,
                path=file_path,
                bytes_completed=copied_file_bytes,
                bytes_total=total_file_bytes,
            )

        self._customize_generated_project_files(project_path)

        self._write_empty_directory_placeholders(project_path)
        completed_steps += 1
        self._emit_structure_progress(
            stage="placeholders",
            completed=completed_steps,
            total=total_steps,
        )

        if folder_list_path:
            self._copy_structure_manifest(
                project_path,
                folder_list_path,
                len(folders),
                len(files),
            )
            completed_steps += 1
            self._emit_structure_progress(
                stage="manifest",
                completed=completed_steps,
                total=total_steps,
                path=folder_list_path,
            )

        self.emit("project_structure_created", {
            "folder_count": len(folders),
            "file_count": len(files),
            "folder_list_path": folder_list_path,
        })

    # -----------------------
    def _emit_structure_progress(self, stage, completed, total, path=None, bytes_completed=None, bytes_total=None):
        metadata = {
            "stage": stage,
            "completed": completed,
            "total": total,
        }
        if path:
            metadata["path"] = path
        if bytes_completed is not None:
            metadata["bytes_completed"] = bytes_completed
        if bytes_total is not None:
            metadata["bytes_total"] = bytes_total
        self.emit("project_structure_progress", metadata)

    # -----------------------
    def _resolve_folder_list_path(self):
        candidates = []
        if self.folder_list_path:
            candidates.append(self.folder_list_path)

        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        candidates.extend([
            os.path.join(os.getcwd(), "ProjectFolderList.txt"),
            os.path.join(os.getcwd(), "ViewController", "0-MainUI", "ProjectFolderList.txt"),
            os.path.join(repo_root, "ProjectFolderList.txt"),
            os.path.join(repo_root, "ViewController", "0-MainUI", "ProjectFolderList.txt"),
        ])

        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return os.path.abspath(candidate)
        return None

    # -----------------------
    def _read_folder_list_entries(self, folder_list_path):
        with open(folder_list_path, "r", encoding="utf-8-sig") as f:
            return [line.strip() for line in f if line.strip()]

            # -----------------------
    def _normalize_structure_entry(self, entry, folder_list_path):

        normalized = entry.replace("\\", "/").strip()

        if not normalized:
            return None

        source_entry, destination_entry = self._split_structure_copy_entry(normalized)
        source_path = self._normalize_structure_path(source_entry)
        if not source_path:
            return None

        if destination_entry is None:
            return source_path

        destination_path = self._normalize_structure_path(destination_entry)
        if not destination_path:
            return None

        return f"{source_path} => {destination_path}"

    # -----------------------
    def _normalize_structure_path(self, path):
        normalized = path.replace("\\", "/").strip().lstrip("./")
        if not normalized:
            return None

        drive, _ = os.path.splitdrive(normalized)
        if drive or normalized.startswith("/"):
            return None

        parts = [part for part in normalized.split("/") if part]
        if not parts or ".git" in parts:
            return None
        return "/".join(parts)

    # -----------------------
    def _split_structure_copy_entry(self, entry):
        if "=>" not in entry:
            return entry.strip(), None

        source_entry, destination_entry = entry.split("=>", 1)
        source_entry = source_entry.strip()
        destination_entry = destination_entry.strip()
        if not source_entry or not destination_entry:
            return entry.strip(), None
        return source_entry, destination_entry

    # -----------------------
    def _is_file_structure_entry(self, entry, folder_list_path):
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        source_entry, destination_entry = self._split_structure_copy_entry(entry)
        destination_or_source = destination_entry or source_entry
        source_candidate = os.path.join(repo_root, *source_entry.split("/"))

        if os.path.isfile(source_candidate):
            return True
        if os.path.isdir(source_candidate):
            return False

        return bool(os.path.splitext(destination_or_source.rsplit("/", 1)[-1])[1])


    
    
    # -----------------------
    def _create_file_from_template(self, project_path, relative_file_path, bytes_completed_before=0, bytes_total=0):
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

        source_entry, destination_entry = self._split_structure_copy_entry(relative_file_path)
        destination_entry = destination_entry or source_entry
        source_file = os.path.join(repo_root, *source_entry.split("/"))
        destination_file = os.path.join(project_path, *destination_entry.split("/"))
        os.makedirs(os.path.dirname(destination_file), exist_ok=True)

        if os.path.isfile(source_file):
            copied_size = self._copy_file_with_progress(
                source_file,
                destination_file,
                relative_file_path,
                bytes_completed_before,
                bytes_total,
            )
            return copied_size

        with open(destination_file, "w", encoding="utf-8"):
            pass
        return 0

    # -----------------------
    def _calculate_total_structure_bytes(self, repo_root, relative_file_paths):
        total_bytes = 0
        for relative_file_path in relative_file_paths:
            source_entry, _destination_entry = self._split_structure_copy_entry(relative_file_path)
            source_file = os.path.join(repo_root, *source_entry.split("/"))
            if os.path.isfile(source_file):
                total_bytes += os.path.getsize(source_file)
        return total_bytes


    # -----------------------
    def _copy_file_with_progress(self, source_file, destination_file, relative_file_path, bytes_completed_before, bytes_total):
        chunk_size = 1024 * 1024
        file_size = os.path.getsize(source_file)
        bytes_copied = 0

        with open(source_file, "rb") as src, open(destination_file, "wb") as dst:
            while True:
                chunk = src.read(chunk_size)
                if not chunk:
                    break
                dst.write(chunk)
                bytes_copied += len(chunk)
                self._emit_structure_progress(
                    stage="file_copy",
                    completed=0,
                    total=0,
                    path=relative_file_path,
                    bytes_completed=bytes_completed_before + bytes_copied,
                    bytes_total=bytes_total,
                )

        shutil.copystat(source_file, destination_file)
        return file_size

    # -----------------------
    def _write_empty_directory_placeholders(self, project_path):
        for root, dirs, files in os.walk(project_path):
            parts = root.replace(project_path, "", 1).replace("\\", "/").split("/")
            if ".git" in parts:
                continue
            if not dirs and not files:
                keep_path = os.path.join(root, ".gitkeep")
                with open(keep_path, "w", encoding="utf-8"):
                    pass

    # -----------------------
    def _copy_structure_manifest(self, project_path, folder_list_path, folder_count, file_count):
        manifest_dir = os.path.join(project_path, "src", "manifests")
        log_dir = os.path.join(project_path, "logs", "processing")
        os.makedirs(manifest_dir, exist_ok=True)
        os.makedirs(log_dir, exist_ok=True)

        shutil.copyfile(
            folder_list_path,
            os.path.join(manifest_dir, "ProjectFolderList.txt")
        )

        log_path = os.path.join(log_dir, "project_folder_list_structure_rebuild.md")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("# Project Folder Structure Rebuild\n\n")
            f.write("## Source\n\n")
            f.write(f"`{folder_list_path}`\n\n")
            f.write("## Action\n\n")
            f.write("Generated the project folder structure from ProjectFolderList.txt.\n\n")
            f.write("## Notes\n\n")
            f.write("* Directory entries were created directly.\n")
            f.write("* File entries were copied from the repository template when available.\n")
            f.write("* Manifest entries in `source => destination` form were copied from source to destination.\n")
            f.write("* Missing file templates were created as empty placeholders.\n")
            f.write("* Empty directories were given `.gitkeep` placeholders.\n\n")

            f.write("## Folder Count\n\n")
            f.write(f"{folder_count}\n")
            f.write("\n## File Count\n\n")
            f.write(f"{file_count}\n")

    # -----------------------
    def _customize_generated_project_files(self, project_path):
        self._disable_generated_project_creation_action(project_path)

    # -----------------------
    def _disable_generated_project_creation_action(self, project_path):
        mainui_dir = os.path.join(project_path, "ViewController", "0-MainUI")
        myserver_path = os.path.join(mainui_dir, "MyServer.py")

        if os.path.exists(myserver_path):
            with open(myserver_path, "r", encoding="utf-8") as f:
                text = f.read()

            text = text.replace(
                "        self.ui.actionNewProject.setText(\"New Project\")\n"
                "        self.ui.actionNewProject.triggered.connect(self.on_new_project_clicked)\n",
                "        self.ui.actionNewProject.setText(\"New Project\")\n"
                "        self.ui.actionNewProject.setEnabled(False)\n"
                "        self.ui.actionNewProject.setToolTip(\"New project creation is only available from the main BiblionOCR MyServer.\")\n"
                "        self.ui.actionNewProject.setStatusTip(\"New project creation is only available from the main BiblionOCR MyServer.\")\n"
                "        self.ui.actionNewProject.triggered.connect(self.on_new_project_clicked)\n",
            )

            with open(myserver_path, "w", encoding="utf-8") as f:
                f.write(text)

    # -----------------------
    def _write_git_support_files(self, project_path):
        readme_path = os.path.join(project_path, "README.md")
        gitignore_path = os.path.join(project_path, ".gitignore")

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(f"# {self.context['project_name']}\n\n")
            f.write("Local BiblionOCR project repository.\n")

        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write("__pycache__/\n")
            f.write("*.pyc\n")
            f.write("*.tmp\n")
            f.write("*.log\n")
            f.write(".DS_Store\n")
            f.write("Thumbs.db\n")

    # -----------------------
    def _initialize_git_repository(self, project_path):
        git_executable = shutil.which("git")
        if not git_executable:
            raise RuntimeError("Git executable not found; cannot initialize local repository.")

        result = subprocess.run(
            [git_executable, "init"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Git repository initialization failed: {result.stderr.strip()}")

        branch_result = subprocess.run(
            [git_executable, "branch", "-M", "main"],
            cwd=project_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if branch_result.returncode != 0:
            raise RuntimeError(f"Git default branch setup failed: {branch_result.stderr.strip()}")

        self.emit("git_repository_initialized", {"path": project_path})