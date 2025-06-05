import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import axios from 'axios'
import { toast } from 'sonner'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Lightbulb, Mail, Lock, User, LogIn, UserPlus } from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

interface AuthProps {
  onAuthenticated: (token: string, user: any) => void
}

export function Auth({ onAuthenticated }: AuthProps) {
  const [isLogin, setIsLogin] = useState(true)
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: ''
  })

  const loginMutation = useMutation({
    mutationFn: async (data: { email: string; password: string }) => {
      const response = await axios.post(`${API_BASE}/auth/login`, data)
      return response.data
    },
    onSuccess: (data) => {
      localStorage.setItem('auth_token', data.access_token)
      onAuthenticated(data.access_token, data.user)
      toast.success('Welcome back! 🎉')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Login failed')
    },
  })

  const registerMutation = useMutation({
    mutationFn: async (data: { email: string; password: string; name: string }) => {
      const response = await axios.post(`${API_BASE}/auth/register`, data)
      return response.data
    },
    onSuccess: (data) => {
      localStorage.setItem('auth_token', data.access_token)
      onAuthenticated(data.access_token, data.user)
      toast.success('Account created successfully! ✨')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Registration failed')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (isLogin) {
      loginMutation.mutate({
        email: formData.email,
        password: formData.password
      })
    } else {
      if (!formData.name.trim()) {
        toast.error('Please enter your name')
        return
      }
      registerMutation.mutate({
        email: formData.email,
        password: formData.password,
        name: formData.name
      })
    }
  }

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const isLoading = loginMutation.isPending || registerMutation.isPending

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted/20 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="p-3 rounded-full bg-primary/10">
              <Lightbulb className="h-8 w-8 text-primary" />
            </div>
          </div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-foreground to-muted-foreground bg-clip-text text-transparent">
            Gotham Lights
          </h1>
          <p className="text-muted-foreground mt-2">
            Smart curtain light automation
          </p>
        </div>

        {/* Auth Card */}
        <Card>
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl">
              {isLogin ? 'Welcome back' : 'Create account'}
            </CardTitle>
            <CardDescription>
              {isLogin 
                ? 'Sign in to your account to control your lights'
                : 'Get started with your smart lighting automation'
              }
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <form onSubmit={handleSubmit} className="space-y-4">
              {!isLogin && (
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="name"
                      type="text"
                      placeholder="John Doe"
                      value={formData.name}
                      onChange={(e) => handleInputChange('name', e.target.value)}
                      className="pl-10"
                      required={!isLogin}
                    />
                  </div>
                </div>
              )}
              
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="you@example.com"
                    value={formData.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    className="pl-10"
                    required
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={(e) => handleInputChange('password', e.target.value)}
                    className="pl-10"
                    required
                    minLength={6}
                  />
                </div>
              </div>
              
              <Button 
                type="submit" 
                className="w-full" 
                disabled={isLoading}
              >
                {isLoading ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    {isLogin ? 'Signing in...' : 'Creating account...'}
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    {isLogin ? <LogIn className="h-4 w-4" /> : <UserPlus className="h-4 w-4" />}
                    {isLogin ? 'Sign In' : 'Create Account'}
                  </div>
                )}
              </Button>
            </form>

            {/* Toggle between login/register */}
            <div className="text-center">
              <Button 
                variant="ghost" 
                onClick={() => {
                  setIsLogin(!isLogin)
                  setFormData({ email: '', password: '', name: '' })
                }}
                className="text-sm"
              >
                {isLogin ? (
                  <>Don't have an account? <span className="font-medium ml-1">Sign up</span></>
                ) : (
                  <>Already have an account? <span className="font-medium ml-1">Sign in</span></>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Demo Note */}
        <div className="text-center mt-6 text-sm text-muted-foreground">
          <p>🎯 Demo credentials available for testing</p>
        </div>
      </div>
    </div>
  )
} 