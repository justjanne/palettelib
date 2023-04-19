def print_columns(header: (list[str] | tuple[str, ...]),
                  entries: list[list[int | str] | tuple[int | str, ...]],
                  file=None):
    column_widths = [len(column) for column in header]
    for entry in entries:
        for i in range(len(entry)):
            length = len(str(entry[i]))
            if len(column_widths) < i:
                column_widths.append(length)
            elif length > column_widths[i]:
                column_widths[i] = length
    line = []
    for i in range(len(column_widths)):
        if i < len(header):
            value = header[i]
            width = column_widths[i]
            line.append(value.ljust(width))
    print(" ".join(line), file=file)
    for entry in entries:
        line = []
        for i in range(len(column_widths)):
            if i < len(entry):
                value = entry[i]
                width = column_widths[i]
                if isinstance(value, int) or isinstance(value, float):
                    line.append(str(value).rjust(width))
                else:
                    line.append(value.ljust(width))
        print(" ".join(line), file=file)
