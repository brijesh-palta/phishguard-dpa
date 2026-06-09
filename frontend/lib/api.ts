import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface DetectionRequest {
  subject: string
  body: string
  html_body?: string
  urls: string[]
  image_urls?: string[]
  attachment_names?: string[]
  sender_email?: string
  reply_to_email?: string
  expected_domain?: string
}

export interface DetectionResult {
  id: string
  label: string
  confidence: number
  phishing_probability: number
  content_probability: number
  structure_probability: number
  risk_level: string
  model_accuracy: number
  reasons: string[]
  sender_analysis?: {
    verdict: string
    risk_score: number
    findings: string[]
  }
  structure_analysis?: {
    verdict: string
    risk_score: number
    findings: string[]
  }
}

export interface TrainingChallengeRequest {
  scenario?: string
  difficulty?: 'easy' | 'medium' | 'hard'
  employee_name?: string
  company_name?: string
  base_url?: string
}

export interface TrainingChallengeResponse {
  scenario: string
  difficulty: 'easy' | 'medium' | 'hard'
  subject: string
  body: string
  plain_text_body: string
  html_body: string
  links: Array<{ label: string; url: string; purpose: string }>
  images: Array<{ role: string; url: string; alt_text: string }>
  tracking_id: number
  landing_page_url: string
  red_flags: string[]
  hints: string[]
  points_available: {
    report: number
    identify_all_red_flags: number
    avoid_click: number
  }
  generated_at: string
  safety_note: string
  gophish_template: {
    name: string
    subject: string
    text: string
    html: string
  }
}

export const detectionAPI = {
  async detectEmail(payload: DetectionRequest): Promise<DetectionResult> {
    const response = await api.post('/api/detect', payload)
    return response.data
  },

  async detectURL(url: string): Promise<any> {
    return api.post('/api/detect', {
      subject: 'URL Analysis',
      body: `Scanning URL: ${url}`,
      urls: [url],
    })
  },

  async generateTrainingChallenge(
    payload: TrainingChallengeRequest,
  ): Promise<TrainingChallengeResponse> {
    const response = await api.post('/api/training/challenge', payload)
    return response.data
  },

  async getDetectionHistory(limit: number = 25): Promise<any> {
    const response = await api.get(`/api/detections?limit=${limit}`)
    return response.data
  },

  async getMetrics(): Promise<any> {
    const response = await api.get('/api/metrics')
    return response.data
  },

  async health(): Promise<any> {
    const response = await api.get('/api/health')
    return response.data
  },
}

export default api
