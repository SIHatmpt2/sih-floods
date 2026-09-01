'use client';

import React, { useState, useRef, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { Shield, Radar, Trash2, ClipboardPaste, Upload, FileText, Image, X, FileUp } from 'lucide-react';
import type { FileData } from './ScannerPageClient';

interface InputPanelProps {
  onScan: (text: string, fileData?: FileData) => void;
  isScanning: boolean;
}

interface FormValues {
  jobText: string;
}

type InputMode = 'text' | 'file';

const EXAMPLE_SCAM = `URGENT HIRING - Remote Customer Service Agent

We are looking for enthusiastic individuals to join our team immediately! No experience required. Earn $8,500/month working from home.

REQUIREMENTS:
- Must be available to start TODAY
- You will need to purchase a starter kit ($250 processing fee) — this will be reimbursed in your first paycheck
- Contact us ONLY via Telegram: @jobs_remote_fast (no email responses)
- Wire transfer your fee to: account details provided on Telegram
- Government clearance fee may apply

IMMEDIATE HIRE. Limited slots available. Apply now before positions are filled!`;

const EXAMPLE_SAFE = `Senior Product Designer — Meridian Systems (Series B, Remote/NYC Hybrid)

Meridian Systems is hiring a Senior Product Designer to lead our core product experience across web and mobile. We're a 120-person fintech company backed by Andreessen Horowitz.

RESPONSIBILITIES:
- Own end-to-end design for 3 product squads
- Collaborate with Engineering and Product Management
- Conduct user research and usability testing

REQUIREMENTS:
- 5+ years product design experience
- Strong Figma skills, design systems experience preferred
- Portfolio demonstrating complex B2B product work

COMPENSATION: $140,000–$175,000 base + equity + full benefits
PROCESS: Intro call → Portfolio review → Design exercise → Final loop (4 rounds total)

Apply via: careers.meridiansystems.com/design — recruiter contact: hiring@meridiansystems.com`;

const ACCEPTED_TYPES = ['image/png', 'image/jpeg', 'image/jpg', 'application/pdf'];
const ACCEPTED_EXTENSIONS = '.png,.jpg,.jpeg,.pdf';

async function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const result = reader.result as string;
      // Strip the data URI prefix to get raw base64
      const base64 = result.split(',')[1];
      resolve(base64);
    };
    reader.onerror = reject;
  });
}

