import axios from 'axios';
import type {
    TailorRequest,
    TailorResult,
    TailoredCV,
    ChangeLogEntry,
    BorderlineItem,
    MatchScore,
    CoverLetter,
    JobRequirements,
    CVFacts,
    ApiError,
} from '../types';

// The requirement-to-evidence mapping is an opaque blob the client never
// inspects — it simply receives it from /map and passes it back to the
// downstream steps. Typing it as `unknown` keeps the contract honest.
export type Mapping = unknown;

function resolveApiBaseUrl(): string {
    const configuredUrl = import.meta.env.VITE_API_URL?.trim();
    if (configuredUrl) {
        return configuredUrl.replace(/\/+$/, '');
    }

    return '/api';
}

const API_BASE_URL = resolveApiBaseUrl();
const API_ACCESS_KEY_STORAGE_KEY = 'tailorcv_api_key';

export function getApiAccessKey(): string {
    const configuredKey = import.meta.env.VITE_TAILORCV_API_KEY?.trim();
    if (configuredKey) {
        return configuredKey;
    }

    if (typeof window === 'undefined') {
        return '';
    }

    return window.sessionStorage.getItem(API_ACCESS_KEY_STORAGE_KEY)?.trim() ?? '';
}

export function setApiAccessKey(apiKey: string): void {
    if (typeof window === 'undefined') {
        return;
    }

    const trimmed = apiKey.trim();
    if (trimmed) {
        window.sessionStorage.setItem(API_ACCESS_KEY_STORAGE_KEY, trimmed);
    } else {
        window.sessionStorage.removeItem(API_ACCESS_KEY_STORAGE_KEY);
    }
}

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

api.interceptors.request.use((config) => {
    const apiKey = getApiAccessKey();
    if (apiKey) {
        config.headers.set('X-API-Key', apiKey);
    }
    return config;
});

export async function tailorCV(request: TailorRequest): Promise<TailorResult> {
    const response = await api.post<TailorResult>('/tailor', request);
    return response.data;
}

