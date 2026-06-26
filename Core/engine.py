import os
import json
import time
import shutil
import hashlib
import subprocess

from .state import ProjectState


class ProjectCreationEngine:
    def __init__(self, base_path, event_bus):
        self.base_path = base_path
        self.event_bus = event_bus
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

            self.state = ProjectState.COMPLETE
            self.emit("project_created")

            return {"status": "ok"}

        except Exception as e:
            self.state = ProjectState.FAILED
            self.emit("project_failed", {"error": str(e)})
            return {"status": "error", "error": str(e)}

    # -----------------------
    def validate(self):
        self.state = ProjectState.VALIDATE

        name = self.context["project_name"]
        path = os.path.join(self.base_path, name)

        if os.path.exists(path):
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
        tmp = path + "_tmp"

        os.makedirs(self.base_path, exist_ok=True)

        if os.path.exists(tmp):
            shutil.rmtree(tmp)

        os.makedirs(tmp)

        with open(os.path.join(tmp, "project.ris.json"), "w", encoding="utf-8") as f:
            json.dump(self.ris, f, indent=2)

        os.makedirs(os.path.join(tmp, "src"))
        os.makedirs(os.path.join(tmp, "assets"))
        os.makedirs(os.path.join(tmp, "logs"))
        os.makedirs(os.path.join(tmp, "output"))
        self._write_git_support_files(tmp)

        os.rename(tmp, path)
        self._initialize_git_repository(path)

        self.emit("filesystem_written")

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