import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 30000 })

// Documents
export const uploadDocuments  = (formData) => api.post('/documents/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
export const listDocuments    = (params)   => api.get('/documents/', { params })
export const getDocument      = (id)       => api.get(`/documents/${id}`)
export const getDocStatus     = (id)       => api.get(`/documents/${id}/status`)
export const validateDoc      = (id)       => api.patch(`/documents/${id}/validate`)
export const rejectDoc        = (id)       => api.patch(`/documents/${id}/reject`)
export const reprocessDoc     = (id)       => api.post(`/documents/${id}/process`)

// Suppliers
export const listSuppliers    = ()         => api.get('/suppliers/')
export const getSupplier      = (id)       => api.get(`/suppliers/${id}`)
export const createSupplier   = (data)     => api.post('/suppliers/', data)
export const updateSupplier   = (id, data) => api.patch(`/suppliers/${id}`, data)
export const supplierDocs     = (id)       => api.get(`/suppliers/${id}/documents`)
export const autofillCRM      = ()         => api.post('/suppliers/autofill-from-curated')

// Compliance
export const listAnomalies    = (params)   => api.get('/compliance/anomalies', { params })
export const listFraudulent   = ()         => api.get('/compliance/fraudulent')
export const resolveAnomaly   = (id, res)  => api.patch(`/compliance/anomalies/${id}/resolve`, null, { params: { resolution: res } })
export const checkInterDocs   = ()         => api.get('/compliance/check-inter-docs')
export const refreshCompliance= ()         => api.post('/compliance/refresh')

// Data Lake
export const datalakeStats    = ()         => api.get('/datalake/stats')
export const datalakeZone     = (zone)     => api.get(`/datalake/${zone}`)

// Stats
export const dashboardStats   = ()         => api.get('/stats/dashboard')

// Airflow
export const triggerDAG       = (dag_id)   => api.post(`/airflow/trigger/${dag_id}`)
export const dagStatus        = (dag_id)   => api.get(`/airflow/status/${dag_id}`)

export default api
