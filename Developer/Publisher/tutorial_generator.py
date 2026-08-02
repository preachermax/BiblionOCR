from __future__ import annotations

from typing import Callable, Dict, List, Optional

from .application_ui_model import ApplicationModule, ApplicationUIModel
from .tutorial_events import TutorialEvent
from .tutorial_state import TutorialState


class TutorialGenerator:
	"""Drives tutorial progression from launcher-aligned module metadata."""

	def __init__(
		self,
		application_ui_model: ApplicationUIModel,
		launcher_interface_id: str = "MyLauncher",
		module_metadata: Optional[Dict[str, Dict[str, object]]] = None,
	) -> None:
		self.model = application_ui_model
		self.launcher_interface_id = launcher_interface_id
		self.module_metadata = dict(module_metadata or {})

		self.state = TutorialState()
		self._listeners: List[Callable] = []
		self._modules = self._build_sequence()

	def _build_sequence(self) -> List[ApplicationModule]:
		modules: List[ApplicationModule] = []

		launch_targets = self.model.launches(self.launcher_interface_id)
		for module_id in launch_targets:
			module = self.model.get_module(module_id)
			if module is None:
				continue
			modules.append(module)

		modules.sort(key=lambda m: int(self._module_order(m.module_id)))
		return modules

	def _module_order(self, module_id: str) -> int:
		metadata = self.module_metadata.get(module_id, {})
		value = metadata.get("order", 999)
		try:
			return int(value)
		except (TypeError, ValueError):
			return 999

	def subscribe(self, callback: Callable) -> None:
		self._listeners.append(callback)

	def _emit(self, event: TutorialEvent, module: Optional[ApplicationModule]) -> None:
		for callback in self._listeners:
			callback(event, module)

	def start(self) -> None:
		if not self._modules:
			return

		first = self._modules[0]
		self.state.running = True
		self.state.module_name = first.module_id
		self.state.order = self._module_order(first.module_id)

		self._emit(TutorialEvent.START, first)

	def stop(self) -> None:
		self.state.reset()
		self._emit(TutorialEvent.STOP, None)

	def next(self) -> None:
		if not self.state.running:
			return

		current = self.state.order

		for module in self._modules:
			module_order = self._module_order(module.module_id)
			if module_order > current:
				self.state.module_name = module.module_id
				self.state.order = module_order
				self._emit(TutorialEvent.NEXT, module)
				self._emit(TutorialEvent.MODULE_CHANGED, module)
				return

	def previous(self) -> None:
		if not self.state.running:
			return

		current = self.state.order
		previous_module: Optional[ApplicationModule] = None

		for module in self._modules:
			module_order = self._module_order(module.module_id)
			if module_order >= current:
				break
			previous_module = module

		if previous_module is None:
			return

		previous_order = self._module_order(previous_module.module_id)
		self.state.module_name = previous_module.module_id
		self.state.order = previous_order
		self._emit(TutorialEvent.PREVIOUS, previous_module)
		self._emit(TutorialEvent.MODULE_CHANGED, previous_module)

	def select(self, module_name: str) -> None:
		for module in self._modules:
			if module.module_id != module_name:
				continue

			self.state.module_name = module.module_id
			self.state.order = self._module_order(module.module_id)
			self._emit(TutorialEvent.MODULE_CHANGED, module)
			return


# Backward-compat alias while code migrates from TutorialEngine naming.
TutorialEngine = TutorialGenerator
