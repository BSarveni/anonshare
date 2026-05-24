import { useEffect, useRef, useState } from 'react'
import { postsApi } from '../lib/api'

type UploadModalProps = {
  open: boolean
  onClose: () => void
  onUploaded: () => void
}

export default function UploadModal({ open, onClose, onUploaded }: UploadModalProps) {
  const [caption, setCaption] = useState('')
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const captionRef = useRef(caption)
  const widgetRef = useRef<ReturnType<NonNullable<Window['cloudinary']>['createUploadWidget']> | null>(
    null,
  )

  captionRef.current = caption

  useEffect(() => {
    if (!open || !window.cloudinary) return

    const cloudName = import.meta.env.VITE_CLOUDINARY_CLOUD_NAME
    const uploadPreset = import.meta.env.VITE_CLOUDINARY_UPLOAD_PRESET

    if (!cloudName || !uploadPreset) {
      setError('Cloudinary is not configured (cloud name / upload preset).')
      return
    }

    setError(null)
    widgetRef.current = window.cloudinary.createUploadWidget(
      {
        cloudName,
        uploadPreset,
        sources: ['local', 'url', 'camera'],
        multiple: false,
        maxFiles: 1,
      },
      async (err, result) => {
        if (err) {
          setError('Upload failed')
          return
        }
        if (result.event === 'success' && result.info?.secure_url) {
          setUploading(true)
          setError(null)
          try {
            await postsApi.upload(result.info.secure_url, captionRef.current || undefined)
            setCaption('')
            onUploaded()
            onClose()
          } catch {
            setError('Could not save post to server')
          } finally {
            setUploading(false)
          }
        }
      },
    )

    return () => {
      widgetRef.current?.close()
      widgetRef.current = null
    }
  }, [open, onClose, onUploaded])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-slate-900">New post</h2>
        <textarea
          className="mt-4 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-slate-400"
          placeholder="Caption (optional)"
          rows={3}
          value={caption}
          onChange={(e) => setCaption(e.target.value)}
        />
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        <div className="mt-6 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-slate-200 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={uploading || !!error?.includes('not configured')}
            onClick={() => widgetRef.current?.open()}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
          >
            {uploading ? 'Saving…' : 'Choose image'}
          </button>
        </div>
      </div>
    </div>
  )
}
