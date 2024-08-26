IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp", ".dcm", ".dicom"]

RE_WIN_BACKSLASH = r"(?<!\\)(\\{1}(?:\\{2})*)(?!\\)"

DEFAULT_KEYBINDS_IN_ORDER = [
    "A",
    "S",
    "D",
    "F",
    "J",
    "K",
    "L",
    ";",
    "Q",
    "W",
    "E",
    "R",
    "T",
    "Y",
    "U",
    "I",
    "O",
    "P",
    # cannot include Z since needed for ctrl + z
    "X",
    "C",
    "V",
    "N",
    "M",
    "B",
    "1",
    "2",
    "3",
    "4",
    "8",
    "9",
    "0",
    "5",
    "6",
    "7",
]
KEYBOARD_LAYOUT = [
    "q",
    "w",
    "e",
    "r",
    "t",
    "y",
    "u",
    "i",
    "o",
    "p",
    "a",
    "s",
    "d",
    "f",
    "g",
    "space",  # space is 'central'
    "h",
    "j",
    "k",
    "l",
    ";",
    # cannot have 'z' because it is used for undo
    "x",
    "c",
    "v",
    "b",
    "n",
    "m",
    "arrowleft",
    "arrowup",
    "arrowdown",
    "arrowright",
]