export default function InputPanel({ onScan, isScanning }: InputPanelProps) {
  const [charCount, setCharCount] = useState(0);
  const [inputMode, setInputMode] = useState<InputMode>('text');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<FormValues>({ defaultValues: { jobText: '' } });

  const textValue = watch('jobText');

  const validateAndSetFile = (file: File) => {
    setFileError(null);
    if (!ACCEPTED_TYPES.includes(file.type)) {
      setFileError('Unsupported file type. Please upload PNG, JPG, JPEG, or PDF.');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setFileError('File too large. Maximum size is 10MB.');
      return;
    }
    setUploadedFile(file);
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) validateAndSetFile(file);
  }, []);

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) validateAndSetFile(file);
  };

  const clearFile = () => {
    setUploadedFile(null);
    setFileError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const onSubmit = async (data: FormValues) => {
    if (inputMode === 'file') {
      if (!uploadedFile) {
        setFileError('Please upload a file to scan.');
        return;
      }
      const base64 = await fileToBase64(uploadedFile);
      const fileData: FileData = {
        base64,
        mimeType: uploadedFile.type,
        fileName: uploadedFile.name,
      };
      onScan(data.jobText, fileData);
    } else {
      onScan(data.jobText);
    }
  };

  const handleClear = () => {
    setValue('jobText', '');
    setCharCount(0);
    clearFile();
  };

  const loadExample = (type: 'scam' | 'safe') => {
    const text = type === 'scam' ? EXAMPLE_SCAM : EXAMPLE_SAFE;
    setValue('jobText', text);
    setCharCount(text.length);
    setInputMode('text');
  };

  const getFileIcon = (file: File) => {
    if (file.type === 'application/pdf') return <FileText size={20} className="text-red-400" />;
    return <Image size={20} className="text-blue-400" />;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="card-glass rounded-2xl border border-slate-800/60 flex flex-col">
      {/* Card header */}
      <div className="flex items-center justify-between p-5 border-b border-slate-800/60">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center">
            <Shield size={15} className="text-red-400" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-200">Target Intelligence</h2>
            <p className="text-xs font-mono text-slate-600">Paste text or upload a file for analysis</p>
          </div>
        </div>
        <button
          type="button"
          onClick={handleClear}
          className="p-1.5 rounded-lg text-slate-600 hover:text-slate-400 hover:bg-slate-800/60 transition-all duration-200"
          title="Clear input"
          aria-label="Clear input"
        >
          <Trash2 size={14} />
        </button>
      </div>

      {/* Mode toggle */}
      <div className="px-5 pt-4 flex items-center gap-1 p-1 bg-slate-900/60 mx-5 mt-4 rounded-xl border border-slate-800/60">
        <button
          type="button"
          onClick={() => setInputMode('text')}
          className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-mono font-semibold transition-all duration-200 ${
            inputMode === 'text' ?'bg-slate-700/80 text-slate-100 shadow-sm' :'text-slate-500 hover:text-slate-400'
          }`}
        >
          <ClipboardPaste size={12} />
          Paste Text
        </button>
        <button
          type="button"
          onClick={() => setInputMode('file')}
          className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-mono font-semibold transition-all duration-200 ${
            inputMode === 'file' ?'bg-slate-700/80 text-slate-100 shadow-sm' :'text-slate-500 hover:text-slate-400'
          }`}
        >
          <FileUp size={12} />
          Upload File
        </button>
      </div>

      {/* Quick load examples (text mode only) */}
      {inputMode === 'text' && (
        <div className="px-5 pt-3 flex items-center gap-2 flex-wrap">
          <span className="text-xs font-mono text-slate-600">Load example:</span>
          <button
            type="button"
            onClick={() => loadExample('scam')}
            className="flex items-center gap-1.5 text-xs font-mono px-2.5 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-500/20 transition-all duration-200"
          >
            <ClipboardPaste size={11} />
            Scam Posting
          </button>
          <button
            type="button"
            onClick={() => loadExample('safe')}
            className="flex items-center gap-1.5 text-xs font-mono px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20 transition-all duration-200"
          >
            <ClipboardPaste size={11} />
            Safe Posting
          </button>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col flex-1 p-5 gap-4">

        {/* File upload zone */}
        {inputMode === 'file' && (
          <div className="space-y-3">
            {!uploadedFile ? (
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`relative flex flex-col items-center justify-center gap-3 min-h-[180px] rounded-xl border-2 border-dashed cursor-pointer transition-all duration-200 ${
                  isDragging
                    ? 'border-red-500/60 bg-red-500/5 scale-[1.01]'
                    : 'border-slate-700/60 bg-slate-900/40 hover:border-slate-600/60 hover:bg-slate-900/60'
                }`}
              >
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-200 ${
                  isDragging ? 'bg-red-500/20 border border-red-500/30' : 'bg-slate-800/60 border border-slate-700/60'
                }`}>
                  <Upload size={20} className={isDragging ? 'text-red-400' : 'text-slate-500'} />
                </div>
                <div className="text-center">
                  <p className="text-sm font-semibold text-slate-300 mb-1">
                    {isDragging ? 'Drop file here' : 'Drag & drop or click to upload'}
                  </p>
                  <p className="text-xs font-mono text-slate-600">
                    Offer Letter · Chat Screenshot · Job Posting
                  </p>
                  <p className="text-xs font-mono text-slate-700 mt-1">
                    PNG · JPG · JPEG · PDF · Max 10MB
                  </p>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={ACCEPTED_EXTENSIONS}
                  onChange={handleFileInputChange}
                  className="hidden"
                  aria-label="Upload file for scanning"
                />
              </div>
            ) : (
              <div className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-900/60 border border-slate-700/60">
                <div className="w-10 h-10 rounded-lg bg-slate-800/80 border border-slate-700/40 flex items-center justify-center flex-shrink-0">
                  {getFileIcon(uploadedFile)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-slate-200 truncate">{uploadedFile.name}</p>
                  <p className="text-xs font-mono text-slate-600">
                    {uploadedFile.type === 'application/pdf' ? 'PDF Document' : 'Image'} · {formatFileSize(uploadedFile.size)}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={clearFile}
                  className="p-1.5 rounded-lg text-slate-600 hover:text-red-400 hover:bg-red-500/10 transition-all duration-200 flex-shrink-0"
                  aria-label="Remove uploaded file"
                >
                  <X size={14} />
                </button>
              </div>
            )}

            {fileError && (
              <p className="text-xs text-red-400 font-mono bg-red-500/10 border border-red-500/20 px-3 py-2 rounded-lg">
                {fileError}
              </p>
            )}

            {/* Optional additional context for file mode */}
            <div className="relative">
              <textarea
                {...register('jobText')}
                className="input-cyber p-3 min-h-[80px] w-full text-xs"
                placeholder="Optional: Add context or notes about this file..."
                disabled={isScanning}
                onChange={(e) => setCharCount(e.target.value.length)}
                aria-label="Optional context for file upload"
              />
            </div>
          </div>
        )}

        {/* Text input zone */}
        {inputMode === 'text' && (
          <div className="flex-1 relative">
            <textarea
              {...register('jobText', {
                required: inputMode === 'text' ? 'Paste a job posting, recruiter message, or offer letter to scan.' : false,
                minLength: inputMode === 'text' ? {
                  value: 20,
                  message: 'Please provide at least 20 characters for a meaningful analysis.',
                } : undefined,
              })}
              className="input-cyber p-4 min-h-[320px] h-full w-full"
              placeholder="Paste the job description, recruiter email, or offer letter text here...&#10;&#10;Example: 'Remote Customer Service Rep — $8,500/mo, no experience needed, contact via Telegram, wire $250 processing fee...'"
              disabled={isScanning}
              onChange={(e) => setCharCount(e.target.value.length)}
              aria-label="Job posting text input"
            />
            {errors.jobText && (
              <p className="absolute bottom-2 left-2 text-xs text-red-400 font-mono bg-slate-950/90 px-2 py-0.5 rounded">
                {errors.jobText.message}
              </p>
            )}
          </div>
        )}

        {/* Character count + PII notice (text mode) */}
        {inputMode === 'text' && (
          <div className="flex items-center justify-between text-xs font-mono text-slate-600">
            <span className={textValue?.length > 5000 ? 'text-amber-400' : ''}>
              {charCount.toLocaleString()} chars
            </span>
            <span className="text-emerald-600/80">PII will be stripped before AI processing</span>
          </div>
        )}

        {/* Submit button */}
        <button
          type="submit"
          disabled={isScanning}
          className={`relative flex items-center justify-center gap-2.5 w-full py-3.5 rounded-xl text-sm font-semibold text-white transition-all duration-200 ${
            isScanning
              ? 'bg-slate-800 border border-slate-700 cursor-not-allowed opacity-80' :'btn-primary-glow'
          }`}
          aria-label={isScanning ? 'Scanning in progress' : 'Start scan'}
        >
          {isScanning ? (
            <>
              <span className="radar-spin">
                <Radar size={16} className="text-red-400" />
              </span>
              <span className="font-mono text-slate-400">
                {inputMode === 'file' ? 'Processing File & Analyzing via Gemini...' : 'Stripping PII & Analyzing via Gemini API...'}
              </span>
              <span className="flex gap-0.5 ml-1">
                {[0, 1, 2].map((i) => (
                  <span
                    key={`dot-${i}`}
                    className="w-1 h-1 rounded-full bg-red-400 animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }}
                  />
                ))}
              </span>
            </>
          ) : (
            <>
              {inputMode === 'file' ? <Upload size={16} /> : <Radar size={16} />}
              {inputMode === 'file' ? 'Scan Uploaded File' : 'Sanitize & Scan'}
            </>
          )}
        </button>

        {/* Security note */}
        <div className="flex items-start gap-2 p-3 rounded-lg bg-slate-900/60 border border-slate-800/40">
          <Shield size={12} className="text-slate-600 flex-shrink-0 mt-0.5" />
          <p className="text-xs font-mono text-slate-600 leading-relaxed">
            {inputMode === 'file' ?'Files are converted to Base64 client-side. PII is redacted from any extracted text. No data is stored after scan completion.' :'Text is processed locally for PII removal before transmission. No input data is stored after scan completion.'}
          </p>
        </div>
      </form>
    </div>
  );
}