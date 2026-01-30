import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Loader2, User, Lock, Eye, EyeOff } from 'lucide-react'
import toast from 'react-hot-toast'
import { Button, Input, Card, CardHeader, CardTitle, CardContent } from '@/components/ui'
import { authService } from '@/services/authService'
import { useAuthStore } from '@/stores/authStore'
import { useLanguage } from '@/contexts/LanguageContext'
import { LanguageSwitcher } from '@/components/LanguageSwitcher'

const loginSchema = z.object({
  username: z.string().min(3, 'Login kamida 3 ta belgi bo\'lishi kerak'),
  password: z.string().min(1, 'Parol kiriting'),
})

type LoginForm = z.infer<typeof loginSchema>

export default function LoginPage() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const { t, language, setLanguage } = useLanguage()
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginForm) => {
    setIsLoading(true)
    try {
      const response = await authService.login(data)
      
      // Extract tokens from response.tokens
      setAuth(
        response.user, 
        response.tokens.access_token, 
        response.tokens.refresh_token
      )
      
      // Set language from user's preference
      if (response.user.language) {
        setLanguage(response.user.language as 'uz' | 'ru' | 'uz_cyrl')
      }
      
      const welcomeText = language === 'ru' ? 'Добро пожаловать' : language === 'uz_cyrl' ? 'Хуш келибсиз' : 'Xush kelibsiz'
      toast.success(`${welcomeText}, ${response.user.first_name}!`)
      navigate('/')
    } catch (error: any) {
      // Handle different error formats
      let message = t('loginError')
      
      try {
        if (error.response?.data?.detail) {
          const detail = error.response.data.detail
          // FastAPI validation error - array of objects
          if (Array.isArray(detail)) {
            message = detail.map((d: any) => {
              if (typeof d === 'string') return d
              if (d && typeof d === 'object' && d.msg) return String(d.msg)
              return t('errorOccurred')
            }).join(', ')
          } else if (typeof detail === 'string') {
            message = detail
          } else if (typeof detail === 'object' && detail.msg) {
            message = String(detail.msg)
          } else {
            message = JSON.stringify(detail)
          }
        } else if (error.response?.data?.message) {
          message = String(error.response.data.message)
        } else if (error.message) {
          message = String(error.message)
        }
      } catch {
        message = t('errorOccurred')
      }
      
      // Ensure message is always a string
      toast.error(String(message))
    } finally {
      setIsLoading(false)
    }
  }

  // Translated labels
  const labels = {
    title: language === 'ru' ? 'Вход в систему' : language === 'uz_cyrl' ? 'Тизимга кириш' : 'Tizimga kirish',
    subtitle: language === 'ru' ? 'Введите логин и пароль' : language === 'uz_cyrl' ? 'Логин ва паролингизни киритинг' : 'Login va parolingizni kiriting',
    loginLabel: language === 'ru' ? 'Логин' : 'Login',
    loginPlaceholder: language === 'ru' ? 'Введите логин' : language === 'uz_cyrl' ? 'Логин киритинг' : 'Login kiriting',
    passwordLabel: language === 'ru' ? 'Пароль' : language === 'uz_cyrl' ? 'Парол' : 'Parol',
    passwordPlaceholder: language === 'ru' ? 'Введите пароль' : language === 'uz_cyrl' ? 'Парол киритинг' : 'Parol kiriting',
    loginButton: language === 'ru' ? 'Войти' : language === 'uz_cyrl' ? 'Кириш' : 'Kirish',
    loggingIn: language === 'ru' ? 'Вход...' : language === 'uz_cyrl' ? 'Кириш...' : 'Kirish...',
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      {/* Language Switcher at top right */}
      <div className="absolute top-4 right-4">
        <LanguageSwitcher variant="default" />
      </div>

      <Card className="w-full max-w-md">
        <CardHeader className="text-center p-6 lg:p-8">
          <div className="mx-auto mb-6">
            <img 
              src="/logo.png" 
              alt="G'ayrat Stroy House" 
              className="h-24 lg:h-28 w-auto object-contain mx-auto"
            />
          </div>
          <CardTitle className="text-xl lg:text-pos-xl">{labels.title}</CardTitle>
          <p className="text-text-secondary mt-2 text-sm lg:text-base">{labels.subtitle}</p>
        </CardHeader>
        <CardContent className="p-6 lg:p-8 pt-0 lg:pt-0">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5 lg:space-y-6">
            {/* Username */}
            <div className="space-y-2">
              <label className="text-sm lg:text-pos-base font-medium">{labels.loginLabel}</label>
              <Input
                {...register('username')}
                icon={<User className="w-5 h-5" />}
                placeholder={labels.loginPlaceholder}
                autoComplete="username"
                className={`text-base ${errors.username ? 'border-danger' : ''}`}
              />
              {errors.username && (
                <p className="text-danger text-sm">{errors.username.message}</p>
              )}
            </div>

            {/* Password */}
            <div className="space-y-2">
              <label className="text-sm lg:text-pos-base font-medium">{labels.passwordLabel}</label>
              <div className="relative">
                <Input
                  {...register('password')}
                  type={showPassword ? 'text' : 'password'}
                  icon={<Lock className="w-5 h-5" />}
                  placeholder={labels.passwordPlaceholder}
                  autoComplete="current-password"
                  className={`text-base ${errors.password ? 'border-danger' : ''}`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text-primary p-1"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {errors.password && (
                <p className="text-danger text-sm">{errors.password.message}</p>
              )}
            </div>

            {/* Submit */}
            <Button
              type="submit"
              size="lg"
              className="w-full text-base py-4"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  {labels.loggingIn}
                </>
              ) : (
                labels.loginButton
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
