/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_WS_URL: string
  readonly VITE_CLOUDINARY_CLOUD_NAME: string
  readonly VITE_CLOUDINARY_UPLOAD_PRESET?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

interface CloudinaryUploadResult {
  event: string
  info?: {
    secure_url?: string
  }
}

interface CloudinaryWidget {
  open: () => void
  close: () => void
}

interface Window {
  cloudinary?: {
    createUploadWidget: (
      options: Record<string, unknown>,
      callback: (error: unknown, result: CloudinaryUploadResult) => void,
    ) => CloudinaryWidget
  }
}