export async function tailorCVWithFile(
    jobDescription: string,
    cvFile: File,
    options: {
        generateCoverLetter?: boolean;
        strictnessLevel?: string;
        outputFormat?: string;
        userInstructions?: string;
    } = {}
): Promise<TailorResult> {
    const formData = new FormData();
    formData.append('job_description', jobDescription);
    formData.append('cv_file', cvFile);
    formData.append('generate_cover_letter', String(options.generateCoverLetter ?? true));
    formData.append('strictness_level', options.strictnessLevel ?? 'moderate');
    formData.append('output_format', options.outputFormat ?? 'markdown');
    if (options.userInstructions) {
        formData.append('user_instructions', options.userInstructions);
    }

    const response = await api.post<TailorResult>('/tailor/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
}

export async function extractJobRequirements(jobDescription: string): Promise<JobRequirements> {
    const response = await api.post<JobRequirements>('/extract-job', {
        job_description: jobDescription,
    });
    return response.data;
}

export async function extractCVFacts(cvText: string): Promise<CVFacts> {
    const response = await api.post<CVFacts>('/extract-cv', {
        cv_text: cvText,
    });
    return response.data;
}

export async function exportResult(
    format: 'markdown' | 'docx' | 'pdf',
    result: TailorResult
): Promise<Blob> {
    const response = await api.post(`/export/${format}`, result, {
        responseType: 'blob',
    });
    return response.data;
}

export function isApiError(error: unknown): error is { response: { data: ApiError } } {
    if (typeof error !== 'object' || error === null) {
        return false;
    }
    if (!('response' in error)) {
        return false;
    }
    const maybeError = error as { response?: { data?: ApiError } };
    return typeof maybeError.response?.data?.error === 'string';
}

export interface ProgressEvent {
    step?: number;
    total?: number;
    message?: string;
    complete?: boolean;
    result?: TailorResult;
    error?: boolean;
    details?: string[];
}

// ---------------------------------------------------------------------------
// Per-step pipeline calls
//
// Each call performs a single pipeline stage so no request approaches the
// serverless time limit. The client orchestrates them in tailorCV* below.
// ---------------------------------------------------------------------------

export async function parseCvFile(cvFile: File): Promise<string> {
    const formData = new FormData();
    formData.append('cv_file', cvFile);
    const response = await api.post<{ cv_text: string }>('/parse-file', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data.cv_text;
}

export async function mapRequirements(
    requirements: JobRequirements,
    cvFacts: CVFacts,
    strictnessLevel: string
): Promise<Mapping> {
    const response = await api.post<Mapping>('/map', {
        requirements,
        cv_facts: cvFacts,
        strictness_level: strictnessLevel,
    });
    return response.data;
}

export interface GenerateCVStepResponse {
    tailored_cv: TailoredCV;
    changes_log: ChangeLogEntry[];
    borderline_items: BorderlineItem[];
    match_score: MatchScore;
    mapping_summary: TailorResult['mapping_summary'];
    warnings: string[];
}

export async function generateTailoredCv(
    requirements: JobRequirements,
    cvFacts: CVFacts,
    mapping: Mapping,
    strictnessLevel: string,
    userInstructions?: string
): Promise<GenerateCVStepResponse> {
    const response = await api.post<GenerateCVStepResponse>('/generate-cv', {
        requirements,
        cv_facts: cvFacts,
        mapping,
        strictness_level: strictnessLevel,
        user_instructions: userInstructions ?? null,
    });
    return response.data;
}

export async function generateCoverLetterStep(
    requirements: JobRequirements,
    cvFacts: CVFacts,
    mapping: Mapping,
    strictnessLevel: string,
    userInstructions?: string
): Promise<CoverLetter> {
    const response = await api.post<CoverLetter>('/cover-letter', {
        requirements,
        cv_facts: cvFacts,
        mapping,
        strictness_level: strictnessLevel,
        user_instructions: userInstructions ?? null,
    });
    return response.data;
}

// ---------------------------------------------------------------------------
// Client-side orchestration
//
// Replaces the old SSE streaming endpoints. Running the pipeline as separate
// requests means each one finishes quickly (no 60s serverless timeout) and the
// progress reported here is real, not buffered-until-the-end.
// ---------------------------------------------------------------------------

export interface TailorOrchestrationOptions {
    generateCoverLetter?: boolean;
    strictnessLevel?: string;
    userInstructions?: string;
}

export async function tailorCVOrchestrated(
    jobDescription: string,
    cvSource: { text: string } | { file: File },
    onProgress: (event: ProgressEvent) => void,
    options: TailorOrchestrationOptions = {}
): Promise<TailorResult> {
    const generateCoverLetter = options.generateCoverLetter ?? true;
    const strictness = options.strictnessLevel ?? 'moderate';
    const userInstructions = options.userInstructions;

    const isFile = 'file' in cvSource;
    const total = (isFile ? 1 : 0) + 3 + (generateCoverLetter ? 1 : 0);
    let step = 0;
    const emit = (message: string) => {
        step += 1;
        onProgress({ step, total, message });
    };

    // Stage 0 (uploads only): extract plain text from the file
    let cvText: string;
    if (isFile) {
        emit('Reading uploaded CV file...');
        cvText = await parseCvFile(cvSource.file);
    } else {
        cvText = cvSource.text;
    }

    // Stage 1+2: analyze the job and the CV in parallel
    emit('Analyzing job description and CV...');
    const [requirements, cvFacts] = await Promise.all([
        extractJobRequirements(jobDescription),
        extractCVFacts(cvText),
    ]);

    // Stage 3: map requirements to evidence
    emit('Mapping requirements to experience...');
    const mapping = await mapRequirements(requirements, cvFacts, strictness);

    // Stage 4+5: generate the tailored CV and run quality checks
    emit('Generating tailored CV...');
    const generated = await generateTailoredCv(
        requirements,
        cvFacts,
        mapping,
        strictness,
        userInstructions
    );

    // Stage 6: cover letter (optional)
    let coverLetter: CoverLetter | null = null;
    if (generateCoverLetter) {
        emit('Generating cover letter...');
        coverLetter = await generateCoverLetterStep(
            requirements,
            cvFacts,
            mapping,
            strictness,
            userInstructions
        );
    }

    onProgress({ step: total, total, complete: true, message: 'Complete' });

    return {
        tailored_cv: generated.tailored_cv,
        cover_letter: coverLetter,
        changes_log: generated.changes_log,
        borderline_items: generated.borderline_items,
        match_score: generated.match_score,
        mapping_summary: generated.mapping_summary,
        job_title: requirements.job_title,
        // /map returns the full MappingResult; surface it for the Analysis tab.
        mapping_detail: mapping as TailorResult['mapping_detail'],
    };
}
