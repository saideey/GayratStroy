import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Printer, Plus, Trash2, Edit2, RefreshCw, Loader2,
  Wifi, WifiOff, Copy, Check, TestTube, Users, Link2, Unlink
} from 'lucide-react'
import toast from 'react-hot-toast'
import { Button, Input, Card, CardContent, Badge } from '@/components/ui'
import api from '@/services/api'

interface PrinterData {
  id: number
  name: string
  description?: string
  printer_type: string
  paper_width: number
  connection_type: string
  connection_address?: string
  warehouse_id?: number
  warehouse_name?: string
  is_active: boolean
  is_online: boolean
  last_seen?: string
  agent_token?: string
  assigned_users: Array<{
    user_id: number
    user_name: string
    is_default: boolean
  }>
}

interface UserData {
  id: number
  first_name: string
  last_name: string
  username: string
  role_name: string
}

export default function PrintersSettings() {
  const queryClient = useQueryClient()

  // Modal states
  const [showAddModal, setShowAddModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [showTokenModal, setShowTokenModal] = useState(false)

  // Selected printer
  const [selectedPrinter, setSelectedPrinter] = useState<PrinterData | null>(null)

  // Form states
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    printer_type: 'thermal_80mm',
    paper_width: 80,
    connection_type: 'usb',
    connection_address: ''
  })

  // Token copy state
  const [copiedToken, setCopiedToken] = useState(false)

  // Assign modal state
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null)
  const [isDefaultPrinter, setIsDefaultPrinter] = useState(true)

  // Fetch printers
  const { data: printersData, isLoading: printersLoading } = useQuery({
    queryKey: ['printers'],
    queryFn: async () => {
      const response = await api.get('/printers')
      return response.data
    }
  })

  // Fetch users for assignment
  const { data: usersData } = useQuery({
    queryKey: ['users-for-printer'],
    queryFn: async () => {
      const response = await api.get('/users')
      return response.data
    }
  })

  // Create printer mutation
  const createPrinter = useMutation({
    mutationFn: async (data: typeof formData) => {
      const response = await api.post('/printers', data)
      return response.data
    },
    onSuccess: (data) => {
      toast.success('Printer qo\'shildi!')
      queryClient.invalidateQueries({ queryKey: ['printers'] })
      setShowAddModal(false)
      resetForm()

      // Show token modal
      if (data.data?.agent_token) {
        setSelectedPrinter({ ...formData, id: data.data.id, agent_token: data.data.agent_token } as any)
        setShowTokenModal(true)
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Xatolik yuz berdi')
    }
  })

  // Update printer mutation
  const updatePrinter = useMutation({
    mutationFn: async ({ id, data }: { id: number, data: Partial<typeof formData> }) => {
      const response = await api.put(`/printers/${id}`, data)
      return response.data
    },
    onSuccess: () => {
      toast.success('Printer yangilandi!')
      queryClient.invalidateQueries({ queryKey: ['printers'] })
      setShowEditModal(false)
      setSelectedPrinter(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Xatolik yuz berdi')
    }
  })

  // Delete printer mutation
  const deletePrinter = useMutation({
    mutationFn: async (id: number) => {
      const response = await api.delete(`/printers/${id}`)
      return response.data
    },
    onSuccess: () => {
      toast.success('Printer o\'chirildi!')
      queryClient.invalidateQueries({ queryKey: ['printers'] })
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Xatolik yuz berdi')
    }
  })

  // Regenerate token mutation
  const regenerateToken = useMutation({
    mutationFn: async (id: number) => {
      const response = await api.post(`/printers/${id}/regenerate-token`)
      return response.data
    },
    onSuccess: (data) => {
      toast.success('Token yangilandi!')
      queryClient.invalidateQueries({ queryKey: ['printers'] })
      if (selectedPrinter && data.data?.agent_token) {
        setSelectedPrinter({ ...selectedPrinter, agent_token: data.data.agent_token })
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Xatolik yuz berdi')
    }
  })

  // Assign printer to user mutation
  const assignPrinter = useMutation({
    mutationFn: async (data: { user_id: number, printer_id: number, is_default: boolean }) => {
      const response = await api.post('/printers/assign', data)
      return response.data
    },
    onSuccess: () => {
      toast.success('Printer biriktirildi!')
      queryClient.invalidateQueries({ queryKey: ['printers'] })
      setShowAssignModal(false)
      setSelectedUserId(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Xatolik yuz berdi')
    }
  })

  // Unassign printer from user mutation
  const unassignPrinter = useMutation({
    mutationFn: async ({ user_id, printer_id }: { user_id: number, printer_id: number }) => {
      const response = await api.delete(`/printers/assign/${user_id}/${printer_id}`)
      return response.data
    },
    onSuccess: () => {
      toast.success('Biriktiruv olib tashlandi!')
      queryClient.invalidateQueries({ queryKey: ['printers'] })
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Xatolik yuz berdi')
    }
  })

  // Test print mutation
  const testPrint = useMutation({
    mutationFn: async (printer_id: number) => {
      const response = await api.post('/printers/queue', {
        printer_id,
        job_type: 'test',
        content: JSON.stringify({ test: true }),
        priority: 1
      })
      return response.data
    },
    onSuccess: () => {
      toast.success('Test chop yuborildi!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Xatolik yuz berdi')
    }
  })

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      printer_type: 'thermal_80mm',
      paper_width: 80,
      connection_type: 'usb',
      connection_address: ''
    })
  }

  const openEditModal = (printer: PrinterData) => {
    setSelectedPrinter(printer)
    setFormData({
      name: printer.name,
      description: printer.description || '',
      printer_type: printer.printer_type,
      paper_width: printer.paper_width,
      connection_type: printer.connection_type,
      connection_address: printer.connection_address || ''
    })
    setShowEditModal(true)
  }

  const openAssignModal = (printer: PrinterData) => {
    setSelectedPrinter(printer)
    setSelectedUserId(null)
    setIsDefaultPrinter(true)
    setShowAssignModal(true)
  }

  const openTokenModal = (printer: PrinterData) => {
    setSelectedPrinter(printer)
    setShowTokenModal(true)
  }

  const copyToken = async (token: string) => {
    try {
      await navigator.clipboard.writeText(token)
      setCopiedToken(true)
      toast.success('Token nusxalandi!')
      setTimeout(() => setCopiedToken(false), 2000)
    } catch {
      toast.error('Nusxalab bo\'lmadi')
    }
  }

  const printers: PrinterData[] = printersData?.data || []
  const users: UserData[] = usersData?.data || []

  // Filter out already assigned users
  const availableUsers = selectedPrinter
    ? users.filter(u => !selectedPrinter.assigned_users?.some(au => au.user_id === u.id))
    : users

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <Printer className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <h2 className="text-lg font-bold">Printerlar</h2>
              <p className="text-sm text-gray-500">Chek printerlarni boshqarish</p>
            </div>
          </div>
          <Button
            variant="default"
            onClick={() => {
              resetForm()
              setShowAddModal(true)
            }}
          >
            <Plus className="w-4 h-4 mr-2" />
            Yangi printer
          </Button>
        </div>

        {printersLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
          </div>
        ) : printers.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Printer className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>Hech qanday printer qo'shilmagan</p>
            <p className="text-sm">Yuqoridagi tugmani bosib printer qo'shing</p>
          </div>
        ) : (
          <div className="space-y-4">
            {printers.map((printer) => (
              <div
                key={printer.id}
                className={`border rounded-lg p-4 ${printer.is_active ? 'border-gray-200' : 'border-red-200 bg-red-50'}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    {/* Status indicator */}
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                      printer.is_online ? 'bg-green-100' : 'bg-gray-100'
                    }`}>
                      {printer.is_online ? (
                        <Wifi className="w-5 h-5 text-green-600" />
                      ) : (
                        <WifiOff className="w-5 h-5 text-gray-400" />
                      )}
                    </div>

                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold">{printer.name}</h3>
                        <Badge variant={printer.is_online ? 'success' : 'secondary'}>
                          {printer.is_online ? 'Online' : 'Offline'}
                        </Badge>
                        {!printer.is_active && (
                          <Badge variant="danger">O'chirilgan</Badge>
                        )}
                      </div>

                      <div className="text-sm text-gray-500 mt-1">
                        <span className="mr-3">📄 {printer.paper_width}mm</span>
                        <span className="mr-3">🔌 {printer.connection_type.toUpperCase()}</span>
                        {printer.last_seen && (
                          <span>🕐 {new Date(printer.last_seen).toLocaleString('uz-UZ')}</span>
                        )}
                      </div>

                      {/* Assigned users */}
                      {printer.assigned_users && printer.assigned_users.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {printer.assigned_users.map((au) => (
                            <span
                              key={au.user_id}
                              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${
                                au.is_default ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'
                              }`}
                            >
                              <Users className="w-3 h-3" />
                              {au.user_name}
                              {au.is_default && ' ⭐'}
                              <button
                                onClick={() => unassignPrinter.mutate({
                                  user_id: au.user_id,
                                  printer_id: printer.id
                                })}
                                className="ml-1 hover:text-red-500"
                              >
                                ×
                              </button>
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => testPrint.mutate(printer.id)}
                      disabled={!printer.is_online || testPrint.isLoading}
                      title="Test chop"
                    >
                      <TestTube className="w-4 h-4" />
                    </Button>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openAssignModal(printer)}
                      title="Kassir biriktirish"
                    >
                      <Link2 className="w-4 h-4" />
                    </Button>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openTokenModal(printer)}
                      title="Token ko'rish"
                    >
                      <Copy className="w-4 h-4" />
                    </Button>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openEditModal(printer)}
                      title="Tahrirlash"
                    >
                      <Edit2 className="w-4 h-4" />
                    </Button>

                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => {
                        if (confirm('Printerni o\'chirishni xohlaysizmi?')) {
                          deletePrinter.mutate(printer.id)
                        }
                      }}
                      title="O'chirish"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Add/Edit Modal */}
        {(showAddModal || showEditModal) && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
              <h3 className="text-lg font-bold mb-4">
                {showAddModal ? 'Yangi printer qo\'shish' : 'Printerni tahrirlash'}
              </h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Printer nomi *</label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Masalan: Kassa 1 printer"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Tavsif</label>
                  <Input
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Ixtiyoriy tavsif"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Printer turi</label>
                    <select
                      value={formData.printer_type}
                      onChange={(e) => {
                        const type = e.target.value
                        setFormData({
                          ...formData,
                          printer_type: type,
                          paper_width: type === 'thermal_80mm' ? 80 : type === 'thermal_58mm' ? 58 : 210
                        })
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="thermal_80mm">Thermal 80mm</option>
                      <option value="thermal_58mm">Thermal 58mm</option>
                      <option value="a4">A4</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Qog'oz kengligi (mm)</label>
                    <Input
                      type="number"
                      value={formData.paper_width}
                      onChange={(e) => setFormData({ ...formData, paper_width: parseInt(e.target.value) || 80 })}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Ulanish turi</label>
                    <select
                      value={formData.connection_type}
                      onChange={(e) => setFormData({ ...formData, connection_type: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="usb">USB</option>
                      <option value="network">Tarmoq (IP)</option>
                      <option value="bluetooth">Bluetooth</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">
                      {formData.connection_type === 'network' ? 'IP manzil' : 'Port/Manzil'}
                    </label>
                    <Input
                      value={formData.connection_address}
                      onChange={(e) => setFormData({ ...formData, connection_address: e.target.value })}
                      placeholder={formData.connection_type === 'network' ? '192.168.1.100' : 'USB001'}
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowAddModal(false)
                    setShowEditModal(false)
                    setSelectedPrinter(null)
                  }}
                >
                  Bekor qilish
                </Button>
                <Button
                  variant="default"
                  onClick={() => {
                    if (!formData.name.trim()) {
                      toast.error('Printer nomini kiriting')
                      return
                    }

                    if (showAddModal) {
                      createPrinter.mutate(formData)
                    } else if (selectedPrinter) {
                      updatePrinter.mutate({ id: selectedPrinter.id, data: formData })
                    }
                  }}
                  disabled={createPrinter.isLoading || updatePrinter.isLoading}
                >
                  {(createPrinter.isLoading || updatePrinter.isLoading) && (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  )}
                  {showAddModal ? 'Qo\'shish' : 'Saqlash'}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Assign User Modal */}
        {showAssignModal && selectedPrinter && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
              <h3 className="text-lg font-bold mb-4">
                Kassir biriktirish: {selectedPrinter.name}
              </h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Kassirni tanlang</label>
                  <select
                    value={selectedUserId || ''}
                    onChange={(e) => setSelectedUserId(parseInt(e.target.value) || null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">-- Tanlang --</option>
                    {availableUsers.map((user) => (
                      <option key={user.id} value={user.id}>
                        {user.first_name} {user.last_name} ({user.role_name})
                      </option>
                    ))}
                  </select>
                </div>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isDefaultPrinter}
                    onChange={(e) => setIsDefaultPrinter(e.target.checked)}
                    className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm">Asosiy printer sifatida belgilash</span>
                </label>

                {selectedPrinter.assigned_users && selectedPrinter.assigned_users.length > 0 && (
                  <div className="pt-4 border-t">
                    <p className="text-sm font-medium mb-2">Hozirda biriktirilgan:</p>
                    <div className="space-y-1">
                      {selectedPrinter.assigned_users.map((au) => (
                        <div key={au.user_id} className="flex items-center justify-between text-sm">
                          <span>
                            {au.user_name} {au.is_default && '⭐'}
                          </span>
                          <button
                            onClick={() => unassignPrinter.mutate({
                              user_id: au.user_id,
                              printer_id: selectedPrinter.id
                            })}
                            className="text-red-500 hover:text-red-700"
                          >
                            <Unlink className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowAssignModal(false)
                    setSelectedPrinter(null)
                  }}
                >
                  Yopish
                </Button>
                <Button
                  variant="default"
                  onClick={() => {
                    if (!selectedUserId) {
                      toast.error('Kassirni tanlang')
                      return
                    }
                    assignPrinter.mutate({
                      user_id: selectedUserId,
                      printer_id: selectedPrinter.id,
                      is_default: isDefaultPrinter
                    })
                  }}
                  disabled={!selectedUserId || assignPrinter.isLoading}
                >
                  {assignPrinter.isLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                  Biriktirish
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Token Modal */}
        {showTokenModal && selectedPrinter && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-6 w-full max-w-lg mx-4">
              <h3 className="text-lg font-bold mb-4">
                🔑 Print Agent Token: {selectedPrinter.name}
              </h3>

              <div className="bg-gray-100 rounded-lg p-4 mb-4">
                <p className="text-xs text-gray-500 mb-2">Agent Token (config.json ga qo'ying):</p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 text-sm bg-white p-2 rounded border break-all">
                    {selectedPrinter.agent_token || 'Token mavjud emas'}
                  </code>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => selectedPrinter.agent_token && copyToken(selectedPrinter.agent_token)}
                  >
                    {copiedToken ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                  </Button>
                </div>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
                <p className="text-sm text-yellow-700">
                  ⚠️ <strong>Diqqat:</strong> Token faqat bitta Print Agent dasturida ishlatilishi kerak.
                  Token o'zgartirilsa, eski agent ishlamay qoladi.
                </p>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
                <p className="text-sm text-blue-700 font-medium mb-2">📋 config.json namunasi:</p>
                <pre className="text-xs bg-white p-2 rounded overflow-x-auto">
{`{
  "api_url": "http://YOUR_SERVER_IP:8000",
  "agent_token": "${selectedPrinter.agent_token || 'TOKEN'}",
  "poll_interval": 3,
  "printer": {
    "type": "usb",
    "vendor_id": "0x0483",
    "product_id": "0x5743"
  }
}`}
                </pre>
              </div>

              <div className="flex justify-between">
                <Button
                  variant="outline"
                  onClick={() => {
                    if (confirm('Tokenni yangilashni xohlaysizmi? Eski token ishlamay qoladi.')) {
                      regenerateToken.mutate(selectedPrinter.id)
                    }
                  }}
                  disabled={regenerateToken.isLoading}
                >
                  {regenerateToken.isLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Yangi token
                </Button>

                <Button
                  variant="default"
                  onClick={() => {
                    setShowTokenModal(false)
                    setSelectedPrinter(null)
                  }}
                >
                  Yopish
                </Button>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}