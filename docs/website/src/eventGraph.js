export const eventGraph = {
  node_selected: [],
  autoplay_toggled: ["sequence_started", "sequence_stopped"],
  sequence_started: ["sequence_step_advanced", "sequence_completed", "sequence_stopped"],
  sequence_step_advanced: ["sequence_step_advanced", "sequence_completed", "node_selected"],
  sequence_reset: ["sequence_step_advanced", "node_selected"],
  sequence_completed: [],
  sequence_stopped: []
};