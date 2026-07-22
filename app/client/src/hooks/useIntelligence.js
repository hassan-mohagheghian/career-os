import { useState, useCallback } from 'react'

const API = '/api'

export function useIntelligence(refreshJobs) {
  const [analysis, setAnalysis] = useState(null)
  const [timestamps, setTimestamps] = useState({})
  const [intelligenceSubTab, setIntelligenceSubTab] = useState('market')
  const [refreshing, setRefreshing] = useState({})

  const fetchAnalysis = useCallback(() => {
    return fetch(`${API}/intelligence`)
      .then(r => r.ok ? r.json() : null)
      .then(data => setAnalysis(data))
      .catch(() => setAnalysis(null))
  }, [])

  const fetchTimestamps = useCallback(() => {
    return fetch(`${API}/intelligence/timestamps`)
      .then(r => r.ok ? r.json() : {})
      .then(data => setTimestamps(data))
      .catch(() => setTimestamps({}))
  }, [])

  const refreshSection = useCallback(async (section, endpoint) => {
    setRefreshing(r => ({ ...r, [section]: true }))
    try {
      await fetch(`${API}${endpoint}`, { method: 'POST' })
    } catch {}
    refreshJobs?.()
    await Promise.all([fetchAnalysis(), fetchTimestamps()])
    setRefreshing(r => ({ ...r, [section]: false }))
  }, [refreshJobs, fetchAnalysis, fetchTimestamps])

  const refreshAnalysis = useCallback(() => refreshSection('all', '/intelligence/refresh'), [refreshSection])
  const refreshStrategy = useCallback(() => refreshSection('strategy', '/intelligence/strategy/refresh'), [refreshSection])
  const refreshNetworking = useCallback(() => refreshSection('networking', '/intelligence/networking/refresh'), [refreshSection])
  const refreshSkills = useCallback(() => refreshSection('skills', '/intelligence/skills/refresh'), [refreshSection])
  const refreshMarket = useCallback(() => refreshSection('market', '/intelligence/market/refresh'), [refreshSection])
  const refreshOpportunity = useCallback(() => refreshSection('opportunity', '/intelligence/opportunity/refresh'), [refreshSection])

  // Get the last updated time for a section (falls back to 'all' if section-specific not available)
  const getLastUpdated = useCallback((section) => {
    return timestamps[section] || timestamps['all'] || null
  }, [timestamps])

  return {
    analysis, setAnalysis, timestamps,
    intelligenceSubTab, setIntelligenceSubTab, refreshing,
    fetchAnalysis, fetchTimestamps, getLastUpdated,
    refreshAnalysis, refreshStrategy, refreshNetworking,
    refreshSkills, refreshMarket, refreshOpportunity
  }
}
