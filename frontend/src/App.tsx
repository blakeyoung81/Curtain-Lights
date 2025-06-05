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
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      console.log(`${buttonText} Success:`, result)
      
      setResults(prev => ({
        ...prev,
        [testType]: { success: true, data: result, timestamp: new Date() }
      }))
      
    } catch (error) {
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
        
        {/* Header */}
        <div style={{ marginBottom: '3rem' }}>
          <h1 style={{ 
            fontSize: '3rem', 
            fontWeight: 'bold', 
            marginBottom: '1rem',
            background: 'linear-gradient(to right, #60a5fa, #34d399)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            💡 Curtain Lights
          </h1>
          <p style={{ fontSize: '1.2rem', color: '#94a3b8' }}>
            Test your Govee DIY scenes
          </p>
        </div>

        {/* Test Buttons */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
          gap: '2rem',
          marginBottom: '3rem'
        }}>
          
          {/* Payment Test */}
          <div style={{
            backgroundColor: '#1e293b',
            padding: '2rem',
            borderRadius: '1rem',
            border: '1px solid #334155'
          }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>💰</div>
            <h3 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>Payment Test</h3>
            <p style={{ color: '#94a3b8', marginBottom: '1.5rem' }}>
              Triggers Money DIY scene
            </p>
            <button
              onClick={() => handleTest('payment', '/test/payment', 'Payment Test')}
              disabled={loading === 'payment'}
              style={{
                backgroundColor: loading === 'payment' ? '#4b5563' : '#10b981',
                color: 'white',
                border: 'none',
                padding: '0.75rem 1.5rem',
                borderRadius: '0.5rem',
                fontSize: '1rem',
                fontWeight: '600',
                cursor: loading === 'payment' ? 'not-allowed' : 'pointer',
                width: '100%'
              }}
            >
              {loading === 'payment' ? 'Testing...' : 'Test Now'}
            </button>
          </div>

          {/* Subscriber Test */}
          <div style={{
            backgroundColor: '#1e293b',
            padding: '2rem',
            borderRadius: '1rem',
            border: '1px solid #334155'
          }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🎯</div>
            <h3 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>Subscriber Test</h3>
            <p style={{ color: '#94a3b8', marginBottom: '1.5rem' }}>
              Triggers YouTube DIY scene
            </p>
            <button
              onClick={() => handleTest('subscriber', '/test/subscriber-milestone', 'Subscriber Test')}
              disabled={loading === 'subscriber'}
              style={{
                backgroundColor: loading === 'subscriber' ? '#4b5563' : '#ef4444',
                color: 'white',
                border: 'none',
                padding: '0.75rem 1.5rem',
                borderRadius: '0.5rem',
                fontSize: '1rem',
                fontWeight: '600',
                cursor: loading === 'subscriber' ? 'not-allowed' : 'pointer',
                width: '100%'
              }}
            >
              {loading === 'subscriber' ? 'Testing...' : 'Test Now'}
            </button>
          </div>

          {/* Goal Test */}
          <div style={{
            backgroundColor: '#1e293b',
            padding: '2rem',
            borderRadius: '1rem',
            border: '1px solid #334155'
          }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🏆</div>
            <h3 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>Goal Test</h3>
            <p style={{ color: '#94a3b8', marginBottom: '1.5rem' }}>
              Triggers Goal DIY scene (200 subs)
            </p>
            <button
              onClick={() => handleTest('goal', '/test/goal', 'Goal Test')}
              disabled={loading === 'goal'}
              style={{
                backgroundColor: loading === 'goal' ? '#4b5563' : '#8b5cf6',
                color: 'white',
                border: 'none',
                padding: '0.75rem 1.5rem',
                borderRadius: '0.5rem',
                fontSize: '1rem',
                fontWeight: '600',
                cursor: loading === 'goal' ? 'not-allowed' : 'pointer',
                width: '100%'
              }}
            >
              {loading === 'goal' ? 'Testing...' : 'Test Now'}
            </button>
          </div>
        </div>

        {/* Results */}
        {Object.keys(results).length > 0 && (
          <div style={{ textAlign: 'left' }}>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Test Results</h2>
            {Object.entries(results).map(([testType, result]: [string, any]) => (
              <div key={testType} style={{
                backgroundColor: result.success ? '#064e3b' : '#7f1d1d',
                border: `1px solid ${result.success ? '#065f46' : '#991b1b'}`,
                padding: '1rem',
                borderRadius: '0.5rem',
                marginBottom: '1rem'
              }}>
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  marginBottom: '0.5rem'
                }}>
                  <strong>{testType.toUpperCase()}</strong>
                  <span style={{ fontSize: '0.875rem', color: '#94a3b8' }}>
                    {result.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                {result.success ? (
                  <div>
                    <div style={{ color: '#6ee7b7' }}>✅ {result.data.message}</div>
                    {result.data.celebration && (
                      <div style={{ fontSize: '0.875rem', color: '#94a3b8', marginTop: '0.5rem' }}>
                        Scene: {result.data.celebration.scene_name} (ID: {result.data.celebration.scene_id})
                      </div>
                    )}
                  </div>
                ) : (
                  <div style={{ color: '#fca5a5' }}>❌ {result.error}</div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Footer */}
        <div style={{ 
          marginTop: '3rem', 
          padding: '1rem',
          borderTop: '1px solid #334155',
          color: '#94a3b8',
          fontSize: '0.875rem'
        }}>
          <p>Each test triggers a DIY scene for 5 seconds, then returns to previous state</p>
          <p>API: {API_BASE}</p>
        </div>
      </div>
    </div>
  )
}

export default App 