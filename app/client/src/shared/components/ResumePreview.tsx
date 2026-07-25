import React, { useMemo } from 'react'

function cleanHtml(html) {
  if (!html) return ''
  let out = html
  // Strip <style> blocks
  out = out.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
  // Strip inline style attributes
  out = out.replace(/\s*style="[^"]*"/gi, '')
  out = out.replace(/\s*style='[^']*'/gi, '')
  // Strip <html>, <head>, <body> wrapper tags (keep inner content)
  out = out.replace(/<\/?html[^>]*>/gi, '')
  out = out.replace(/<\/?head[^>]*>/gi, '')
  out = out.replace(/<\/?body[^>]*>/gi, '')
  // Strip <meta> and <link> tags
  out = out.replace(/<meta[^>]*>/gi, '')
  out = out.replace(/<link[^>]*>/gi, '')
  // Strip common emoji characters (unicode emoji ranges)
  out = out.replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{FE00}-\u{FE0F}\u{1F900}-\u{1F9FF}\u{200D}\u{20E3}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2702}-\u{27B0}]/gu, '')
  // Trim whitespace
  out = out.trim()
  return out
}

export default function ResumePreview({ html, className = '' }) {
  const cleaned = useMemo(() => cleanHtml(html), [html])

  if (!cleaned) {
    return (
      <div className={`resume-preview-container ${className}`}>
        <div className="p-8 text-center text-gray-400 text-sm">No content</div>
      </div>
    )
  }

  return (
    <div className={`resume-preview-container ${className}`}>
      <div
        className="resume-body"
        dangerouslySetInnerHTML={{ __html: cleaned }}
      />
    </div>
  )
}
