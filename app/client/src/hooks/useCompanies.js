import { useState, useEffect, useCallback } from 'react'

const API = '/api'

export function useCompanies() {
  const [companies, setCompanies] = useState([])
  const [pendingCompanies, setPendingCompanies] = useState([])

  const fetchCompanies = useCallback(() => {
    return fetch(`${API}/companies`).then(r => r.json()).then(setCompanies)
  }, [])

  const fetchPendingCompanies = useCallback(() => {
    return fetch(`${API}/pending-companies`).then(r => r.json()).then(setPendingCompanies)
  }, [])

  const deleteCompany = useCallback(async (id) => {
    await fetch(`${API}/companies/${id}`, { method: 'DELETE' })
    fetchCompanies()
  }, [fetchCompanies])

  const reprocessCompany = useCallback(async (id) => {
    await fetch(`${API}/companies/${id}/reprocess`, { method: 'POST' })
    fetchCompanies()
  }, [fetchCompanies])

  const refresh = useCallback(() => {
    fetchCompanies()
    fetchPendingCompanies()
  }, [fetchCompanies, fetchPendingCompanies])

  useEffect(() => {
    let es
    const connect = () => {
      es = new EventSource(`${API}/pending-companies/stream`)
      es.onmessage = (e) => {
        try {
          const list = JSON.parse(e.data)
          setPendingCompanies(list)
          if (list.some(p => p.status === 'done')) fetchCompanies()
        } catch {}
      }
      es.onerror = () => { es.close(); setTimeout(connect, 5000) }
    }
    connect()
    const poll = setInterval(() => { fetchPendingCompanies(); fetchCompanies() }, 5000)
    return () => { es?.close(); clearInterval(poll) }
  }, [fetchCompanies, fetchPendingCompanies])

  return {
    companies, setCompanies, pendingCompanies,
    fetchCompanies, fetchPendingCompanies,
    deleteCompany, reprocessCompany, refresh
  }
}
