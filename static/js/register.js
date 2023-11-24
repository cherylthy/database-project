// JavaScript to control the modal
const openTermsModal = document.getElementById("openTermsModal");
const termsModal = document.getElementById("termsModal");
const closeModalButton = document.getElementById("closeModal");

openTermsModal.addEventListener("click", function (e) {
  e.preventDefault(); // Prevent the default link behavior
  termsModal.style.display = "block";
});

closeModalButton.addEventListener("click", function () {
  termsModal.style.display = "none";
});
