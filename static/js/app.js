document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".toggle-password").forEach((button) => {
    button.addEventListener("click", () => {
      const input = button.parentElement.querySelector("input");
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      button.textContent = show ? "Hide" : "Show";
      button.setAttribute(
        "aria-label",
        show ? "Hide password" : "Show password",
      );
    });
  });

  const menuButton = document.querySelector(".menu-button");
  if (menuButton)
    menuButton.addEventListener("click", () =>
      document.querySelector(".app-shell").classList.toggle("menu-open"),
    );

  const search = document.querySelector("#note-search");
  if (search)
    search.addEventListener("input", () => {
      const query = search.value.trim().toLowerCase();
      const cards = [...document.querySelectorAll(".note-card")];
      let matches = 0;
      cards.forEach((card) => {
        const visible = card.dataset.search.includes(query);
        card.hidden = !visible;
        if (visible) matches += 1;
      });
      document.querySelector("#empty-search").hidden = matches !== 0;
    });

  document.querySelectorAll("[data-delete-form]").forEach((form) =>
    form.addEventListener("submit", (event) => {
      if (!window.confirm("Delete this note? This cannot be undone."))
        event.preventDefault();
    }),
  );
});
