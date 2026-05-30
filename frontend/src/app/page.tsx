'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useRouter } from 'next/navigation'
import { ArrowRight, FileText, Loader2, Upload } from 'lucide-react'
import { uploadCV } from '@/lib/api'
import { cn } from '@/lib/utils'

const STEPS = [
  { n: 1, label: 'Upload CV' },
  { n: 2, label: 'Get matches' },
  { n: 3, label: 'Close the gap' },
]

export default function HomePage() {
  const router = useRouter()
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) {
      setFile(accepted[0])
      setError(null)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    multiple: false,
    disabled: loading,
  })

  async function handleSubmit() {
    if (!file || loading) return
    setLoading(true)
    setError(null)
    try {
      const result = await uploadCV(file)
      sessionStorage.setItem('matchResponse', JSON.stringify(result))
      router.push('/matches')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.')
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col items-center gap-14 py-16">

      {/* ── Hero ── */}
      <div className="max-w-2xl space-y-4 text-center">
        <h1 className="text-4xl font-bold leading-tight tracking-tight sm:text-5xl">
          Find your next role in{' '}
          <span style={{ color: '#5DCAA5' }}>Switzerland</span>
        </h1>
        <p className="text-lg leading-relaxed text-white/60">
          Upload your CV and instantly see which Swiss jobs match your skills&nbsp;—
          and exactly what to learn to close the gap.
        </p>
      </div>

      {/* ── Upload card ── */}
      <div className="w-full max-w-lg space-y-3">

        {/* Drop zone */}
        <div
          {...getRootProps()}
          className={cn(
            'cursor-pointer rounded-2xl border-2 border-dashed p-10 text-center transition-colors',
            isDragActive
              ? 'border-teal-400 bg-teal-400/5'
              : file
              ? 'border-teal-500/50 bg-teal-500/5'
              : 'border-white/20 hover:border-white/40 hover:bg-white/5',
            loading && 'pointer-events-none opacity-50',
          )}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center gap-3">
            {file ? (
              <>
                <FileText className="h-10 w-10 text-teal-400" />
                <div>
                  <p className="font-medium text-white">{file.name}</p>
                  <p className="mt-0.5 text-sm text-white/40">Click or drag to replace</p>
                </div>
              </>
            ) : (
              <>
                <Upload className="h-10 w-10 text-white/30" />
                <div>
                  <p className="font-medium text-white">
                    {isDragActive ? 'Drop your CV here' : 'Drag & drop your CV here'}
                  </p>
                  <p className="mt-0.5 text-sm text-white/40">PDF or DOCX</p>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Error banner */}
        {error && (
          <div className="flex items-center justify-between rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3">
            <p className="text-sm text-red-300">{error}</p>
            <button
              onClick={() => { setError(null); setFile(null) }}
              className="ml-4 shrink-0 text-sm font-medium text-red-300 underline hover:text-red-200"
            >
              Try again
            </button>
          </div>
        )}

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={!file || loading}
          className={cn(
            'flex w-full items-center justify-center gap-2 rounded-xl py-3.5 text-base font-semibold transition-all',
            'bg-teal-500 text-white hover:bg-teal-400 active:scale-[0.98]',
            'disabled:cursor-not-allowed disabled:opacity-40',
          )}
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Analysing your CV…
            </>
          ) : (
            'Find matching jobs'
          )}
        </button>
      </div>

      {/* ── Steps ── */}
      <div className="flex items-center gap-3 text-sm text-white/50">
        {STEPS.flatMap((step, i) => [
          <div key={step.n} className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-white/10 text-xs font-semibold text-white/70">
              {step.n}
            </span>
            <span>{step.label}</span>
          </div>,
          i < STEPS.length - 1 ? (
            <ArrowRight key={`a${i}`} className="h-4 w-4 shrink-0 text-white/20" />
          ) : null,
        ])}
      </div>

    </div>
  )
}
