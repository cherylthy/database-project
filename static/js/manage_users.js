    $(document).ready(function () {
        // Event handler for the delete button
        // Event handler for the delete button
    $("#delete_selected_users").click(function () {
        var selectedUsers = [];

        // Loop through all checkboxes
        $("input[name='select_user']:checked").each(function () {
            selectedUsers.push($(this).val());
        });

        // Log the payload to the console for debugging
        console.log("Selected Users:", selectedUsers);

        // Ask for confirmation
        if (confirm("Are you sure you want to delete the selected users?")) {
            // Log the payload to the console for debugging
            console.log("Deleting Users...");

            // Make an AJAX request to the Flask server to delete selected rows
            $.ajax({
                type: "POST",
                url: "/manage_users",
                data: JSON.stringify({ users: selectedUsers }),
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