def classify_gaze_binary(blendshapes: dict, thresholds: dict = None) -> str:
    look_down_left = blendshapes.get('eyeLookDownLeft', 0.0)
    look_down_right = blendshapes.get('eyeLookDownRight', 0.0)
    look_up_left = blendshapes.get('eyeLookUpLeft', 0.0)
    look_up_right = blendshapes.get('eyeLookUpRight', 0.0)
    look_in_left = blendshapes.get('eyeLookInLeft', 0.0)
    look_out_left = blendshapes.get('eyeLookOutLeft', 0.0)
    look_in_right = blendshapes.get('eyeLookInRight', 0.0)
    look_out_right = blendshapes.get('eyeLookOutRight', 0.0)

    avg_down = (look_down_left + look_down_right) / 2.0
    avg_up = (look_up_left + look_up_right) / 2.0
    left_gaze = (look_out_left + look_in_right) / 2.0
    right_gaze = (look_out_right + look_in_left) / 2.0
    horizontal_magnitude = max(left_gaze, right_gaze)

    if thresholds:
        down_baseline = thresholds.get('down_baseline', 0.40)
        horizontal_threshold = thresholds.get('horizontal_threshold', 0.25)
        vertical_threshold = thresholds.get('vertical_threshold', 0.20)
    else:
        down_baseline = 0.40
        horizontal_threshold = 0.25
        vertical_threshold = 0.20

    adjusted_down = max(0.0, avg_down - down_baseline)
    vertical_magnitude = max(avg_up, adjusted_down)

    if horizontal_magnitude > horizontal_threshold or vertical_magnitude > vertical_threshold:
        return "LOOK_AWAY"

    return "CENTER"
