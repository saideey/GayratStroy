import { useState, useCallback, useMemo, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Search, Trash2, User, ShoppingCart, CreditCard,
  Banknote, Building, Check, AlertCircle, Edit3,
  Loader2, Ruler, Star, Grid3X3, X, ChevronUp, GripVertical, Plus, Minus, Phone, Printer, ArrowLeft, Bookmark, Clock, FolderOpen
} from 'lucide-react'
import toast from 'react-hot-toast'
import { 
  Button, 
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription,
  Input
} from '@/components/ui'
import { productsService, salesService, customersService } from '@/services'
import api from '@/services/api'
import { formatMoney, formatNumber, formatInputNumber, cn, debounce, formatDateTashkent, formatTimeTashkent } from '@/lib/utils'
import { usePOSStore } from '@/stores'
import { useLanguage } from '@/contexts/LanguageContext'
import type { Product, Customer, UOMConversion } from '@/types'

// Category order storage key
const CATEGORY_ORDER_KEY = 'pos_category_order'

const PAYMENT_TYPES = [
  { type: 'CASH', labelKey: 'cash', icon: Banknote, color: 'bg-green-600' },
  { type: 'CARD', labelKey: 'card', icon: CreditCard, color: 'bg-blue-600' },
  { type: 'TRANSFER', labelKey: 'transfer', icon: Building, color: 'bg-purple-600' },
  { type: 'DEBT', labelKey: 'onCredit', icon: AlertCircle, color: 'bg-orange-500' },
]

const CATEGORY_COLORS = [
  '#2563EB', '#059669', '#D97706', '#DC2626', '#7C3AED', 
  '#DB2777', '#0891B2', '#65A30D', '#EA580C', '#4F46E5'
]

interface CartItem {
  id: string
  product_id: number
  product_name: string
  quantity: number
  uom_id: number
  uom_symbol: string
  uom_name: string
  conversion_factor: number
  base_uom_id: number
  base_uom_symbol: string
  cost_price: number
  original_price: number
  unit_price: number
  available_stock: number
}

