export function canAdvance(current: string, next: string): boolean {
  return { draft: ["submitted"], submitted: ["approved"] }[current]?.includes(next) ?? false;
}

export function advance(current: string, next: string) {
  if (!canAdvance(current, next)) throw new Error("invalid transition");
  return next;
}
