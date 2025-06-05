import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  Settings as SettingsIcon, 
  Lightbulb, 
  Wifi, 
  TestTube, 
  Check, 
  X, 
  RefreshCw,
  ExternalLink,
  Calendar,
  Youtube,
  CreditCard,
  Link,
  CheckCircle,
  AlertCircle,
  Palette
} from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

interface Device {
  device: string
  model: string
  deviceName: string
  controllable: boolean
  retrievable: boolean
}

interface DeviceConfig {
  device_id: string
  model: string
  name: string
}

interface ColorPattern {
  r: number
  g: number
  b: number
}

interface SettingsProps {
  authToken: string
}

export function Settings({ authToken }: SettingsProps) {
  const [testColor, setTestColor] = useState('#ff0000')
  const [testScene, setTestScene] = useState('1')
  const [isTestingLight, setIsTestingLight] = useState(false)
  const queryClient = useQueryClient()

  const axiosConfig = {
    headers: { Authorization: `Bearer ${authToken}` }
  }

  // Fetch available devices
  const { data: devicesData, isLoading: devicesLoading } = useQuery({
    queryKey: ['devices'],
    queryFn: async (): Promise<{ devices: Device[] }> => {
      const response = await axios.get(`${API_BASE}/devices`, axiosConfig)
      return response.data
    },
  })

  // Fetch current device config
  const { data: deviceConfig, refetch: refetchDeviceConfig } = useQuery({
    queryKey: ['deviceConfig'],
    queryFn: async (): Promise<DeviceConfig> => {
      const response = await axios.get(`${API_BASE}/config/device`, axiosConfig)
      return response.data
    },
  })

  // Fetch color patterns
  const { data: colorPatterns, isLoading: patternsLoading } = useQuery({
    queryKey: ['colorPatterns'],
    queryFn: async (): Promise<{ patterns: Record<string, ColorPattern> }> => {
      const response = await axios.get(`${API_BASE}/color-patterns`, axiosConfig)
      return response.data
    },
  })

  // Fetch scene configuration
  const { data: sceneConfig, isLoading: sceneLoading } = useQuery({
    queryKey: ['sceneConfig'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE}/config/scene`, axiosConfig)
      return response.data
    },
  })

  // Fetch OAuth status
  const { data: oauthStatus, isLoading: oauthLoading } = useQuery({
    queryKey: ['oauthStatus'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE}/oauth/status`, axiosConfig)
      return response.data
    },
  })

  // Update device config mutation
  const updateDeviceMutation = useMutation({
    mutationFn: async (device: DeviceConfig) => {
      const response = await axios.put(`${API_BASE}/config/device`, device, axiosConfig)
      return response.data
    },
    onSuccess: () => {
      toast.success('Device updated successfully! ✨')
      refetchDeviceConfig()
    },
    onError: () => {
      toast.error('Failed to update device')
    },
  })

  // Update scene configuration
  const updateSceneMutation = useMutation({
    mutationFn: async (newConfig: any) => {
      const response = await axios.put(`${API_BASE}/config/scene`, newConfig, axiosConfig)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sceneConfig'] })
      toast.success('Scene configuration updated!')
    },
    onError: () => {
      toast.error('Failed to update scene configuration')
    },
  })

  // Test light mutation
  const testLightMutation = useMutation({
    mutationFn: async (action: { action: string; value?: any }) => {
      const response = await axios.post(`${API_BASE}/test/light`, action, axiosConfig)
      return response.data
    },
    onSuccess: () => {
      toast.success('Light test successful!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Light test failed')
    },
  })

  // OAuth authorization
  const authorizeMutation = useMutation({
    mutationFn: async (service: 'google' | 'stripe') => {
      const response = await axios.get(`${API_BASE}/oauth/${service}/authorize`, axiosConfig)
      return response.data
    },
    onSuccess: (data) => {
      // Open OAuth URL in popup or redirect
      window.open(data.oauth_url, '_blank', 'width=600,height=700')
      // Refresh OAuth status after a delay
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['oauthStatus'] })
      }, 2000)
    },
    onError: () => {
      toast.error('Failed to start OAuth flow')
    },
  })

  const handleDeviceSelect = (device: Device) => {
    updateDeviceMutation.mutate({
      device_id: device.device,
      model: device.model,
      name: device.deviceName
    })
  }

  const handleSceneChange = (trigger: string, sceneId: string) => {
    const newConfig = {
      ...sceneConfig,
      [trigger]: parseInt(sceneId)
    }
    updateSceneMutation.mutate(newConfig)
  }

  const handleTestLight = async (action: string, value?: any) => {
    setIsTestingLight(true)
    try {
      await testLightMutation.mutateAsync({ action, value })
    } finally {
      setIsTestingLight(false)
    }
  }

  const handleOAuth = (service: 'google' | 'stripe') => {
    authorizeMutation.mutate(service)
  }

  const handleColorTest = () => {
    const hex = testColor.replace('#', '')
    const r = parseInt(hex.substr(0, 2), 16)
    const g = parseInt(hex.substr(2, 2), 16)
    const b = parseInt(hex.substr(4, 2), 16)
    handleTestLight('color', { r, g, b })
  }

  const rgbToHex = (r: number, g: number, b: number) => {
    return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`
  }

  const getColorPreview = (sceneId: number) => {
    const color = colorPatterns?.patterns?.[sceneId]
    if (!color) return '#ffffff'
    return `rgb(${color.r}, ${color.g}, ${color.b})`
  }

  const isLoading = devicesLoading || sceneLoading || patternsLoading || oauthLoading

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted/20 p-4">
      <div className="container mx-auto max-w-4xl">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <SettingsIcon className="h-8 w-8" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-foreground to-muted-foreground bg-clip-text text-transparent">
              Settings
            </h1>
          </div>
          <p className="text-lg text-muted-foreground">
            Configure your devices and test integrations
          </p>
        </div>

        <div className="grid gap-6">
          {/* Device Selection */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Lightbulb className="h-5 w-5" />
                <CardTitle>Govee Device Selection</CardTitle>
              </div>
              <CardDescription>
                Choose which Govee device to control
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {devicesLoading ? (
                <div className="text-center py-4">
                  <Wifi className="h-6 w-6 mx-auto mb-2 animate-pulse" />
                  <p className="text-muted-foreground">Loading devices...</p>
                </div>
              ) : (
                <>
                  <div className="grid gap-3">
                    {devicesData?.devices?.map((device) => (
                      <div
                        key={device.device}
                        className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                          deviceConfig?.device_id === device.device
                            ? 'border-primary bg-primary/5'
                            : 'border-border hover:border-primary/50'
                        }`}
                        onClick={() => handleDeviceSelect(device)}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="font-medium">{device.deviceName}</h3>
                            <p className="text-sm text-muted-foreground">
                              {device.model} • {device.device}
                            </p>
                          </div>
                          <div className="flex gap-2">
                            {device.controllable && (
                              <Badge variant="secondary">Controllable</Badge>
                            )}
                            {deviceConfig?.device_id === device.device && (
                              <Badge variant="default">Selected</Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  {deviceConfig && (
                    <div className="p-4 bg-muted/50 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        <span className="font-medium">Current Device</span>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {deviceConfig.name} ({deviceConfig.model})
                      </p>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>

          {/* Color Patterns */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Palette className="h-5 w-5" />
                <CardTitle>Available Color Patterns</CardTitle>
              </div>
              <CardDescription>
                Pre-defined color scenes for events
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {colorPatterns && Object.entries(colorPatterns.patterns).map(([id, color]) => (
                  <div key={id} className="text-center">
                    <div
                      className="w-16 h-16 rounded-lg border-2 border-border mx-auto mb-2 cursor-pointer hover:scale-105 transition-transform"
                      style={{ backgroundColor: rgbToHex(color.r, color.g, color.b) }}
                      onClick={() => handleTestLight('scene', parseInt(id))}
                      title={`Pattern ${id}: RGB(${color.r}, ${color.g}, ${color.b})`}
                    />
                    <p className="text-xs text-muted-foreground">Scene {id}</p>
                  </div>
                ))}
              </div>
              <p className="text-sm text-muted-foreground mt-4">
                Click any color to test it on your lights
              </p>
            </CardContent>
          </Card>

          {/* Light Testing */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <TestTube className="h-5 w-5" />
                <CardTitle>Light Testing</CardTitle>
              </div>
              <CardDescription>
                Test your light controls to make sure everything works
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Basic Controls */}
              <div>
                <h4 className="font-medium mb-3">Basic Controls</h4>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => handleTestLight('on')}
                    disabled={isTestingLight}
                  >
                    Turn On
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => handleTestLight('off')}
                    disabled={isTestingLight}
                  >
                    Turn Off
                  </Button>
                </div>
              </div>

              {/* Color Testing */}
              <div>
                <h4 className="font-medium mb-3">Custom Color Testing</h4>
                <div className="flex gap-2 items-center">
                  <input
                    type="color"
                    value={testColor}
                    onChange={(e) => setTestColor(e.target.value)}
                    className="w-12 h-10 rounded border cursor-pointer"
                  />
                  <Button
                    variant="outline"
                    onClick={handleColorTest}
                    disabled={isTestingLight}
                  >
                    Test Color
                  </Button>
                  <span className="text-sm text-muted-foreground">
                    {testColor.toUpperCase()}
                  </span>
                </div>
              </div>

              {/* Scene Testing */}
              <div>
                <h4 className="font-medium mb-3">Scene Testing by ID</h4>
                <div className="flex gap-2 items-center">
                  <Input
                    type="number"
                    min="0"
                    max="10"
                    value={testScene}
                    onChange={(e) => setTestScene(e.target.value)}
                    placeholder="Scene ID"
                    className="w-24"
                  />
                  <Button
                    variant="outline"
                    onClick={() => handleTestLight('scene', parseInt(testScene))}
                    disabled={isTestingLight || !testScene}
                  >
                    Test Scene
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Integration Setup */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5" />
                <CardTitle>Integration Setup</CardTitle>
              </div>
              <CardDescription>
                Complete setup instructions for each service
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Stripe Setup */}
              <div className="space-y-2">
                <h4 className="font-medium flex items-center gap-2">
                  💰 Stripe Webhooks
                </h4>
                <div className="text-sm space-y-1 text-muted-foreground">
                  <p>1. Get your Stripe secret key from the dashboard</p>
                  <p>2. Create a webhook endpoint: <code className="bg-muted px-1 rounded">your-domain.com/stripe</code></p>
                  <p>3. Select events: <code className="bg-muted px-1 rounded">payment_intent.succeeded</code> and <code className="bg-muted px-1 rounded">checkout.session.completed</code></p>
                  <p>4. Copy the webhook signing secret</p>
                </div>
              </div>

              {/* YouTube Setup */}
              <div className="space-y-2">
                <h4 className="font-medium flex items-center gap-2">
                  🔴 YouTube Data API
                </h4>
                <div className="text-sm space-y-1 text-muted-foreground">
                  <p>1. Go to Google Cloud Console</p>
                  <p>2. Enable YouTube Data API v3</p>
                  <p>3. Create API credentials (API Key)</p>
                  <p>4. Your channel must be verified for subscriber data</p>
                </div>
              </div>

              {/* Calendar Setup */}
              <div className="space-y-2">
                <h4 className="font-medium flex items-center gap-2">
                  📅 Google Calendar
                </h4>
                <div className="text-sm space-y-1 text-muted-foreground">
                  <p>1. Create a service account in Google Cloud Console</p>
                  <p>2. Enable Google Calendar API</p>
                  <p>3. Download the service account JSON key</p>
                  <p>4. Share your calendar with the service account email</p>
                  <p>5. Extract client_email and private_key for .env</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* OAuth Integrations */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Link className="h-5 w-5" />
                Connected Services
              </CardTitle>
              <CardDescription>
                Connect your accounts to enable automated light triggers
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Google Integration */}
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-full bg-red-100 dark:bg-red-900/20">
                    <div className="w-5 h-5 bg-gradient-to-r from-blue-500 via-red-500 to-yellow-500 rounded-full" />
                  </div>
                  <div>
                    <p className="font-medium">Google Account</p>
                    <p className="text-sm text-muted-foreground">
                      Calendar events & YouTube subscribers
                    </p>
                    {oauthStatus?.google?.connected && (
                      <div className="flex gap-1 mt-1">
                        <Badge variant="secondary" className="text-xs">
                          <Calendar className="w-3 h-3 mr-1" />
                          Calendar
                        </Badge>
                        <Badge variant="secondary" className="text-xs">
                          <Youtube className="w-3 h-3 mr-1" />
                          YouTube
                        </Badge>
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {oauthStatus?.google?.connected ? (
                    <div className="flex items-center gap-2 text-green-600">
                      <CheckCircle className="h-4 w-4" />
                      <span className="text-sm font-medium">Connected</span>
                    </div>
                  ) : (
                    <Button 
                      onClick={() => handleOAuth('google')}
                      disabled={authorizeMutation.isPending}
                      variant="outline"
                      size="sm"
                    >
                      <ExternalLink className="h-4 w-4 mr-2" />
                      Connect
                    </Button>
                  )}
                </div>
              </div>

              {/* Stripe Integration */}
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-full bg-purple-100 dark:bg-purple-900/20">
                    <CreditCard className="h-5 w-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="font-medium">Stripe Account</p>
                    <p className="text-sm text-muted-foreground">
                      Payment notifications & webhooks
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {oauthStatus?.stripe?.connected ? (
                    <div className="flex items-center gap-2 text-green-600">
                      <CheckCircle className="h-4 w-4" />
                      <span className="text-sm font-medium">Connected</span>
                    </div>
                  ) : (
                    <Button 
                      onClick={() => handleOAuth('stripe')}
                      disabled={authorizeMutation.isPending}
                      variant="outline"
                      size="sm"
                    >
                      <ExternalLink className="h-4 w-4 mr-2" />
                      Connect
                    </Button>
                  )}
                </div>
              </div>

              {!oauthStatus?.google?.connected && !oauthStatus?.stripe?.connected && (
                <div className="flex items-center gap-2 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg">
                  <AlertCircle className="h-4 w-4 text-amber-600" />
                  <p className="text-sm text-amber-800 dark:text-amber-200">
                    Connect your services to enable automated light triggers
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
} 