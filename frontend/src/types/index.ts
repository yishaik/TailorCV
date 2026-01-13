// API types matching backend Pydantic models

export type StrictnessLevel = 'conservative' | 'moderate' | 'aggressive';
export type OutputFormat = 'markdown' | 'docx' | 'pdf' | 'json';

export interface TailorOptions {
    generate_cover_letter: boolean;
    output_format: OutputFormat;
    language: string;
    strictness_level: StrictnessLevel;
    user_notes?: string;
}

export interface TailorRequest {
    job_description: string;
    original_cv: string;
    options: TailorOptions;
}

// Job Requirements
export interface Requirement {
    category: 'technical_skill' | 'soft_skill' | 'experience' | 'certification' | 'education';
    description: string;
    keywords: string[];
    years_required: number | null;
    specificity: 'exact' | 'flexible';
}

export interface JobRequirements {
    job_title: string;
    company: string | null;
    department: string | null;
    must_have: Requirement[];
    nice_to_have: Requirement[];
    inferred: Requirement[];
    ats_keywords: {
        high_priority: string[];
        medium_priority: string[];
        contextual: string[];
    };
    culture_signals: {
        work_style: string[];
        values: string[];
    };
}

// CV Facts
export interface Experience {
    id: string;
    company: string;
    title: string;
    start_date: string;
    end_date: string;
    duration_months: number | null;
    location: string | null;
    responsibilities: {
        original_text: string;
        extracted_facts: {
            action: string;
            context: string | null;
            result: string | null;
            technologies: string[];
            scope: string | null;
        };
    }[];
    achievements: {
        original_text: string;
        quantified: boolean;
        metrics: {
            type: 'percentage' | 'number' | 'currency' | 'time' | 'other';
            value: string;
            context: string;
        } | null;
    }[];
}

export interface CVFacts {
    personal_info: {
        name: string;
        email: string | null;
        phone: string | null;
        location: string | null;
        linkedin: string | null;
        website: string | null;
    };
    professional_summary: {
        original_text: string | null;
        extracted_claims: string[];
    } | null;
    experience: Experience[];
    skills: {
        explicitly_listed: string[];
        inferred_from_experience: {
            skill: string;
            evidence_source: string;
        }[];
    };
    education: {
        institution: string;
        degree: string;
        field: string;
        graduation_year: number | null;
        achievements: string[];
    }[];
    certifications: {
        name: string;
        issuer: string;
        date: string | null;
        status: 'completed' | 'in_progress' | 'expired';
    }[];
    projects: {
        name: string;
        description: string;
        technologies: string[];
        role: string | null;
        outcomes: string[];
    }[];
    languages: {
        language: string;
        proficiency: string | null;
    }[];
}

// Tailored Output
export interface TailoredCV {
    header: {
        name: string;
        title: string;
        contact: Record<string, string>;
    };
    summary: string;
    experience: {
        company: string;
        title: string;
        dates: string;
        location: string | null;
        bullets: {
            text: string;
            keywords_used: string[];
        }[];
    }[];
    skills: {
        primary: string[];
        secondary: string[];
        tools: string[];
    };
    education: {
        institution: string;
        degree: string;
        field: string;
        year: string | null;
        highlights: string[];
    }[];
    certifications: {
        name: string;
        issuer: string;
        date: string | null;
    }[];
    projects: {
        name: string;
        description: string;
        technologies: string[];
    }[];
}

export interface ChangeLogEntry {
    section: string;
    change_type: 'reorder' | 'rewrite' | 'add_keyword' | 'quantify' | 'remove';
    original: string | null;
    new: string;
    justification: string;
    confidence: 'high' | 'medium' | 'low';
    requires_review: boolean;
}

export interface BorderlineItem {
    content: string;
    category: 'inferred_but_reasonable' | 'reframed_significantly' | 'gap_mitigation';
    original_evidence: string;
    risk_level: 'low' | 'medium' | 'high';
    user_prompt: string;
}

export interface CoverLetter {
    hook: string;
    value_proposition: string;
    fit_narrative: string;
    closing: string;
}

export interface MatchScore {
    score: number;
    breakdown: {
        must_have_component: number;
        nice_to_have_component: number;
        bonuses: string[];
        penalties: string[];
    };
    explanation: string;
}

export interface TailorResult {
    tailored_cv: TailoredCV;
    cover_letter: CoverLetter | null;
    changes_log: ChangeLogEntry[];
    borderline_items: BorderlineItem[];
    match_score: MatchScore;
    mapping_summary: {
        overall_score: number;
        must_have_coverage: string;
        nice_to_have_coverage: string;
        strongest_matches: string[];
        critical_gaps: string[];
        keywords_present: string[];
        keywords_missing: string[];
    } | null;
}

export interface ApiError {
    error: string;
    message: string;
    details?: string[];
}
