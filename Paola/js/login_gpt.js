const $password = document.getElementById("password"),
      $togglePassword = document.getElementById("toggle-password");

$togglePassword.addEventListener("click", () => {
    // Cambia el tipo de input entre password y text
    const type = $password.type === "password" ? "text" : "password";
    $password.type = type;
    
    // Alterna el icono del ojo
    $togglePassword.classList.toggle("fa-eye-slash");
});
