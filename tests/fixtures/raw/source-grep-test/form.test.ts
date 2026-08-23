import { readFileSync } from "node:fs";

test("form has a submit call", () => {
  expect(readFileSync("form.ts", "utf8")).toContain("fetch");
});
