document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message and existing content
      activitiesList.innerHTML = "";
      
      // Clear and reset activity dropdown (keep the default option)
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;
        
        // Create participants section safely
        const participantsSection = document.createElement("div");
        participantsSection.className = "participants-section";
        const participantsHeader = document.createElement("p");
        participantsHeader.className = "participants-header";
        const strong = document.createElement("strong");
        strong.textContent = "Current Participants:";
        participantsHeader.appendChild(strong);
        participantsSection.appendChild(participantsHeader);

        if (details.participants.length > 0) {
          const ul = document.createElement("ul");
          ul.className = "participants-list";
          details.participants.forEach(email => {
            const li = document.createElement("li");
            li.className = "participant-item";

            const span = document.createElement("span");
            span.className = "participant-email";
            span.textContent = email;

            const button = document.createElement("button");
            button.className = "delete-participant";
            button.dataset.activity = name;
            button.dataset.email = email;
            button.title = "Remove participant";
            button.textContent = "✕";

            li.appendChild(span);
            li.appendChild(button);
            ul.appendChild(li);
          });
          participantsSection.appendChild(ul);
        } else {
          const p = document.createElement("p");
          p.className = "no-participants";
          p.textContent = "No participants yet";
          participantsSection.appendChild(p);
        }

        activityCard.innerHTML = `
          <h4></h4>
          <p></p>
          <p><strong>Schedule:</strong> </p>
          <p><strong>Availability:</strong> </p>
        `;
        activityCard.querySelector("h4").textContent = name;
        activityCard.querySelectorAll("p")[0].textContent = details.description;
        activityCard.querySelectorAll("p")[1].innerHTML = `<strong>Schedule:</strong> ${details.schedule}`;
        activityCard.querySelectorAll("p")[2].innerHTML = `<strong>Availability:</strong> ${spotsLeft} spots left`;
        activityCard.appendChild(participantsSection);

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
      
      // Refresh activities list
      fetchActivities();
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Handle participant deletion with event delegation
  activitiesList.addEventListener("click", async (event) => {
    if (event.target.classList.contains("delete-participant")) {
      const button = event.target;
      const activity = button.dataset.activity;
      const email = button.dataset.email;

      if (!confirm(`Are you sure you want to unregister ${email} from ${activity}?`)) {
        return;
      }

      try {
        const response = await fetch(
          `/activities/${encodeURIComponent(activity)}/unregister?email=${encodeURIComponent(email)}`,
          {
            method: "DELETE",
          }
        );

        const result = await response.json();

        if (response.ok) {
          messageDiv.textContent = result.message;
          messageDiv.className = "success";
          // Refresh activities list
          fetchActivities();
        } else {
          messageDiv.textContent = result.detail || "An error occurred";
          messageDiv.className = "error";
        }

        messageDiv.classList.remove("hidden");

        // Hide message after 5 seconds
        setTimeout(() => {
          messageDiv.classList.add("hidden");
        }, 5000);
      } catch (error) {
        messageDiv.textContent = "Failed to unregister. Please try again.";
        messageDiv.className = "error";
        messageDiv.classList.remove("hidden");
        console.error("Error unregistering:", error);
      }
    }
  });

  // Initialize app
  fetchActivities();
});
