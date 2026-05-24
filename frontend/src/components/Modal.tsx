type ModalProps = {
  open: boolean
  title: string
  children: React.ReactNode
  onClose?: () => void
  primaryLabel?: string
  onPrimary?: () => void
}

export default function Modal({
  open,
  title,
  children,
  onClose,
  primaryLabel = 'OK',
  onPrimary,
}: ModalProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
        <div className="mt-4 text-sm text-slate-600">{children}</div>
        <div className="mt-6 flex justify-end gap-2">
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-slate-200 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
          )}
          <button
            type="button"
            onClick={onPrimary ?? onClose}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            {primaryLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
