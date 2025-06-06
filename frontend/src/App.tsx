import React, { useState } from 'react'

// Get the API URL from environment or use default
const API_BASE = import.meta.env.VITE_API_URL || 'https://curtain-lights.onrender.com'

function App() {
  const [loading, setLoading] = useState<string | null>(null)
  const [results, setResults] = useState<Record<string, any>>({})

  const handleTest = async (testType: string, endpoint: string, buttonText: string) => {
    setLoading(testType)
    try {
      console.log(`Testing ${buttonText} via ${API_BASE}${endpoint}`)
      
      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      
      const result = await response.json()
      if (!response.ok) {
        throw new Error(result.detail || `HTTP error! status: ${response.status}`)
      }
      
      console.log(`${buttonText} Success:`, result)
      
      setResults(prev => ({
        ...prev,
        [testType]: { success: true, data: result, timestamp: new Date() }
      }))
      
    } catch (error: any) {
      console.error(`${buttonText} Error:`, error)
      setResults(prev => ({
        ...prev,
        [testType]: { success: false, error: error.message, timestamp: new Date() }
      }))
    } finally {
      setLoading(null)
    }
  }

  return (
    <div style={{ 
      minHeight: '100vh', 
      backgroundColor: '#0f172a',
      color: 'white',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      padding: '2rem'
    }}>
      <div style={{ maxWidth: '800px', margin: '0 auto', textAlign: 'center' }}>
        
        <div style={{ marginBottom: '3rem' }}>
          <h1 style={{ 
            fontSize: '3rem', 
            fontWeight: 'bold', 
            marginBottom: '1rem',
            background: 'linear-gradient(to right, #60a5fa, #34d399)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            💡 Curtain Lights Pro
          </h1>
          <p style={{ fontSize: '1.2rem', color: '#94a3b8' }}>
            Trigger continuous, looping color palettes on your Govee lights.
          </p>
        </div>

        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', 
          gap: '1.5rem',
          marginBottom: '3rem'
        }}>
          
          <div style={{ backgroundColor: '#1e293b', padding: '2rem', borderRadius: '1rem', border: '1px solid #334155' }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>💰</div>
            <h3 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>Money Palette</h3>
            <p style={{ color: '#94a3b8', marginBottom: '1.5rem' }}>Loops Green & Gold</p>
            <button onClick={() => handleTest('payment', '/test/payment', 'Payment Test')} disabled={!!loading} style={getButtonStyle('payment', loading, '#10b981')}>
              {loading === 'payment' ? 'Running...' : 'Run Money'}
            </button>
          </div>

          <div style={{ backgroundColor: '#1e293b', padding: '2rem', borderRadius: '1rem', border: '1px solid #334155' }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🎯</div>
            <h3 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>YouTube Palette</h3>
            <p style={{ color: '#94a3b8', marginBottom: '1.5rem' }}>Loops Red & White</p>
            <button onClick={() => handleTest('subscriber', '/test/subscriber-milestone', 'Subscriber Test')} disabled={!!loading} style={getButtonStyle('subscriber', loading, '#ef4444')}>
              {loading === 'subscriber' ? 'Running...' : 'Run YouTube'}
            </button>
          </div>

          <div style={{ backgroundColor: '#1e293b', padding: '2rem', borderRadius: '1rem', border: '1px solid #334155' }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🏆</div>
            <h3 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>Goal Palette</h3>
            <p style={{ color: '#94a3b8', marginBottom: '1.5rem' }}>Loops Purple & Gold</p>
            <button onClick={() => handleTest('goal', '/test/goal', 'Goal Test')} disabled={!!loading} style={getButtonStyle('goal', loading, '#8b5cf6')}>
              {loading === 'goal' ? 'Running...' : 'Run Goal'}
            </button>
          </div>
          
          <div style={{ backgroundColor: '#374151', padding: '2rem', borderRadius: '1rem', border: '1px solid #4b5563' }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🛑</div>
            <h3 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>Stop Animation</h3>
            <p style={{ color: '#d1d5db', marginBottom: '1.5rem' }}>Turn the lights off</p>
            <button onClick={() => handleTest('off', '/test/off', 'Stop Test')} disabled={!!loading} style={getButtonStyle('off', loading, '#6b7280')}>
              {loading === 'off' ? 'Stopping...' : 'Turn Off'}
            </button>
          </div>

        </div>

        {Object.keys(results).length > 0 && (
          <div style={{ textAlign: 'left' }}>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Last Action Result</h2>
            {Object.entries(results)
              .sort(([, a]: [string, any], [, b]: [string, any]) => b.timestamp - a.timestamp)
              .slice(0, 1) // Only show the most recent result
              .map(([testType, result]: [string, any]) => (
                <div key={testType} style={{ backgroundColor: result.success ? '#064e3b' : '#7f1d1d', border: `1px solid ${result.success ? '#065f46' : '#991b1b'}`, padding: '1rem', borderRadius: '0.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <strong>{testType.toUpperCase()}</strong>
                    <span style={{ fontSize: '0.875rem', color: '#94a3b8' }}>{result.timestamp.toLocaleTimeString()}</span>
                  </div>
                  {result.success ? (
                    <div>
                      <div style={{ color: '#6ee7b7' }}>✅ {result.data.message}</div>
                      {result.data.palette_name && <div style={{ fontSize: '0.875rem', color: '#94a3b8', marginTop: '0.5rem' }}>Palette: {result.data.palette_name}</div>}
                    </div>
                  ) : (
                    <div style={{ color: '#fca5a5' }}>❌ {result.error}</div>
                  )}
                </div>
              ))}
          </div>
        )}

        <div style={{ marginTop: '3rem', padding: '1rem', borderTop: '1px solid #334155', color: '#94a3b8', fontSize: '0.875rem' }}>
          <p>Each action sends a single command. The palettes will loop until a new command is sent.</p>
          <p>API: {API_BASE}</p>
        </div>
      </div>
    </div>
  )
}

// Helper function for button styling
const getButtonStyle = (buttonType: string, loading: string | null, color: string): React.CSSProperties => ({
  backgroundColor: loading === buttonType ? '#4b5563' : color,
  color: 'white',
  border: 'none',
  padding: '0.75rem 1.5rem',
  borderRadius: '0.5rem',
  fontSize: '1rem',
  fontWeight: '600',
  cursor: loading ? 'not-allowed' : 'pointer',
  width: '100%',
  opacity: loading && loading !== buttonType ? 0.5 : 1,
});

export default App 