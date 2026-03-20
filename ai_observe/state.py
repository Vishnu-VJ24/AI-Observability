import contextvars

# Context variables to trace asynchronous or nested calls invisibly
current_trace_id = contextvars.ContextVar("current_trace_id", default=None)
current_parent_id = contextvars.ContextVar("current_parent_id", default=None)

# In-memory storage for active spans to reconstruct trees before dumping
# Format: { "trace_id_uuid": [ span_dict, span_dict ] }
active_traces = {}
