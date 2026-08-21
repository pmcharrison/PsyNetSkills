(function () {
  function openPlanDetails() {
    const details = document.getElementById("plan-details");
    if (details && details.tagName === "DETAILS") {
      details.open = true;
    }
  }

  document.addEventListener("click", (event) => {
    const link = event.target.closest('a[href$="#plan-details"]');
    if (link) {
      openPlanDetails();
    }
  });

  window.addEventListener("hashchange", () => {
    if (window.location.hash === "#plan-details") {
      openPlanDetails();
    }
  });

  if (window.location.hash === "#plan-details") {
    openPlanDetails();
    const details = document.getElementById("plan-details");
    if (details) {
      details.scrollIntoView();
    }
  }
})();
