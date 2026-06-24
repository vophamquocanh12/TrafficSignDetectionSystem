import state


def add_sound_event(class_name):
    with state.sound_lock:
        if class_name not in state.sound_events:
            state.sound_events.append(class_name)


def get_and_clear_sound_events():
    with state.sound_lock:
        events = state.sound_events.copy()
        state.sound_events.clear()
    return events


def clear_sound_events():
    with state.sound_lock:
        state.sound_events.clear()