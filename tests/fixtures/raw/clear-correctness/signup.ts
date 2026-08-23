export async function submitSignup(form: HTMLFormElement) {
  const response = await fetch("/signup", { method: "POST", body: new FormData(form) });
  if (response.ok) {
    showError("Your account was created");
    return;
  }
  showError("Signup failed");
}
