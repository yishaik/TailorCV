import type { ApplyTarget } from '../types';

// Matches plain emails. Deliberately conservative to avoid catching things like
// version numbers or handles.
const EMAIL_RE = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
// Matches http(s) URLs up to the first whitespace or closing bracket/quote.
const URL_RE = /https?:\/\/[^\s<>"')\]]+/g;

function trimTrailingPunctuation(value: string): string {
    return value.replace(/[.,;:!?)\]]+$/, '');
}

/**
 * Find ways to apply (email or link) mentioned in a job description.
 *
 * The candidate's own contact details are excluded so we never point the user
 * at their own email/site. Results are de-duplicated and emails are listed
 * before generic links, since "email to apply" is the stronger signal.
 */
export function extractApplyTargets(
    jobDescription: string,
    exclude: Array<string | null | undefined> = []
): ApplyTarget[] {
    if (!jobDescription) return [];

    const excludeSet = new Set(
        exclude
            .filter((v): v is string => !!v)
            .map((v) => v.toLowerCase().trim())
    );

    const seen = new Set<string>();
    const emails: ApplyTarget[] = [];
    const urls: ApplyTarget[] = [];

    for (const raw of jobDescription.match(EMAIL_RE) ?? []) {
        const value = trimTrailingPunctuation(raw);
        const key = value.toLowerCase();
        if (excludeSet.has(key) || seen.has(key)) continue;
        seen.add(key);
        emails.push({
            type: 'email',
            value,
            href: `mailto:${value}`,
            label: value,
        });
    }

    for (const raw of jobDescription.match(URL_RE) ?? []) {
        const value = trimTrailingPunctuation(raw);
        const key = value.toLowerCase();
        if (seen.has(key)) continue;
        // Skip links whose host matches an excluded contact (e.g. the
        // candidate's own LinkedIn/portfolio).
        const host = (() => {
            try {
                return new URL(value).host.toLowerCase();
            } catch {
                return '';
            }
        })();
        if (host && [...excludeSet].some((e) => e.includes(host) || host.includes(e))) {
            continue;
        }
        seen.add(key);
        let label = value;
        try {
            label = new URL(value).host.replace(/^www\./, '');
        } catch {
            /* keep full value as label */
        }
        urls.push({ type: 'url', value, href: value, label });
    }

    return [...emails, ...urls];
}

/**
 * Build a mailto href that pre-fills a sensible application subject line.
 */
export function buildApplicationMailto(
    email: string,
    applicantName?: string | null,
    jobTitle?: string | null
): string {
    const role = jobTitle?.trim();
    const name = applicantName?.trim();
    const subject = role
        ? `Application for ${role}${name ? ` – ${name}` : ''}`
        : name
          ? `Job application – ${name}`
          : 'Job application';
    return `mailto:${email}?subject=${encodeURIComponent(subject)}`;
}
