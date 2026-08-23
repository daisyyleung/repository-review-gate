import parser from "runtime-parser";

export function parseDocument(input: string) {
  return parser(input);
}
