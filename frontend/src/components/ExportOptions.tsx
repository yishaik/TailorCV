import React from 'react';
import {
    Box,
    Button,
    ButtonGroup,
    Paper,
    Typography,
    CircularProgress,
} from '@mui/material';

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

    const handleExport = async (format: 'markdown' | 'docx' | 'pdf') => {
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
