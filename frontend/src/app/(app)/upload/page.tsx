'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { FileText, Loader2, ScanLine, UploadCloud } from 'lucide-react'
import { uploadCV } from '@/lib/api'
import { Reveal } from '@/components/ui/motion'
import { cn } from '@/lib/utils'

export default function UploadPage() {
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

  async function analyze() {
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
    <div className="mx-auto max-w-2xl">
      <Reveal className="text-center">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-primary/70">Step 1 · Analysis</p>
        <h1 className="mt-3 font-display text-4xl font-bold tracking-tight">
          Upload your CV
        </h1>
        <p className="mx-auto mt-3 max-w-md text-white/55">
          Drop your CV and the engine extracts your skills, transferable strengths, and the roles
          within reach.
        </p>
      </Reveal>

      <Reveal delay={0.1} className="mt-10">
        <div
          {...getRootProps()}
          className={cn(
            'group relative cursor-pointer overflow-hidden rounded-3xl border-2 border-dashed p-12 text-center transition-all',
            isDragActive
              ? 'border-primary bg-primary/[0.06]'
              : file
                ? 'border-primary/50 bg-primary/[0.04]'
                : 'border-white/15 hover:border-white/30 hover:bg-white/[0.03]',
            loading && 'pointer-events-none opacity-60',
          )}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center gap-4">
            {loading ? (
              <>
                <motion.span
                  animate={{ opacity: [0.4, 1, 0.4] }}
                  transition={{ repeat: Infinity, duration: 1.6 }}
                  className="grid h-16 w-16 place-items-center rounded-2xl bg-primary/15 ring-1 ring-primary/30"
                >
                  <ScanLine className="h-7 w-7 text-primary" />
                </motion.span>
                <div>
                  <p className="font-medium text-white">Analyzing your CV…</p>
                  <p className="mt-1 text-sm text-white/40">Extracting skills & matching roles</p>
                </div>
              </>
            ) : file ? (
              <>
                <span className="grid h-16 w-16 place-items-center rounded-2xl bg-primary/15 ring-1 ring-primary/30">
                  <FileText className="h-7 w-7 text-primary" />
                </span>
                <div>
                  <p className="font-medium text-white">{file.name}</p>
                  <p className="mt-1 text-sm text-white/40">Click or drag to replace</p>
                </div>
              </>
            ) : (
              <>
                <span className="grid h-16 w-16 place-items-center rounded-2xl bg-white/5 ring-1 ring-white/10 transition-transform group-hover:-translate-y-0.5">
                  <UploadCloud className="h-7 w-7 text-white/40" />
                </span>
                <div>
                  <p className="font-medium text-white">
                    {isDragActive ? 'Drop it here' : 'Drag & drop your CV'}
                  </p>
                  <p className="mt-1 text-sm text-white/40">PDF or DOCX · stays private</p>
                </div>
              </>
            )}
          </div>
        </div>

        {error && (
          <div className="mt-3 flex items-center justify-between rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3">
            <p className="text-sm text-red-300">{error}</p>
            <button
              onClick={() => {
                setError(null)
                setFile(null)
              }}
              className="ml-4 shrink-0 text-sm font-medium text-red-300 underline hover:text-red-200"
            >
              Try again
            </button>
          </div>
        )}

        <button
          onClick={analyze}
          disabled={!file || loading}
          className={cn(
            'mt-4 flex w-full items-center justify-center gap-2 rounded-2xl py-4 text-base font-semibold transition-all',
            'bg-primary text-white shadow-[0_10px_40px_-10px_rgba(178,0,67,0.58)] hover:bg-primary-400 active:scale-[0.99]',
            'disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none',
          )}
        >
          {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : 'Reveal my matches'}
        </button>
      </Reveal>
    </div>
  )
}
