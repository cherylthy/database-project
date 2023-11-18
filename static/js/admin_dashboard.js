  $(document).ready(function () {
      // Event handler for the delete button
      // Event handler for the delete button
  $("#delete-selected").click(function () {
      var selectedRows = [];

      // Loop through all checkboxes
      $("input[name='select_row']:checked").each(function () {
          selectedRows.push($(this).val());
      });

      // Log the payload to the console for debugging
      console.log("Selected Rows:", selectedRows);

      // Ask for confirmation
      if (confirm("Are you sure you want to delete the selected rows?")) {
          // Log the payload to the console for debugging
          console.log("Deleting rows...");

          // Make an AJAX request to the Flask server to delete selected rows
          $.ajax({
              type: "POST",
              url: "/admin_dashboard",
              data: JSON.stringify({ rows: selectedRows }),
              contentType: "application/json;charset=utf-8",
              success: function (response) {
                  // Log the server response for debugging
                  console.log("Server Response:", response);

                  // Reload the page or update the table as needed
                  location.reload();
              },
              error: function (error) {
                  console.log("Error:", error);
              }
          });
      }
  });
});