export default function POSPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const { t } = useLanguage()
  
  // Get edit mode state from posStore
  const { 
    editingSaleId, 
    editingSaleNumber, 
    items: editItems,
    customer: editCustomer,
    warehouseId: editWarehouseId,
    subtotal: editSubtotal,
    discountAmount: editDiscountAmount,
    finalTotal: editFinalTotal,
    clearEditMode,
    resetPOS,
    // Saqlangan xaridlar
    savedCarts,
    addSavedCart,
    removeSavedCart,
  } = usePOSStore()
  
  const isEditMode = !!editingSaleId
  
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<number | 'favorites' | null>('favorites')
  const [showPaymentDialog, setShowPaymentDialog] = useState(false)
  const [showCustomerDialog, setShowCustomerDialog] = useState(false)
  const [showEditPriceDialog, setShowEditPriceDialog] = useState(false)
  const [showEditQuantityDialog, setShowEditQuantityDialog] = useState(false)
  const [showUOMSelectDialog, setShowUOMSelectDialog] = useState(false)
  const [editingItemId, setEditingItemId] = useState<string | null>(null)
  const [editPriceValue, setEditPriceValue] = useState('')
  const [editQuantityValue, setEditQuantityValue] = useState('')
  const [paymentType, setPaymentType] = useState<string>('CASH')
  const [paymentAmount, setPaymentAmount] = useState('')
  const [paymentCurrency, setPaymentCurrency] = useState<'UZS' | 'USD'>('UZS')
  const [isProcessing, setIsProcessing] = useState(false)
  const [selectedProductForUOM, setSelectedProductForUOM] = useState<Product | null>(null)
  const [changingUOMItemId, setChangingUOMItemId] = useState<string | null>(null)
  
  // General discount
  const [generalDiscount, setGeneralDiscount] = useState<number>(0)
  const [showDiscountInput, setShowDiscountInput] = useState(false)
  
  // Edit mode reason
  const [editReason, setEditReason] = useState('')
  
  // Drag and drop state
  const [draggedProduct, setDraggedProduct] = useState<Product | null>(null)
  const [dragOverProduct, setDragOverProduct] = useState<number | null>(null)
  
  // Mobile cart visibility
  const [mobileCartOpen, setMobileCartOpen] = useState(false)
  
  // Print preview state
  const [showPrintPreview, setShowPrintPreview] = useState(false)
  const printRef = useRef<HTMLDivElement>(null)
  
  // NEW: Add product dialog state
  const [showAddProductDialog, setShowAddProductDialog] = useState(false)
  const [addProductData, setAddProductData] = useState<{
    product: Product | null
    selectedUomId: number
    selectedUomSymbol: string
    selectedUomName: string
    conversionFactor: number
    unitPrice: number
    costPrice: number
    quantity: number
  }>({
    product: null,
    selectedUomId: 0,
    selectedUomSymbol: '',
    selectedUomName: '',
    conversionFactor: 1,
    unitPrice: 0,
    costPrice: 0,
    quantity: 1
  })
  
  // NEW: Customer search
  const [customerSearchQuery, setCustomerSearchQuery] = useState('')
  const [customerSellerFilter, setCustomerSellerFilter] = useState<number | ''>('')
  
  // NEW: Driver phone for receipt
  const [driverPhone, setDriverPhone] = useState('')
  
  // NEW: Barcode scanner
  const barcodeInputRef = useRef<HTMLInputElement>(null)
  const [barcodeValue, setBarcodeValue] = useState('')
  const [barcodeLoading, setBarcodeLoading] = useState(false)

  // NEW: Receipt edit mode
  const [receiptEditMode, setReceiptEditMode] = useState(false)
  const [receiptData, setReceiptData] = useState({
    companyName: 'GAYRAT STROY HOUSE',
    customerName: '',
    customerPhone: '',
    customerCompany: '',
    additionalPhone: '',
  })

  // NEW: Category ordering
  const [categoryOrder, setCategoryOrder] = useState<number[]>([])
  const [draggingCategoryId, setDraggingCategoryId] = useState<number | null>(null)
  const [dragOverCategoryId, setDragOverCategoryId] = useState<number | null>(null)

  const [items, setItems] = useState<CartItem[]>([])
  const [customer, setCustomer] = useState<Customer | null>(null)
  const [warehouseId] = useState(1)

  // Load edit mode data
  useEffect(() => {
    if (isEditMode && editItems.length > 0) {
      // Convert posStore items to CartItem format
      const cartItems: CartItem[] = editItems.map(item => ({
        id: item.id,
        product_id: item.product_id,
        product_name: item.product_name,
        quantity: item.quantity,
        uom_id: item.uom_id,
        uom_symbol: item.uom_symbol || '',
        uom_name: item.uom_symbol || '',
        conversion_factor: 1,
        base_uom_id: item.uom_id,
        base_uom_symbol: item.uom_symbol || '',
        cost_price: 0,
        original_price: item.original_price || item.unit_price,
        unit_price: item.unit_price,
        available_stock: 999999, // Not tracked in edit mode
      }))
      setItems(cartItems)

      if (editCustomer) {
        setCustomer(editCustomer)
      }

      // Set general discount if there was one
      if (editDiscountAmount > 0) {
        setGeneralDiscount(editDiscountAmount)
      }
    }
  }, [isEditMode, editItems, editCustomer, editDiscountAmount])

  // Update receiptData when customer changes or print preview opens
  useEffect(() => {
    if (showPrintPreview) {
      setReceiptData({
        companyName: 'GAYRAT STROY HOUSE',
        customerName: customer?.name || '',
        customerPhone: customer?.phone || '',
        customerCompany: customer?.company_name || '',
        additionalPhone: driverPhone,
      })
      setReceiptEditMode(false)
    }
  }, [showPrintPreview, customer, driverPhone])

  const { data: exchangeRateData } = useQuery({
    queryKey: ['exchange-rate'],
    queryFn: async () => {
      const response = await api.get('/settings/exchange-rate')
      return response.data
    },
    staleTime: 60000,
  })
  const usdRate = exchangeRateData?.usd_rate || 12800

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: productsService.getCategories,
  })

  // Load category order from localStorage
  useEffect(() => {
    const savedOrder = localStorage.getItem(CATEGORY_ORDER_KEY)
    if (savedOrder) {
      try {
        setCategoryOrder(JSON.parse(savedOrder))
      } catch (e) {
        console.error('Failed to parse category order')
      }
    }
  }, [])

  // Save category order to localStorage when it changes
  useEffect(() => {
    if (categoryOrder.length > 0) {
      localStorage.setItem(CATEGORY_ORDER_KEY, JSON.stringify(categoryOrder))
    }
  }, [categoryOrder])

  // Sorted categories based on saved order
  const sortedCategories = useMemo(() => {
    if (!categories) return []
    if (categoryOrder.length === 0) return categories

    return [...categories].sort((a: any, b: any) => {
      const indexA = categoryOrder.indexOf(a.id)
      const indexB = categoryOrder.indexOf(b.id)
      if (indexA === -1 && indexB === -1) return 0
      if (indexA === -1) return 1
      if (indexB === -1) return -1
      return indexA - indexB
    })
  }, [categories, categoryOrder])

  const { data: productsData, isLoading: loadingProducts } = useQuery({
    queryKey: ['products-pos', searchQuery, selectedCategory === 'favorites' ? null : selectedCategory],
    queryFn: () => productsService.getProducts({
      q: searchQuery || undefined,
      category_id: selectedCategory === 'favorites' ? undefined : (selectedCategory || undefined),
      is_active: true,
      per_page: 500,
    }),
    staleTime: 30000,
  })

  const toggleFavorite = useMutation({
    mutationFn: async (product: Product) => {
      const response = await api.patch(`/products/${product.id}`, {
        is_favorite: !product.is_favorite
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products-pos'] })
      toast.success(t('saved'))
    },
    onError: () => {
      toast.error(t('errorOccurred'))
    }
  })

  // Update product sort order
  const updateSortOrder = useMutation({
    mutationFn: async ({ productId, sortOrder }: { productId: number; sortOrder: number }) => {
      const response = await api.patch(`/products/${productId}`, {
        sort_order: sortOrder
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products-pos'] })
    }
  })

  const filteredProducts = useMemo(() => {
    if (!productsData?.data) return []
    let products = productsData.data as Product[]
    if (selectedCategory === 'favorites') {
      products = products.filter(p => p.is_favorite)
    }
    return products.sort((a, b) => {
      // First sort by sort_order
      const orderA = a.sort_order || 999999
      const orderB = b.sort_order || 999999
      if (orderA !== orderB) return orderA - orderB
      // Then by name
      return a.name.localeCompare(b.name)
    })
  }, [productsData, selectedCategory])

  const favoritesCount = useMemo(() => {
    return productsData?.data?.filter((p: Product) => p.is_favorite).length || 0
  }, [productsData])

  const { data: customersData } = useQuery({
    queryKey: ['customers-pos'],
    queryFn: () => customersService.getCustomers({ per_page: 100, is_active: true }),
    staleTime: 30000,
  })

  // Fetch sellers for customer filter
  const { data: sellersData } = useQuery({
    queryKey: ['sellers-pos'],
    queryFn: async () => {
      const response = await api.get('/users?per_page=100')
      return response.data
    },
    staleTime: 60000,
  })

  // Fetch company phones for receipt
  const { data: companyPhonesData } = useQuery({
    queryKey: ['company-phones'],
    queryFn: async () => {
      const response = await api.get('/settings/company-phones')
      return response.data
    },
    staleTime: 60000,
  })
  const companyPhone1 = companyPhonesData?.data?.phone1 || '+998 XX XXX XX XX'
  const companyPhone2 = companyPhonesData?.data?.phone2 || ''

  const debouncedSearch = useCallback(
    debounce((value: string) => setSearchQuery(value), 300),
    []
  )

  // Subtotal before discount
  const subtotal = items.reduce((sum, item) => sum + (item.unit_price * item.quantity), 0)
  // Grand total after general discount
  const finalTotal = subtotal - generalDiscount
  const totalCost = items.reduce((sum, item) => sum + (item.cost_price * item.conversion_factor * item.quantity), 0)
  const expectedProfit = finalTotal - totalCost

  const getSalePrice = (product: Product, conversionFactor: number = 1): number => {
    if (product.sale_price_usd) {
      return product.sale_price_usd * usdRate * conversionFactor
    }
    return Number(product.sale_price) * conversionFactor
  }

  const getCostPrice = (product: Product): number => {
    if (product.cost_price_usd) {
      return product.cost_price_usd * usdRate
    }
    return Number(product.cost_price) || 0
  }

  const handleProductClick = (product: Product) => {
    const salePrice = getSalePrice(product)
    const costPrice = getCostPrice(product)

    // Open add product dialog with product info
    setAddProductData({
      product,
      selectedUomId: product.base_uom_id,
      selectedUomSymbol: product.base_uom_symbol,
      selectedUomName: product.base_uom_name || product.base_uom_symbol,
      conversionFactor: 1,
      unitPrice: salePrice,
      costPrice: costPrice,
      quantity: 1
    })
    setShowAddProductDialog(true)
  }

  // Barcode scanner handler - scan and add to cart instantly
  const handleBarcodeSubmit = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== 'Enter') return

    const barcode = barcodeValue.trim()
    if (!barcode) return

    setBarcodeLoading(true)

    try {
      const product = await productsService.getProductByBarcode(barcode)

      if (product) {
        const baseStock = Number(product.current_stock) || 0

        if (baseStock <= 0) {
          toast.error(`${product.name} - ${t('outOfStock')}`)
          setBarcodeValue('')
          barcodeInputRef.current?.focus()
          return
        }

        // Add to cart with base UOM and quantity 1
        const salePrice = getSalePrice(product)
        addItemToCart(
          product,
          product.base_uom_id,
          product.base_uom_symbol,
          product.base_uom_name || product.base_uom_symbol,
          1,
          salePrice
        )

        // Clear barcode input and refocus
        setBarcodeValue('')
        barcodeInputRef.current?.focus()
      }
    } catch (error: any) {
      if (error?.response?.status === 404) {
        toast.error(`Shtrix kod topilmadi: ${barcode}`)
      } else {
        toast.error('Xatolik yuz berdi')
      }
      setBarcodeValue('')
      barcodeInputRef.current?.focus()
    } finally {
      setBarcodeLoading(false)
    }
  }

  // Handle UOM change in add product dialog
  const handleAddProductUOMChange = (uomConv: UOMConversion | null) => {
    if (!addProductData.product) return

    if (uomConv === null) {
      // Base UOM selected
      const salePrice = getSalePrice(addProductData.product)
      setAddProductData(prev => ({
        ...prev,
        selectedUomId: addProductData.product!.base_uom_id,
        selectedUomSymbol: addProductData.product!.base_uom_symbol,
        selectedUomName: addProductData.product!.base_uom_name || addProductData.product!.base_uom_symbol,
        conversionFactor: 1,
        unitPrice: salePrice
      }))
    } else {
      const convPrice = uomConv.sale_price || getSalePrice(addProductData.product, uomConv.conversion_factor)
      setAddProductData(prev => ({
        ...prev,
        selectedUomId: uomConv.uom_id,
        selectedUomSymbol: uomConv.uom_symbol,
        selectedUomName: uomConv.uom_name,
        conversionFactor: uomConv.conversion_factor,
        unitPrice: convPrice
      }))
    }
  }

  // Confirm add product to cart
  const handleConfirmAddProduct = () => {
    if (!addProductData.product) return

    const existingItem = items.find(i =>
      i.product_id === addProductData.product!.id &&
      i.uom_id === addProductData.selectedUomId
    )

    if (existingItem) {
      setItems(items.map(item =>
        item.id === existingItem.id
          ? { ...item, quantity: item.quantity + addProductData.quantity, unit_price: addProductData.unitPrice }
          : item
      ))
    } else {
      setItems([...items, {
        id: `${addProductData.product.id}-${addProductData.selectedUomId}-${Date.now()}`,
        product_id: addProductData.product.id,
        product_name: addProductData.product.name,
        quantity: addProductData.quantity,
        uom_id: addProductData.selectedUomId,
        uom_symbol: addProductData.selectedUomSymbol,
        uom_name: addProductData.selectedUomName,
        conversion_factor: addProductData.conversionFactor,
        base_uom_id: addProductData.product.base_uom_id,
        base_uom_symbol: addProductData.product.base_uom_symbol,
        cost_price: addProductData.costPrice,
        original_price: addProductData.unitPrice,
        unit_price: addProductData.unitPrice,
        available_stock: Number(addProductData.product.current_stock) || 0,
      }])
    }

    setShowAddProductDialog(false)
    setAddProductData({
      product: null,
      selectedUomId: 0,
      selectedUomSymbol: '',
      selectedUomName: '',
      conversionFactor: 1,
      unitPrice: 0,
      costPrice: 0,
      quantity: 1
    })
    toast.success(t('added'))
  }

  // Category drag handlers
  const handleCategoryDragStart = (categoryId: number) => {
    setDraggingCategoryId(categoryId)
  }

  const handleCategoryDragOver = (e: React.DragEvent, categoryId: number) => {
    e.preventDefault()
    if (draggingCategoryId !== categoryId) {
      setDragOverCategoryId(categoryId)
    }
  }

  const handleCategoryDrop = (targetCategoryId: number) => {
    if (!draggingCategoryId || draggingCategoryId === targetCategoryId) {
      setDraggingCategoryId(null)
      setDragOverCategoryId(null)
      return
    }

    const currentOrder = categoryOrder.length > 0
      ? [...categoryOrder]
      : sortedCategories.map((c: any) => c.id)

    const dragIndex = currentOrder.indexOf(draggingCategoryId)
    const dropIndex = currentOrder.indexOf(targetCategoryId)

    if (dragIndex !== -1 && dropIndex !== -1) {
      currentOrder.splice(dragIndex, 1)
      currentOrder.splice(dropIndex, 0, draggingCategoryId)
      setCategoryOrder(currentOrder)
    }

    setDraggingCategoryId(null)
    setDragOverCategoryId(null)
  }

  // Filtered customers based on search and seller filter
  const filteredCustomers = useMemo(() => {
    if (!customersData?.data) return []

    let filtered = customersData.data

    // Filter by seller
    if (customerSellerFilter) {
      filtered = filtered.filter((c: Customer) => c.manager_id === customerSellerFilter)
    }

    // Filter by search query
    if (customerSearchQuery.trim()) {
      const query = customerSearchQuery.toLowerCase()
      filtered = filtered.filter((c: Customer) =>
        c.name?.toLowerCase().includes(query) ||
        c.company_name?.toLowerCase().includes(query) ||
        c.phone?.toLowerCase().includes(query)
      )
    }

    return filtered
  }, [customersData, customerSearchQuery, customerSellerFilter])

  const handleToggleFavorite = (e: React.MouseEvent, product: Product) => {
    e.stopPropagation()
    e.preventDefault()
    toggleFavorite.mutate(product)
  }

  const addItemToCart = (
    product: Product,
    uomId: number,
    uomSymbol: string,
    uomName: string,
    conversionFactor: number,
    unitPrice: number
  ) => {
    const existingItem = items.find(i => i.product_id === product.id && i.uom_id === uomId)

    if (existingItem) {
      setItems(items.map(item =>
        item.id === existingItem.id
          ? { ...item, quantity: item.quantity + 1 }
          : item
      ))
    } else {
      let salePrice = unitPrice
      if (customer?.customer_type?.toUpperCase() === 'VIP') {
        if (product.vip_price_usd) {
          salePrice = product.vip_price_usd * usdRate * conversionFactor
        } else if (product.vip_price) {
          salePrice = Number(product.vip_price) * conversionFactor
        }
      }

      const costPrice = getCostPrice(product)

      setItems([...items, {
        id: `${product.id}-${uomId}-${Date.now()}`,
        product_id: product.id,
        product_name: product.name,
        quantity: 1,
        uom_id: uomId,
        uom_symbol: uomSymbol,
        uom_name: uomName,
        conversion_factor: conversionFactor,
        base_uom_id: product.base_uom_id,
        base_uom_symbol: product.base_uom_symbol,
        cost_price: costPrice,
        original_price: salePrice,
        unit_price: salePrice,
        available_stock: Number(product.current_stock) || 0,
      }])
    }

    setShowUOMSelectDialog(false)
    setSelectedProductForUOM(null)
    toast.success(t('added'))
  }

  const handleSelectUOM = (uomConv: UOMConversion | null) => {
    if (!selectedProductForUOM) return

    if (changingUOMItemId) {
      if (uomConv === null) {
        const salePrice = getSalePrice(selectedProductForUOM)
        setItems(items.map(i =>
          i.id === changingUOMItemId
            ? {
                ...i,
                uom_id: selectedProductForUOM.base_uom_id,
                uom_symbol: selectedProductForUOM.base_uom_symbol,
                uom_name: selectedProductForUOM.base_uom_name || selectedProductForUOM.base_uom_symbol,
                conversion_factor: 1,
                original_price: salePrice,
                unit_price: salePrice,
              }
            : i
        ))
      } else {
        const convPrice = uomConv.sale_price || getSalePrice(selectedProductForUOM, uomConv.conversion_factor)
        setItems(items.map(i =>
          i.id === changingUOMItemId
            ? {
                ...i,
                uom_id: uomConv.uom_id,
                uom_symbol: uomConv.uom_symbol,
                uom_name: uomConv.uom_name,
                conversion_factor: uomConv.conversion_factor,
                original_price: convPrice,
                unit_price: convPrice,
              }
            : i
        ))
      }
      setChangingUOMItemId(null)
      setShowUOMSelectDialog(false)
      setSelectedProductForUOM(null)
      return
    }

    if (uomConv === null) {
      const salePrice = getSalePrice(selectedProductForUOM)
      addItemToCart(
        selectedProductForUOM,
        selectedProductForUOM.base_uom_id,
        selectedProductForUOM.base_uom_symbol,
        selectedProductForUOM.base_uom_name || selectedProductForUOM.base_uom_symbol,
        1,
        salePrice
      )
    } else {
      const convPrice = uomConv.sale_price || getSalePrice(selectedProductForUOM, uomConv.conversion_factor)
      addItemToCart(
        selectedProductForUOM,
        uomConv.uom_id,
        uomConv.uom_symbol,
        uomConv.uom_name,
        uomConv.conversion_factor,
        convPrice
      )
    }
  }

  const handleChangeItemUOM = (item: CartItem) => {
    const product = productsData?.data?.find((p: Product) => p.id === item.product_id)
    if (product) {
      setSelectedProductForUOM(product)
      setChangingUOMItemId(item.id)
      setShowUOMSelectDialog(true)
    }
  }

  const handleQuantityChange = (itemId: string, delta: number) => {
    setItems(items.map(item => {
      if (item.id === itemId) {
        const newQty = Math.max(0.1, item.quantity + delta)
        return { ...item, quantity: newQty }
      }
      return item
    }))
  }

  const handleRemoveItem = (itemId: string) => {
    setItems(items.filter(item => item.id !== itemId))
  }

  const handleClearCart = () => {
    setItems([])
    setCustomer(null)
    setPaymentType('CASH')
    setPaymentAmount('')
    setGeneralDiscount(0)
    setShowDiscountInput(false)
  }

  const handleEditPrice = (item: CartItem) => {
    setEditingItemId(item.id)
    setEditPriceValue(item.unit_price.toString())
    setShowEditPriceDialog(true)
  }

  const handleSavePrice = () => {
    if (editingItemId && editPriceValue) {
      const newPrice = parseFloat(editPriceValue)
      if (!isNaN(newPrice) && newPrice >= 0) {
        setItems(items.map(item =>
          item.id === editingItemId
            ? { ...item, unit_price: newPrice }
            : item
        ))
        toast.success(t('priceChanged'))
      }
    }
    setShowEditPriceDialog(false)
    setEditingItemId(null)
  }

  const handleEditQuantity = (item: CartItem) => {
    setEditingItemId(item.id)
    setEditQuantityValue(item.quantity.toString())
    setShowEditQuantityDialog(true)
  }

  const handleSaveQuantity = () => {
    if (editingItemId && editQuantityValue) {
      const newQty = parseFloat(editQuantityValue)
      if (!isNaN(newQty) && newQty > 0) {
        setItems(items.map(item =>
          item.id === editingItemId
            ? { ...item, quantity: newQty }
            : item
        ))
        toast.success(t('quantityChanged'))
      }
    }
    setShowEditQuantityDialog(false)
    setEditingItemId(null)
  }

  // Apply general discount - calculate final price after discount
  const applyGeneralDiscount = (discountAmount: number) => {
    if (discountAmount >= 0 && discountAmount <= subtotal) {
      setGeneralDiscount(discountAmount)
    } else {
      toast.error(t('invalidDiscount'))
    }
  }

  // Set final total directly (user enters what they want to receive)
  const setFinalTotalDirectly = (newTotal: number) => {
    if (newTotal > 0 && newTotal <= subtotal) {
      setGeneralDiscount(subtotal - newTotal)
    } else {
      toast.error(t('invalidAmount'))
    }
  }

  const processSale = async () => {
    if (items.length === 0) {
      toast.error(t('cartEmpty'))
      return
    }

    if (paymentType === 'DEBT' && !customer) {
      toast.error(t('selectCustomerForDebt'))
      return
    }

    // Edit mode validation
    if (isEditMode && !editReason.trim()) {
      toast.error(t('enterEditReason'))
      return
    }

    if (isEditMode && editReason.trim().length < 3) {
      toast.error(t('reasonMinLength'))
      return
    }

    setIsProcessing(true)

    try {
      let paymentInUZS = finalTotal
      const inputAmount = parseFloat(paymentAmount) || 0

      if (paymentType !== 'DEBT' && inputAmount > 0) {
        paymentInUZS = paymentCurrency === 'USD' ? inputAmount * usdRate : inputAmount
      }

      // Distribute general discount proportionally across items
      const saleItems = items.map(item => {
        const itemTotal = item.unit_price * item.quantity
        // Calculate this item's share of the general discount
        const itemDiscountShare = subtotal > 0
          ? (itemTotal / subtotal) * generalDiscount
          : 0
        // Per-item discount from price changes + share of general discount
        const perItemDiscount = (item.original_price - item.unit_price) * item.quantity + itemDiscountShare

        return {
          product_id: item.product_id,
          quantity: item.quantity,
          uom_id: item.uom_id,
          unit_price: item.unit_price,
          original_price: item.original_price,
          discount_amount: perItemDiscount,
          discount_percent: 0,
        }
      })

      if (isEditMode && editingSaleId) {
        // EDIT MODE - Update existing sale
        const saleData = {
          customer_id: customer?.id || null,
          warehouse_id: editWarehouseId || warehouseId,
          items: saleItems,
          final_total: finalTotal,
          payments: paymentType !== 'DEBT' && paymentInUZS > 0 ? [
            { payment_type: paymentType, amount: paymentInUZS }
          ] : [],
          notes: generalDiscount > 0 ? `Umumiy chegirma: ${formatMoney(generalDiscount)}` : '',
        }

        await api.put(`/sales/${editingSaleId}/full?edit_reason=${encodeURIComponent(editReason)}`, saleData)

        toast.success(t('saleEdited'))

        // Clear edit mode and navigate back
        handleClearCart()
        clearEditMode()
        resetPOS()
        setShowPaymentDialog(false)
        setEditReason('')
        queryClient.invalidateQueries({ queryKey: ['sales'] })
        navigate('/sales')

      } else {
        // NEW SALE MODE
        const saleData = {
          customer_id: customer?.id || null,
          warehouse_id: warehouseId,
          items: saleItems,
          payment_type: paymentType,
          payment_amount: paymentType === 'DEBT' ? 0 : paymentInUZS,
          notes: generalDiscount > 0 ? `Umumiy chegirma: ${formatMoney(generalDiscount)}` : '',
        }

        const result = await salesService.quickSale(saleData)

        toast.success(
          paymentType === 'DEBT'
            ? `Qarzga sotildi`
            : `Sotuv yakunlandi ${result.change > 0 ? `Qaytim: ${formatMoney(result.change)}` : ''}`
        )

        handleClearCart()
        setShowPaymentDialog(false)
        queryClient.invalidateQueries({ queryKey: ['products-pos'] })
      }

    } catch (error: any) {
      toast.error(error.response?.data?.detail || t('errorOccurred'))
    } finally {
      setIsProcessing(false)
    }
  }

  const getProductColor = (product: Product, categoryIndex: number): string => {
    if (product.color) return product.color
    return CATEGORY_COLORS[categoryIndex % CATEGORY_COLORS.length]
  }

  // Drag and drop handlers
  const handleDragStart = (e: React.DragEvent, product: Product) => {
    setDraggedProduct(product)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragOver = (e: React.DragEvent, productId: number) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    setDragOverProduct(productId)
  }

  const handleDragLeave = () => {
    setDragOverProduct(null)
  }

  const handleDrop = (e: React.DragEvent, targetProduct: Product) => {
    e.preventDefault()
    if (!draggedProduct || draggedProduct.id === targetProduct.id) {
      setDraggedProduct(null)
      setDragOverProduct(null)
      return
    }

    // Get current products in order
    const currentProducts = [...filteredProducts]
    const draggedIndex = currentProducts.findIndex(p => p.id === draggedProduct.id)
    const targetIndex = currentProducts.findIndex(p => p.id === targetProduct.id)

    if (draggedIndex === -1 || targetIndex === -1) return

    // Calculate new sort orders
    const updates: { productId: number; sortOrder: number }[] = []

    // Remove dragged product and insert at new position
    currentProducts.splice(draggedIndex, 1)
    currentProducts.splice(targetIndex, 0, draggedProduct)

    // Update sort_order for all affected products
    currentProducts.forEach((product, index) => {
      const newOrder = (index + 1) * 10
      if (product.sort_order !== newOrder) {
        updates.push({ productId: product.id, sortOrder: newOrder })
      }
    })

    // Send updates to API
    updates.forEach(update => {
      updateSortOrder.mutate(update)
    })

    setDraggedProduct(null)
    setDragOverProduct(null)
    toast.success(t('orderSaved'))
  }

  const handleDragEnd = () => {
    setDraggedProduct(null)
    setDragOverProduct(null)
  }

  return (
    <div className="h-[calc(100vh-4rem)] lg:h-[calc(100vh-1.5rem)] flex flex-col lg:flex-row bg-gray-100">
      {/* Mobile Cart Button */}
      <button
        onClick={() => setMobileCartOpen(true)}
        className={cn(
          "lg:hidden fixed bottom-4 right-4 z-40 flex items-center gap-2 px-4 py-3 rounded-full shadow-lg transition-all",
          items.length > 0 ? "bg-blue-600 text-white" : "bg-white text-gray-600 border"
        )}
      >
        <ShoppingCart className="w-5 h-5" />
        {items.length > 0 && (
          <>
            <span className="font-medium">{items.length}</span>
            <span className="text-sm">• {formatMoney(finalTotal, false)}</span>
          </>
        )}
      </button>

      {/* LEFT - Categories (hidden on mobile, horizontal on tablet) */}
      <div className="hidden lg:flex w-52 bg-white border-r flex-col shrink-0">
        <div className="p-3 border-b">
          <h3 className="font-semibold text-sm text-gray-500 uppercase">{t('categories')}</h3>
          <p className="text-[10px] text-gray-400 mt-0.5">{t('dragToReorder')}</p>
        </div>

        <div className="flex-1 overflow-y-auto">
          <button
            onClick={() => setSelectedCategory('favorites')}
            className={cn(
              'w-full flex items-center gap-3 px-4 py-3 text-left border-b transition-colors',
              selectedCategory === 'favorites'
                ? 'bg-blue-50 text-blue-700 border-l-4 border-l-blue-600'
                : 'hover:bg-gray-50'
            )}
          >
            <Star className={cn('w-5 h-5', selectedCategory === 'favorites' ? 'fill-yellow-400 text-yellow-400' : 'text-gray-400')} />
            <span className="flex-1 text-[15px] font-medium">{t('favorites')}</span>
            <span className="text-sm text-gray-500">{favoritesCount}</span>
          </button>

          <button
            onClick={() => setSelectedCategory(null)}
            className={cn(
              'w-full flex items-center gap-3 px-4 py-3 text-left border-b transition-colors',
              selectedCategory === null
                ? 'bg-blue-50 text-blue-700 border-l-4 border-l-blue-600'
                : 'hover:bg-gray-50'
            )}
          >
            <Grid3X3 className="w-5 h-5 text-gray-400" />
            <span className="flex-1 text-[15px] font-medium">{t('all')}</span>
          </button>

          {sortedCategories?.map((cat: any, index: number) => (
            <div
              key={cat.id}
              draggable
              onDragStart={() => handleCategoryDragStart(cat.id)}
              onDragOver={(e) => handleCategoryDragOver(e, cat.id)}
              onDrop={() => handleCategoryDrop(cat.id)}
              onDragEnd={() => { setDraggingCategoryId(null); setDragOverCategoryId(null) }}
              className={cn(
                'w-full flex items-center gap-2 px-2 py-3 text-left border-b transition-all cursor-grab active:cursor-grabbing',
                selectedCategory === cat.id
                  ? 'bg-blue-50 text-blue-700 border-l-4 border-l-blue-600'
                  : 'hover:bg-gray-50',
                draggingCategoryId === cat.id && 'opacity-50',
                dragOverCategoryId === cat.id && 'bg-blue-100 border-blue-300'
              )}
            >
              <GripVertical className="w-4 h-4 text-gray-300 flex-shrink-0" />
              <button
                onClick={() => setSelectedCategory(cat.id)}
                className="flex items-center gap-2 flex-1 min-w-0"
              >
                <div
                  className="w-3 h-3 rounded-full flex-shrink-0"
                  style={{ backgroundColor: CATEGORY_COLORS[index % CATEGORY_COLORS.length] }}
                />
                <span className="text-[15px] truncate">{cat.name}</span>
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Mobile Categories - Horizontal scroll */}
      <div className="lg:hidden flex items-center gap-2 px-3 py-2 bg-white border-b overflow-x-auto no-scrollbar">
        <button
          onClick={() => setSelectedCategory('favorites')}
          className={cn(
            'flex items-center gap-1.5 px-3 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors',
            selectedCategory === 'favorites'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700'
          )}
        >
          <Star className={cn('w-4 h-4', selectedCategory === 'favorites' && 'fill-white')} />
          {t('favorites')}
        </button>

        <button
          onClick={() => setSelectedCategory(null)}
          className={cn(
            'flex items-center gap-1.5 px-3 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors',
            selectedCategory === null
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700'
          )}
        >
          <Grid3X3 className="w-4 h-4" />
          {t('all')}
        </button>

        {sortedCategories?.map((cat: any, index: number) => (
          <button
            key={cat.id}
            onClick={() => setSelectedCategory(cat.id)}
            className={cn(
              'flex items-center gap-1.5 px-3 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors',
              selectedCategory === cat.id
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700'
            )}
          >
            <div
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: selectedCategory === cat.id ? '#fff' : CATEGORY_COLORS[index % CATEGORY_COLORS.length] }}
            />
            {cat.name}
          </button>
        ))}
      </div>

      {/* CENTER - Products */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Search & Barcode */}
        <div className="p-3 lg:p-4 bg-white border-b flex items-center gap-2 lg:gap-4">
          {/* Barcode Scanner Input */}
          <div className="relative w-40 lg:w-48">
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
              {barcodeLoading ? (
                <Loader2 className="w-4 h-4 lg:w-5 lg:h-5 animate-spin" />
              ) : (
                <span className="text-sm lg:text-base">📦</span>
              )}
            </div>
            <input
              ref={barcodeInputRef}
              type="text"
              value={barcodeValue}
              onChange={(e) => setBarcodeValue(e.target.value)}
              onKeyDown={handleBarcodeSubmit}
              placeholder="Shtrix kod..."
              className="w-full h-10 lg:h-11 pl-10 lg:pl-11 pr-4 text-sm lg:text-[15px] border-2 border-green-500 rounded-lg focus:border-green-600 focus:outline-none bg-green-50"
              autoFocus
            />
          </div>

          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 lg:w-5 lg:h-5 text-gray-400" />
            <input
              type="text"
              placeholder={t('search') + '...'}
              className="w-full h-10 lg:h-11 pl-10 lg:pl-11 pr-4 text-sm lg:text-[15px] border rounded-lg focus:border-blue-500 focus:outline-none"
              onChange={(e) => debouncedSearch(e.target.value)}
            />
          </div>

          <div className="flex items-center gap-1 lg:gap-2 text-xs lg:text-sm bg-blue-50 px-2 lg:px-3 py-1.5 lg:py-2 rounded-lg">
            <span className="text-gray-500">$</span>
            <span className="font-semibold text-blue-600">{formatNumber(usdRate)}</span>
          </div>
        </div>

        {/* Products Grid */}
        <div className="flex-1 overflow-y-auto p-2 lg:p-4 pb-20 lg:pb-4">
          {loadingProducts ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="w-8 h-8 lg:w-10 lg:h-10 animate-spin text-blue-600" />
            </div>
          ) : filteredProducts.length > 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-2 lg:gap-3">
              {filteredProducts.map((product: Product) => {
                const baseStock = Number(product.current_stock) || 0
                const isOutOfStock = baseStock <= 0
                const categoryIndex = categories?.findIndex((c: any) => c.id === product.category_id) || 0
                const productColor = getProductColor(product, categoryIndex)
                const salePrice = getSalePrice(product)
                const costPrice = getCostPrice(product)
                const isDragOver = dragOverProduct === product.id

                return (
                  <div
                    key={product.id}
                    draggable={!isOutOfStock}
                    onDragStart={(e) => handleDragStart(e, product)}
                    onDragOver={(e) => handleDragOver(e, product.id)}
                    onDragLeave={handleDragLeave}
                    onDrop={(e) => handleDrop(e, product)}
                    onDragEnd={handleDragEnd}
                    className={cn(
                      "relative flex flex-col rounded-lg border bg-white transition-all",
                      isOutOfStock
                        ? "opacity-50"
                        : "hover:shadow-lg hover:border-blue-400 cursor-grab active:cursor-grabbing",
                      isDragOver && "ring-2 ring-blue-500 ring-offset-2",
                      draggedProduct?.id === product.id && "opacity-50"
                    )}
                    style={!isOutOfStock ? { borderLeftColor: productColor, borderLeftWidth: '4px' } : undefined}
                  >
                    {/* Favorite button */}
                    <button
                      onClick={(e) => handleToggleFavorite(e, product)}
                      className="absolute top-1.5 lg:top-2 right-1.5 lg:right-2 p-1 rounded-full hover:bg-gray-100 z-10"
                    >
                      <Star className={cn(
                        'w-3.5 h-3.5 lg:w-4 lg:h-4',
                        product.is_favorite ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'
                      )} />
                    </button>

                    <button
                      onClick={() => !isOutOfStock && handleProductClick(product)}
                      disabled={isOutOfStock}
                      className="flex flex-col p-2 lg:p-3 text-left flex-1"
                    >
                      {/* Name */}
                      <p className="font-semibold text-xs lg:text-[15px] leading-tight line-clamp-2 pr-4 lg:pr-6 mb-1.5 lg:mb-2">
                        {product.name}
                      </p>

                      {/* UOM */}
                      <div className="flex flex-wrap gap-1 mb-1.5 lg:mb-2">
                        <span className="text-[10px] lg:text-xs px-1.5 lg:px-2 py-0.5 bg-blue-100 text-blue-700 rounded font-medium">
                          {product.base_uom_symbol}
                        </span>
                        {product.uom_conversions?.map((conv) => (
                          <span key={conv.uom_id} className="text-[10px] lg:text-xs px-1.5 lg:px-2 py-0.5 bg-gray-100 text-gray-600 rounded hidden sm:inline-block">
                            {conv.uom_symbol}
                          </span>
                        ))}
                      </div>

                      {/* Price */}
                      <div className="mt-auto">
                        <p className="text-sm lg:text-lg font-bold text-green-600">
                          {formatMoney(salePrice, false)}
                        </p>
                        {product.sale_price_usd && (
                          <p className="text-[10px] lg:text-xs text-gray-500">${formatNumber(product.sale_price_usd, 2)}</p>
                        )}
                        {/* Cost price */}
                        <p className="text-[10px] lg:text-xs text-orange-600 mt-0.5">
                          {t('costPrice')}: {formatMoney(costPrice, false)}
                        </p>
                      </div>

                      {/* Stock */}
                      <p className={cn(
                        'text-[10px] lg:text-xs mt-1.5 lg:mt-2',
                        isOutOfStock ? 'text-red-500' : 'text-gray-500'
                      )}>
                        {formatNumber(baseStock)} {product.base_uom_symbol}
                        {product.uom_conversions?.map((conv, idx) => (
                          <span key={conv.uom_id} className="hidden sm:inline"> • {formatNumber(baseStock / conv.conversion_factor, 0)} {conv.uom_symbol}</span>
                        ))}
                      </p>
                    </button>
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
              <ShoppingCart className="w-12 h-12 lg:w-16 lg:h-16 mb-3 opacity-30" />
              <p className="text-base lg:text-lg">{t('noProductsFound')}</p>
            </div>
          )}
        </div>
      </div>

      {/* RIGHT - Cart (Desktop) */}
      <div className="hidden lg:flex w-80 bg-white border-l flex-col shrink-0">
        {/* Edit Mode Banner */}
        {isEditMode && (
          <div className="bg-warning/20 border-b border-warning p-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold text-warning text-sm">Tahrirlash rejimi</p>
                <p className="text-xs text-gray-600">Sotuv #{editingSaleNumber}</p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  clearEditMode()
                  resetPOS()
                  handleClearCart()
                  navigate('/sales')
                }}
                className="text-danger"
              >
                <X className="w-4 h-4 mr-1" />
                {t('cancel')}
              </Button>
            </div>
          </div>
        )}

        {/* Customer */}
        <div className="p-3 border-b">
          <button
            onClick={() => setShowCustomerDialog(true)}
            className={cn(
              "w-full h-10 flex items-center justify-center gap-2 rounded-lg text-sm font-medium transition-colors",
              customer
                ? "bg-blue-600 text-white"
                : "border border-dashed border-gray-300 text-gray-600 hover:border-blue-500"
            )}
          >
            <User className="w-4 h-4" />
            {customer ? customer.name : t('selectCustomer')}
          </button>

          {customer && customer.current_debt > 0 && (
            <p className="text-xs text-red-600 text-center mt-1">{t('debt')}: {formatMoney(customer.current_debt)}</p>
          )}

          {/* Driver Phone Input */}
          <div className="mt-2">
            <input
              type="tel"
              value={driverPhone}
              onChange={(e) => setDriverPhone(e.target.value)}
              placeholder={t('driverPhone')}
              className="w-full h-9 px-3 text-sm border border-gray-200 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
            />
          </div>
        </div>

        {/* Saqlangan xaridlar */}
        {savedCarts.length > 0 && (
          <div className="p-2 border-b bg-amber-50">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-amber-700 flex items-center gap-1">
                <FolderOpen className="w-3 h-3" />
                {t('savedCarts')} ({savedCarts.length})
              </span>
            </div>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {savedCarts.map((cart) => (
                <div
                  key={cart.id}
                  className="flex items-center justify-between p-2 bg-white rounded-lg border border-amber-200 hover:border-amber-400 transition-colors"
                >
                  <button
                    onClick={() => {
                      // Avval joriy xaridni saqlash (agar bo'lsa)
                      if (items.length > 0) {
                        addSavedCart({
                          id: `cart_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                          name: `Xarid ${new Date().toLocaleString('uz-UZ')}`,
                          items: [...items],
                          customer,
                          warehouseId,
                          subtotal,
                          discountAmount: generalDiscount,
                          customTotal: generalDiscount > 0 ? finalTotal : null,
                          savedAt: new Date().toISOString(),
                        })
                      }

                      // Saqlangan xaridni local state'ga yuklash
                      const cartItems: CartItem[] = cart.items.map((item: any) => ({
                        id: item.id || `item_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                        product_id: item.product_id,
                        product_name: item.product_name,
                        quantity: item.quantity,
                        uom_id: item.uom_id,
                        uom_symbol: item.uom_symbol || '',
                        uom_name: item.uom_name || item.uom_symbol || '',
                        conversion_factor: item.conversion_factor || 1,
                        base_uom_id: item.base_uom_id || item.uom_id,
                        base_uom_symbol: item.base_uom_symbol || item.uom_symbol || '',
                        cost_price: item.cost_price || 0,
                        original_price: item.original_price || item.unit_price,
                        unit_price: item.unit_price,
                        available_stock: item.available_stock || 999999,
                      }))

                      setItems(cartItems)
                      setCustomer(cart.customer)
                      setGeneralDiscount(cart.discountAmount || 0)

                      // Saqlangan xaridni ro'yxatdan o'chirish
                      removeSavedCart(cart.id)

                      toast.success(t('cartLoaded'))
                    }}
                    className="flex-1 text-left"
                  >
                    <div className="flex items-center gap-2">
                      <ShoppingCart className="w-4 h-4 text-amber-600" />
                      <div>
                        <p className="text-xs font-medium text-gray-800">
                          {cart.items.length} ta tovar
                          {cart.customer && <span className="text-gray-500"> • {cart.customer.name}</span>}
                        </p>
                        <p className="text-xs text-amber-600 font-semibold">{formatMoney(cart.customTotal || cart.subtotal)}</p>
                      </div>
                    </div>
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      removeSavedCart(cart.id)
                      toast.success(t('deleted'))
                    }}
                    className="p-1.5 hover:bg-red-100 rounded ml-2"
                  >
                    <Trash2 className="w-3.5 h-3.5 text-red-500" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Items */}
        <div className="flex-1 overflow-y-auto">
          {items.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
              <ShoppingCart className="w-12 h-12 mb-2 opacity-30" />
              <p className="text-sm">{t('cartEmpty')}</p>
            </div>
          ) : (
            <div className="p-2 space-y-2">
              {items.map((item, index) => (
                <div key={item.id} className="p-2 bg-gray-50 rounded-lg">
                  <div className="flex items-start justify-between mb-1">
                    <p className="text-sm font-medium flex-1 pr-2">{index + 1}. {item.product_name}</p>
                    <button onClick={() => handleRemoveItem(item.id)} className="p-1 hover:bg-red-100 rounded">
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </button>
                  </div>

                  <div className="flex items-center gap-2 mb-1">
                    <button
                      onClick={() => handleChangeItemUOM(item)}
                      className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                    >
                      {item.uom_symbol}
                    </button>
                    <span className="text-sm text-green-600 font-medium">{formatMoney(item.unit_price, false)}</span>
                    <button onClick={() => handleEditPrice(item)} className="p-1 hover:bg-gray-200 rounded ml-auto">
                      <Edit3 className="w-3 h-3 text-blue-600" />
                    </button>
                  </div>

                  <p className="text-xs text-orange-600 mb-2">{t('costPrice')}: {formatMoney(item.cost_price * item.conversion_factor, false)}</p>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleQuantityChange(item.id, -1)}
                        className="w-8 h-8 rounded bg-gray-200 hover:bg-gray-300 flex items-center justify-center text-lg font-bold"
                      >
                        -
                      </button>
                      <button
                        onClick={() => handleEditQuantity(item)}
                        className="w-14 h-8 text-center text-sm font-medium bg-white border rounded hover:bg-blue-50 hover:border-blue-300"
                        title={t('quantity')}
                      >
                        {formatNumber(item.quantity, 1)}
                      </button>
                      <button
                        onClick={() => handleQuantityChange(item.id, 1)}
                        className="w-8 h-8 rounded bg-gray-200 hover:bg-gray-300 flex items-center justify-center text-lg font-bold"
                      >
                        +
                      </button>
                    </div>
                    <p className="text-sm font-bold">{formatMoney(item.unit_price * item.quantity, false)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t p-3 space-y-2">
          {/* Subtotal */}
          {items.length > 0 && (
            <>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">{t('subtotal')}:</span>
                <span className="font-medium">{formatMoney(subtotal, false)}</span>
              </div>

              {/* Discount section */}
              <div className="border rounded-lg p-2 bg-orange-50">
                <button
                  onClick={() => setShowDiscountInput(!showDiscountInput)}
                  className="w-full flex items-center justify-between text-sm"
                >
                  <span className="text-orange-700 font-medium">{t('discount')}:</span>
                  <span className="text-orange-700 font-bold">
                    {generalDiscount > 0 ? `-${formatMoney(generalDiscount, false)}` : `${t('add')} +`}
                  </span>
                </button>

                {showDiscountInput && (
                  <div className="mt-2 space-y-2">
                    <div className="flex gap-2">
                      <input
                        type="text"
                        inputMode="numeric"
                        value={generalDiscount > 0 ? formatInputNumber(generalDiscount) : ''}
                        onChange={(e) => {
                          const value = e.target.value.replace(/\s/g, '')
                          applyGeneralDiscount(parseFloat(value) || 0)
                        }}
                        onFocus={(e) => e.target.select()}
                        placeholder={t('discount')}
                        className="flex-1 h-9 px-3 text-sm font-medium border rounded-lg"
                      />
                      <button
                        onClick={() => { setGeneralDiscount(0); setShowDiscountInput(false) }}
                        className="px-3 h-9 text-sm bg-gray-200 hover:bg-gray-300 rounded-lg"
                      >
                        {t('cancel')}
                      </button>
                    </div>
                    <div className="text-xs text-gray-500">
                      {t('finalTotal')}:
                    </div>
                    <input
                      type="text"
                      inputMode="numeric"
                      value={finalTotal > 0 ? formatInputNumber(finalTotal) : ''}
                      onChange={(e) => {
                        const value = e.target.value.replace(/\s/g, '')
                        setFinalTotalDirectly(parseFloat(value) || 0)
                      }}
                      onFocus={(e) => e.target.select()}
                      placeholder={t('finalTotal')}
                      className="w-full h-9 px-3 text-sm font-medium border rounded-lg"
                    />
                  </div>
                )}
              </div>

              {/* Profit */}
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">{t('profit')}:</span>
                <span className={expectedProfit >= 0 ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
                  {formatMoney(expectedProfit, false)}
                </span>
              </div>
            </>
          )}

          {/* Total */}
          <div className="flex justify-between items-end">
            <div className="min-w-0">
              <p className="text-xs text-gray-500 whitespace-nowrap">{t('finalTotal')}:</p>
              <p className="text-2xl font-bold text-green-700 whitespace-nowrap">{formatMoney(finalTotal, false)}</p>
              <p className="text-xs text-gray-500 whitespace-nowrap">≈ ${formatNumber(finalTotal / usdRate, 2)}</p>
            </div>
            <div className="flex items-center gap-1 flex-shrink-0">
              <button
                onClick={() => {
                  if (items.length === 0) {
                    toast.error(t('cartEmpty'))
                    return
                  }
                  // Saqlash
                  addSavedCart({
                    id: `cart_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                    name: `Xarid ${new Date().toLocaleString('uz-UZ')}`,
                    items: [...items],
                    customer,
                    warehouseId,
                    subtotal,
                    discountAmount: generalDiscount,
                    customTotal: generalDiscount > 0 ? finalTotal : null,
                    savedAt: new Date().toISOString(),
                  })
                  // Clear local cart
                  setItems([])
                  setCustomer(null)
                  setGeneralDiscount(0)
                  toast.success(t('cartSavedForLater'))
                }}
                disabled={items.length === 0}
                className="flex items-center gap-1 px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded disabled:opacity-50"
                title={t('saveForLater')}
              >
                <Bookmark className="w-4 h-4" />
                {t('saveLater')}
              </button>
              <button
                onClick={handleClearCart}
                disabled={items.length === 0}
                className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded disabled:opacity-50"
              >
                <Trash2 className="w-4 h-4" />
                {t('clear')}
              </button>
            </div>
          </div>

          <button
            onClick={() => setShowPaymentDialog(true)}
            disabled={items.length === 0}
            className="w-full h-12 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg text-lg font-medium"
          >
            <Check className="w-5 h-5" />
            {t('payment')}
          </button>

          <button
            onClick={() => setShowPrintPreview(true)}
            disabled={items.length === 0}
            className="w-full h-10 flex items-center justify-center gap-2 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 text-gray-700 rounded-lg text-base font-medium border border-gray-300"
          >
            <Printer className="w-4 h-4" />
            {t('printReceipt')}
          </button>
        </div>
      </div>

      {/* Mobile Cart Modal */}
      {mobileCartOpen && (
        <div className="lg:hidden fixed inset-0 z-50">
          <div className="absolute inset-0 bg-black/50" onClick={() => setMobileCartOpen(false)} />
          <div className="absolute bottom-0 left-0 right-0 bg-white rounded-t-2xl max-h-[85vh] flex flex-col animate-in slide-in-from-bottom duration-300">
            {/* Handle */}
            <div className="flex justify-center py-2">
              <div className="w-10 h-1 bg-gray-300 rounded-full" />
            </div>

            {/* Header */}
            <div className="flex items-center justify-between px-4 pb-2 border-b">
              <h3 className="text-lg font-bold flex items-center gap-2">
                <ShoppingCart className="w-5 h-5" />
                {t('cart')} ({items.length})
              </h3>
              <button onClick={() => setMobileCartOpen(false)} className="p-2 hover:bg-gray-100 rounded-full">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Customer */}
            <div className="p-3 border-b">
              <button
                onClick={() => setShowCustomerDialog(true)}
                className={cn(
                  "w-full h-10 flex items-center justify-center gap-2 rounded-lg text-sm font-medium transition-colors",
                  customer
                    ? "bg-blue-600 text-white"
                    : "border border-dashed border-gray-300 text-gray-600"
                )}
              >
                <User className="w-4 h-4" />
                {customer ? customer.name : t('selectCustomer')}
              </button>
              {customer && customer.current_debt > 0 && (
                <p className="text-xs text-red-600 text-center mt-1">{t('debt')}: {formatMoney(customer.current_debt)}</p>
              )}

              {/* Driver Phone Input - Mobile */}
              <div className="mt-2">
                <input
                  type="tel"
                  value={driverPhone}
                  onChange={(e) => setDriverPhone(e.target.value)}
                  placeholder={t('driverPhone')}
                  className="w-full h-9 px-3 text-sm border border-gray-200 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
                />
              </div>
            </div>

            {/* Saqlangan xaridlar - Mobile */}
            {savedCarts.length > 0 && (
              <div className="p-2 border-b bg-amber-50">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-amber-700 flex items-center gap-1">
                    <FolderOpen className="w-3 h-3" />
                    Saqlangan ({savedCarts.length})
                  </span>
                </div>
                <div className="space-y-1 max-h-24 overflow-y-auto">
                  {savedCarts.map((cart) => (
                    <div
                      key={cart.id}
                      className="flex items-center justify-between p-2 bg-white rounded-lg border border-amber-200"
                    >
                      <button
                        onClick={() => {
                          // Joriy xaridni saqlash
                          if (items.length > 0) {
                            addSavedCart({
                              id: `cart_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                              name: `Xarid ${new Date().toLocaleString('uz-UZ')}`,
                              items: [...items],
                              customer,
                              warehouseId,
                              subtotal,
                              discountAmount: generalDiscount,
                              customTotal: generalDiscount > 0 ? finalTotal : null,
                              savedAt: new Date().toISOString(),
                            })
                          }

                          // Saqlangan xaridni yuklash
                          const cartItems: CartItem[] = cart.items.map((item: any) => ({
                            id: item.id || `item_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                            product_id: item.product_id,
                            product_name: item.product_name,
                            quantity: item.quantity,
                            uom_id: item.uom_id,
                            uom_symbol: item.uom_symbol || '',
                            uom_name: item.uom_name || item.uom_symbol || '',
                            conversion_factor: item.conversion_factor || 1,
                            base_uom_id: item.base_uom_id || item.uom_id,
                            base_uom_symbol: item.base_uom_symbol || item.uom_symbol || '',
                            cost_price: item.cost_price || 0,
                            original_price: item.original_price || item.unit_price,
                            unit_price: item.unit_price,
                            available_stock: item.available_stock || 999999,
                          }))

                          setItems(cartItems)
                          setCustomer(cart.customer)
                          setGeneralDiscount(cart.discountAmount || 0)
                          removeSavedCart(cart.id)

                          toast.success(t('cartLoaded'))
                        }}
                        className="flex-1 text-left"
                      >
                        <p className="text-xs font-medium">
                          {cart.items.length} ta • {formatMoney(cart.customTotal || cart.subtotal)}
                        </p>
                      </button>
                      <button
                        onClick={() => {
                          removeSavedCart(cart.id)
                          toast.success(t('deleted'))
                        }}
                        className="p-1 hover:bg-red-100 rounded ml-2"
                      >
                        <Trash2 className="w-3 h-3 text-red-500" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Items */}
            <div className="flex-1 overflow-y-auto">
              {items.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-40 text-gray-400">
                  <ShoppingCart className="w-10 h-10 mb-2 opacity-30" />
                  <p className="text-sm">{t('cartEmpty')}</p>
                </div>
              ) : (
                <div className="p-3 space-y-2">
                  {items.map((item, index) => (
                    <div key={item.id} className="p-2 bg-gray-50 rounded-lg">
                      <div className="flex items-start justify-between mb-1">
                        <p className="text-sm font-medium flex-1 pr-2">{index + 1}. {item.product_name}</p>
                        <button onClick={() => handleRemoveItem(item.id)} className="p-1 hover:bg-red-100 rounded">
                          <Trash2 className="w-4 h-4 text-red-500" />
                        </button>
                      </div>

                      <div className="flex items-center gap-2 mb-1">
                        <button
                          onClick={() => handleChangeItemUOM(item)}
                          className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                        >
                          {item.uom_symbol}
                        </button>
                        <span className="text-sm text-green-600 font-medium">{formatMoney(item.unit_price, false)}</span>
                        <button onClick={() => handleEditPrice(item)} className="p-1 hover:bg-gray-200 rounded ml-auto">
                          <Edit3 className="w-3 h-3 text-blue-600" />
                        </button>
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => handleQuantityChange(item.id, -1)}
                            className="w-8 h-8 rounded bg-gray-200 hover:bg-gray-300 flex items-center justify-center text-lg font-bold"
                          >
                            -
                          </button>
                          <button
                            onClick={() => handleEditQuantity(item)}
                            className="w-14 h-8 text-center text-sm font-medium bg-white border rounded"
                          >
                            {formatNumber(item.quantity, 1)}
                          </button>
                          <button
                            onClick={() => handleQuantityChange(item.id, 1)}
                            className="w-8 h-8 rounded bg-gray-200 hover:bg-gray-300 flex items-center justify-center text-lg font-bold"
                          >
                            +
                          </button>
                        </div>
                        <p className="font-bold">{formatMoney(item.unit_price * item.quantity, false)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Totals */}
            <div className="p-3 border-t bg-gray-50 space-y-2">
              {items.length > 0 && (
                <>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">{t('total')}:</span>
                    <span className="font-medium">{formatMoney(subtotal, false)}</span>
                  </div>
                  {generalDiscount > 0 && (
                    <div className="flex justify-between text-sm text-orange-600">
                      <span>{t('discount')}:</span>
                      <span>-{formatMoney(generalDiscount, false)}</span>
                    </div>
                  )}
                </>
              )}

              <div className="flex justify-between items-center">
                <div className="min-w-0">
                  <p className="text-xs text-gray-500 whitespace-nowrap">{t('finalTotal')}:</p>
                  <p className="text-xl font-bold text-green-700 whitespace-nowrap">{formatMoney(finalTotal, false)}</p>
                  <p className="text-xs text-gray-500 whitespace-nowrap">≈ ${formatNumber(finalTotal / usdRate, 2)}</p>
                </div>
                <div className="flex items-center gap-1 flex-shrink-0">
                  <button
                    onClick={() => {
                      if (items.length === 0) return
                      addSavedCart({
                        id: `cart_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                        name: `Xarid ${new Date().toLocaleString('uz-UZ')}`,
                        items: [...items],
                        customer,
                        warehouseId,
                        subtotal,
                        discountAmount: generalDiscount,
                        customTotal: generalDiscount > 0 ? finalTotal : null,
                        savedAt: new Date().toISOString(),
                      })
                      setItems([])
                      setCustomer(null)
                      setGeneralDiscount(0)
                      toast.success(t('cartSavedForLater'))
                    }}
                    disabled={items.length === 0}
                    className="flex items-center gap-1 px-2 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded disabled:opacity-50"
                  >
                    <Bookmark className="w-4 h-4" />
                  </button>
                  <button
                    onClick={handleClearCart}
                    disabled={items.length === 0}
                    className="flex items-center gap-1 px-2 py-1.5 text-sm text-gray-600 hover:bg-gray-200 rounded disabled:opacity-50"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <button
                onClick={() => { setMobileCartOpen(false); setShowPaymentDialog(true); }}
                disabled={items.length === 0}
                className="w-full h-12 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg text-base font-medium"
              >
                <Check className="w-5 h-5" />
                {t('payment')}
              </button>

              <button
                onClick={() => { setMobileCartOpen(false); setShowPrintPreview(true); }}
                disabled={items.length === 0}
                className="w-full h-10 flex items-center justify-center gap-2 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 text-gray-700 rounded-lg text-sm font-medium border border-gray-300"
              >
                <Printer className="w-4 h-4" />
                {t('printReceipt')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Product Dialog - NEW */}
      <Dialog open={showAddProductDialog} onOpenChange={(open) => {
        setShowAddProductDialog(open)
        if (!open) {
          setAddProductData({
            product: null,
            selectedUomId: 0,
            selectedUomSymbol: '',
            selectedUomName: '',
            conversionFactor: 1,
            unitPrice: 0,
            costPrice: 0,
            quantity: 1
          })
        }
      }}>
        <DialogContent className="max-w-[340px]">
          <DialogHeader>
            <DialogTitle className="text-base pr-6">{t('addToCart')}</DialogTitle>
            <DialogDescription className="font-semibold text-sm text-gray-800 line-clamp-2 pr-6">
              {addProductData.product?.name}
            </DialogDescription>
          </DialogHeader>

          {addProductData.product && (
            <div className="space-y-3 pt-2 w-full">
              {/* Cost Price Info */}
              <div className="bg-orange-50 px-3 py-2 rounded-lg border border-orange-200 w-full box-border">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-orange-600">{t('costPrice')}:</span>
                  <span className="text-sm font-bold text-orange-700">
                    {formatMoney(addProductData.costPrice)}
                  </span>
                </div>
              </div>

              {/* UOM Selection */}
              <div className="w-full">
                <label className="block text-xs font-medium text-gray-600 mb-1.5">{t('unit')}</label>
                <div className="flex flex-wrap gap-2">
                  {/* Base UOM */}
                  <button
                    type="button"
                    onClick={() => handleAddProductUOMChange(null)}
                    className={cn(
                      "px-3 py-2 rounded-lg border-2 text-sm font-medium transition-all",
                      addProductData.selectedUomId === addProductData.product.base_uom_id
                        ? "border-blue-500 bg-blue-50 text-blue-700"
                        : "border-gray-200 hover:border-blue-300 text-gray-700"
                    )}
                  >
                    {addProductData.product.base_uom_symbol}
                  </button>

                  {/* Other UOMs */}
                  {addProductData.product.uom_conversions?.map((conv) => (
                    <button
                      key={conv.uom_id}
                      type="button"
                      onClick={() => handleAddProductUOMChange(conv)}
                      className={cn(
                        "px-3 py-2 rounded-lg border-2 text-sm font-medium transition-all",
                        addProductData.selectedUomId === conv.uom_id
                          ? "border-blue-500 bg-blue-50 text-blue-700"
                          : "border-gray-200 hover:border-blue-300 text-gray-700"
                      )}
                    >
                      {conv.uom_symbol}
                    </button>
                  ))}
                </div>
              </div>

              {/* Price Input */}
              <div className="w-full">
                <label className="block text-xs font-medium text-gray-600 mb-1.5">{t('sellingPriceSum')}</label>
                <input
                  type="text"
                  inputMode="numeric"
                  value={formatInputNumber(addProductData.unitPrice)}
                  onChange={(e) => {
                    const value = e.target.value.replace(/\s/g, '')
                    const num = parseFloat(value) || 0
                    setAddProductData(prev => ({ ...prev, unitPrice: num }))
                  }}
                  className="w-full h-11 px-3 text-base font-bold text-center border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none box-border"
                />
                {addProductData.unitPrice < addProductData.costPrice * addProductData.conversionFactor && addProductData.unitPrice > 0 && (
                  <p className="text-xs text-red-500 mt-1">⚠️ {t('priceBelowCost')}</p>
                )}
              </div>

              {/* Quantity Input */}
              <div className="w-full">
                <label className="block text-xs font-medium text-gray-600 mb-1.5">{t('quantityUnit')} ({addProductData.selectedUomSymbol})</label>
                <div className="flex items-center gap-2 w-full">
                  <button
                    type="button"
                    onClick={() => setAddProductData(prev => ({ ...prev, quantity: Math.max(0.5, prev.quantity - 1) }))}
                    className="w-11 h-11 flex-shrink-0 rounded-lg bg-gray-100 hover:bg-gray-200 flex items-center justify-center active:scale-95 transition-transform"
                  >
                    <Minus className="w-5 h-5" />
                  </button>
                  <input
                    type="text"
                    inputMode="decimal"
                    value={addProductData.quantity === 0 ? '' : addProductData.quantity}
                    onChange={(e) => {
                      const value = e.target.value
                      // Allow empty input
                      if (value === '' || value === '0') {
                        setAddProductData(prev => ({ ...prev, quantity: 0 }))
                        return
                      }
                      // Parse and set number
                      const num = parseFloat(value)
                      if (!isNaN(num) && num >= 0) {
                        setAddProductData(prev => ({ ...prev, quantity: num }))
                      }
                    }}
                    onFocus={(e) => e.target.select()}
                    onBlur={(e) => {
                      // Set minimum value on blur if empty or zero
                      if (!e.target.value || parseFloat(e.target.value) <= 0) {
                        setAddProductData(prev => ({ ...prev, quantity: 1 }))
                      }
                    }}
                    className="flex-1 min-w-0 h-11 px-3 text-center text-lg font-bold border-2 border-gray-200 rounded-lg focus:border-blue-500 outline-none box-border"
                    placeholder="1"
                  />
                  <button
                    type="button"
                    onClick={() => setAddProductData(prev => ({ ...prev, quantity: prev.quantity + 1 }))}
                    className="w-11 h-11 flex-shrink-0 rounded-lg bg-gray-100 hover:bg-gray-200 flex items-center justify-center active:scale-95 transition-transform"
                  >
                    <Plus className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Total */}
              <div className="bg-green-50 px-3 py-2 rounded-lg border border-green-200 w-full box-border">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-green-700">{t('total')}:</span>
                  <span className="text-base font-bold text-green-700">
                    {formatMoney(addProductData.unitPrice * addProductData.quantity)}
                  </span>
                </div>
              </div>

              {/* Confirm Button */}
              <button
                onClick={handleConfirmAddProduct}
                disabled={addProductData.quantity <= 0 || addProductData.unitPrice <= 0}
                className="w-full h-11 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors box-border"
              >
                <Check className="w-4 h-4" />
                {t('addToCart')}
              </button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* UOM Dialog */}
      <Dialog open={showUOMSelectDialog} onOpenChange={(open) => {
        setShowUOMSelectDialog(open)
        if (!open) { setChangingUOMItemId(null); setSelectedProductForUOM(null) }
      }}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>{t('unit')}</DialogTitle>
            <DialogDescription>{selectedProductForUOM?.name}</DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <button
              onClick={() => handleSelectUOM(null)}
              className="w-full flex items-center justify-between p-3 rounded-lg border-2 border-blue-500 bg-blue-50 hover:bg-blue-100"
            >
              <div className="flex items-center gap-2">
                <Ruler className="w-5 h-5 text-blue-600" />
                <div className="text-left">
                  <p className="font-medium">{selectedProductForUOM?.base_uom_name || selectedProductForUOM?.base_uom_symbol}</p>
                  <p className="text-xs text-gray-500">{t('baseUnitLabel')}</p>
                </div>
              </div>
              <p className="font-bold text-green-600">{selectedProductForUOM && formatMoney(getSalePrice(selectedProductForUOM))}</p>
            </button>
            {selectedProductForUOM?.uom_conversions?.map((conv) => (
              <button
                key={conv.uom_id}
                onClick={() => handleSelectUOM(conv)}
                className="w-full flex items-center justify-between p-3 rounded-lg border-2 border-gray-200 hover:border-blue-500"
              >
                <div className="flex items-center gap-2">
                  <Ruler className="w-5 h-5 text-gray-400" />
                  <div className="text-left">
                    <p className="font-medium">{conv.uom_name}</p>
                    <p className="text-xs text-gray-500">1 {conv.uom_symbol} = {formatNumber(conv.conversion_factor)} {selectedProductForUOM?.base_uom_symbol}</p>
                  </div>
                </div>
                <p className="font-bold text-green-600">{formatMoney(conv.sale_price || getSalePrice(selectedProductForUOM!, conv.conversion_factor))}</p>
              </button>
            ))}
          </div>
        </DialogContent>
      </Dialog>

      {/* Customer Dialog - Large and User Friendly */}
      <Dialog open={showCustomerDialog} onOpenChange={(open) => {
        setShowCustomerDialog(open)
        if (!open) {
          setCustomerSearchQuery('')
          setCustomerSellerFilter('')
        }
      }}>
        <DialogContent className="max-w-2xl w-[95vw] max-h-[90vh] flex flex-col">
          <DialogHeader className="pb-2 border-b">
            <DialogTitle className="text-xl pr-8">{t('selectCustomer')}</DialogTitle>
            <p className="text-sm text-gray-500 mt-1">
              {t('total')}: {customersData?.data?.length || 0} | {t('all')}: {filteredCustomers.length}
            </p>
          </DialogHeader>

          {/* Filters Row */}
          <div className="flex flex-col sm:flex-row gap-3 py-3 border-b bg-gray-50 -mx-4 px-4 sm:-mx-6 sm:px-6">
            {/* Seller filter */}
            <div className="flex-1 sm:max-w-[200px]">
              <label className="block text-xs font-medium text-gray-600 mb-1">{t('seller')}</label>
              <select
                value={customerSellerFilter}
                onChange={(e) => setCustomerSellerFilter(e.target.value ? Number(e.target.value) : '')}
                className="w-full h-11 px-3 border-2 border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">{t('all')}</option>
                {sellersData?.data?.map((seller: any) => (
                  <option key={seller.id} value={seller.id}>
                    {seller.first_name} {seller.last_name}
                  </option>
                ))}
              </select>
            </div>

            {/* Search input */}
            <div className="flex-1">
              <label className="block text-xs font-medium text-gray-600 mb-1">{t('search')}</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={customerSearchQuery}
                  onChange={(e) => setCustomerSearchQuery(e.target.value)}
                  placeholder={t('searchProducts')}
                  className="w-full h-11 pl-11 pr-4 border-2 border-gray-200 rounded-lg text-base focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  autoFocus
                />
              </div>
            </div>
          </div>

          {/* Customer List */}
          <div className="flex-1 overflow-y-auto py-3 -mx-4 px-4 sm:-mx-6 sm:px-6" style={{ maxHeight: 'calc(90vh - 220px)', minHeight: '300px' }}>
            {/* Oddiy xaridor */}
            <button
              onClick={() => { setCustomer(null); setShowCustomerDialog(false); setCustomerSearchQuery(''); setCustomerSellerFilter('') }}
              className="w-full p-4 mb-3 text-left rounded-xl border-2 border-dashed border-gray-300 hover:border-blue-400 hover:bg-blue-50 transition-all"
            >
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center">
                  <User className="w-6 h-6 text-gray-400" />
                </div>
                <div>
                  <p className="font-semibold text-base">{t('retail')}</p>
                  <p className="text-sm text-gray-500">{t('noData')}</p>
                </div>
              </div>
            </button>

            {filteredCustomers.length === 0 ? (
              <div className="text-center py-12">
                <User className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 text-lg">{t('notFound')}</p>
                <p className="text-gray-400 text-sm mt-1">{t('search')}</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {filteredCustomers.map((c: Customer) => (
                  <button
                    key={c.id}
                    onClick={() => { setCustomer(c); setShowCustomerDialog(false); setCustomerSearchQuery(''); setCustomerSellerFilter('') }}
                    className={cn(
                      "w-full p-4 text-left rounded-xl border-2 hover:shadow-md transition-all",
                      customer?.id === c.id
                        ? "border-blue-500 bg-blue-50 shadow-md"
                        : "border-gray-200 hover:border-blue-300"
                    )}
                  >
                    <div className="flex items-start gap-3">
                      {/* Avatar */}
                      <div className={cn(
                        "w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0",
                        c.customer_type?.toUpperCase() === 'VIP' ? "bg-yellow-100" : "bg-blue-100"
                      )}>
                        <User className={cn(
                          "w-6 h-6",
                          c.customer_type?.toUpperCase() === 'VIP' ? "text-yellow-600" : "text-blue-600"
                        )} />
                      </div>

                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0">
                            <p className="font-semibold text-base truncate">{c.name}</p>
                            {c.company_name && (
                              <p className="text-sm text-blue-600 truncate">{c.company_name}</p>
                            )}
                          </div>
                          <div className="flex flex-col gap-1 flex-shrink-0">
                            {c.customer_type?.toUpperCase() === 'VIP' && (
                              <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded font-medium">VIP</span>
                            )}
                            {c.current_debt > 0 && (
                              <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded font-medium">Qarz</span>
                            )}
                          </div>
                        </div>

                        <div className="mt-2 space-y-1">
                          <p className="text-sm text-gray-600 flex items-center gap-1">
                            <Phone className="w-3.5 h-3.5" />
                            {c.phone}
                          </p>
                          {c.current_debt > 0 && (
                            <p className="text-sm text-red-600 font-medium">
                              Qarz: {formatMoney(c.current_debt)}
                            </p>
                          )}
                          {c.manager_name && (
                            <p className="text-xs text-gray-400">
                              Kassir: {c.manager_name}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="pt-3 border-t -mx-4 px-4 sm:-mx-6 sm:px-6">
            <button
              onClick={() => setShowCustomerDialog(false)}
              className="w-full h-12 border-2 border-gray-200 rounded-xl text-base font-medium hover:bg-gray-50 transition-colors"
            >
              {t('cancel')}
            </button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Price Dialog */}
      <Dialog open={showEditPriceDialog} onOpenChange={setShowEditPriceDialog}>
        <DialogContent className="max-w-xs">
          <DialogHeader>
            <DialogTitle>{t('editPrice')}</DialogTitle>
          </DialogHeader>
          <input
            type="text"
            inputMode="numeric"
            value={formatInputNumber(parseFloat(editPriceValue) || 0)}
            onChange={(e) => {
              const value = e.target.value.replace(/\s/g, '')
              setEditPriceValue(value)
            }}
            onFocus={(e) => e.target.select()}
            className="w-full h-12 px-4 text-lg font-bold text-center border rounded-lg"
            autoFocus
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditPriceDialog(false)}>{t('cancel')}</Button>
            <Button variant="primary" onClick={handleSavePrice}>{t('save')}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Quantity Dialog */}
      <Dialog open={showEditQuantityDialog} onOpenChange={setShowEditQuantityDialog}>
        <DialogContent className="max-w-xs">
          <DialogHeader>
            <DialogTitle>{t('editQuantity')}</DialogTitle>
          </DialogHeader>
          <input
            type="number"
            step="0.1"
            value={editQuantityValue}
            onChange={(e) => setEditQuantityValue(e.target.value)}
            className="w-full h-12 px-4 text-lg border rounded-lg text-center"
            autoFocus
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditQuantityDialog(false)}>{t('cancel')}</Button>
            <Button variant="primary" onClick={handleSaveQuantity}>{t('save')}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Payment Dialog */}
      <Dialog open={showPaymentDialog} onOpenChange={setShowPaymentDialog}>
        <DialogContent className="max-w-[340px]">
          <DialogHeader>
            <DialogTitle className="text-base pr-6">
              {isEditMode ? `${t('sales')} #${editingSaleNumber} ${t('editSaleTitle')}` : t('makePayment')}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-3 pt-2 w-full">
            {/* Edit Reason - Only in Edit Mode */}
            {isEditMode && (
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-gray-700">{t('editReason')} *</label>
                <input
                  type="text"
                  value={editReason}
                  onChange={(e) => setEditReason(e.target.value)}
                  placeholder={t('editReasonPlaceholder')}
                  className="w-full h-10 px-3 text-sm border-2 border-warning/50 rounded-lg focus:border-warning focus:ring-2 focus:ring-warning/20 outline-none"
                />
              </div>
            )}

            {/* Payment Types */}
            <div className="grid grid-cols-2 gap-2 w-full">
              {PAYMENT_TYPES.map((pt) => (
                <button
                  key={pt.type}
                  onClick={() => setPaymentType(pt.type)}
                  className={cn(
                    'flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg border-2 text-sm font-medium transition-all',
                    paymentType === pt.type ? `${pt.color} text-white border-transparent` : 'border-gray-200 hover:border-blue-400'
                  )}
                >
                  <pt.icon className="w-4 h-4" />
                  {t(pt.labelKey as any)}
                </button>
              ))}
            </div>

            {paymentType !== 'DEBT' && (
              <>
                {/* Currency Selection */}
                <div className="flex gap-2 w-full">
                  <button
                    onClick={() => setPaymentCurrency('UZS')}
                    className={cn(
                      'flex-1 h-10 rounded-lg text-sm font-medium border-2 transition-all',
                      paymentCurrency === 'UZS' ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-200 hover:border-blue-400'
                    )}
                  >
                    So'm
                  </button>
                  <button
                    onClick={() => setPaymentCurrency('USD')}
                    className={cn(
                      'flex-1 h-10 rounded-lg text-sm font-medium border-2 transition-all',
                      paymentCurrency === 'USD' ? 'bg-green-600 text-white border-green-600' : 'border-gray-200 hover:border-green-400'
                    )}
                  >
                    Dollar
                  </button>
                </div>

                {/* Amount Input */}
                <input
                  type="text"
                  inputMode="numeric"
                  value={paymentAmount ? formatInputNumber(parseFloat(paymentAmount.replace(/\s/g, '')) || 0) : ''}
                  onChange={(e) => {
                    const value = e.target.value.replace(/\s/g, '')
                    setPaymentAmount(value)
                  }}
                  onFocus={(e) => e.target.select()}
                  placeholder={paymentCurrency === 'USD' ? `${(finalTotal / usdRate).toFixed(2)}` : formatInputNumber(finalTotal)}
                  className="w-full h-11 px-3 text-base font-bold text-center border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none box-border"
                />
              </>
            )}

            {/* Total Summary */}
            <div className="bg-gray-50 px-3 py-2.5 rounded-lg space-y-1.5 w-full box-border">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">{t('totalSum')}:</span>
                <span className="font-bold text-base">{formatMoney(finalTotal)}</span>
              </div>
              <div className="flex justify-between items-center text-xs text-gray-500">
                <span>{t('inDollars')}:</span>
                <span>${formatNumber(finalTotal / usdRate, 2)}</span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2 pt-1 w-full">
              <button
                onClick={() => setShowPaymentDialog(false)}
                className="flex-1 h-10 border-2 border-gray-200 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors"
              >
                {t('cancel')}
              </button>
              <button
                onClick={processSale}
                disabled={isProcessing || (isEditMode && editReason.trim().length < 3)}
                className={cn(
                  "flex-1 h-10 disabled:opacity-50 text-white rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-colors",
                  isEditMode ? "bg-warning hover:bg-warning/90" : "bg-blue-600 hover:bg-blue-700"
                )}
              >
                {isProcessing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                {isEditMode ? t('save') : t('confirmSale')}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Print Preview Dialog */}
      <Dialog open={showPrintPreview} onOpenChange={setShowPrintPreview}>
        <DialogContent className="max-w-md p-0 overflow-hidden">
          <DialogHeader className="p-4 border-b">
            <DialogTitle className="flex items-center gap-2">
              <Printer className="w-5 h-5" />
              {t('receiptPreview')}
            </DialogTitle>
          </DialogHeader>

          {/* Edit Form - Compact 2 column grid */}
          {receiptEditMode && (
            <div className="px-4 py-3 bg-blue-50 border-b">
              <div className="grid grid-cols-2 gap-2">
                <div className="col-span-2">
                  <input
                    type="text"
                    value={receiptData.companyName}
                    onChange={(e) => setReceiptData(prev => ({ ...prev, companyName: e.target.value }))}
                    className="w-full px-2 py-1.5 border rounded text-sm"
                    placeholder={t('company')}
                  />
                </div>
                <input
                  type="text"
                  value={receiptData.customerName}
                  onChange={(e) => setReceiptData(prev => ({ ...prev, customerName: e.target.value }))}
                  className="w-full px-2 py-1.5 border rounded text-sm"
                  placeholder={t('customer')}
                />
                <input
                  type="text"
                  value={receiptData.customerPhone}
                  onChange={(e) => setReceiptData(prev => ({ ...prev, customerPhone: e.target.value }))}
                  className="w-full px-2 py-1.5 border rounded text-sm"
                  placeholder={t('phone')}
                />
                <input
                  type="text"
                  value={receiptData.customerCompany}
                  onChange={(e) => setReceiptData(prev => ({ ...prev, customerCompany: e.target.value }))}
                  className="w-full px-2 py-1.5 border rounded text-sm"
                  placeholder={t('companyLabel')}
                />
                <input
                  type="text"
                  value={receiptData.additionalPhone}
                  onChange={(e) => setReceiptData(prev => ({ ...prev, additionalPhone: e.target.value }))}
                  className="w-full px-2 py-1.5 border rounded text-sm"
                  placeholder={t('driverPhone')}
                />
              </div>
            </div>
          )}

          {/* Print Content */}
          <div className="p-4 max-h-[50vh] overflow-y-auto">
            <div
              ref={printRef}
              className="bg-white p-3 border-2 border-black rounded-lg"
              style={{ maxWidth: '80mm', fontFamily: 'Arial, sans-serif' }}
            >
              {/* Header */}
              <div className="text-center mb-2">
                <img
                  src="/logo.png"
                  alt="Logo"
                  className="h-24 mx-auto mb-1"
                />
                <h2 className="font-black text-xl tracking-tight">{receiptData.companyName}</h2>
                <p className="text-sm font-bold mt-1">
                  {formatDateTashkent(new Date())} {formatTimeTashkent(new Date())}
                </p>
              </div>

              {/* Divider */}
              <div className="border-t-2 border-black my-2" />

              {/* Customer info */}
              {(receiptData.customerName || receiptData.additionalPhone) && (
                <div className="mb-2 py-1 border-y-2 border-black text-sm">
                  {receiptData.customerName && (
                    <p className="font-black">{t('customerLabel')}: {receiptData.customerName}</p>
                  )}
                  {receiptData.customerPhone && (
                    <p className="font-bold">{t('phoneLabel')}: {receiptData.customerPhone}</p>
                  )}
                  {receiptData.customerCompany && (
                    <p className="font-bold">{t('companyLabel')}: {receiptData.customerCompany}</p>
                  )}
                  {receiptData.additionalPhone && (
                    <p className="font-bold">{t('driverLabel')}: {receiptData.additionalPhone}</p>
                  )}
                </div>
              )}

              {/* Items Table */}
              <table className="w-full text-sm" style={{ borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th className="border-2 border-black p-1 text-left font-black">{t('productLabel')}</th>
                    <th className="border-2 border-black p-1 text-center font-black w-16">{t('quantityLabel')}</th>
                    <th className="border-2 border-black p-1 text-right font-black w-20">{t('amountLabel')}</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item, index) => (
                    <tr key={item.id}>
                      <td className="border-2 border-black p-1">
                        <div className="font-bold">{index + 1}. {item.product_name}</div>
                        <div className="font-bold text-xs">({formatMoney(item.unit_price, false)} x)</div>
                      </td>
                      <td className="border-2 border-black p-1 text-center font-black">
                        {formatNumber(item.quantity)} {item.uom_symbol}
                      </td>
                      <td className="border-2 border-black p-1 text-right font-black">
                        {formatMoney(item.quantity * item.unit_price, false)}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr>
                    <td colSpan={2} className="border-2 border-black p-1 text-right font-black">
                      {t('totalWithCount')} ({items.length} {t('unit').toLowerCase()}):
                    </td>
                    <td className="border-2 border-black p-1 text-right font-black">
                      {formatMoney(items.reduce((sum, item) => sum + item.quantity * item.unit_price, 0), false)}
                    </td>
                  </tr>
                  {generalDiscount > 0 && (
                    <tr>
                      <td colSpan={2} className="border-2 border-black p-1 text-right font-black">
                        {t('discount')}:
                      </td>
                      <td className="border-2 border-black p-1 text-right font-black">
                        -{formatMoney(generalDiscount, false)}
                      </td>
                    </tr>
                  )}
                </tfoot>
              </table>

              {/* Grand Total Box */}
              <div className="border-4 border-black my-2 p-2 text-center bg-white">
                <div className="text-sm font-black">{t('grandTotalLabel')}:</div>
                <div className="text-2xl font-black">
                  {formatMoney(items.reduce((sum, item) => sum + item.quantity * item.unit_price, 0) - generalDiscount, false)}
                </div>
              </div>

              {/* Footer */}
              <div className="border-t-2 border-black pt-2 text-center">
                <p className="text-base font-black">{t('thanksMessage')}</p>
                <p className="text-sm font-bold mt-1">{companyPhone1}</p>
                {companyPhone2 && <p className="text-sm font-bold">{companyPhone2}</p>}
              </div>

              {/* Bottom spacing for tear line */}
              <div className="h-10"></div>
            </div>
          </div>

          {/* Actions */}
          <div className="p-4 border-t flex gap-2">
            <button
              onClick={() => setShowPrintPreview(false)}
              className="flex-1 h-10 border-2 border-gray-200 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors"
            >
              {t('close')}
            </button>
            <button
              onClick={() => setReceiptEditMode(!receiptEditMode)}
              className={`h-10 px-4 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${
                receiptEditMode
                  ? 'bg-blue-100 text-blue-600 border-2 border-blue-300'
                  : 'border-2 border-gray-200 hover:bg-gray-50'
              }`}
            >
              <Edit3 className="w-4 h-4" />
              {t('edit')}
            </button>
            <button
              onClick={() => {
                const printContent = printRef.current
                if (!printContent) return

                const printWindow = window.open('', '_blank')
                if (!printWindow) {
                  toast.error(t('popupBlocked'))
                  return
                }

                printWindow.document.write(`
                  <!DOCTYPE html>
                  <html>
                  <head>
                    <title>Chek - GAYRAT STROY HOUSE</title>
                    <meta charset="UTF-8">
                    <style>
                      * { margin: 0; padding: 0; box-sizing: border-box; }
                      html {
                        height: auto !important;
                      }
                      body {
                        font-family: 'Courier New', monospace;
                        font-size: 12px;
                        width: 76mm;
                        height: auto !important;
                        min-height: auto !important;
                        max-height: none !important;
                        padding: 1mm;
                        margin: 0;
                        color: #000;
                        background: #fff;
                        -webkit-print-color-adjust: exact;
                        print-color-adjust: exact;
                      }

                      /* Header */
                      .header {
                        text-align: center;
                        padding-bottom: 2px;
                      }
                      .header img {
                        height: 40px;
                        max-width: 50mm;
                      }
                      .header h1 {
                        font-size: 14px;
                        font-weight: 900;
                        margin: 2px 0;
                        letter-spacing: 0px;
                      }
                      .header .date {
                        font-size: 11px;
                        font-weight: bold;
                      }

                      /* Divider */
                      .divider {
                        border-top: 1px dashed #000;
                        margin: 2px 0;
                      }

                      /* Customer */
                      .customer {
                        padding: 2px 0;
                        border-top: 1px dashed #000;
                        border-bottom: 1px dashed #000;
                        font-size: 10px;
                        margin: 2px 0;
                      }
                      .customer p { margin: 1px 0; font-weight: bold; }

                      /* Table */
                      table {
                        width: 100%;
                        border-collapse: collapse;
                        margin: 3px 0;
                        table-layout: fixed;
                      }
                      th, td {
                        border: 1px solid #000;
                        padding: 2px 1px;
                        font-size: 10px;
                        word-wrap: break-word;
                        overflow: hidden;
                      }
                      th {
                        font-weight: 900;
                        text-align: left;
                      }
                      .col-product { width: 50%; }
                      .col-qty { width: 22%; text-align: center; }
                      .col-sum { width: 28%; text-align: right; }
                      .text-center { text-align: center; }
                      .text-right { text-align: right; }
                      .font-bold { font-weight: 900; }
                      .product-name { font-weight: bold; font-size: 10px; }
                      .product-price { font-size: 9px; font-weight: bold; }
                      .qty-cell { font-weight: 900; font-size: 10px; }
                      .sum-cell { font-weight: 900; font-size: 10px; }

                      /* Grand Total Box */
                      .grand-total-box {
                        border: 2px solid #000;
                        padding: 3px;
                        margin: 3px 0;
                        text-align: center;
                      }
                      .grand-total-label {
                        font-size: 11px;
                        font-weight: 900;
                      }
                      .grand-total-amount {
                        font-size: 16px;
                        font-weight: 900;
                        letter-spacing: 0px;
                      }

                      /* Footer */
                      .footer {
                        text-align: center;
                        padding-top: 3px;
                        border-top: 1px dashed #000;
                      }
                      .footer .thanks {
                        font-size: 11px;
                        font-weight: 900;
                        margin-bottom: 1px;
                      }
                      .footer .contact {
                        font-size: 10px;
                        font-weight: bold;
                      }

                      /* Bottom spacing for tearing */
                      .tear-space {
                        height: 5mm;
                      }

                      @media print {
                        html, body {
                          width: 76mm;
                          height: auto !important;
                          padding: 1mm;
                          margin: 0 !important;
                        }
                        @page {
                          size: 80mm auto !important;
                          margin: 2mm !important;
                          padding: 0 !important;
                        }
                        * {
                          page-break-inside: avoid;
                        }
                        table {
                          width: 100% !important;
                        }
                      }
                    </style>
                  </head>
                  <body>
                    <div class="header">
                      <img src="/logo.png" alt="Logo" onerror="this.style.display='none'" />
                      <h1>${receiptData.companyName}</h1>
                      <p class="date">${formatDateTashkent(new Date())} ${formatTimeTashkent(new Date())}</p>
                    </div>

                    <div class="divider"></div>

                    ${(receiptData.customerName || receiptData.additionalPhone) ? `
                      <div class="customer">
                        ${receiptData.customerName ? `<p>${t('customerLabel')}: ${receiptData.customerName}</p>` : ''}
                        ${receiptData.customerPhone ? `<p>${t('phoneLabel')}: ${receiptData.customerPhone}</p>` : ''}
                        ${receiptData.customerCompany ? `<p>${t('companyLabel')}: ${receiptData.customerCompany}</p>` : ''}
                        ${receiptData.additionalPhone ? `<p>${t('driverLabel')}: ${receiptData.additionalPhone}</p>` : ''}
                      </div>
                    ` : ''}

                    <table>
                      <thead>
                        <tr>
                          <th class="col-product">${t('productLabel')}</th>
                          <th class="col-qty">${t('quantityLabel')}</th>
                          <th class="col-sum">${t('amountLabel')}</th>
                        </tr>
                      </thead>
                      <tbody>
                        ${items.map((item, index) => `
                          <tr>
                            <td class="col-product">
                              <div class="product-name">${index + 1}. ${item.product_name}</div>
                              <div class="product-price">(${item.unit_price.toLocaleString('uz-UZ')} x)</div>
                            </td>
                            <td class="col-qty qty-cell">${item.quantity.toLocaleString('uz-UZ')} ${item.uom_symbol}</td>
                            <td class="col-sum sum-cell">${(item.quantity * item.unit_price).toLocaleString('uz-UZ')}</td>
                          </tr>
                        `).join('')}
                      </tbody>
                      <tfoot>
                        <tr>
                          <td colspan="2" class="text-right font-bold" style="font-size:10px;">${t('totalWithCount')} (${items.length}):</td>
                          <td class="col-sum font-bold" style="font-size:10px;">${items.reduce((sum, item) => sum + item.quantity * item.unit_price, 0).toLocaleString('uz-UZ')}</td>
                        </tr>
                        ${generalDiscount > 0 ? `
                          <tr>
                            <td colspan="2" class="text-right font-bold" style="font-size:10px;">${t('discount')}:</td>
                            <td class="col-sum font-bold" style="font-size:10px;">-${generalDiscount.toLocaleString('uz-UZ')}</td>
                          </tr>
                        ` : ''}
                      </tfoot>
                    </table>

                    <div class="grand-total-box">
                      <div class="grand-total-label">${t('grandTotalLabel')}:</div>
                      <div class="grand-total-amount">${(items.reduce((sum, item) => sum + item.quantity * item.unit_price, 0) - generalDiscount).toLocaleString('uz-UZ')}</div>
                    </div>

                    <div class="footer">
                      <p class="thanks">${t('thanksMessage')}</p>
                      <p class="contact">${companyPhone1}</p>
                      ${companyPhone2 ? `<p class="contact">${companyPhone2}</p>` : ''}
                    </div>

                    <!-- Bottom spacing for tearing -->
                    <div class="tear-space"></div>
                  </body>
                  </html>
                `)

                printWindow.document.close()
                printWindow.focus()

                // Wait for images to load
                setTimeout(() => {
                  printWindow.print()
                  printWindow.close()
                }, 500)
              }}
              className="flex-1 h-10 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-colors"
            >
              <Printer className="w-4 h-4" />
              {t('printButton')}
            </button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}