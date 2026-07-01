import os

from .engine import ProjectCreationEngine
from .event_bus import EventBus
from .event_store import SQLiteEventStore


def create_runtime(base_path="user/Max/Projects"):
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    folder_list_path = os.path.join(repo_root, "ViewController", "0-MainUI", "ProjectFolderList.txt")

    store = SQLiteEventStore()
    bus = EventBus(store=store)
    engine = ProjectCreationEngine(base_path, bus, folder_list_path=folder_list_path)

    return engine, bus, store