document.addEventListener("DOMContentLoaded", () => {
  // Tab switching
  const tabs = document.querySelectorAll(".tab")
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      // Remove active class from all tabs and content
      document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"))
      document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"))

      // Add active class to clicked tab
      tab.classList.add("active")

      // Show corresponding content
      const tabName = tab.getAttribute("data-tab")
      document.getElementById(`${tabName}-tab`).classList.add("active")
    })
  })

  // Jobs tab functionality
  const scrapeJobsBtn = document.getElementById("scrapeJobsBtn")
  const getJobsBtn = document.getElementById("getJobsBtn")
  const jobsResult = document.getElementById("jobsResult")
  const jobsLoading = document.getElementById("jobsLoading")

  scrapeJobsBtn.addEventListener("click", async () => {
    try {
      scrapeJobsBtn.disabled = true
      jobsLoading.style.display = "inline"
      jobsResult.textContent = "Scraping jobs... This may take a few minutes."

      const response = await fetch("/scrape_jobs")
      const data = await response.json()

      jobsResult.textContent = JSON.stringify(data, null, 2)
    } catch (error) {
      jobsResult.textContent = `Error: ${error.message}`
    } finally {
      scrapeJobsBtn.disabled = false
      jobsLoading.style.display = "none"
    }
  })

  getJobsBtn.addEventListener("click", async () => {
    try {
      getJobsBtn.disabled = true
      jobsLoading.style.display = "inline"

      const response = await fetch("/jobs")
      const data = await response.json()

      jobsResult.textContent = JSON.stringify(data, null, 2)
    } catch (error) {
      jobsResult.textContent = `Error: ${error.message}`
    } finally {
      getJobsBtn.disabled = false
      jobsLoading.style.display = "none"
    }
  })

  // Profiles tab functionality
  const getProfilesBtn = document.getElementById("getProfilesBtn")
  const profilesResult = document.getElementById("profilesResult")
  const profilesLoading = document.getElementById("profilesLoading")

  getProfilesBtn.addEventListener("click", async () => {
    try {
      getProfilesBtn.disabled = true
      profilesLoading.style.display = "inline"

      const response = await fetch("/profiles")
      const data = await response.json()

      profilesResult.textContent = JSON.stringify(data, null, 2)
    } catch (error) {
      profilesResult.textContent = `Error: ${error.message}`
    } finally {
      getProfilesBtn.disabled = false
      profilesLoading.style.display = "none"
    }
  })

  // Matches tab functionality
  const matchProfilesBtn = document.getElementById("matchProfilesBtn")
  const getMatchesBtn = document.getElementById("getMatchesBtn")
  const matchesResult = document.getElementById("matchesResult")
  const matchesLoading = document.getElementById("matchesLoading")
  const pageInput = document.getElementById("pageInput")
  const perPageInput = document.getElementById("perPageInput")

  matchProfilesBtn.addEventListener("click", async () => {
    try {
      matchProfilesBtn.disabled = true
      matchesLoading.style.display = "inline"
      matchesResult.textContent = "Matching profiles... This may take a few minutes."

      const page = pageInput.value || 1
      const perPage = perPageInput.value || 10

      const response = await fetch(`/match_profiles?page=${page}&per_page=${perPage}&run=true`, {
        method: "POST",
      })
      const data = await response.json()

      matchesResult.textContent = JSON.stringify(data, null, 2)
    } catch (error) {
      matchesResult.textContent = `Error: ${error.message}`
    } finally {
      matchProfilesBtn.disabled = false
      matchesLoading.style.display = "none"
    }
  })

  getMatchesBtn.addEventListener("click", async () => {
    try {
      getMatchesBtn.disabled = true
      matchesLoading.style.display = "inline"

      const page = pageInput.value || 1
      const perPage = perPageInput.value || 10

      const response = await fetch(`/match_profiles?page=${page}&per_page=${perPage}`, {
        method: "POST",
      })
      const data = await response.json()

      matchesResult.textContent = JSON.stringify(data, null, 2)
    } catch (error) {
      matchesResult.textContent = `Error: ${error.message}`
    } finally {
      getMatchesBtn.disabled = false
      matchesLoading.style.display = "none"
    }
  })

  // Initialize pagination inputs
  pageInput.addEventListener("change", () => {
    if (Number.parseInt(pageInput.value) < 1) {
      pageInput.value = 1
    }
  })

  perPageInput.addEventListener("change", () => {
    if (Number.parseInt(perPageInput.value) < 1) {
      perPageInput.value = 1
    } else if (Number.parseInt(perPageInput.value) > 100) {
      perPageInput.value = 100
    }
  })
})
