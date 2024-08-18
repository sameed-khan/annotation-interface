export const KEYBOARD_LAYOUT = [
  'q',
  'w',
  'e',
  'r',
  't',
  'y',
  'u',
  'i',
  'o',
  'p',
  'a',
  's',
  'd',
  'f',
  'g',
  'space', // space is 'central'
  'h',
  'j',
  'k',
  'l',
  ';',
  // cannot have 'z' because it is used for undo
  'x',
  'c',
  'v',
  'b',
  'n',
  'm',
  'arrowleft',
  'arrowup',
  'arrowdown',
  'arrowright',
];

export function sortByKeyboardLayout(a: string | null, b: string | null) {
  if (a === b) return 0;
  if (a === null) return 1;
  if (b === null) return -1;

  const indexA = KEYBOARD_LAYOUT.indexOf(a.toLowerCase());
  const indexB = KEYBOARD_LAYOUT.indexOf(b.toLowerCase());

  // Handle cases where the keybind is not in the layout
  if (indexA === -1 && indexB === -1) return 0;
  if (indexA === -1) return 1;
  if (indexB === -1) return -1;

  return indexA - indexB;
}
