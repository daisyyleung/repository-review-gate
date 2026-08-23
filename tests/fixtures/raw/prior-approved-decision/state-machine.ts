export function advance(current: string, next: string) {
  if (current === "draft" && next === "submitted") return next;
  throw new Error("invalid transition");
}
