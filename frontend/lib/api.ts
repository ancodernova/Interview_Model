const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000"

interface ApiOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE"
  headers?: Record<string, string>
  body?: any
  requiresAuth?: boolean
}

export async function apiCall(endpoint: string, options: ApiOptions = {}) {
  const { method = "GET", headers = {}, body, requiresAuth = true } = options

  const url = `${API_BASE_URL}${endpoint}`

  const requestHeaders: Record<string, string> = {
    ...headers,
  }

  // Add authorization header if required
  if (requiresAuth) {
    const token = localStorage.getItem("token")
    if (!token || token === "null" || token === "undefined") {
      throw new Error("No valid authentication token found. Please log in again.")
    }

    // Ensure token is a clean string without extra quotes or whitespace
    const cleanToken = token.replace(/^["']|["']$/g, "").trim()
    if (!cleanToken) {
      throw new Error("Invalid authentication token. Please log in again.")
    }

    requestHeaders["Authorization"] = `Bearer ${cleanToken}`
    console.log("Using token:", cleanToken.substring(0, 20) + "...")
  }

  const config: RequestInit = {
    method,
    headers: requestHeaders,
    mode: "cors",
  }

  // Handle body for non-GET requests
  if (body && method !== "GET") {
    if (body instanceof FormData) {
      // Don't set Content-Type for FormData - let browser handle it
      config.body = body
      console.log("Sending FormData with keys:", Array.from(body.keys()))
    } else {
      requestHeaders["Content-Type"] = "application/json"
      config.body = JSON.stringify(body)
      console.log("Sending JSON body:", body)
    }
  }

  // Update headers after potential Content-Type changes
  config.headers = requestHeaders

  console.log(`Making ${method} request to:`, url)
  console.log("Request headers:", requestHeaders)

  try {
    const response = await fetch(url, config)

    console.log(`Response status: ${response.status} ${response.statusText}`)

    if (!response.ok) {
      let errorMessage = `${response.status} ${response.statusText}`
      try {
        const errorData = await response.json()
        console.error("Backend error response:", errorData)
        errorMessage += ` - ${JSON.stringify(errorData)}`
      } catch {
        const errorText = await response.text().catch(() => "Unknown error")
        console.error("Backend error text:", errorText)
        errorMessage += ` - ${errorText}`
      }
      throw new Error(`API call failed: ${errorMessage}`)
    }

    return response
  } catch (error) {
    console.error("API call error:", error)
    if (error instanceof Error) {
      throw error
    }
    throw new Error("Network error occurred")
  }
}

export async function uploadFile(
  endpoint: string,
  file: File,
  fileKey = "file",
  additionalFields?: Record<string, string>,
) {
  // Validate file
  if (!file || !(file instanceof File)) {
    throw new Error("Invalid file provided")
  }

  const formData = new FormData()
  formData.append(fileKey, file)

  // Add any additional fields
  if (additionalFields) {
    Object.entries(additionalFields).forEach(([key, value]) => {
      formData.append(key, value)
    })
  }

  return apiCall(endpoint, {
    method: "POST",
    body: formData,
    requiresAuth: true,
  })
}

export async function uploadResume(file: File): Promise<any> {
  const token = localStorage.getItem("token")
  if (!token || token === "null" || token === "undefined") {
    throw new Error("No valid authentication token found. Please log in again.")
  }

  // Clean the token of any extra quotes or whitespace
  const cleanToken = token.replace(/^["']|["']$/g, "").trim()
  if (!cleanToken) {
    throw new Error("Invalid authentication token. Please log in again.")
  }

  const formData = new FormData()
  formData.append("resume", file)

  console.log("Uploading resume:", file.name, "Size:", file.size, "Type:", file.type)

  const res = await fetch(`${API_BASE_URL}/api/interview/upload_resume`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${cleanToken}`,
    },
    body: formData,
  })

  if (!res.ok) {
    let errorMessage = `Upload failed: ${res.status}`
    try {
      const errorData = await res.json()
      console.error("Resume upload error response:", errorData)
      errorMessage += ` - ${JSON.stringify(errorData)}`
    } catch {
      const errorText = await res.text().catch(() => "Unknown error")
      console.error("Resume upload error text:", errorText)
      errorMessage += ` - ${errorText}`
    }
    throw new Error(errorMessage)
  }

  return await res.json()
}
