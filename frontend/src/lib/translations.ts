// Translations for the ERP system
// Languages: uz (O'zbek latin), ru (Русский), uz_cyrl (Ўзбек кирилл)

export type LanguageCode = 'uz' | 'ru' | 'uz_cyrl'

export const LANGUAGES: { code: LanguageCode; name: string; flag: string }[] = [
  { code: 'uz', name: "O'zbek", flag: '🇺🇿' },
  { code: 'ru', name: 'Русский', flag: '🇷🇺' },
  { code: 'uz_cyrl', name: 'Ўзбек', flag: '🇺🇿' },
]

type TranslationKeys = {
  // Common
  save: string
  cancel: string
  delete: string
  edit: string
  add: string
  search: string
  filter: string
  loading: string
  noData: string
  confirm: string
  close: string
  yes: string
  no: string
  all: string
  total: string
  actions: string
  status: string
  date: string
  time: string
  name: string
  phone: string
  address: string
  description: string
  amount: string
  price: string
  quantity: string
  sum: string
  discount: string
  debt: string
  paid: string
  balance: string
  today: string
  yesterday: string
  thisWeek: string
  thisMonth: string
  from: string
  to: string
  export: string
  print: string
  refresh: string
  back: string
  next: string
  previous: string
  
  // Auth
  login: string
  logout: string
  username: string
  password: string
  rememberMe: string
  forgotPassword: string
  loginError: string
  loginSuccess: string
  logoutConfirm: string
  
  // Navigation
  dashboard: string
  pos: string
  products: string
  customers: string
  sales: string
  warehouse: string
  reports: string
  settings: string
  users: string
  expenses: string
  suppliers: string
  
  // Dashboard
  todaySales: string
  monthSales: string
  totalDebt: string
  lowStock: string
  recentSales: string
  topProducts: string
  salesChart: string
  
  // POS
  cart: string
  cartEmpty: string
  selectCustomer: string
  customerDebt: string
  payment: string
  paymentType: string
  cash: string
  card: string
  transfer: string
  onCredit: string
  change: string
  clear: string
  checkout: string
  printReceipt: string
  saleCompleted: string
  addToCart: string
  removeFromCart: string
  selectWarehouse: string
  availableStock: string
  outOfStock: string
  categories: string
  favorites: string
  allProducts: string
  searchProducts: string
  unitPrice: string
  totalPrice: string
  costPrice: string
  profit: string
  finalTotal: string
  subtotal: string
  saveLater: string
  savedCarts: string
  loadCart: string
  driverPhone: string
  
  // Products
  productName: string
  productCode: string
  article: string
  category: string
  unit: string
  baseUnit: string
  conversionFactor: string
  sellingPrice: string
  purchasePrice: string
  minStock: string
  currentStock: string
  addProduct: string
  editProduct: string
  deleteProduct: string
  productDeleted: string
  productSaved: string
  importProducts: string
  exportProducts: string
  
  // Customers
  customerName: string
  customerType: string
  companyName: string
  telegramId: string
  currentDebt: string
  addCustomer: string
  editCustomer: string
  deleteCustomer: string
  customerDeleted: string
  customerSaved: string
  retail: string
  wholesale: string
  vip: string
  customerHistory: string
  salesHistory: string
  paymentHistory: string
  debtHistory: string
  makePayment: string
  paymentReceived: string
  downloadReport: string
  
  // Sales
  saleNumber: string
  saleDate: string
  seller: string
  customer: string
  paymentStatus: string
  paidStatus: string
  debtStatus: string
  partialStatus: string
  itemsCount: string
  viewDetails: string
  editSale: string
  deleteSale: string
  cancelSale: string
  saleDeleted: string
  returnSale: string
  
  // Warehouse
  warehouseName: string
  stockIn: string
  stockOut: string
  stockTransfer: string
  stockAdjustment: string
  inventory: string
  movements: string
  movementType: string
  sourceWarehouse: string
  destinationWarehouse: string
  reason: string
  reference: string
  addMovement: string
  movementSaved: string
  lowStockAlert: string
  
  // Reports
  salesReport: string
  stockReport: string
  debtReport: string
  profitReport: string
  sellerReport: string
  periodReport: string
  dailyReport: string
  weeklyReport: string
  monthlyReport: string
  customPeriod: string
  generateReport: string
  downloadExcel: string
  downloadPdf: string
  
  // Settings
  companySettings: string
  companyName2: string
  companyPhone: string
  companyAddress: string
  exchangeRate: string
  usdRate: string
  language: string
  selectLanguage: string
  languageChanged: string
  generalSettings: string
  receiptSettings: string
  notificationSettings: string
  telegramBot: string
  telegramNotifications: string
  telegramDirectorIds: string
  telegramHowToFind: string
  telegramGroupReport: string
  groupChatId: string
  reportTime: string
  reportTimeHint: string
  autoSend: string
  dailyAt: string
  enterGroupChatId: string
  test: string
  sendNow: string
  version: string
  database: string
  salesSettings: string
  maxDiscount: string
  maxDiscountHint: string
  allowDebtSales: string
  autoPrintReceipt: string
  
  // Users
  userManagement: string
  addUser: string
  editUser: string
  deleteUser: string
  firstName: string
  lastName: string
  email: string
  role: string
  assignedWarehouse: string
  active: string
  blocked: string
  blockUser: string
  unblockUser: string
  resetPassword: string
  changePassword: string
  currentPassword: string
  newPassword: string
  confirmPassword: string
  passwordChanged: string
  
  // Roles
  director: string
  seller2: string
  warehouseManager: string
  accountant: string
  
  // Validation messages
  required: string
  invalidEmail: string
  minLength: string
  maxLength: string
  invalidPhone: string
  passwordMismatch: string
  
  // Success messages
  savedSuccess: string
  deletedSuccess: string
  updatedSuccess: string
  
  // Error messages
  errorOccurred: string
  notFound: string
  accessDenied: string
  serverError: string
  networkError: string
  
  // Additional keys for full i18n support
  product: string
  units: string
  saving: string
  adding: string
  notSelected: string
  select: string
  productUpdated: string
  uomAdded: string
  uomDeleted: string
  categoryAdded: string
  categoryUpdated: string
  categoryDeleted: string
  categoryHasProducts: string
  confirmDelete: string
  noProductsFound: string
  noCustomersFound: string
  noSalesFound: string
  noHistoryFound: string
  totalItems: string
  newProduct: string
  enterProductDetails: string
  barcode: string
  vipPrice: string
  minStockHint: string
  favoriteProduct: string
  favoriteHint: string
  productColor: string
  costPriceHint: string
  configureUnits: string
  sellInDifferentUnits: string
  existingUnits: string
  addNewUnit: string
  fromUnit: string
  toUnit: string
  exampleText: string
  salePriceOptional: string
  autoCalculated: string
  newCategory: string
  enterCategoryName: string
  categoryName: string
  editCategory: string
  changeCategoryName: string
  itemsCount2: string
  receiptNumber: string
  totalAmount: string
  reportDownloaded: string
  customerAdded: string
  customerUpdated: string
  saleEdited: string
  cancelled: string
  items: string
  itemsList: string
  forSelectedPeriod: string
  profitByProducts: string
  showPasswords: string
  updatePasswordHint: string
  help: string
  helpText: string
  allRightsReserved: string
  validationError: string
  measure: string
  
  // Reports page
  totalRevenue: string
  totalCostPrice: string
  profitPercent: string
  salesCount: string
  totalSum: string
  discounts: string
  soldOnCredit: string
  selectSeller: string
  sellersList: string
  totalSales: string
  customersCount: string
  salesReportTitle: string
  stockReportTitle: string
  debtorsReportTitle: string
  dailyReportTitle: string
  priceListTitle: string
  excelPreparing: string
  excelDownloaded: string
  excelError: string
  downloadExcel2: string
  downloadPdf2: string
  averageCheck: string
  anonymousSales: string
  forToday: string
  recentSalesTitle: string
  dailySales: string
  reportPreparing: string
  reportError: string
  dailyIndicators: string
  timesSold: string
  pieces: string
  purchase: string
  currentStatus: string
  currentDebts: string
  
  // Customer dialog
  editCustomerTitle: string
  addCustomerTitle: string
  enterCustomerDetails: string
  fullName: string
  nameRequired: string
  phoneLabel: string
  phonePlaceholder: string
  addressLabel: string
  addressPlaceholder: string
  regularCustomer: string
  vipCustomer: string
  balanceLabel: string
  notesLabel: string
  notesPlaceholder: string
  
  // Dashboard
  welcomeMessage: string
  
  // POS
  orderSaved: string
  editSaleTitle: string
  deleteError: string
  editError: string
  selectProduct: string
  additionalInfo: string
  
  // Settings
  reportNotSent: string
  messageNotSent: string
  
  // Customer form additional
  phoneRequired: string
  secondaryPhone: string
  telegramPlaceholder: string
  emailLabel: string
  companyPlaceholder: string
  fullAddress: string
  regular: string
  creditLimit: string
  assignedSeller: string
  notAssigned: string
  
  // Edit reason
  editReason: string
  editReasonPlaceholder: string
  
  // Settings additional
  dailyReportSent: string
  testMessageSent: string
  
  // Warehouse
  movementEdited: string
  movementDeleted: string

  // Warehouse page
  addAtLeastOneProduct: string
  allCategories: string
  avgCostUsd: string
  avgCostUzs: string
  totalValue: string
  low: string
  productsNotFound: string
  incomeType: string
  soldType: string
  clearFilters: string
  totalCount: string
  priceUsd: string
  priceUzs: string
  documentNo: string
  supplier: string
  supplierName: string
  transferIn: string
  transferOut: string
  adjustmentPlus: string
  adjustmentMinus: string
  writeOff: string
  movementHistoryNotFound: string
  stockIncomeUsd: string
  stockIncome: string
  currentRateInfo: string
  invoiceNo: string
  productsLabel: string
  measureUnit: string
  totalUsd: string
  totalUzs: string
  inUzs: string
  inUsd: string
  currency: string
  incomeSuccess: string
  saveIncome: string
  editMovementTitle: string
  quantityChangeWarning: string
  deleteMovementTitle: string
  confirmDeleteMovement: string
  attentionWarning: string
  deleteMovementWarning: string
  deleteReasonLabel: string
  enterReasonRequired: string

  // Customer dialogs
  deleteCustomerTitle: string
  confirmDeleteCustomer: string
  customerHasDebt: string
  deleting: string
  acceptPayment: string
  paymentAmount: string
  enterAmount: string
  optionalNote: string
  accept: string
  customerDetails: string
  fullHistoryAndStats: string
  totalPurchases: string
  advanceBalance: string
  downloadFullReport: string
  allSalesProductsDebtInExcel: string
  receiptNo: string
  paidAmount: string
  debtAmount: string
  debtPaymentHistory: string
  debtBefore: string
  debtAfter: string
  paymentTransaction: string
  purchaseTransaction: string
  onDebt: string
  partial: string
  productsList: string

  // Sales page
  lastSale: string
  edited: string
  unknownCustomer: string
  deleteSaleTitle: string
  confirmDeleteSale: string
  saleDeleteWarning: string
  grandTotal: string
  editedBy: string
  editedWhen: string
  cancelledStatus: string
  cancelledBy: string
  cancelledWhen: string
  pending: string
  saleLoadError: string
  saleDeletedSuccess: string

  // POS page extended
  dragToReorder: string
  sellingPriceSum: string
  quantityUnit: string
  priceBelowCost: string
  editPrice: string
  editQuantity: string
  inDollars: string
  saveForLater: string
  cartSavedForLater: string
  receiptPreview: string
  confirmSale: string

  // POS toasts
  saved: string
  added: string
  deleted: string
  priceChanged: string
  quantityChanged: string
  invalidDiscount: string
  invalidAmount: string
  selectCustomerForDebt: string
  enterEditReason: string
  reasonMinLength: string
  cartLoaded: string

  // POS receipt and print
  baseUnitLabel: string
  customerLabel: string
  companyLabel: string
  company: string
  driverLabel: string
  productLabel: string
  quantityLabel: string
  amountLabel: string
  totalWithCount: string
  grandTotalLabel: string
  thanksMessage: string
  printButton: string
  popupBlocked: string
}

