function openModal(licensePlate, make, model, bodyType, engineType, transmission, dailyRates) {
            
  // Populate your modal fields here
  document.getElementById('editModal').style.display = 'block';
  document.getElementById('license-plate').value = licensePlate;
  document.getElementById('car-make').value = make;
  document.getElementById('car-model').value = model;
  document.getElementById('body-type').value = bodyType;
  document.getElementById('engine-type').value = engineType;
  document.getElementById('transmission-type').value = transmission;
  document.getElementById('daily-rates').value = dailyRates;
}

function closeModal() {
  document.getElementById('editModal').style.display = 'none';
}

function saveChanges(event) {
event.preventDefault();

// Gather the form data
var licensePlate = document.getElementById('license-plate').value;
var carMake = document.getElementById('car-make').value;
var carModel = document.getElementById('car-model').value;
var bodyType = document.getElementById('body-type').value;
var engineType = document.getElementById('engine-type').value;
var transmissionType = document.getElementById('transmission-type').value;
var dailyRates = document.getElementById('daily-rates').value;

// Make an AJAX request to update the data in the backend
fetch('/admin_dashboard', {
  method: 'POST',
  headers: {
      'Content-Type': 'application/json'
  },
  body: JSON.stringify({
      license_plate: licensePlate,
      car_make: carMake,
      car_model: carModel,
      body_type: bodyType,
      engine_size: engineType,
      transmission_type: transmissionType,
      daily_rate: dailyRates
  })
})
.then(response => response.json())
.then(data => {
  // Handle the response, e.g., close the modal and display a message
  closeModal();
  alert(data.message); // You might want to use a better UI element for this
  location.reload();
})
.catch(error => {
  // Handle errors, e.g., display an error message
  alert('Error: ' + error.message);
});
}

// Close the modal if the user clicks outside of it
window.onclick = function (event) {
  var modal = document.getElementById('editModal');
  if (event.target == modal) {
      closeModal();
  }
}