import { useState, useEffect, useCallback } from 'react'

const API = '/api'

export function useCompanies() {
  const [companies, setCompanies] = useState<any[]>([])

  const fetchCompanies = useCallback(() => {
    return fetch(`${API}/companies`).then(r => r.json()).then((list: any[]) => {
      setCompanies(list)
      return list
    })
  }, [])

  const deleteCompany = useCallback(async (id: number) => {
    await fetch(`${API}/companies/${id}`, { method: 'DELETE' })
    fetchCompanies()
  }, [fetchCompanies])

  const reprocessCompany = useCallback(async (id: number) => {
    await fetch(`${API}/companies/${id}/reprocess`, { method: 'POST' })
    fetchCompanies()
  }, [fetchCompanies])

  const cancelCompanyAction = useCallback((id: number) => {
    fetchCompanies()
  }, [fetchCompanies])

  const resetCompanyAction = useCallback((id: number) => {
    fetchCompanies()
  }, [fetchCompanies])

  const refresh = useCallback(() => {
    fetchCompanies()
  }, [fetchCompanies])

  useEffect(() => {
    fetchCompanies()
  }, [fetchCompanies])

  return {
    companies, setCompanies,
    fetchCompanies,
    deleteCompany, reprocessCompany, cancelCompanyAction, resetCompanyAction, refresh
  }
}
