export function submit(form: HTMLFormElement) {
  return fetch(form.action, { method: "POST" });
}
