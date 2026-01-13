import React from 'react';
import {
    Box,
    Button,
    ButtonGroup,
    Paper,
    Typography,
    CircularProgress,
} from '@mui/material';
import html2pdf from 'html2pdf.js';

import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import ArticleIcon from '@mui/icons-material/Article';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import DescriptionIcon from '@mui/icons-material/Description';
import type { TailorResult } from '../types';
import { exportResult } from '../services/api';

interface ExportOptionsProps {
    result: TailorResult;
}

export function ExportOptions({ result }: ExportOptionsProps) {
    const [exporting, setExporting] = React.useState<string | null>(null);
    const [copied, setCopied] = React.useState(false);

    const generatePdfHtml = () => {
        const cv = result.tailored_cv;
        const coverLetter = result.cover_letter;

        let html = `
            <div style="font-family: 'Segoe UI', Arial, sans-serif; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <h1 style="margin: 0; font-size: 28px; color: #1a1a2e;">${cv.header.name}</h1>
                    <p style="margin: 5px 0; font-size: 16px; color: #666;">${cv.header.title}</p>
                    <p style="margin: 5px 0; font-size: 12px; color: #888;">${Object.values(cv.header.contact).join(' | ')}</p>
                </div>

                <div style="margin-bottom: 20px;">
                    <h2 style="font-size: 18px; color: #1a1a2e; border-bottom: 2px solid #7c4dff; padding-bottom: 5px;">Summary</h2>
                    <p style="font-size: 14px; line-height: 1.6;">${cv.summary}</p>
                </div>

                <div style="margin-bottom: 20px;">
                    <h2 style="font-size: 18px; color: #1a1a2e; border-bottom: 2px solid #7c4dff; padding-bottom: 5px;">Experience</h2>
                    ${cv.experience.map(exp => `
                        <div style="margin-bottom: 15px;">
                            <h3 style="margin: 0; font-size: 16px; color: #333;">${exp.title}</h3>
                            <p style="margin: 2px 0; font-size: 14px; color: #666;"><strong>${exp.company}</strong> | ${exp.dates}${exp.location ? ` | ${exp.location}` : ''}</p>
                            <ul style="margin: 10px 0; padding-left: 20px;">
                                ${exp.bullets.map(b => `<li style="font-size: 13px; line-height: 1.5; margin-bottom: 5px;">${b.text}</li>`).join('')}
                            </ul>
                        </div>
                    `).join('')}
                </div>

                ${(cv.skills.primary.length || cv.skills.secondary.length) ? `
                <div style="margin-bottom: 20px;">
                    <h2 style="font-size: 18px; color: #1a1a2e; border-bottom: 2px solid #7c4dff; padding-bottom: 5px;">Skills</h2>
                    ${cv.skills.primary.length ? `<p style="font-size: 13px;"><strong>Core:</strong> ${cv.skills.primary.join(', ')}</p>` : ''}
                    ${cv.skills.secondary.length ? `<p style="font-size: 13px;"><strong>Additional:</strong> ${cv.skills.secondary.join(', ')}</p>` : ''}
                    ${cv.skills.tools.length ? `<p style="font-size: 13px;"><strong>Tools:</strong> ${cv.skills.tools.join(', ')}</p>` : ''}
                </div>
                ` : ''}

                ${cv.education.length ? `
                <div style="margin-bottom: 20px;">
                    <h2 style="font-size: 18px; color: #1a1a2e; border-bottom: 2px solid #7c4dff; padding-bottom: 5px;">Education</h2>
                    ${cv.education.map(edu => `
                        <p style="font-size: 14px; margin: 5px 0;">
                            <strong>${edu.degree} in ${edu.field}</strong>${edu.year ? ` (${edu.year})` : ''}<br/>
                            <span style="color: #666;">${edu.institution}</span>
                        </p>
                    `).join('')}
                </div>
                ` : ''}

                ${cv.certifications.length ? `
                <div style="margin-bottom: 20px;">
                    <h2 style="font-size: 18px; color: #1a1a2e; border-bottom: 2px solid #7c4dff; padding-bottom: 5px;">Certifications</h2>
                    ${cv.certifications.map(cert => `
                        <p style="font-size: 13px; margin: 5px 0;">${cert.name} - ${cert.issuer}${cert.date ? ` (${cert.date})` : ''}</p>
                    `).join('')}
                </div>
                ` : ''}

                ${coverLetter ? `
                <div style="page-break-before: always; padding-top: 20px;">
                    <h2 style="font-size: 20px; color: #1a1a2e; text-align: center; margin-bottom: 20px;">Cover Letter</h2>
                    <p style="font-size: 14px; line-height: 1.8; margin-bottom: 15px;">${coverLetter.hook}</p>
                    <p style="font-size: 14px; line-height: 1.8; margin-bottom: 15px;">${coverLetter.value_proposition}</p>
                    <p style="font-size: 14px; line-height: 1.8; margin-bottom: 15px;">${coverLetter.fit_narrative}</p>
                    <p style="font-size: 14px; line-height: 1.8;">${coverLetter.closing}</p>
                </div>
                ` : ''}
            </div>
        `;
        return html;
    };

    const handlePdfExport = async () => {
        setExporting('pdf');
        try {
            const html = generatePdfHtml();
            const container = document.createElement('div');
            container.innerHTML = html;
            document.body.appendChild(container);

            const opt = {
                margin: 10,
                filename: 'tailored_cv.pdf',
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { scale: 2, useCORS: true },
                jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' as const }
            };

            await html2pdf().set(opt).from(container).save();
            document.body.removeChild(container);
        } catch (error) {
            console.error('PDF export failed:', error);
            alert('PDF export failed. Please try again.');
        } finally {
            setExporting(null);
        }
    };

    const handleExport = async (format: 'markdown' | 'docx' | 'pdf') => {
        if (format === 'pdf') {
            return handlePdfExport();
        }

        setExporting(format);
        try {
            const blob = await exportResult(format, result);

            // Create download link
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `tailored_cv.${format === 'markdown' ? 'md' : format}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Export failed:', error);
            alert('Export failed. Please try again.');
        } finally {
            setExporting(null);
        }
    };

    const handleCopyMarkdown = async () => {
        const cv = result.tailored_cv;
        const coverLetter = result.cover_letter;

        let markdown = `# ${cv.header.name}\n`;
        markdown += `**${cv.header.title}**\n\n`;
        markdown += `${Object.values(cv.header.contact).join(' | ')}\n\n`;
        markdown += `## Summary\n${cv.summary}\n\n`;

        markdown += `## Experience\n`;
        for (const exp of cv.experience) {
            markdown += `### ${exp.title}\n`;
            markdown += `**${exp.company}** | ${exp.dates}\n\n`;
            for (const bullet of exp.bullets) {
                markdown += `- ${bullet.text}\n`;
            }
            markdown += '\n';
        }

        if (cv.skills.primary.length || cv.skills.secondary.length) {
            markdown += `## Skills\n`;
            if (cv.skills.primary.length) {
                markdown += `**Core:** ${cv.skills.primary.join(', ')}\n`;
            }
            if (cv.skills.secondary.length) {
                markdown += `**Additional:** ${cv.skills.secondary.join(', ')}\n`;
            }
            markdown += '\n';
        }

        if (cv.education.length) {
            markdown += `## Education\n`;
            for (const edu of cv.education) {
                markdown += `**${edu.degree} in ${edu.field}** ${edu.year ? `(${edu.year})` : ''}\n`;
                markdown += `${edu.institution}\n\n`;
            }
        }

        if (coverLetter) {
            markdown += `---\n\n# Cover Letter\n\n`;
            markdown += `${coverLetter.hook}\n\n`;
            markdown += `${coverLetter.value_proposition}\n\n`;
            markdown += `${coverLetter.fit_narrative}\n\n`;
            markdown += `${coverLetter.closing}\n`;
        }

        try {
            await navigator.clipboard.writeText(markdown);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (error) {
            console.error('Copy failed:', error);
        }
    };

    return (
        <Paper
            elevation={0}
            sx={{
                p: 3,
                background: 'linear-gradient(145deg, #1e1e2e 0%, #2a2a3e 100%)',
                borderRadius: 3,
                border: '1px solid rgba(255,255,255,0.1)',
            }}
        >
            <Typography variant="h6" sx={{ color: '#fff', fontWeight: 600, mb: 2 }}>
                📥 Export
            </Typography>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <ButtonGroup variant="contained" fullWidth>
                    <Button
                        startIcon={exporting === 'markdown' ? <CircularProgress size={16} /> : <ArticleIcon />}
                        onClick={() => handleExport('markdown')}
                        disabled={!!exporting}
                        sx={{
                            backgroundColor: 'rgba(124, 77, 255, 0.2)',
                            color: 'primary.main',
                            '&:hover': { backgroundColor: 'rgba(124, 77, 255, 0.3)' },
                        }}
                    >
                        Markdown
                    </Button>
                    <Button
                        startIcon={exporting === 'docx' ? <CircularProgress size={16} /> : <DescriptionIcon />}
                        onClick={() => handleExport('docx')}
                        disabled={!!exporting}
                        sx={{
                            backgroundColor: 'rgba(33, 150, 243, 0.2)',
                            color: '#2196f3',
                            '&:hover': { backgroundColor: 'rgba(33, 150, 243, 0.3)' },
                        }}
                    >
                        Word
                    </Button>
                    <Button
                        startIcon={exporting === 'pdf' ? <CircularProgress size={16} /> : <PictureAsPdfIcon />}
                        onClick={() => handleExport('pdf')}
                        disabled={!!exporting}
                        sx={{
                            backgroundColor: 'rgba(244, 67, 54, 0.2)',
                            color: '#f44336',
                            '&:hover': { backgroundColor: 'rgba(244, 67, 54, 0.3)' },
                        }}
                    >
                        PDF
                    </Button>
                </ButtonGroup>

                <Button
                    variant="outlined"
                    startIcon={<ContentCopyIcon />}
                    onClick={handleCopyMarkdown}
                    fullWidth
                    sx={{
                        color: copied ? 'success.main' : 'primary.main',
                        borderColor: copied ? 'success.main' : 'primary.main',
                    }}
                >
                    {copied ? '✓ Copied to Clipboard' : 'Copy as Markdown'}
                </Button>
            </Box>
        </Paper>
    );
}