export const translations: Record<LanguageCode, TranslationKeys> = {
  uz: {
    // Common
    save: 'Saqlash',
    cancel: 'Bekor qilish',
    delete: "O'chirish",
    edit: 'Tahrirlash',
    add: "Qo'shish",
    search: 'Qidirish',
    filter: 'Filtr',
    loading: 'Yuklanmoqda...',
    noData: "Ma'lumot yo'q",
    confirm: 'Tasdiqlash',
    close: 'Yopish',
    yes: 'Ha',
    no: "Yo'q",
    all: 'Barchasi',
    total: 'Jami',
    actions: 'Amallar',
    status: 'Holat',
    date: 'Sana',
    time: 'Vaqt',
    name: 'Nomi',
    phone: 'Telefon',
    address: 'Manzil',
    description: 'Tavsif',
    amount: 'Miqdor',
    price: 'Narx',
    quantity: 'Soni',
    sum: "So'm",
    discount: 'Chegirma',
    debt: 'Qarz',
    paid: "To'langan",
    balance: 'Balans',
    today: 'Bugun',
    yesterday: 'Kecha',
    thisWeek: 'Shu hafta',
    thisMonth: 'Shu oy',
    from: 'Dan',
    to: 'Gacha',
    export: 'Eksport',
    print: 'Chop etish',
    refresh: 'Yangilash',
    back: 'Orqaga',
    next: 'Keyingi',
    previous: 'Oldingi',

    // Auth
    login: 'Kirish',
    logout: 'Chiqish',
    username: 'Foydalanuvchi nomi',
    password: 'Parol',
    rememberMe: 'Eslab qolish',
    forgotPassword: 'Parolni unutdingizmi?',
    loginError: "Login yoki parol noto'g'ri",
    loginSuccess: 'Muvaffaqiyatli kirdingiz',
    logoutConfirm: 'Tizimdan chiqmoqchimisiz?',

    // Navigation
    dashboard: 'Boshqaruv paneli',
    pos: 'Kassa',
    products: 'Mahsulotlar',
    customers: 'Mijozlar',
    sales: 'Sotuvlar',
    warehouse: 'Ombor',
    reports: 'Hisobotlar',
    settings: 'Sozlamalar',
    users: 'Foydalanuvchilar',
    expenses: 'Chiqimlar',
    suppliers: "Ta'minotchilar",

    // Dashboard
    todaySales: 'Bugungi savdo',
    monthSales: 'Oylik savdo',
    totalDebt: 'Umumiy qarz',
    lowStock: 'Kam qolgan tovarlar',
    recentSales: 'So\'nggi sotuvlar',
    topProducts: 'Top mahsulotlar',
    salesChart: 'Sotuv grafigi',

    // POS
    cart: 'Savat',
    cartEmpty: "Savat bo'sh",
    selectCustomer: 'Mijoz tanlash',
    customerDebt: 'Mijoz qarzi',
    payment: "To'lov",
    paymentType: "To'lov turi",
    cash: 'Naqd',
    card: 'Karta',
    transfer: "O'tkazma",
    onCredit: 'Qarzga',
    change: 'Qaytim',
    clear: 'Tozalash',
    checkout: 'Rasmiylashtirish',
    printReceipt: 'Chek chiqarish',
    saleCompleted: 'Sotuv amalga oshirildi',
    addToCart: "Savatga qo'shish",
    removeFromCart: "Savatdan o'chirish",
    selectWarehouse: 'Ombor tanlash',
    availableStock: 'Mavjud miqdor',
    outOfStock: 'Tugagan',
    categories: 'Kategoriyalar',
    favorites: 'Sevimlilar',
    allProducts: 'Barcha mahsulotlar',
    searchProducts: 'Mahsulot qidirish',
    unitPrice: 'Birlik narxi',
    totalPrice: 'Umumiy narx',
    costPrice: 'Kelish narxi',
    profit: 'Foyda',
    finalTotal: 'Yakuniy summa',
    subtotal: 'Jami',
    saveLater: 'Keyinroq',
    savedCarts: 'Saqlangan xaridlar',
    loadCart: 'Yuklash',
    driverPhone: 'Mijoz telefoni',

    // Products
    productName: 'Mahsulot nomi',
    productCode: 'Mahsulot kodi',
    article: 'Artikul',
    category: 'Kategoriya',
    unit: "O'lchov birligi",
    baseUnit: 'Asosiy birlik',
    conversionFactor: "O'tkazish koeffitsienti",
    sellingPrice: 'Sotuv narxi',
    purchasePrice: 'Xarid narxi',
    minStock: 'Minimal miqdor',
    currentStock: 'Joriy miqdor',
    addProduct: "Mahsulot qo'shish",
    editProduct: 'Mahsulotni tahrirlash',
    deleteProduct: "Mahsulotni o'chirish",
    productDeleted: "Mahsulot o'chirildi",
    productSaved: 'Mahsulot saqlandi',
    importProducts: 'Import qilish',
    exportProducts: 'Eksport qilish',

    // Customers
    customerName: 'Mijoz ismi',
    customerType: 'Mijoz turi',
    companyName: 'Kompaniya nomi',
    telegramId: 'Telegram ID',
    currentDebt: 'Joriy qarz',
    addCustomer: "Mijoz qo'shish",
    editCustomer: 'Mijozni tahrirlash',
    deleteCustomer: "Mijozni o'chirish",
    customerDeleted: "Mijoz o'chirildi",
    customerSaved: 'Mijoz saqlandi',
    retail: 'Chakana',
    wholesale: 'Ulgurji',
    vip: 'VIP',
    customerHistory: 'Mijoz tarixi',
    salesHistory: 'Sotuvlar tarixi',
    paymentHistory: "To'lovlar tarixi",
    debtHistory: 'Qarzlar tarixi',
    makePayment: "To'lov qilish",
    paymentReceived: "To'lov qabul qilindi",
    downloadReport: 'Hisobotni yuklash',

    // Sales
    saleNumber: 'Sotuv raqami',
    saleDate: 'Sotuv sanasi',
    seller: 'Sotuvchi',
    customer: 'Mijoz',
    paymentStatus: "To'lov holati",
    paidStatus: "To'langan",
    debtStatus: 'Qarzga',
    partialStatus: 'Qisman',
    itemsCount: 'Tovarlar soni',
    viewDetails: 'Batafsil',
    editSale: 'Sotuvni tahrirlash',
    deleteSale: "Sotuvni o'chirish",
    cancelSale: 'Sotuvni bekor qilish',
    saleDeleted: "Sotuv o'chirildi",
    returnSale: 'Qaytarish',

    // Warehouse
    warehouseName: 'Ombor nomi',
    stockIn: 'Kirim',
    stockOut: 'Chiqim',
    stockTransfer: "O'tkazma",
    stockAdjustment: 'Tuzatish',
    inventory: 'Inventarizatsiya',
    movements: 'Harakatlar',
    movementType: 'Harakat turi',
    sourceWarehouse: 'Qayerdan',
    destinationWarehouse: 'Qayerga',
    reason: 'Sabab',
    reference: 'Havola',
    addMovement: "Harakat qo'shish",
    movementSaved: 'Harakat saqlandi',
    lowStockAlert: 'Kam qolgan tovarlar',

    // Reports
    salesReport: 'Sotuvlar hisoboti',
    stockReport: 'Ombor hisoboti',
    debtReport: 'Qarzlar hisoboti',
    profitReport: 'Foyda hisoboti',
    sellerReport: 'Sotuvchilar hisoboti',
    periodReport: 'Davr hisoboti',
    dailyReport: 'Kunlik hisobot',
    weeklyReport: 'Haftalik hisobot',
    monthlyReport: 'Oylik hisobot',
    customPeriod: 'Boshqa davr',
    generateReport: 'Hisobot yaratish',
    downloadExcel: 'Excel yuklash',
    downloadPdf: 'PDF yuklash',

    // Settings
    companySettings: 'Kompaniya sozlamalari',
    companyName2: 'Kompaniya nomi',
    companyPhone: 'Kompaniya telefoni',
    companyAddress: 'Kompaniya manzili',
    exchangeRate: 'Valyuta kursi',
    usdRate: 'Dollar kursi',
    language: 'Til',
    selectLanguage: 'Tilni tanlang',
    languageChanged: "Til o'zgartirildi",
    generalSettings: 'Umumiy sozlamalar',
    receiptSettings: 'Chek sozlamalari',
    notificationSettings: 'Bildirishnoma sozlamalari',
    telegramBot: 'Telegram Bot',
    telegramNotifications: 'Telegram xabarnomalar',
    telegramDirectorIds: 'Direktor Telegram ID lari',
    telegramHowToFind: 'Telegram ID qanday topiladi?',
    telegramGroupReport: 'Telegram guruhga hisobot',
    groupChatId: 'Guruh Chat ID',
    reportTime: 'Hisobot vaqti',
    reportTimeHint: 'Har kuni shu vaqtda hisobot yuboriladi',
    autoSend: 'Avtomatik yuborish',
    dailyAt: 'Har kuni belgilangan vaqtda',
    enterGroupChatId: 'Guruh Chat ID kiriting',
    test: 'Test',
    sendNow: 'Hozir yuborish',
    version: 'Versiya',
    database: "Ma'lumotlar bazasi",
    salesSettings: 'Sotuv sozlamalari',
    maxDiscount: 'Maksimal chegirma',
    maxDiscountHint: 'Sotuvchi bera oladigan maksimal chegirma',
    allowDebtSales: 'Qarzga sotish imkoniyati',
    autoPrintReceipt: 'Avtomatik chek chop etish',

    // Users
    userManagement: 'Foydalanuvchilarni boshqarish',
    addUser: "Foydalanuvchi qo'shish",
    editUser: 'Foydalanuvchini tahrirlash',
    deleteUser: "Foydalanuvchini o'chirish",
    firstName: 'Ism',
    lastName: 'Familiya',
    email: 'Email',
    role: 'Rol',
    assignedWarehouse: 'Biriktirilgan ombor',
    active: 'Faol',
    blocked: 'Bloklangan',
    blockUser: 'Bloklash',
    unblockUser: 'Blokdan chiqarish',
    resetPassword: 'Parolni tiklash',
    changePassword: "Parolni o'zgartirish",
    currentPassword: 'Joriy parol',
    newPassword: 'Yangi parol',
    confirmPassword: 'Parolni tasdiqlash',
    passwordChanged: "Parol o'zgartirildi",

    // Roles
    director: 'Direktor',
    seller2: 'Sotuvchi',
    warehouseManager: 'Omborchi',
    accountant: 'Hisobchi',

    // Validation messages
    required: 'Bu maydon talab qilinadi',
    invalidEmail: "Email noto'g'ri formatda",
    minLength: 'Minimal uzunlik: {min}',
    maxLength: 'Maksimal uzunlik: {max}',
    invalidPhone: "Telefon raqami noto'g'ri",
    passwordMismatch: 'Parollar mos kelmaydi',

    // Success messages
    savedSuccess: 'Muvaffaqiyatli saqlandi',
    deletedSuccess: "Muvaffaqiyatli o'chirildi",
    updatedSuccess: 'Muvaffaqiyatli yangilandi',

    // Error messages
    errorOccurred: 'Xatolik yuz berdi',
    notFound: 'Topilmadi',
    accessDenied: 'Ruxsat berilmagan',
    serverError: 'Server xatosi',
    networkError: 'Tarmoq xatosi',

    // Additional translations
    product: 'Tovar',
    units: "O'lchov birliklari",
    saving: 'Saqlanmoqda...',
    adding: "Qo'shilmoqda...",
    notSelected: 'Tanlanmagan',
    select: 'Tanlang',
    productUpdated: 'Tovar yangilandi',
    uomAdded: "O'lchov birligi qo'shildi",
    uomDeleted: "O'lchov birligi o'chirildi",
    categoryAdded: "Kategoriya qo'shildi",
    categoryUpdated: 'Kategoriya yangilandi',
    categoryDeleted: "Kategoriya o'chirildi",
    categoryHasProducts: "Kategoriyada tovarlar bor, avval ularni o'chiring",
    confirmDelete: "O'chirishni tasdiqlaysizmi?",
    noProductsFound: 'Tovar topilmadi',
    noCustomersFound: 'Mijozlar topilmadi',
    noSalesFound: 'Sotuvlar topilmadi',
    noHistoryFound: 'Tarix topilmadi',
    totalItems: 'Jami',
    newProduct: 'Yangi tovar',
    enterProductDetails: "Tovar ma'lumotlarini kiriting",
    barcode: 'Shtrix-kod',
    vipPrice: 'VIP narx',
    minStockHint: "Qoldiq shu miqdordan kam bo'lganda ogohlantirish",
    favoriteProduct: 'Sevimli tovar',
    favoriteHint: 'Kassada tez topish uchun',
    productColor: 'Tovar rangi',
    costPriceHint: 'Kelish narxi omborga kirim qilganda avtomatik aniqlanadi',
    configureUnits: "O'lchov birliklarini sozlash",
    sellInDifferentUnits: "Turli o'lchovlarda sotish",
    existingUnits: "Mavjud o'lchov birliklari",
    addNewUnit: "Yangi o'lchov qo'shish",
    fromUnit: "Qaysi o'lchovdan",
    toUnit: "Qaysi o'lchovga",
    exampleText: 'Misol',
    salePriceOptional: 'Sotish narxi (ixtiyoriy)',
    autoCalculated: "Bo'sh qoldiring = avtomatik hisoblanadi",
    newCategory: 'Yangi kategoriya',
    enterCategoryName: 'Kategoriya nomini kiriting',
    categoryName: 'Kategoriya nomi',
    editCategory: 'Kategoriyani tahrirlash',
    changeCategoryName: "Kategoriya nomini o'zgartiring",
    itemsCount2: 'Tovarlar soni',
    receiptNumber: 'Chek raqami',
    totalAmount: 'Umumiy summa',
    reportDownloaded: 'Hisobot muvaffaqiyatli yuklandi',
    customerAdded: "Mijoz muvaffaqiyatli qo'shildi",
    customerUpdated: 'Mijoz muvaffaqiyatli yangilandi',
    saleEdited: 'Sotuv muvaffaqiyatli tahrirlandi',
    cancelled: 'Bekor qilingan',
    items: 'Tovarlar',
    itemsList: "Tovarlar ro'yxati",
    forSelectedPeriod: 'Tanlangan davr uchun',
    profitByProducts: "Tovarlar bo'yicha foyda",
    showPasswords: "Parollarni ko'rsatish",
    updatePasswordHint: "Xavfsizlik uchun parolingizni yangilang",
    help: 'Yordam',
    helpText: "Dastur bo'yicha yordam yoki qo'shimcha xizmatlar uchun biz bilan bog'laning",
    allRightsReserved: 'Barcha huquqlar himoyalangan',
    validationError: 'Validatsiya xatosi',
    measure: "O'lchov",

    // Reports page
    totalRevenue: 'Jami daromad',
    totalCostPrice: 'Jami tan narx',
    profitPercent: 'Foyda foizi',
    salesCount: 'Sotuvlar soni',
    totalSum: 'Jami summa',
    discounts: 'Chegirmalar',
    soldOnCredit: 'Qarzga sotilgan',
    selectSeller: 'Kassirni tanlang',
    sellersList: "Kassirlar ro'yxati",
    totalSales: 'Jami sotuvlar',
    customersCount: 'Mijozlar soni',
    salesReportTitle: 'Sotuvlar hisoboti',
    stockReportTitle: 'Qoldiqlar hisoboti',
    debtorsReportTitle: 'Qarzdorlar hisoboti',
    dailyReportTitle: 'Kunlik hisobot',
    priceListTitle: "Narxlar ro'yxati",
    excelPreparing: 'Excel tayyorlanmoqda...',
    excelDownloaded: 'Excel yuklandi!',
    excelError: 'Excel yuklanmadi',
    downloadExcel2: 'Excel yuklash',
    downloadPdf2: 'PDF yuklash',
    averageCheck: "O'rtacha chek",
    anonymousSales: 'Anonim sotuvlar',
    forToday: 'Bugun uchun',
    recentSalesTitle: "So'nggi sotuvlar",
    dailySales: 'Kunlik savdolar',
    reportPreparing: 'Hisobot tayyorlanmoqda...',
    reportError: 'Hisobot yuklanmadi',
    dailyIndicators: "Kunlik ko'rsatkichlar",
    timesSold: 'marta sotildi',
    pieces: 'dona',
    purchase: 'xarid',
    currentStatus: 'Joriy holat',
    currentDebts: 'Joriy qarzlar',

    // Customer dialog
    editCustomerTitle: 'Mijozni tahrirlash',
    addCustomerTitle: "Yangi mijoz qo'shish",
    enterCustomerDetails: "Mijoz ma'lumotlarini kiriting",
    fullName: "To'liq ism",
    nameRequired: 'Ism kiritilishi shart',
    phoneLabel: 'Telefon raqami',
    phonePlaceholder: 'Telefon raqamini kiriting',
    addressLabel: 'Manzil',
    addressPlaceholder: 'Manzilni kiriting',
    regularCustomer: 'Oddiy mijoz',
    vipCustomer: 'VIP mijoz',
    balanceLabel: 'Balans',
    notesLabel: 'Izoh',
    notesPlaceholder: "Qo'shimcha ma'lumot",

    // Dashboard
    welcomeMessage: 'Xush kelibsiz',

    // POS
    orderSaved: 'Tartib saqlandi',
    editSaleTitle: 'tahrirlash',
    deleteError: "O'chirishda xatolik",
    editError: 'Tahrirlashda xatolik',
    selectProduct: 'Tovar tanlang',
    additionalInfo: "Qo'shimcha ma'lumot",

    // Settings
    reportNotSent: 'Hisobot yuborilmadi',
    messageNotSent: 'Xabar yuborilmadi',

    // Customer form additional
    phoneRequired: 'Telefon kiritilishi shart',
    secondaryPhone: "Qo'shimcha telefon",
    telegramPlaceholder: '@username yoki 123456789',
    emailLabel: 'Email',
    companyPlaceholder: 'Kompaniya nomi',
    fullAddress: "To'liq manzil",
    regular: 'Oddiy',
    creditLimit: 'Kredit limiti',
    assignedSeller: 'Biriktirilgan kassir',
    notAssigned: 'Tanlanmagan',

    // Edit reason
    editReason: 'Tahrirlash sababi',
    editReasonPlaceholder: 'Sabab kiriting (kamida 3 ta belgi)',

    // Settings additional
    dailyReportSent: 'Kunlik hisobot yuborildi!',
    testMessageSent: 'Test xabar yuborildi!',

    // Warehouse
    movementEdited: 'Harakat muvaffaqiyatli tahrirlandi!',
    movementDeleted: "Harakat o'chirildi!",

    // Warehouse page
    addAtLeastOneProduct: "Kamida bitta tovar qo'shing",
    allCategories: 'Barcha kategoriyalar',
    avgCostUsd: "O'rtacha kelish (USD)",
    avgCostUzs: "O'rtacha kelish (UZS)",
    totalValue: 'Jami qiymat',
    low: 'Kam',
    productsNotFound: 'Tovarlar topilmadi',
    incomeType: 'Kirim',
    soldType: 'Sotildi',
    clearFilters: 'Tozalash',
    totalCount: 'Jami',
    priceUsd: 'Narx (USD)',
    priceUzs: 'Narx (UZS)',
    documentNo: 'Hujjat №',
    supplier: 'Yetkazuvchi',
    supplierName: 'Yetkazuvchi nomi',
    transferIn: 'Keldi',
    transferOut: "Jo'natildi",
    adjustmentPlus: 'Tuzatish+',
    adjustmentMinus: 'Tuzatish-',
    writeOff: 'Zarar',
    movementHistoryNotFound: 'Harakatlar tarixi topilmadi',
    stockIncomeUsd: 'Omborga kirim (USD)',
    stockIncome: 'Omborga kirim',
    currentRateInfo: 'Joriy kurs',
    invoiceNo: 'Faktura №',
    productsLabel: 'Tovarlar',
    measureUnit: "O'lchov",
    totalUsd: 'Jami (USD)',
    totalUzs: "Jami (so'm)",
    inUzs: "So'mda",
    inUsd: 'Dollarda',
    currency: 'Valyuta',
    incomeSuccess: 'Kirim muvaffaqiyatli amalga oshirildi!',
    saveIncome: 'Kirimni saqlash',
    editMovementTitle: 'Harakatni tahrirlash',
    quantityChangeWarning: "Miqdorni o'zgartirsangiz, ombor qoldig'i avtomatik yangilanadi.",
    deleteMovementTitle: "Harakatni o'chirish",
    confirmDeleteMovement: "kirimini o'chirmoqchimisiz?",
    attentionWarning: 'Diqqat!',
    deleteMovementWarning: "Bu harakat ombor qoldig'ini teskari o'zgartiradi. Kirim o'chirilsa, tovar qoldig'i kamayadi.",
    deleteReasonLabel: "O'chirish sababi",
    enterReasonRequired: 'Sabab kiriting (majburiy)',

    // Customer dialogs
    deleteCustomerTitle: "Mijozni o'chirish",
    confirmDeleteCustomer: "ni o'chirmoqchimisiz?",
    customerHasDebt: "Diqqat: Bu mijozda qarz mavjud!",
    deleting: "O'chirilmoqda...",
    acceptPayment: "To'lov qabul qilish",
    paymentAmount: "To'lov summasi",
    enterAmount: "Summa kiriting",
    optionalNote: "Ixtiyoriy izoh",
    accept: "Qabul qilish",
    customerDetails: "Mijoz ma'lumotlari",
    fullHistoryAndStats: "To'liq tarix va statistika",
    totalPurchases: "Jami xarid",
    advanceBalance: "Avans",
    downloadFullReport: "To'liq hisobot yuklash",
    allSalesProductsDebtInExcel: "Barcha sotuvlar, tovarlar va qarz tarixi bitta Excel faylda",
    receiptNo: "Chek №",
    paidAmount: "To'langan",
    debtAmount: "Qarz",
    debtPaymentHistory: "Qarz va to'lovlar tarixi",
    debtBefore: "Qarz oldin",
    debtAfter: "Qarz keyin",
    paymentTransaction: "To'lov",
    purchaseTransaction: "Xarid",
    onDebt: "Qarzga",
    partial: "Qisman",
    productsList: "Tovarlar ro'yxati",

    // Sales page
    lastSale: "Oxirgi",
    edited: "Tahrirlangan",
    unknownCustomer: "Noma'lum",
    deleteSaleTitle: "Sotuvni o'chirish",
    confirmDeleteSale: "ni o'chirmoqchimisiz?",
    saleDeleteWarning: "Sotuv bekor qilinadi va tovarlar omborga qaytariladi. Mijoz qarzlari ham yangilanadi.",
    grandTotal: "Umumiy",
    editedBy: "Kim",
    editedWhen: "Qachon",
    cancelledStatus: "Bekor qilingan",
    cancelledBy: "Kim",
    cancelledWhen: "Qachon",
    pending: "Kutilmoqda",
    saleLoadError: "Sotuv ma'lumotlarini yuklashda xatolik",
    saleDeletedSuccess: "Sotuv o'chirildi!",

    // POS page extended
    dragToReorder: "Tartibni o'zgartirish uchun surish",
    sellingPriceSum: "Sotish narxi (so'm)",
    quantityUnit: "Miqdor",
    priceBelowCost: "Narx tan narxdan past",
    editPrice: "Narxni o'zgartirish",
    editQuantity: "Miqdorni o'zgartirish",
    inDollars: "Dollarda",
    saveForLater: "Keyinroqqa saqlash",
    cartSavedForLater: "Xarid keyinroqqa saqlandi!",
    receiptPreview: "Chek ko'rinishi",
    confirmSale: "Tasdiqlash",

    // POS toasts
    saved: "Saqlandi",
    added: "Qo'shildi",
    deleted: "O'chirildi",
    priceChanged: "Narx o'zgartirildi",
    quantityChanged: "Miqdor o'zgartirildi",
    invalidDiscount: "Chegirma summasi noto'g'ri",
    invalidAmount: "Summa noto'g'ri",
    selectCustomerForDebt: "Qarzga sotuv uchun mijoz tanlang!",
    enterEditReason: "Tahrirlash sababini kiriting!",
    reasonMinLength: "Sabab kamida 3 ta belgidan iborat bo'lishi kerak!",
    cartLoaded: "Xarid yuklandi!",

    // POS receipt and print
    baseUnitLabel: "Asosiy",
    customerLabel: "Mijoz",
    companyLabel: "Kompaniya",
    company: "Kompaniya",
    driverLabel: "Tel",
    productLabel: "Mahsulot",
    quantityLabel: "Soni",
    amountLabel: "Summa",
    totalWithCount: "Jami",
    grandTotalLabel: "YAKUNIY SUMMA",
    thanksMessage: "★ RAHMAT! ★",
    printButton: "Chop etish",
    popupBlocked: "Popup bloklangan. Ruxsat bering.",
  },

  ru: {
    // Common
    save: 'Сохранить',
    cancel: 'Отмена',
    delete: 'Удалить',
    edit: 'Редактировать',
    add: 'Добавить',
    search: 'Поиск',
    filter: 'Фильтр',
    loading: 'Загрузка...',
    noData: 'Нет данных',
    confirm: 'Подтвердить',
    close: 'Закрыть',
    yes: 'Да',
    no: 'Нет',
    all: 'Все',
    total: 'Всего',
    actions: 'Действия',
    status: 'Статус',
    date: 'Дата',
    time: 'Время',
    name: 'Название',
    phone: 'Телефон',
    address: 'Адрес',
    description: 'Описание',
    amount: 'Количество',
    price: 'Цена',
    quantity: 'Кол-во',
    sum: 'Сум',
    discount: 'Скидка',
    debt: 'Долг',
    paid: 'Оплачено',
    balance: 'Баланс',
    today: 'Сегодня',
    yesterday: 'Вчера',
    thisWeek: 'Эта неделя',
    thisMonth: 'Этот месяц',
    from: 'От',
    to: 'До',
    export: 'Экспорт',
    print: 'Печать',
    refresh: 'Обновить',
    back: 'Назад',
    next: 'Далее',
    previous: 'Назад',

    // Auth
    login: 'Войти',
    logout: 'Выйти',
    username: 'Имя пользователя',
    password: 'Пароль',
    rememberMe: 'Запомнить',
    forgotPassword: 'Забыли пароль?',
    loginError: 'Неверный логин или пароль',
    loginSuccess: 'Успешный вход',
    logoutConfirm: 'Вы уверены, что хотите выйти?',

    // Navigation
    dashboard: 'Панель управления',
    pos: 'Касса',
    products: 'Товары',
    customers: 'Клиенты',
    sales: 'Продажи',
    warehouse: 'Склад',
    reports: 'Отчеты',
    settings: 'Настройки',
    users: 'Пользователи',
    expenses: 'Расходы',
    suppliers: 'Поставщики',

    // Dashboard
    todaySales: 'Продажи за сегодня',
    monthSales: 'Продажи за месяц',
    totalDebt: 'Общий долг',
    lowStock: 'Мало на складе',
    recentSales: 'Последние продажи',
    topProducts: 'Топ товары',
    salesChart: 'График продаж',

    // POS
    cart: 'Корзина',
    cartEmpty: 'Корзина пуста',
    selectCustomer: 'Выбрать клиента',
    customerDebt: 'Долг клиента',
    payment: 'Оплата',
    paymentType: 'Способ оплаты',
    cash: 'Наличные',
    card: 'Карта',
    transfer: 'Перевод',
    onCredit: 'В долг',
    change: 'Сдача',
    clear: 'Очистить',
    checkout: 'Оформить',
    printReceipt: 'Печать чека',
    saleCompleted: 'Продажа завершена',
    addToCart: 'В корзину',
    removeFromCart: 'Удалить',
    selectWarehouse: 'Выбрать склад',
    availableStock: 'В наличии',
    outOfStock: 'Нет в наличии',
    categories: 'Категории',
    favorites: 'Избранное',
    allProducts: 'Все товары',
    searchProducts: 'Поиск товаров',
    unitPrice: 'Цена за ед.',
    totalPrice: 'Общая цена',
    costPrice: 'Себестоимость',
    profit: 'Прибыль',
    finalTotal: 'Итого',
    subtotal: 'Подытог',
    saveLater: 'На потом',
    savedCarts: 'Сохраненные',
    loadCart: 'Загрузить',
    driverPhone: 'Телефон клиента',

    // Products
    productName: 'Название товара',
    productCode: 'Код товара',
    article: 'Артикул',
    category: 'Категория',
    unit: 'Единица измерения',
    baseUnit: 'Базовая единица',
    conversionFactor: 'Коэффициент',
    sellingPrice: 'Цена продажи',
    purchasePrice: 'Цена закупки',
    minStock: 'Мин. остаток',
    currentStock: 'Текущий остаток',
    addProduct: 'Добавить товар',
    editProduct: 'Редактировать товар',
    deleteProduct: 'Удалить товар',
    productDeleted: 'Товар удален',
    productSaved: 'Товар сохранен',
    importProducts: 'Импорт',
    exportProducts: 'Экспорт',

    // Customers
    customerName: 'Имя клиента',
    customerType: 'Тип клиента',
    companyName: 'Название компании',
    telegramId: 'Telegram ID',
    currentDebt: 'Текущий долг',
    addCustomer: 'Добавить клиента',
    editCustomer: 'Редактировать клиента',
    deleteCustomer: 'Удалить клиента',
    customerDeleted: 'Клиент удален',
    customerSaved: 'Клиент сохранен',
    retail: 'Розничный',
    wholesale: 'Оптовый',
    vip: 'VIP',
    customerHistory: 'История клиента',
    salesHistory: 'История продаж',
    paymentHistory: 'История оплат',
    debtHistory: 'История долгов',
    makePayment: 'Принять оплату',
    paymentReceived: 'Оплата принята',
    downloadReport: 'Скачать отчет',

    // Sales
    saleNumber: 'Номер продажи',
    saleDate: 'Дата продажи',
    seller: 'Продавец',
    customer: 'Клиент',
    paymentStatus: 'Статус оплаты',
    paidStatus: 'Оплачено',
    debtStatus: 'В долг',
    partialStatus: 'Частично',
    itemsCount: 'Кол-во товаров',
    viewDetails: 'Подробнее',
    editSale: 'Редактировать',
    deleteSale: 'Удалить',
    cancelSale: 'Отменить',
    saleDeleted: 'Продажа удалена',
    returnSale: 'Возврат',

    // Warehouse
    warehouseName: 'Название склада',
    stockIn: 'Приход',
    stockOut: 'Расход',
    stockTransfer: 'Перемещение',
    stockAdjustment: 'Корректировка',
    inventory: 'Инвентаризация',
    movements: 'Движения',
    movementType: 'Тип движения',
    sourceWarehouse: 'Откуда',
    destinationWarehouse: 'Куда',
    reason: 'Причина',
    reference: 'Ссылка',
    addMovement: 'Добавить движение',
    movementSaved: 'Движение сохранено',
    lowStockAlert: 'Мало на складе',

    // Reports
    salesReport: 'Отчет по продажам',
    stockReport: 'Отчет по складу',
    debtReport: 'Отчет по долгам',
    profitReport: 'Отчет по прибыли',
    sellerReport: 'Отчет по продавцам',
    periodReport: 'Отчет за период',
    dailyReport: 'Дневной отчет',
    weeklyReport: 'Недельный отчет',
    monthlyReport: 'Месячный отчет',
    customPeriod: 'Другой период',
    generateReport: 'Сформировать',
    downloadExcel: 'Скачать Excel',
    downloadPdf: 'Скачать PDF',

    // Settings
    companySettings: 'Настройки компании',
    companyName2: 'Название компании',
    companyPhone: 'Телефон компании',
    companyAddress: 'Адрес компании',
    exchangeRate: 'Курс валюты',
    usdRate: 'Курс доллара',
    language: 'Язык',
    selectLanguage: 'Выберите язык',
    languageChanged: 'Язык изменен',
    generalSettings: 'Общие настройки',
    receiptSettings: 'Настройки чека',
    notificationSettings: 'Уведомления',
    telegramBot: 'Telegram Бот',
    telegramNotifications: 'Telegram уведомления',
    telegramDirectorIds: 'Telegram ID директоров',
    telegramHowToFind: 'Как найти Telegram ID?',
    telegramGroupReport: 'Отчет в группу Telegram',
    groupChatId: 'ID группы',
    reportTime: 'Время отчета',
    reportTimeHint: 'Отчет отправляется каждый день в это время',
    autoSend: 'Автоотправка',
    dailyAt: 'Каждый день в указанное время',
    enterGroupChatId: 'Введите ID группы',
    test: 'Тест',
    sendNow: 'Отправить сейчас',
    version: 'Версия',
    database: 'База данных',
    salesSettings: 'Настройки продаж',
    maxDiscount: 'Макс. скидка',
    maxDiscountHint: 'Максимальная скидка продавца',
    allowDebtSales: 'Разрешить продажу в долг',
    autoPrintReceipt: 'Авто-печать чека',

    // Users
    userManagement: 'Управление пользователями',
    addUser: 'Добавить пользователя',
    editUser: 'Редактировать',
    deleteUser: 'Удалить',
    firstName: 'Имя',
    lastName: 'Фамилия',
    email: 'Email',
    role: 'Роль',
    assignedWarehouse: 'Прикрепленный склад',
    active: 'Активен',
    blocked: 'Заблокирован',
    blockUser: 'Заблокировать',
    unblockUser: 'Разблокировать',
    resetPassword: 'Сбросить пароль',
    changePassword: 'Изменить пароль',
    currentPassword: 'Текущий пароль',
    newPassword: 'Новый пароль',
    confirmPassword: 'Подтвердите пароль',
    passwordChanged: 'Пароль изменен',

    // Roles
    director: 'Директор',
    seller2: 'Продавец',
    warehouseManager: 'Кладовщик',
    accountant: 'Бухгалтер',

    // Validation messages
    required: 'Обязательное поле',
    invalidEmail: 'Неверный формат email',
    minLength: 'Минимальная длина: {min}',
    maxLength: 'Максимальная длина: {max}',
    invalidPhone: 'Неверный номер телефона',
    passwordMismatch: 'Пароли не совпадают',

    // Success messages
    savedSuccess: 'Успешно сохранено',
    deletedSuccess: 'Успешно удалено',
    updatedSuccess: 'Успешно обновлено',

    // Error messages
    errorOccurred: 'Произошла ошибка',
    notFound: 'Не найдено',
    accessDenied: 'Доступ запрещен',
    serverError: 'Ошибка сервера',
    networkError: 'Ошибка сети',

    // Additional translations
    product: 'Товар',
    units: 'Единицы измерения',
    saving: 'Сохранение...',
    adding: 'Добавление...',
    notSelected: 'Не выбрано',
    select: 'Выберите',
    productUpdated: 'Товар обновлен',
    uomAdded: 'Единица измерения добавлена',
    uomDeleted: 'Единица измерения удалена',
    categoryAdded: 'Категория добавлена',
    categoryUpdated: 'Категория обновлена',
    categoryDeleted: 'Категория удалена',
    categoryHasProducts: 'В категории есть товары, сначала удалите их',
    confirmDelete: 'Подтвердите удаление?',
    noProductsFound: 'Товары не найдены',
    noCustomersFound: 'Клиенты не найдены',
    noSalesFound: 'Продажи не найдены',
    noHistoryFound: 'История не найдена',
    totalItems: 'Всего',
    newProduct: 'Новый товар',
    enterProductDetails: 'Введите данные товара',
    barcode: 'Штрих-код',
    vipPrice: 'VIP цена',
    minStockHint: 'Предупреждение при низком остатке',
    favoriteProduct: 'Избранный товар',
    favoriteHint: 'Для быстрого поиска в кассе',
    productColor: 'Цвет товара',
    costPriceHint: 'Себестоимость определяется при поступлении на склад',
    configureUnits: 'Настройка единиц измерения',
    sellInDifferentUnits: 'Продажа в разных единицах',
    existingUnits: 'Существующие единицы измерения',
    addNewUnit: 'Добавить единицу измерения',
    fromUnit: 'Из какой единицы',
    toUnit: 'В какую единицу',
    exampleText: 'Пример',
    salePriceOptional: 'Цена продажи (необязательно)',
    autoCalculated: 'Оставьте пустым = авторасчет',
    newCategory: 'Новая категория',
    enterCategoryName: 'Введите название категории',
    categoryName: 'Название категории',
    editCategory: 'Редактировать категорию',
    changeCategoryName: 'Измените название категории',
    itemsCount2: 'Количество товаров',
    receiptNumber: 'Номер чека',
    totalAmount: 'Общая сумма',
    reportDownloaded: 'Отчет успешно загружен',
    customerAdded: 'Клиент успешно добавлен',
    customerUpdated: 'Клиент успешно обновлен',
    saleEdited: 'Продажа успешно изменена',
    cancelled: 'Отменено',
    items: 'Товары',
    itemsList: 'Список товаров',
    forSelectedPeriod: 'За выбранный период',
    profitByProducts: 'Прибыль по товарам',
    showPasswords: 'Показать пароли',
    updatePasswordHint: 'Обновите пароль для безопасности',
    help: 'Помощь',
    helpText: 'Свяжитесь с нами для помощи или дополнительных услуг',
    allRightsReserved: 'Все права защищены',
    validationError: 'Ошибка валидации',
    measure: 'Единица',

    // Reports page
    totalRevenue: 'Общий доход',
    totalCostPrice: 'Общая себестоимость',
    profitPercent: 'Процент прибыли',
    salesCount: 'Количество продаж',
    totalSum: 'Общая сумма',
    discounts: 'Скидки',
    soldOnCredit: 'Продано в долг',
    selectSeller: 'Выберите кассира',
    sellersList: 'Список кассиров',
    totalSales: 'Всего продаж',
    customersCount: 'Количество клиентов',
    salesReportTitle: 'Отчет по продажам',
    stockReportTitle: 'Отчет по остаткам',
    debtorsReportTitle: 'Отчет по должникам',
    dailyReportTitle: 'Ежедневный отчет',
    priceListTitle: 'Прайс-лист',
    excelPreparing: 'Подготовка Excel...',
    excelDownloaded: 'Excel загружен!',
    excelError: 'Ошибка загрузки Excel',
    downloadExcel2: 'Скачать Excel',
    downloadPdf2: 'Скачать PDF',
    averageCheck: 'Средний чек',
    anonymousSales: 'Анонимные продажи',
    forToday: 'На сегодня',
    recentSalesTitle: 'Последние продажи',
    dailySales: 'Ежедневные продажи',
    reportPreparing: 'Подготовка отчета...',
    reportError: 'Ошибка загрузки отчета',
    dailyIndicators: 'Ежедневные показатели',
    timesSold: 'раз продано',
    pieces: 'шт',
    purchase: 'покупка',
    currentStatus: 'Текущее состояние',
    currentDebts: 'Текущие долги',

    // Customer dialog
    editCustomerTitle: 'Редактировать клиента',
    addCustomerTitle: 'Добавить клиента',
    enterCustomerDetails: 'Введите данные клиента',
    fullName: 'Полное имя',
    nameRequired: 'Имя обязательно',
    phoneLabel: 'Номер телефона',
    phonePlaceholder: 'Введите номер телефона',
    addressLabel: 'Адрес',
    addressPlaceholder: 'Введите адрес',
    regularCustomer: 'Обычный клиент',
    vipCustomer: 'VIP клиент',
    balanceLabel: 'Баланс',
    notesLabel: 'Примечание',
    notesPlaceholder: 'Дополнительная информация',

    // Dashboard
    welcomeMessage: 'Добро пожаловать',

    // POS
    orderSaved: 'Порядок сохранен',
    editSaleTitle: 'редактирование',
    deleteError: 'Ошибка удаления',
    editError: 'Ошибка редактирования',
    selectProduct: 'Выберите товар',
    additionalInfo: 'Дополнительная информация',

    // Settings
    reportNotSent: 'Отчет не отправлен',
    messageNotSent: 'Сообщение не отправлено',

    // Customer form additional
    phoneRequired: 'Телефон обязателен',
    secondaryPhone: 'Дополнительный телефон',
    telegramPlaceholder: '@username или 123456789',
    emailLabel: 'Email',
    companyPlaceholder: 'Название компании',
    fullAddress: 'Полный адрес',
    regular: 'Обычный',
    creditLimit: 'Кредитный лимит',
    assignedSeller: 'Назначенный кассир',
    notAssigned: 'Не назначен',

    // Edit reason
    editReason: 'Причина редактирования',
    editReasonPlaceholder: 'Введите причину (минимум 3 символа)',

    // Settings additional
    dailyReportSent: 'Ежедневный отчет отправлен!',
    testMessageSent: 'Тестовое сообщение отправлено!',

    // Warehouse
    movementEdited: 'Движение успешно отредактировано!',
    movementDeleted: 'Движение удалено!',

    // Warehouse page
    addAtLeastOneProduct: 'Добавьте хотя бы один товар',
    allCategories: 'Все категории',
    avgCostUsd: 'Средняя цена (USD)',
    avgCostUzs: 'Средняя цена (UZS)',
    totalValue: 'Общая стоимость',
    low: 'Мало',
    productsNotFound: 'Товары не найдены',
    incomeType: 'Приход',
    soldType: 'Продано',
    clearFilters: 'Очистить',
    totalCount: 'Всего',
    priceUsd: 'Цена (USD)',
    priceUzs: 'Цена (UZS)',
    documentNo: 'Документ №',
    supplier: 'Поставщик',
    supplierName: 'Имя поставщика',
    transferIn: 'Получено',
    transferOut: 'Отправлено',
    adjustmentPlus: 'Корректировка+',
    adjustmentMinus: 'Корректировка-',
    writeOff: 'Списание',
    movementHistoryNotFound: 'История движений не найдена',
    stockIncomeUsd: 'Приход на склад (USD)',
    stockIncome: 'Приход на склад',
    currentRateInfo: 'Текущий курс',
    invoiceNo: 'Счет-фактура №',
    productsLabel: 'Товары',
    measureUnit: 'Ед. изм.',
    totalUsd: 'Итого (USD)',
    totalUzs: 'Итого (сум)',
    inUzs: 'В сумах',
    inUsd: 'В долларах',
    currency: 'Валюта',
    incomeSuccess: 'Приход успешно оформлен!',
    saveIncome: 'Сохранить приход',
    editMovementTitle: 'Редактировать движение',
    quantityChangeWarning: 'При изменении количества остаток на складе обновится автоматически.',
    deleteMovementTitle: 'Удалить движение',
    confirmDeleteMovement: 'удалить приход?',
    attentionWarning: 'Внимание!',
    deleteMovementWarning: 'Это действие изменит остаток на складе. При удалении прихода количество товара уменьшится.',
    deleteReasonLabel: 'Причина удаления',
    enterReasonRequired: 'Введите причину (обязательно)',

    // Customer dialogs
    deleteCustomerTitle: 'Удалить клиента',
    confirmDeleteCustomer: 'удалить?',
    customerHasDebt: 'Внимание: У этого клиента есть долг!',
    deleting: 'Удаление...',
    acceptPayment: 'Принять оплату',
    paymentAmount: 'Сумма оплаты',
    enterAmount: 'Введите сумму',
    optionalNote: 'Необязательный комментарий',
    accept: 'Принять',
    customerDetails: 'Данные клиента',
    fullHistoryAndStats: 'Полная история и статистика',
    totalPurchases: 'Всего покупок',
    advanceBalance: 'Аванс',
    downloadFullReport: 'Скачать полный отчет',
    allSalesProductsDebtInExcel: 'Все продажи, товары и история долга в одном Excel файле',
    receiptNo: 'Чек №',
    paidAmount: 'Оплачено',
    debtAmount: 'Долг',
    debtPaymentHistory: 'История долга и оплат',
    debtBefore: 'Долг до',
    debtAfter: 'Долг после',
    paymentTransaction: 'Оплата',
    purchaseTransaction: 'Покупка',
    onDebt: 'В долг',
    partial: 'Частично',
    productsList: 'Список товаров',

    // Sales page
    lastSale: 'Последняя',
    edited: 'Изменено',
    unknownCustomer: 'Неизвестный',
    deleteSaleTitle: 'Удалить продажу',
    confirmDeleteSale: 'удалить?',
    saleDeleteWarning: 'Продажа будет отменена, товары вернутся на склад. Долги клиента также обновятся.',
    grandTotal: 'Всего',
    editedBy: 'Кто',
    editedWhen: 'Когда',
    cancelledStatus: 'Отменено',
    cancelledBy: 'Кто',
    cancelledWhen: 'Когда',
    pending: 'Ожидание',
    saleLoadError: 'Ошибка загрузки данных продажи',
    saleDeletedSuccess: 'Продажа удалена!',

    // POS page extended
    dragToReorder: 'Перетащите для изменения порядка',
    sellingPriceSum: 'Цена продажи (сум)',
    quantityUnit: 'Количество',
    priceBelowCost: 'Цена ниже себестоимости',
    editPrice: 'Изменить цену',
    editQuantity: 'Изменить количество',
    inDollars: 'В долларах',
    saveForLater: 'Сохранить на потом',
    cartSavedForLater: 'Покупка сохранена на потом!',
    receiptPreview: 'Просмотр чека',
    confirmSale: 'Подтвердить',

    // POS toasts
    saved: 'Сохранено',
    added: 'Добавлено',
    deleted: 'Удалено',
    priceChanged: 'Цена изменена',
    quantityChanged: 'Количество изменено',
    invalidDiscount: 'Неверная сумма скидки',
    invalidAmount: 'Неверная сумма',
    selectCustomerForDebt: 'Выберите клиента для продажи в долг!',
    enterEditReason: 'Введите причину редактирования!',
    reasonMinLength: 'Причина должна содержать минимум 3 символа!',
    cartLoaded: 'Покупка загружена!',

    // POS receipt and print
    baseUnitLabel: 'Основная',
    customerLabel: 'Клиент',
    companyLabel: 'Компания',
    company: 'Компания',
    driverLabel: 'Тел',
    productLabel: 'Товар',
    quantityLabel: 'Кол-во',
    amountLabel: 'Сумма',
    totalWithCount: 'Итого',
    grandTotalLabel: 'ИТОГО',
    thanksMessage: '★ СПАСИБО! ★',
    printButton: 'Печать',
    popupBlocked: 'Popup заблокирован. Разрешите.',
  },

  uz_cyrl: {
    // Common
    save: 'Сақлаш',
    cancel: 'Бекор қилиш',
    delete: 'Ўчириш',
    edit: 'Таҳрирлаш',
    add: 'Қўшиш',
    search: 'Қидириш',
    filter: 'Филтр',
    loading: 'Юкланмоқда...',
    noData: 'Маълумот йўқ',
    confirm: 'Тасдиқлаш',
    close: 'Ёпиш',
    yes: 'Ҳа',
    no: 'Йўқ',
    all: 'Барчаси',
    total: 'Жами',
    actions: 'Амаллар',
    status: 'Ҳолат',
    date: 'Сана',
    time: 'Вақт',
    name: 'Номи',
    phone: 'Телефон',
    address: 'Манзил',
    description: 'Тавсиф',
    amount: 'Миқдор',
    price: 'Нарх',
    quantity: 'Сони',
    sum: 'Сўм',
    discount: 'Чегирма',
    debt: 'Қарз',
    paid: 'Тўланган',
    balance: 'Баланс',
    today: 'Бугун',
    yesterday: 'Кеча',
    thisWeek: 'Шу ҳафта',
    thisMonth: 'Шу ой',
    from: 'Дан',
    to: 'Гача',
    export: 'Экспорт',
    print: 'Чоп этиш',
    refresh: 'Янгилаш',
    back: 'Орқага',
    next: 'Кейинги',
    previous: 'Олдинги',

    // Auth
    login: 'Кириш',
    logout: 'Чиқиш',
    username: 'Фойдаланувчи номи',
    password: 'Парол',
    rememberMe: 'Эслаб қолиш',
    forgotPassword: 'Паролни унутдингизми?',
    loginError: 'Логин ёки парол нотўғри',
    loginSuccess: 'Муваффақиятли кирдингиз',
    logoutConfirm: 'Тизимдан чиқмоқчимисиз?',

    // Navigation
    dashboard: 'Бошқарув панели',
    pos: 'Касса',
    products: 'Маҳсулотлар',
    customers: 'Мижозлар',
    sales: 'Сотувлар',
    warehouse: 'Омбор',
    reports: 'Ҳисоботлар',
    settings: 'Созламалар',
    users: 'Фойдаланувчилар',
    expenses: 'Чиқимлар',

    // Dashboard
    todaySales: 'Бугунги савдо',
    monthSales: 'Ойлик савдо',
    totalDebt: 'Умумий қарз',
    lowStock: 'Кам қолган товарлар',
    recentSales: 'Сўнгги сотувлар',
    topProducts: 'Топ маҳсулотлар',
    salesChart: 'Сотув графиги',

    // POS
    cart: 'Сават',
    cartEmpty: 'Сават бўш',
    selectCustomer: 'Мижоз танлаш',
    customerDebt: 'Мижоз қарзи',
    payment: 'Тўлов',
    paymentType: 'Тўлов тури',
    cash: 'Нақд',
    card: 'Карта',
    transfer: 'Ўтказма',
    onCredit: 'Қарзга',
    change: 'Қайтим',
    clear: 'Тозалаш',
    checkout: 'Расмийлаштириш',
    printReceipt: 'Чек чиқариш',
    saleCompleted: 'Сотув амалга оширилди',
    addToCart: 'Саватга қўшиш',
    removeFromCart: 'Саватдан ўчириш',
    selectWarehouse: 'Омбор танлаш',
    availableStock: 'Мавжуд миқдор',
    outOfStock: 'Тугаган',
    categories: 'Категориялар',
    favorites: 'Севимлилар',
    allProducts: 'Барча маҳсулотлар',
    searchProducts: 'Маҳсулот қидириш',
    unitPrice: 'Бирлик нархи',
    totalPrice: 'Умумий нарх',
    costPrice: 'Келиш нархи',
    profit: 'Фойда',
    finalTotal: 'Якуний сумма',
    subtotal: 'Жами',
    saveLater: 'Кейинроқ',
    savedCarts: 'Сақланган харидлар',
    loadCart: 'Юклаш',
    driverPhone: 'Мижоз телефони',

    // Products
    productName: 'Маҳсулот номи',
    productCode: 'Маҳсулот коди',
    article: 'Артикул',
    category: 'Категория',
    unit: 'Ўлчов бирлиги',
    baseUnit: 'Асосий бирлик',
    conversionFactor: 'Ўтказиш коэффиценти',
    sellingPrice: 'Сотув нархи',
    purchasePrice: 'Харид нархи',
    minStock: 'Минимал миқдор',
    currentStock: 'Жорий миқдор',
    addProduct: 'Маҳсулот қўшиш',
    editProduct: 'Маҳсулотни таҳрирлаш',
    deleteProduct: 'Маҳсулотни ўчириш',
    productDeleted: 'Маҳсулот ўчирилди',
    productSaved: 'Маҳсулот сақланди',
    importProducts: 'Импорт қилиш',
    exportProducts: 'Экспорт қилиш',

    // Customers
    customerName: 'Мижоз исми',
    customerType: 'Мижоз тури',
    companyName: 'Компания номи',
    telegramId: 'Telegram ID',
    currentDebt: 'Жорий қарз',
    addCustomer: 'Мижоз қўшиш',
    editCustomer: 'Мижозни таҳрирлаш',
    deleteCustomer: 'Мижозни ўчириш',
    customerDeleted: 'Мижоз ўчирилди',
    customerSaved: 'Мижоз сақланди',
    retail: 'Чакана',
    wholesale: 'Улгуржи',
    vip: 'VIP',
    customerHistory: 'Мижоз тарихи',
    salesHistory: 'Сотувлар тарихи',
    paymentHistory: 'Тўловлар тарихи',
    debtHistory: 'Қарзлар тарихи',
    makePayment: 'Тўлов қилиш',
    paymentReceived: 'Тўлов қабул қилинди',
    downloadReport: 'Ҳисоботни юклаш',

    // Sales
    saleNumber: 'Сотув рақами',
    saleDate: 'Сотув санаси',
    seller: 'Сотувчи',
    customer: 'Мижоз',
    paymentStatus: 'Тўлов ҳолати',
    paidStatus: 'Тўланган',
    debtStatus: 'Қарзга',
    partialStatus: 'Қисман',
    itemsCount: 'Товарлар сони',
    viewDetails: 'Батафсил',
    editSale: 'Сотувни таҳрирлаш',
    deleteSale: 'Сотувни ўчириш',
    cancelSale: 'Сотувни бекор қилиш',
    saleDeleted: 'Сотув ўчирилди',
    returnSale: 'Қайтариш',

    // Warehouse
    warehouseName: 'Омбор номи',
    stockIn: 'Кирим',
    stockOut: 'Чиқим',
    stockTransfer: 'Ўтказма',
    stockAdjustment: 'Тузатиш',
    inventory: 'Инвентаризация',
    movements: 'Ҳаракатлар',
    movementType: 'Ҳаракат тури',
    sourceWarehouse: 'Қаердан',
    destinationWarehouse: 'Қаерга',
    reason: 'Сабаб',
    reference: 'Ҳавола',
    addMovement: 'Ҳаракат қўшиш',
    movementSaved: 'Ҳаракат сақланди',
    lowStockAlert: 'Кам қолган товарлар',

    // Reports
    salesReport: 'Сотувлар ҳисоботи',
    stockReport: 'Омбор ҳисоботи',
    debtReport: 'Қарзлар ҳисоботи',
    profitReport: 'Фойда ҳисоботи',
    sellerReport: 'Сотувчилар ҳисоботи',
    periodReport: 'Давр ҳисоботи',
    dailyReport: 'Кунлик ҳисобот',
    weeklyReport: 'Ҳафталик ҳисобот',
    monthlyReport: 'Ойлик ҳисобот',
    customPeriod: 'Бошқа давр',
    generateReport: 'Ҳисобот яратиш',
    downloadExcel: 'Excel юклаш',
    downloadPdf: 'PDF юклаш',

    // Settings
    companySettings: 'Компания созламалари',
    companyName2: 'Компания номи',
    companyPhone: 'Компания телефони',
    companyAddress: 'Компания манзили',
    exchangeRate: 'Валюта курси',
    usdRate: 'Доллар курси',
    language: 'Тил',
    selectLanguage: 'Тилни танланг',
    languageChanged: 'Тил ўзгартирилди',
    generalSettings: 'Умумий созламалар',
    receiptSettings: 'Чек созламалари',
    notificationSettings: 'Билдиришнома созламалари',
    telegramBot: 'Телеграм Бот',
    telegramNotifications: 'Телеграм хабарномалар',
    telegramDirectorIds: 'Директор Телеграм ID лари',
    telegramHowToFind: 'Телеграм ID қандай топилади?',
    telegramGroupReport: 'Телеграм гуруҳга ҳисобот',
    groupChatId: 'Гуруҳ Chat ID',
    reportTime: 'Ҳисобот вақти',
    reportTimeHint: 'Ҳар куни шу вақтда ҳисобот юборилади',
    autoSend: 'Автоматик юбориш',
    dailyAt: 'Ҳар куни белгиланган вақтда',
    enterGroupChatId: 'Гуруҳ Chat ID киритинг',
    test: 'Тест',
    sendNow: 'Ҳозир юбориш',
    version: 'Версия',
    database: 'Маълумотлар базаси',
    salesSettings: 'Сотув созламалари',
    maxDiscount: 'Максимал чегирма',
    maxDiscountHint: 'Сотувчи бера оладиган максимал чегирма',
    allowDebtSales: 'Қарзга сотиш имконияти',
    autoPrintReceipt: 'Автоматик чек чоп этиш',

    // Users
    userManagement: 'Фойдаланувчиларни бошқариш',
    addUser: 'Фойдаланувчи қўшиш',
    editUser: 'Фойдаланувчини таҳрирлаш',
    deleteUser: 'Фойдаланувчини ўчириш',
    firstName: 'Исм',
    lastName: 'Фамилия',
    email: 'Email',
    role: 'Рол',
    assignedWarehouse: 'Бириктирилган омбор',
    active: 'Фаол',
    blocked: 'Блокланган',
    blockUser: 'Блоклаш',
    unblockUser: 'Блокдан чиқариш',
    resetPassword: 'Паролни тиклаш',
    changePassword: 'Паролни ўзгартириш',
    currentPassword: 'Жорий парол',
    newPassword: 'Янги парол',
    confirmPassword: 'Паролни тасдиқлаш',
    passwordChanged: 'Парол ўзгартирилди',

    // Roles
    director: 'Директор',
    seller2: 'Сотувчи',
    warehouseManager: 'Омборчи',
    accountant: 'Ҳисобчи',

    // Validation messages
    required: 'Бу майдон талаб қилинади',
    invalidEmail: 'Email нотўғри форматда',
    minLength: 'Минимал узунлик: {min}',
    maxLength: 'Максимал узунлик: {max}',
    invalidPhone: 'Телефон рақами нотўғри',
    passwordMismatch: 'Пароллар мос келмайди',

    // Success messages
    savedSuccess: 'Муваффақиятли сақланди',
    deletedSuccess: 'Муваффақиятли ўчирилди',
    updatedSuccess: 'Муваффақиятли янгиланди',

    // Error messages
    errorOccurred: 'Хатолик юз берди',
    notFound: 'Топилмади',
    accessDenied: 'Рухсат берилмаган',
    serverError: 'Сервер хатоси',
    networkError: 'Тармоқ хатоси',

    // Additional translations
    product: 'Товар',
    units: 'Ўлчов бирликлари',
    saving: 'Сақланмоқда...',
    adding: 'Қўшилмоқда...',
    notSelected: 'Танланмаган',
    select: 'Танланг',
    productUpdated: 'Товар янгиланди',
    uomAdded: 'Ўлчов бирлиги қўшилди',
    uomDeleted: 'Ўлчов бирлиги ўчирилди',
    categoryAdded: 'Категория қўшилди',
    categoryUpdated: 'Категория янгиланди',
    categoryDeleted: 'Категория ўчирилди',
    categoryHasProducts: 'Категорияда товарлар бор, аввал уларни ўчиринг',
    confirmDelete: 'Ўчиришни тасдиқлайсизми?',
    noProductsFound: 'Товар топилмади',
    noCustomersFound: 'Мижозлар топилмади',
    noSalesFound: 'Сотувлар топилмади',
    noHistoryFound: 'Тарих топилмади',
    totalItems: 'Жами',
    newProduct: 'Янги товар',
    enterProductDetails: 'Товар маълумотларини киритинг',
    barcode: 'Штрих-код',
    vipPrice: 'VIP нарх',
    minStockHint: 'Қолдиқ шу миқдордан кам бўлганда огоҳлантириш',
    favoriteProduct: 'Севимли товар',
    favoriteHint: 'Кассада тез топиш учун',
    productColor: 'Товар ранги',
    costPriceHint: 'Келиш нархи омборга кирим қилганда автоматик аниқланади',
    configureUnits: 'Ўлчов бирликларини созлаш',
    sellInDifferentUnits: 'Турли ўлчовларда сотиш',
    existingUnits: 'Мавжуд ўлчов бирликлари',
    addNewUnit: 'Янги ўлчов қўшиш',
    fromUnit: 'Қайси ўлчовдан',
    toUnit: 'Қайси ўлчовга',
    exampleText: 'Мисол',
    salePriceOptional: 'Сотиш нархи (ихтиёрий)',
    autoCalculated: 'Бўш қолдиринг = автоматик ҳисобланади',
    newCategory: 'Янги категория',
    enterCategoryName: 'Категория номини киритинг',
    categoryName: 'Категория номи',
    editCategory: 'Категорияни таҳрирлаш',
    changeCategoryName: 'Категория номини ўзгартиринг',
    itemsCount2: 'Товарлар сони',
    receiptNumber: 'Чек рақами',
    totalAmount: 'Умумий сумма',
    reportDownloaded: 'Ҳисобот муваффақиятли юкланди',
    customerAdded: 'Мижоз муваффақиятли қўшилди',
    customerUpdated: 'Мижоз муваффақиятли янгиланди',
    saleEdited: 'Сотув муваффақиятли таҳрирланди',
    cancelled: 'Бекор қилинган',
    items: 'Товарлар',
    itemsList: 'Товарлар рўйхати',
    forSelectedPeriod: 'Танланган давр учун',
    profitByProducts: 'Товарлар бўйича фойда',
    showPasswords: 'Паролларни кўрсатиш',
    updatePasswordHint: 'Хавфсизлик учун паролингизни янгиланг',
    help: 'Ёрдам',
    helpText: 'Дастур бўйича ёрдам ёки қўшимча хизматлар учун биз билан боғланинг',
    allRightsReserved: 'Барча ҳуқуқлар ҳимояланган',
    validationError: 'Валидация хатоси',
    measure: 'Ўлчов',

    // Reports page
    totalRevenue: 'Жами даромад',
    totalCostPrice: 'Жами тан нарх',
    profitPercent: 'Фойда фоизи',
    salesCount: 'Сотувлар сони',
    totalSum: 'Жами сумма',
    discounts: 'Чегирмалар',
    soldOnCredit: 'Қарзга сотилган',
    selectSeller: 'Кассирни танланг',
    sellersList: 'Кассирлар рўйхати',
    totalSales: 'Жами сотувлар',
    customersCount: 'Мижозлар сони',
    salesReportTitle: 'Сотувлар ҳисоботи',
    stockReportTitle: 'Қолдиқлар ҳисоботи',
    debtorsReportTitle: 'Қарздорлар ҳисоботи',
    dailyReportTitle: 'Кунлик ҳисобот',
    priceListTitle: 'Нархлар рўйхати',
    excelPreparing: 'Excel тайёрланмоқда...',
    excelDownloaded: 'Excel юкланди!',
    excelError: 'Excel юкланмади',
    downloadExcel2: 'Excel юклаш',
    downloadPdf2: 'PDF юклаш',
    averageCheck: 'Ўртача чек',
    anonymousSales: 'Аноним сотувлар',
    forToday: 'Бугун учун',
    recentSalesTitle: 'Сўнгги сотувлар',
    dailySales: 'Кунлик савдолар',
    reportPreparing: 'Ҳисобот тайёрланмоқда...',
    reportError: 'Ҳисобот юкланмади',
    dailyIndicators: 'Кунлик кўрсаткичлар',
    timesSold: 'марта сотилди',
    pieces: 'дона',
    purchase: 'харид',
    currentStatus: 'Жорий ҳолат',
    currentDebts: 'Жорий қарзлар',

    // Customer dialog
    editCustomerTitle: 'Мижозни таҳрирлаш',
    addCustomerTitle: 'Янги мижоз қўшиш',
    enterCustomerDetails: 'Мижоз маълумотларини киритинг',
    fullName: 'Тўлиқ исм',
    nameRequired: 'Исм киритилиши шарт',
    phoneLabel: 'Телефон рақами',
    phonePlaceholder: 'Телефон рақамини киритинг',
    addressLabel: 'Манзил',
    addressPlaceholder: 'Манзилни киритинг',
    regularCustomer: 'Оддий мижоз',
    vipCustomer: 'VIP мижоз',
    balanceLabel: 'Баланс',
    notesLabel: 'Изоҳ',
    notesPlaceholder: 'Қўшимча маълумот',

    // Dashboard
    welcomeMessage: 'Хуш келибсиз',

    // POS
    orderSaved: 'Тартиб сақланди',
    editSaleTitle: 'таҳрирлаш',
    deleteError: 'Ўчиришда хатолик',
    editError: 'Таҳрирлашда хатолик',
    selectProduct: 'Товар танланг',
    additionalInfo: 'Қўшимча маълумот',

    // Settings
    reportNotSent: 'Ҳисобот юборилмади',
    messageNotSent: 'Хабар юборилмади',

    // Customer form additional
    phoneRequired: 'Телефон киритилиши шарт',
    secondaryPhone: 'Қўшимча телефон',
    telegramPlaceholder: '@username ёки 123456789',
    emailLabel: 'Email',
    companyPlaceholder: 'Компания номи',
    fullAddress: 'Тўлиқ манзил',
    regular: 'Оддий',
    creditLimit: 'Кредит лимити',
    assignedSeller: 'Бириктирилган кассир',
    notAssigned: 'Танланмаган',

    // Edit reason
    editReason: 'Таҳрирлаш сабаби',
    editReasonPlaceholder: 'Сабаб киритинг (камида 3 та белги)',

    // Settings additional
    dailyReportSent: 'Кунлик ҳисобот юборилди!',
    testMessageSent: 'Тест хабар юборилди!',

    // Warehouse
    movementEdited: 'Ҳаракат муваффақиятли таҳрирланди!',
    movementDeleted: 'Ҳаракат ўчирилди!',

    // Warehouse page
    addAtLeastOneProduct: 'Камида битта товар қўшинг',
    allCategories: 'Барча категориялар',
    avgCostUsd: 'Ўртача келиш (USD)',
    avgCostUzs: 'Ўртача келиш (UZS)',
    totalValue: 'Жами қиймат',
    low: 'Кам',
    productsNotFound: 'Товарлар топилмади',
    incomeType: 'Кирим',
    soldType: 'Сотилди',
    clearFilters: 'Тозалаш',
    totalCount: 'Жами',
    priceUsd: 'Нарх (USD)',
    priceUzs: 'Нарх (UZS)',
    documentNo: 'Ҳужжат №',
    supplier: 'Етказувчи',
    supplierName: 'Етказувчи номи',
    transferIn: 'Келди',
    transferOut: 'Жўнатилди',
    adjustmentPlus: 'Тузатиш+',
    adjustmentMinus: 'Тузатиш-',
    writeOff: 'Зарар',
    movementHistoryNotFound: 'Ҳаракатлар тарихи топилмади',
    stockIncomeUsd: 'Омборга кирим (USD)',
    stockIncome: 'Омборга кирим',
    currentRateInfo: 'Жорий курс',
    invoiceNo: 'Фактура №',
    productsLabel: 'Товарлар',
    measureUnit: 'Ўлчов',
    totalUsd: 'Жами (USD)',
    totalUzs: 'Жами (сўм)',
    inUzs: 'Сўмда',
    inUsd: 'Долларда',
    currency: 'Валюта',
    incomeSuccess: 'Кирим муваффақиятли амалга оширилди!',
    saveIncome: 'Киримни сақлаш',
    editMovementTitle: 'Ҳаракатни таҳрирлаш',
    quantityChangeWarning: 'Миқдорни ўзгартирсангиз, омбор қолдиғи автоматик янгиланади.',
    deleteMovementTitle: 'Ҳаракатни ўчириш',
    confirmDeleteMovement: 'киримини ўчирмоқчимисиз?',
    attentionWarning: 'Диққат!',
    deleteMovementWarning: 'Бу ҳаракат омбор қолдиғини тескари ўзгартиради. Кирим ўчирилса, товар қолдиғи камаяди.',
    deleteReasonLabel: 'Ўчириш сабаби',
    enterReasonRequired: 'Сабаб киритинг (мажбурий)',

    // Customer dialogs
    deleteCustomerTitle: 'Мижозни ўчириш',
    confirmDeleteCustomer: 'ни ўчирмоқчимисиз?',
    customerHasDebt: 'Диққат: Бу мижозда қарз мавжуд!',
    deleting: 'Ўчирилмоқда...',
    acceptPayment: 'Тўлов қабул қилиш',
    paymentAmount: 'Тўлов суммаси',
    enterAmount: 'Сумма киритинг',
    optionalNote: 'Ихтиёрий изоҳ',
    accept: 'Қабул қилиш',
    customerDetails: 'Мижоз маълумотлари',
    fullHistoryAndStats: 'Тўлиқ тарих ва статистика',
    totalPurchases: 'Жами харид',
    advanceBalance: 'Аванс',
    downloadFullReport: 'Тўлиқ ҳисобот юклаш',
    allSalesProductsDebtInExcel: 'Барча сотувлар, товарлар ва қарз тарихи битта Excel файлда',
    receiptNo: 'Чек №',
    paidAmount: 'Тўланган',
    debtAmount: 'Қарз',
    debtPaymentHistory: 'Қарз ва тўловлар тарихи',
    debtBefore: 'Қарз олдин',
    debtAfter: 'Қарз кейин',
    paymentTransaction: 'Тўлов',
    purchaseTransaction: 'Харид',
    onDebt: 'Қарзга',
    partial: 'Қисман',
    productsList: 'Товарлар рўйхати',

    // Sales page
    lastSale: 'Охирги',
    edited: 'Таҳрирланган',
    unknownCustomer: 'Номаълум',
    deleteSaleTitle: 'Сотувни ўчириш',
    confirmDeleteSale: 'ни ўчирмоқчимисиз?',
    saleDeleteWarning: 'Сотув бекор қилинади ва товарлар омборга қайтарилади. Мижоз қарзлари ҳам янгиланади.',
    grandTotal: 'Умумий',
    editedBy: 'Ким',
    editedWhen: 'Қачон',
    cancelledStatus: 'Бекор қилинган',
    cancelledBy: 'Ким',
    cancelledWhen: 'Қачон',
    pending: 'Кутилмоқда',
    saleLoadError: 'Сотув маълумотларини юклашда хатолик',
    saleDeletedSuccess: 'Сотув ўчирилди!',

    // POS page extended
    dragToReorder: 'Тартибни ўзгартириш учун суриш',
    sellingPriceSum: 'Сотиш нархи (сўм)',
    quantityUnit: 'Миқдор',
    priceBelowCost: 'Нарх тан нархдан паст',
    editPrice: 'Нархни ўзгартириш',
    editQuantity: 'Миқдорни ўзгартириш',
    inDollars: 'Долларда',
    saveForLater: 'Кейинроққа сақлаш',
    cartSavedForLater: 'Харид кейинроққа сақланди!',
    receiptPreview: 'Чек кўриниши',
    confirmSale: 'Тасдиқлаш',

    // POS toasts
    saved: 'Сақланди',
    added: 'Қўшилди',
    deleted: 'Ўчирилди',
    priceChanged: 'Нарх ўзгартирилди',
    quantityChanged: 'Миқдор ўзгартирилди',
    invalidDiscount: 'Чегирма суммаси нотўғри',
    invalidAmount: 'Сумма нотўғри',
    selectCustomerForDebt: 'Қарзга сотув учун мижоз танланг!',
    enterEditReason: 'Таҳрирлаш сабабини киритинг!',
    reasonMinLength: 'Сабаб камида 3 та белгидан иборат бўлиши керак!',
    cartLoaded: 'Харид юкланди!',

    // POS receipt and print
    baseUnitLabel: 'Асосий',
    customerLabel: 'Мижоз',
    companyLabel: 'Компания',
    company: 'Компания',
    driverLabel: 'Тел',
    productLabel: 'Маҳсулот',
    quantityLabel: 'Сони',
    amountLabel: 'Сумма',
    totalWithCount: 'Жами',
    grandTotalLabel: 'ЯКУНИЙ СУММА',
    thanksMessage: '★ РАҲМАТ! ★',
    printButton: 'Чоп этиш',
    popupBlocked: 'Popup блокланган. Рухсат беринг.',
  },
}

// Helper function to get translation
export const t = (key: keyof TranslationKeys, lang: LanguageCode = 'uz'): string => {
  return translations[lang][key] || translations['uz'][key] || key
}

export default translations