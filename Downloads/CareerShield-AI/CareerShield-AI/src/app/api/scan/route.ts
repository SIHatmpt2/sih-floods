import { NextRequest, NextResponse } from 'next/server';
import { GoogleGenAI } from '@google/genai';

interface ForensicFlag {
  id: string;
  type: 'danger' | 'warning' | 'safe';
  label: string;
  detail: string;
}

interface VectorScores {
  communication_security: number;
  financial_risk: number;
  urgency_pressure: number;
  compensation_match: number;
}

interface ScanResult {
  score: number;
  riskLevel: 'HIGH_RISK' | 'SUSPICIOUS' | 'LIKELY_SAFE';
  verdict: string;
  flags: ForensicFlag[];
  vector_scores: VectorScores;
  action_checklist: string[];
  reasoning: string;
  piiStripped: number;
  piiTypes: string[];
  scanDuration: number;
  model: string;
}

interface GeminiScanResponse {
  trust_score: number;
  verdict: 'SAFE' | 'CAUTION' | 'HIGH RISK';
  vector_scores: VectorScores;
  flags: string[];
  action_checklist: string[];
  reasoning: string;
}

/**
 * Scrubs PII (email addresses and phone numbers) from input text before
 * sending to the AI model.
 */
function sanitizePII(text: string): { sanitized: string; piiCount: number; piiTypes: string[] } {
  const emailRegex = /\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b/g;
  const phoneRegex = /(\+?1[\s\-.]?)?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}\b/g;

  const piiTypes: string[] = [];
  let piiCount = 0;

  const emailMatches = text.match(emailRegex);
  if (emailMatches) {
    piiCount += emailMatches.length;
    piiTypes.push('Email Address');
  }

  const phoneMatches = text.match(phoneRegex);
  if (phoneMatches) {
    piiCount += phoneMatches.length;
    piiTypes.push('Phone Number');
  }

  const sanitized = text
    .replace(emailRegex, '[EMAIL REDACTED]')
    .replace(phoneRegex, '[PHONE REDACTED]');

  return { sanitized, piiCount, piiTypes };
}

/**
 * Maps a numeric trust_score to a riskLevel category.
 */
function getRiskLevel(score: number): 'HIGH_RISK' | 'SUSPICIOUS' | 'LIKELY_SAFE' {
  if (score < 35) return 'HIGH_RISK';
  if (score < 65) return 'SUSPICIOUS';
  return 'LIKELY_SAFE';
}

/**
 * Converts the flat flags string array from Gemini into structured ForensicFlag objects.
 */
function parseFlags(rawFlags: string[]): ForensicFlag[] {
  return rawFlags.slice(0, 6).map((label, index) => {
    const lower = label.toLowerCase();
    let type: 'danger' | 'warning' | 'safe' = 'danger';

    if (
      lower.startsWith('✓') ||
      lower.includes('safe') ||
      lower.includes('legitimate') ||
      lower.includes('verified') ||
      lower.includes('standard') ||
      lower.includes('no upfront') ||
      lower.includes('no request') ||
      lower.includes('no financial') ||
      lower.includes('no unusual') ||
      lower.includes('compensation within') ||
      lower.includes('multi-stage') ||
      lower.includes('structured interview')
    ) {
      type = 'safe';
    } else if (
      lower.includes('warn') ||
      lower.includes('unusual') ||
      lower.includes('vague') ||
      lower.includes('missing') ||
      lower.includes('unverified') ||
      lower.includes('suspicious') ||
      lower.includes('unclear')
    ) {
      type = 'warning';
    }

    return {
      id: `flag-${String(index + 1).padStart(3, '0')}`,
      type,
      label,
      detail: '',
    };
  });
}

function clampScore(val: unknown): number {
  const n = typeof val === 'number' ? val : Number(val);
  return isNaN(n) ? 50 : Math.max(0, Math.min(100, Math.round(n)));
}

