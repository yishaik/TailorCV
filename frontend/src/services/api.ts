import axios from 'axios';
import type { TailorRequest, TailorResult, JobRequirements, CVFacts, ApiError } from '../types';

function resolveApiBaseUrl(): string {
    const configuredUrl = import.meta.env.VITE_API_URL?.trim();
    if (configuredUrl) {
        return configuredUrl.replace(/\/+$/, '');
    }

    return '/api';
}

const API_BASE_URL = resolveApiBaseUrl();

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
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

async function parseStreamingTailorResponse(
    response: Response,
    onProgress: (event: ProgressEvent) => void
): Promise<TailorResult> {
    if (!response.ok) {
        try {
            const errorPayload = await response.json();
            const detail =
                errorPayload?.detail?.message ||
                errorPayload?.detail?.error ||
                errorPayload?.detail ||
                errorPayload?.message;
            throw new Error(detail ? String(detail) : `HTTP error! status: ${response.status}`);
        } catch {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
    }

    const reader = response.body?.getReader();
    if (!reader) {
        throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    let buffer = '';
    let finalResult: TailorResult | null = null;
    let shouldStop = false;
    let lastMessage = '';

    const processEventBlock = (eventBlock: string) => {
        const dataLines = eventBlock
            .split('\n')
            .filter((line) => line.startsWith('data: '))
            .map((line) => line.slice(6).trim())
            .filter(Boolean);

        if (dataLines.length === 0) {
            return;
        }

        const payload = dataLines.join('\n');
        const data = JSON.parse(payload) as ProgressEvent;
        onProgress(data);

        if (data.message) {
            lastMessage = data.message;
        }

        if (data.error) {
            throw new Error(data.message || 'Unknown error');
        }

        if (data.complete && data.result) {
            finalResult = data.result;
            shouldStop = true;
        }
    };

    while (true) {
        const { done, value } = await reader.read();
        if (done) {
            if (buffer.trim()) {
                const trailing = buffer.replace(/\r\n/g, '\n').trim();
                if (trailing) {
                    try {
                        processEventBlock(trailing);
                    } catch (e) {
                        if (!(e instanceof SyntaxError)) {
                            throw e;
                        }
                    }
                }
            }
            break;
        }

        buffer += decoder.decode(value, { stream: true });
        const normalized = buffer.replace(/\r\n/g, '\n');
        const blocks = normalized.split('\n\n');
        buffer = blocks.pop() || '';

        for (const block of blocks) {
            try {
                processEventBlock(block);
            } catch (e) {
                if (e instanceof SyntaxError) {
                    console.warn('Failed to parse SSE block:', block);
                } else {
                    throw e;
                }
            }
            if (shouldStop) {
                break;
            }
        }

        if (shouldStop) {
            await reader.cancel();
            break;
        }
    }

    if (!finalResult) {
        throw new Error(lastMessage || 'No result received from server');
    }

    return finalResult;
}

export async function tailorCVWithFileAndProgress(
    jobDescription: string,
    cvFile: File,
    onProgress: (event: ProgressEvent) => void,
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

    let response: Response;
    try {
        response = await fetch(`${API_BASE_URL}/tailor/upload/stream`, {
            method: 'POST',
            headers: {
                Accept: 'text/event-stream',
            },
            body: formData,
        });
    } catch {
        throw new Error(
            'Unable to reach the API. Check that the backend is running and the API URL is configured correctly.'
        );
    }

    return parseStreamingTailorResponse(response, onProgress);
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

export async function setApiKey(apiKey: string): Promise<void> {
    await api.post('/set-api-key', {
        api_key: apiKey,
    });
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

export async function tailorCVWithProgress(
    request: TailorRequest,
    onProgress: (event: ProgressEvent) => void
): Promise<TailorResult> {
    let response: Response;
    try {
        response = await fetch(`${API_BASE_URL}/tailor/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Accept: 'text/event-stream',
            },
            body: JSON.stringify(request),
        });
    } catch {
        throw new Error(
            'Unable to reach the API. Check that the backend is running and the API URL is configured correctly.'
        );
    }

    return parseStreamingTailorResponse(response, onProgress);
}
