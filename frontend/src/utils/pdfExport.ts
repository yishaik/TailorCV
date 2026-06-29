import type { TailorResult } from '../types';

function escapeHtml(value: unknown): string {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function joinEscaped(values: unknown[], separator: string): string {
    return values
        .filter((value) => value !== null && value !== undefined && String(value).trim() !== '')
        .map(escapeHtml)
        .join(separator);
}

export function generatePdfHtml(result: TailorResult): string {
    const cv = result.tailored_cv;
    const coverLetter = result.cover_letter;

    return `
            <div style="font-family: 'Segoe UI', Arial, sans-serif; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <h1 style="margin: 0; font-size: 28px; color: #1a1a2e;">${escapeHtml(cv.header.name)}</h1>
                    <p style="margin: 5px 0; font-size: 16px; color: #666;">${escapeHtml(cv.header.title)}</p>
                    <p style="margin: 5px 0; font-size: 12px; color: #888;">${joinEscaped(Object.values(cv.header.contact), ' | ')}</p>
                </div>

                <div style="margin-bottom: 20px;">
                    <h2 style="font-size: 18px; color: #1a1a2e; border-bottom: 2px solid #7c4dff; padding-bottom: 5px;">Summary</h2>
                    <p style="font-size: 14px; line-height: 1.6;">${escapeHtml(cv.summary)}</p>
                </div>

                <div style="margin-bottom: 20px;">
                    <h2 style="font-size: 18px; color: #1a1a2e; border-bottom: 2px solid #7c4dff; padding-bottom: 5px;">Experience</h2>
                    ${cv.experience.map(exp => `
                        <div style="margin-bottom: 15px;">
                            <h3 style="margin: 0; font-size: 16px; color: #333;">${escapeHtml(exp.title)}</h3>
                            <p style="margin: 2px 0; font-size: 14px; color: #666;"><strong>${escapeHtml(exp.company)}</strong> | ${escapeHtml(exp.dates)}${exp.location ? ` | ${escapeHtml(exp.location)}` : ''}</p>
                            <ul style="margin: 10px 0; padding-left: 20px;">
                                ${exp.bullets.map(b => `<li style="font-size: 13px; line-height: 1.5; margin-bottom: 5px;">${escapeHtml(b.text)}</li>`).join('')}
                            </ul>
                        </div>
                    `).join('')}
                </div>

                ${(cv.skills.primary.length || cv.skills.secondary.length) ? `
                <div style="margin-bottom: 20px;">
                    <h2 style="font-size: 18px; color: #1a1a2e; border-bottom: 2px solid #7c4dff; padding-bottom: 5px;">Skills</h2>
                    ${cv.skills.primary.length ? `<p style="font-size: 13px;"><strong>Core:</strong> ${joinEscaped(cv.skills.primary, ', ')}</p>` : ''}
                    ${cv.skills.secondary.length ? `<p style="font-size: 13px;"><strong>Additional:</strong> ${joinEscaped(cv.skills.secondary, ', ')}</p>` : ''}
                    ${cv.skills.tools.length ? `<p style="font-size: 13px;"><strong>Tools:</strong> ${joinEscaped(cv.skills.tools, ', ')}</p>` : ''}
                </div>
                ` : ''}

                ${cv.education.length ? `
                <div style="margin-bottom: 20px;">
                    <h2 style="font-size: 18px; color: #1a1a2e; border-bottom: 2px solid #7c4dff; padding-bottom: 5px;">Education</h2>
                    ${cv.education.map(edu => `
                        <p style="font-size: 14px; margin: 5px 0;">
                            <strong>${escapeHtml(edu.degree)} in ${escapeHtml(edu.field)}</strong>${edu.year ? ` (${escapeHtml(edu.year)})` : ''}<br/>
                            <span style="color: #666;">${escapeHtml(edu.institution)}</span>
                        </p>
                    `).join('')}
                </div>
                ` : ''}

                ${cv.certifications.length ? `
                <div style="margin-bottom: 20px;">
                    <h2 style="font-size: 18px; color: #1a1a2e; border-bottom: 2px solid #7c4dff; padding-bottom: 5px;">Certifications</h2>
                    ${cv.certifications.map(cert => `
                        <p style="font-size: 13px; margin: 5px 0;">${escapeHtml(cert.name)} - ${escapeHtml(cert.issuer)}${cert.date ? ` (${escapeHtml(cert.date)})` : ''}</p>
                    `).join('')}
                </div>
                ` : ''}

                ${coverLetter ? `
                <div style="page-break-before: always; padding-top: 20px;">
                    <h2 style="font-size: 20px; color: #1a1a2e; text-align: center; margin-bottom: 20px;">Cover Letter</h2>
                    <p style="font-size: 14px; line-height: 1.8; margin-bottom: 15px;">${escapeHtml(coverLetter.hook)}</p>
                    <p style="font-size: 14px; line-height: 1.8; margin-bottom: 15px;">${escapeHtml(coverLetter.value_proposition)}</p>
                    <p style="font-size: 14px; line-height: 1.8; margin-bottom: 15px;">${escapeHtml(coverLetter.fit_narrative)}</p>
                    <p style="font-size: 14px; line-height: 1.8;">${escapeHtml(coverLetter.closing)}</p>
                </div>
                ` : ''}
            </div>
        `;
}
