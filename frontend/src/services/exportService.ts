/**
 * Excel export utility.
 * window.open ishlamaydi — token yuborilmaydi.
 * Bu funksiya axios orqali token bilan so'rov yuboradi va Blob sifatida yuklab oladi.
 */
import api from './api'

export async function downloadExcel(url: string, filename: string): Promise<void> {
  try {
    const response = await api.get(url, {
      responseType: 'blob',
    })
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(link.href)
  } catch (error: any) {
    const msg = error?.response?.data?.detail || 'Excel yuklab olishda xatolik'
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg))
  }
}
