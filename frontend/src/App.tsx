import { useState, useEffect } from 'react'
import { QueryClient, QueryClientProvider, useQuery, useMutation } from '@tanstack/react-query'
import axios from 'axios'
import { toast, Toaster } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { DollarSign, Calendar, Youtube, Lightbulb, Settings as SettingsIcon, Home, LogOut, User, RefreshCw } from 'lucide-react'
import { Settings } from '@/components/Settings'
import { Auth } from './components/Auth'

const queryClient = new QueryClient()

interface SceneConfig {
  stripe: number
  calendar: number
  youtube: number
}

interface ColorPattern {
  r: number
  g: number
  b: number
}

const API_BASE = import.meta.env.VITE_API_URL || '/api'

function SceneCard({ 
  type, 
  icon: Icon, 
  title, 
  description, 
  currentValue, 
  accentColor,
  colorPreview,
  onSave 
}: {
  type: keyof SceneConfig
  icon: any
  title: string
  description: string
  currentValue: number
  accentColor: string
  colorPreview?: string
  onSave: (value: number) => void
}) {
  const [value, setValue] = useState(currentValue.toString())

  useEffect(() => {
    setValue(currentValue.toString())
  }, [currentValue])

  const handleSave = () => {
    const numValue = parseInt(value, 10)
    if (!isNaN(numValue) && numValue >= 0) {
      onSave(numValue)
    }
  }

  return (
    <Card className="w-full max-w-sm">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <div className={`p-2 rounded-lg ${accentColor}`}>
            <Icon className="h-4 w-4 text-white" />
          </div>
          <div className="flex-1">
            <CardTitle className="text-lg">{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Current:</span>
          <Badge variant="secondary">Scene {currentValue}</Badge>
          {colorPreview && (
            <div
              className="w-4 h-4 rounded border"
              style={{ backgroundColor: colorPreview }}
              title="Light color for this scene"
            />
          )}
        </div>
        <div className="flex gap-2">
          <Input
            type="number"
            min="0"
            max="10"
            placeholder="Scene ID"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            className="flex-1"
          />
          <Button onClick={handleSave} size="sm">
            Save
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

function Dashboard({ authToken }: { authToken: string }) {
  const { data: config, refetch } = useQuery({
    queryKey: ['config'],
    queryFn: async (): Promise<SceneConfig> => {
      const response = await axios.get(`${API_BASE}/config/scene`, {
        headers: { Authorization: `Bearer ${authToken}` }
      })
      return response.data
    },
    refetchInterval: 5000, // Refetch every 5 seconds
  })

  // Fetch color patterns for preview
  const { data: colorPatterns } = useQuery({
    queryKey: ['colorPatterns'],
    queryFn: async (): Promise<{ patterns: Record<string, ColorPattern> }> => {
      const response = await axios.get(`${API_BASE}/color-patterns`, {
        headers: { Authorization: `Bearer ${authToken}` }
      })
      return response.data
    },
  })

  const mutation = useMutation({
    mutationFn: async (newConfig: SceneConfig) => {
      const response = await axios.put(`${API_BASE}/config/scene`, newConfig, {
        headers: { Authorization: `Bearer ${authToken}` }
      })
      return response.data
    },
    onSuccess: () => {
      toast.success('Scene configuration saved! ✨')
      refetch()
    },
    onError: () => {
      toast.error('Failed to save configuration')
    },
  })

  const handleSave = (type: keyof SceneConfig, value: number) => {
    if (config) {
      mutation.mutate({
        ...config,
        [type]: value
      })
    }
  }

  const rgbToHex = (r: number, g: number, b: number) => {
    return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`
  }

  const getColorPreview = (sceneId: number) => {
    if (!colorPatterns?.patterns) return undefined
    const pattern = colorPatterns.patterns[sceneId.toString()]
    return pattern ? rgbToHex(pattern.r, pattern.g, pattern.b) : undefined
  }

  if (!config) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Lightbulb className="h-8 w-8 mx-auto mb-4 animate-pulse" />
          <p className="text-muted-foreground">Loading configuration...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted/20">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Lightbulb className="h-8 w-8" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-foreground to-muted-foreground bg-clip-text text-transparent">
              Gotham Lights
            </h1>
          </div>
          <p className="text-lg text-muted-foreground max-w-md mx-auto">
            Configure your curtain light colors for different triggers
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          <SceneCard
            type="stripe"
            icon={DollarSign}
            title="Stripe Payments"
            description="Successful payments & checkouts"
            currentValue={config.stripe}
            accentColor="bg-green-500"
            colorPreview={getColorPreview(config.stripe)}
            onSave={(value) => handleSave('stripe', value)}
          />
          
          <SceneCard
            type="calendar"
            icon={Calendar}
            title="Calendar Events"
            description="Events starting ≤ 10 minutes"
            currentValue={config.calendar}
            accentColor="bg-blue-500"
            colorPreview={getColorPreview(config.calendar)}
            onSave={(value) => handleSave('calendar', value)}
          />
          
          <SceneCard
            type="youtube"
            icon={Youtube}
            title="YouTube Subscribers"
            description="New channel subscribers"
            currentValue={config.youtube}
            accentColor="bg-red-500"
            colorPreview={getColorPreview(config.youtube)}
            onSave={(value) => handleSave('youtube', value)}
          />
        </div>

        <div className="text-center mt-8">
          <div className="text-sm text-muted-foreground mb-2">
            Lights will flash these colors when events occur (auto-off after 3 seconds)
          </div>
          <div className="flex justify-center gap-4 text-xs">
            <div className="flex items-center gap-1">
              <span>💰 Stripe:</span>
              <div
                className="w-3 h-3 rounded border"
                style={{ backgroundColor: getColorPreview(config.stripe) || '#666' }}
              />
              <span className="text-muted-foreground">Scene {config.stripe}</span>
            </div>
            <div className="flex items-center gap-1">
              <span>📅 Calendar:</span>
              <div
                className="w-3 h-3 rounded border"
                style={{ backgroundColor: getColorPreview(config.calendar) || '#666' }}
              />
              <span className="text-muted-foreground">Scene {config.calendar}</span>
            </div>
            <div className="flex items-center gap-1">
              <span>🔴 YouTube:</span>
              <div
                className="w-3 h-3 rounded border"
                style={{ backgroundColor: getColorPreview(config.youtube) || '#666' }}
              />
              <span className="text-muted-foreground">Scene {config.youtube}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function AppContent() {
  const [authToken, setAuthToken] = useState<string | null>(null)
  const [currentUser, setCurrentUser] = useState<any>(null)
  const [currentPage, setCurrentPage] = useState<'dashboard' | 'settings'>('dashboard')

  // Check for existing auth token on app load
  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      setAuthToken(token)
    }
  }, [])

  // Fetch current user info when we have a token
  const { data: userInfo, isLoading: userLoading, error: userError } = useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${authToken}` }
      })
      return response.data
    },
    enabled: !!authToken,
    retry: false
  })

  // Update current user when query succeeds
  useEffect(() => {
    if (userInfo) {
      setCurrentUser(userInfo)
    }
  }, [userInfo])

  // Handle auth token error (invalid/expired)
  useEffect(() => {
    if (userError && authToken) {
      console.log('Auth error, clearing token:', userError)
      handleLogout()
    }
  }, [userError, authToken])

  const handleAuthenticated = (token: string, user: any) => {
    setAuthToken(token)
    setCurrentUser(user)
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    setAuthToken(null)
    setCurrentUser(null)
    setCurrentPage('dashboard')
  }

  // Show auth screen if not authenticated
  if (!authToken) {
    return <Auth onAuthenticated={handleAuthenticated} />
  }

  // Show loading while fetching user info
  if (userLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex items-center gap-3">
          <RefreshCw className="h-6 w-6 animate-spin text-primary" />
          <span className="text-lg">Loading...</span>
        </div>
      </div>
    )
  }

  // Show error if user fetch failed
  if (userError) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-lg text-destructive">Authentication failed</p>
          <Button onClick={handleLogout}>
            Try Again
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation Header */}
      <nav className="border-b border-border bg-card">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo and Brand */}
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <Lightbulb className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h1 className="text-xl font-bold">Gotham Lights</h1>
                <p className="text-xs text-muted-foreground">Smart Automation</p>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex items-center gap-1">
              <Button
                variant={currentPage === 'dashboard' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setCurrentPage('dashboard')}
                className="gap-2"
              >
                <Home className="h-4 w-4" />
                Dashboard
              </Button>
              <Button
                variant={currentPage === 'settings' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setCurrentPage('settings')}
                className="gap-2"
              >
                <SettingsIcon className="h-4 w-4" />
                Settings
              </Button>
            </div>

            {/* User Menu */}
            <div className="flex items-center gap-4">
              {currentUser && (
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <p className="text-sm font-medium">{currentUser.name}</p>
                    <p className="text-xs text-muted-foreground">{currentUser.email}</p>
                  </div>
                  <div className="p-2 rounded-full bg-primary/10">
                    <User className="h-4 w-4 text-primary" />
                  </div>
                </div>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="gap-2 text-muted-foreground hover:text-destructive"
              >
                <LogOut className="h-4 w-4" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentPage === 'dashboard' ? (
          <Dashboard authToken={authToken} />
        ) : (
          <Settings authToken={authToken} />
        )}
      </main>

      {/* Connection Status */}
      <div className="fixed bottom-4 right-4">
        <Badge variant="secondary" className="gap-2 shadow-lg">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          Connected
        </Badge>
      </div>
    </div>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
      <Toaster position="top-right" richColors />
    </QueryClientProvider>
  )
}

export default App 