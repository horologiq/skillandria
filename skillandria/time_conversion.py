

def time_to_milliseconds(time_str):
    parts = time_str.split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = parts[2].replace(",", ".")
    milliseconds = int(float(seconds) * 1000)
    milliseconds += hours * 60 * 60 * 1000
    milliseconds += minutes * 60 * 1000
    return milliseconds


def seconds_to_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return "{:01d}:{:02d}:{:02d}".format(hours, minutes, seconds)


def milliseconds_to_time(milliseconds):
    seconds = int(milliseconds / 1000)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return "{:01d}:{:02d}:{:02d}".format(hours, minutes, seconds)
