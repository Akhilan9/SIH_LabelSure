import { 
  User, 
  InspectionSummary, 
  InspectionImage, 
  Declaration, 
  Finding, 
  Rule, 
  DashboardSummary,
  ReportRecord,
  AnalyticsData,
  UserCreatePayload
} from '../types';

const API_BASE = '/api';

export function getAuthToken(): string | null {
  return localStorage.getItem('labelsure_token');
}

export function setAuthToken(token: string) {
  localStorage.setItem('labelsure_token', token);
}

export function removeAuthToken() {
  localStorage.removeItem('labelsure_token');
  localStorage.removeItem('labelsure_user');
}

export function getCurrentUserFromStorage(): User | null {
  const u = localStorage.getItem('labelsure_user');
  return u ? JSON.parse(u) : null;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getAuthToken();
  const headers = new Headers(options.headers || {});
  
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  
  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers
  });
  
  if (res.status === 401) {
    removeAuthToken();
    window.location.href = '#login';
    throw new Error('Unauthorized');
  }
  
  if (!res.ok) {
    let errMsg = `Request failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson.error?.message) {
        errMsg = errJson.error.message;
      }
    } catch (_) {}
    throw new Error(errMsg);
  }
  
  if (res.status === 204) {
    return {} as T;
  }
  
  return res.json();
}

export const api = {
  // Auth
  async login(username: string, password: string) {
    const data = await request<any>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
    setAuthToken(data.access_token);
    const user: User = {
      id: data.user_id,
      username: data.username,
      email: `${data.username}@labelsure.gov.in`,
      full_name: data.full_name,
      role: data.role,
      badge_number: data.badge_number
    };
    localStorage.setItem('labelsure_user', JSON.stringify(user));
    return user;
  },
  
  async getMe(): Promise<User> {
    return request<User>('/auth/me');
  },
  
  // Dashboard
  async getDashboardSummary(): Promise<DashboardSummary> {
    return request<DashboardSummary>('/dashboard/summary');
  },
  
  // Inspections
  async listInspections(params?: { search?: string; status?: string; compliance_status?: string }): Promise<InspectionSummary[]> {
    const q = new URLSearchParams();
    if (params?.search) q.set('search', params.search);
    if (params?.status) q.set('status', params.status);
    if (params?.compliance_status) q.set('compliance_status', params.compliance_status);
    return request<InspectionSummary[]>(`/inspections?${q.toString()}`);
  },
  
  async getInspection(id: string): Promise<any> {
    return request<any>(`/inspections/${id}`);
  },
  
  async createInspection(payload: any): Promise<InspectionSummary> {
    return request<InspectionSummary>('/inspections', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  
  async finalizeInspection(id: string): Promise<InspectionSummary> {
    return request<InspectionSummary>(`/inspections/${id}/finalize`, {
      method: 'POST'
    });
  },

  async getInspectionContext(id: string): Promise<any> {
    return request<any>(`/inspections/${id}/context`);
  },

  async updateInspectionContext(id: string, payload: any): Promise<any> {
    return request<any>(`/inspections/${id}/context`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    });
  },
  
  // Image Upload
  async uploadImage(inspectionId: string, file: File, viewType: string): Promise<InspectionImage> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('view_type', viewType);
    return request<InspectionImage>(`/inspections/${inspectionId}/images`, {
      method: 'POST',
      body: formData
    });
  },
  
  // Analysis
  async triggerAnalysis(inspectionId: string): Promise<any> {
    return request<any>(`/inspections/${inspectionId}/analyze`, {
      method: 'POST'
    });
  },
  
  // Declarations
  async getDeclarations(inspectionId: string): Promise<Declaration[]> {
    return request<Declaration[]>(`/inspections/${inspectionId}/declarations`);
  },
  
  async updateDeclaration(id: string, payload: any): Promise<Declaration> {
    return request<Declaration>(`/declarations/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    });
  },

  async createDeclaration(inspectionId: string, payload: any): Promise<Declaration> {
    return request<Declaration>(`/inspections/${inspectionId}/declarations`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  
  // Findings & RuleLens Review
  async getFindings(inspectionId: string): Promise<Finding[]> {
    return request<Finding[]>(`/inspections/${inspectionId}/findings`);
  },
  
  async overrideFinding(findingId: string, inspectorStatus: string, comment?: string): Promise<Finding> {
    return request<Finding>(`/findings/${findingId}`, {
      method: 'PATCH',
      body: JSON.stringify({
        inspector_status: inspectorStatus,
        inspector_comment: comment
      })
    });
  },
  
  // Reports
  async generateReport(inspectionId: string): Promise<any> {
    return request<any>(`/inspections/${inspectionId}/report`, {
      method: 'POST'
    });
  },

  async listReports(search?: string): Promise<ReportRecord[]> {
    const q = search ? `?search=${encodeURIComponent(search)}` : '';
    return request<ReportRecord[]>(`/reports${q}`);
  },
  
  // Rules
  async listRules(version?: string): Promise<Rule[]> {
    const q = version ? `?version=${encodeURIComponent(version)}` : '';
    return request<Rule[]>(`/rules${q}`);
  },

  // RuleLens Dossier
  async getRuleLens(inspectionId: string): Promise<any> {
    return request<any>(`/inspections/${inspectionId}/rulelens`);
  },

  // Evidence Images
  async listImages(viewType?: string): Promise<InspectionImage[]> {
    const q = viewType ? `?view_type=${encodeURIComponent(viewType)}` : '';
    return request<InspectionImage[]>(`/images${q}`);
  },

  // Analytics
  async getAnalytics(): Promise<AnalyticsData> {
    return request<AnalyticsData>('/dashboard/analytics');
  },

  // Users Management
  async listUsers(): Promise<User[]> {
    return request<User[]>('/auth/users');
  },

  async registerUser(payload: UserCreatePayload): Promise<User> {
    return request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  
  // Audit Logs
  async listAuditLogs(inspectionId?: string): Promise<any[]> {
    const q = inspectionId ? `?inspection_id=${encodeURIComponent(inspectionId)}` : '';
    return request<any[]>(`/audit-logs${q}`);
  }
};
