import axios from 'axios';
import type { TailorRequest, TailorResult, JobRequirements, CVFacts, ApiError } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

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
    } = {}
): Promise<TailorResult> {
    const formData = new FormData();
    formData.append('job_description', jobDescription);
    formData.append('cv_file', cvFile);
    formData.append('generate_cover_letter', String(options.generateCoverLetter ?? true));
    formData.append('strictness_level', options.strictnessLevel ?? 'moderate');
    formData.append('output_format', options.outputFormat ?? 'markdown');

    const response = await api.post<TailorResult>('/tailor/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
}

export async function extractJobRequirements(jobDescription: string): Promise<JobRequirements> {
    const response = await api.post<JobRequirements>('/extract-job', null, {
        params: { job_description: jobDescription },
    });
    return response.data;
}

export async function extractCVFacts(cvText: string): Promise<CVFacts> {
    const response = await api.post<CVFacts>('/extract-cv', null, {
        params: { cv_text: cvText },
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
    await api.post('/set-api-key', null, {
        params: { api_key: apiKey },
    });
}

export function isApiError(error: unknown): error is { response: { data: ApiError } } {
    return (
        typeof error === 'object' &&
        error !== null &&
        'response' in error &&
        typeof (error as any).response?.data?.error === 'string'
    );
}
