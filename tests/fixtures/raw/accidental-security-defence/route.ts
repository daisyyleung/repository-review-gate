export function proxy(request: Request) {
  const target = new URL(new URL(request.url).searchParams.get("target") ?? "");
  return fetch(target);
}