export async function POST(request: NextRequest) {
  const startTime = Date.now();

  try {
    const body = await request.json();
    const { text, fileData } = body;

    // fileData: { base64: string; mimeType: string } — optional
    const hasFile = fileData && typeof fileData.base64 === 'string' && fileData.base64.length > 0;
    const hasText = text && typeof text === 'string' && text.trim().length >= 10;

    if (!hasFile && !hasText) {
      return NextResponse.json(
        { error: 'Insufficient input. Please provide text or upload a file.' },
        { status: 400 }
      );
    }

    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      return NextResponse.json(
        { error: 'GEMINI_API_KEY is not configured.' },
        { status: 500 }
      );
    }

    // Step 1: Sanitize PII from text portion
    const rawText = text || '';
    const { sanitized, piiCount, piiTypes } = sanitizePII(rawText);

    // Step 2: Build the strict JSON prompt
    const systemPrompt = `You are CareerShield AI, an expert cybersecurity analyst specializing in recruitment fraud detection.
Analyze the provided job posting, recruiter message, or offer letter (which may be supplied as text, an image, or a PDF document) for fraud patterns, red flags, and trust signals.

You MUST respond with ONLY a valid JSON object — no markdown, no code fences, no explanatory text before or after.
The JSON must match this exact schema:
{
  "trust_score": <integer 0-100, where 0 = definite scam, 100 = fully legitimate>,
  "verdict": <string, one of exactly "SAFE", "CAUTION", or "HIGH RISK">,
  "vector_scores": {
    "communication_security": <integer 0-100, how safe the communication channels and contact methods are>,
    "financial_risk": <integer 0-100, absence of financial red flags like fees, wire transfers, crypto>,
    "urgency_pressure": <integer 0-100, absence of high-pressure urgency tactics>,
    "compensation_match": <integer 0-100, how realistic and market-aligned the compensation is>
  },
  "flags": <array of 3-5 strings, each describing a specific red flag or green flag found in the text>,
  "action_checklist": <array of 3-4 strings, each a concrete recommended next step for the user based on the verdict>,
  "reasoning": <string: concise 2-sentence explanation of the overall assessment>
}

Scoring guidance for trust_score:
- 0-34: HIGH RISK — Clear fraud signals (wire transfers, upfront fees, off-platform redirects, implausible salaries)
- 35-64: CAUTION — Suspicious (vague requirements, unverified company, unusual requests)
- 65-100: SAFE — Likely legitimate (verifiable company, standard process, realistic compensation)

For vector_scores: higher = safer/better (e.g., communication_security=90 means communication channels look legitimate).
For flags: prefix green/safe flags with "✓" and describe red flags plainly.
For action_checklist:
- If HIGH RISK or CAUTION: include protective steps (e.g., "Do not send funds or bank details", "Verify recruiter on official company domain")
- If SAFE: include standard safety hygiene tips (e.g., "Verify the job listing on the company's official careers page")`;

    // Step 3: Build multimodal contents array
    const ai = new GoogleGenAI({ apiKey });

    // Build the content parts
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const contentParts: any[] = [];

    if (hasText) {
      contentParts.push({
        text: `${systemPrompt}\n\nContent to analyze:\n${sanitized}`,
      });
    } else {
      contentParts.push({ text: systemPrompt });
    }

    if (hasFile) {
      const mimeType = fileData.mimeType || 'image/png';
      contentParts.push({
        inlineData: {
          mimeType,
          data: fileData.base64,
        },
      });
    }

    // Step 4: Call Gemini
    let rawContent = '';
    try {
      const response = await ai.models.generateContent({
        model: 'gemini-2.5-flash',
        contents: [{ role: 'user', parts: contentParts }],
        config: {
          temperature: 0.2,
          maxOutputTokens: 1500,
        },
      });
      rawContent = response.text ?? '';
    } catch {
      const response = await ai.models.generateContent({
        model: 'gemini-1.5-flash-latest',
        contents: [{ role: 'user', parts: contentParts }],
        config: {
          temperature: 0.2,
          maxOutputTokens: 1500,
        },
      });
      rawContent = response.text ?? '';
    }

    // Step 5: Safely parse the strict JSON response
    let parsed: GeminiScanResponse;
    try {
      const cleaned = rawContent
        .replace(/^```(?:json)?\s*/i, '')
        .replace(/\s*```$/, '')
        .trim();
      parsed = JSON.parse(cleaned);
    } catch {
      const jsonMatch = rawContent.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        throw new Error('AI returned an unparseable response. Please try again.');
      }
      parsed = JSON.parse(jsonMatch[0]);
    }

    // Validate required fields
    if (
      typeof parsed.trust_score !== 'number' ||
      !parsed.verdict ||
      !Array.isArray(parsed.flags)
    ) {
      throw new Error('AI response missing required fields.');
    }

    const score = clampScore(parsed.trust_score);
    const riskLevel = getRiskLevel(score);

    const verdictMap: Record<string, string> = {
      SAFE: 'LIKELY SAFE: LOW FRAUD INDICATORS',
      CAUTION: 'SUSPICIOUS: FURTHER VERIFICATION REQUIRED',
      'HIGH RISK': 'HIGH RISK: LIKELY SCAM',
    };
    const verdict =
      verdictMap[parsed.verdict.toUpperCase()] ??
      (riskLevel === 'HIGH_RISK' ?'HIGH RISK: LIKELY SCAM'
        : riskLevel === 'SUSPICIOUS' ?'SUSPICIOUS: FURTHER VERIFICATION REQUIRED' :'LIKELY SAFE: LOW FRAUD INDICATORS');

    const flags = parseFlags(parsed.flags);
    const reasoning = parsed.reasoning ?? '';

    // Parse vector scores with fallback defaults
    const rawVectors = parsed.vector_scores ?? {};
    const vector_scores: VectorScores = {
      communication_security: clampScore(rawVectors.communication_security ?? 50),
      financial_risk: clampScore(rawVectors.financial_risk ?? 50),
      urgency_pressure: clampScore(rawVectors.urgency_pressure ?? 50),
      compensation_match: clampScore(rawVectors.compensation_match ?? 50),
    };

    const action_checklist: string[] = Array.isArray(parsed.action_checklist)
      ? parsed.action_checklist.slice(0, 4)
      : [];

    const result: ScanResult = {
      score,
      riskLevel,
      verdict,
      flags,
      vector_scores,
      action_checklist,
      reasoning,
      piiStripped: piiCount,
      piiTypes,
      scanDuration: Date.now() - startTime,
      model: 'CareerShield-v2.1 / gemini-2.5-flash',
    };

    return NextResponse.json(result, { status: 200 });
  } catch (err: unknown) {
    const message =
      err instanceof Error ? err.message : 'Scan pipeline failed. Please try again.';
    console.error('[CareerShield Scan Error]', message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}