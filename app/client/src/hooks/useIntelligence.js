import { useState, useCallback } from 'react'

const API = '/api'

export function useIntelligence(refreshJobs) {
  const [analysis, setAnalysis] = useState(null)
  const [intelligenceSubTab, setIntelligenceSubTab] = useState('market')
  const [refreshing, setRefreshing] = useState({})

  const fetchAnalysis = useCallback(() => {
    return fetch(`${API}/intelligence`)
      .then(r => r.ok ? r.json() : null)
      .then(data => setAnalysis(data))
      .catch(() => setAnalysis(null))
  }, [])

  const refreshSection = useCallback(async (section, endpoint) => {
    setRefreshing(r => ({ ...r, [section]: true }))
    try {
      await fetch(`${API}${endpoint}`, { method: 'POST' })
    } catch {}
    refreshJobs?.()
    await fetchAnalysis()
    setRefreshing(r => ({ ...r, [section]: false }))
  }, [refreshJobs, fetchAnalysis])

  const refreshAnalysis = useCallback(() => refreshSection('analysis', '/intelligence/refresh'), [refreshSection])
  const refreshStrategy = useCallback(() => refreshSection('strategy', '/intelligence/strategy/refresh'), [refreshSection])
  const refreshNetworking = useCallback(() => refreshSection('networking', '/intelligence/networking/refresh'), [refreshSection])
  const refreshSkills = useCallback(() => refreshSection('skills', '/intelligence/skills/refresh'), [refreshSection])
  const refreshMarket = useCallback(() => refreshSection('market', '/intelligence/market/refresh'), [refreshSection])
  const refreshOpportunity = useCallback(() => refreshSection('opportunity', '/intelligence/opportunities/refresh'), [refreshSection])

  return {
    analysis, setAnalysis, intelligenceSubTab, setIntelligenceSubTab, refreshing,
    fetchAnalysis, refreshAnalysis, refreshStrategy, refreshNetworking,
    refreshSkills, refreshMarket, refreshOpportunity
  }
}
