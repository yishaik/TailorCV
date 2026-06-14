import { useState } from 'react';
import {
    Box,
    Typography,
    Paper,
    Tabs,
    Tab,
    Chip,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    Divider,
    Button,
    TextField,
    Tooltip,
    Link,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningIcon from '@mui/icons-material/Warning';
import ErrorIcon from '@mui/icons-material/Error';
import WorkIcon from '@mui/icons-material/Work';
import SchoolIcon from '@mui/icons-material/School';
import StarIcon from '@mui/icons-material/Star';
import EditIcon from '@mui/icons-material/Edit';
import DoneIcon from '@mui/icons-material/Done';
import UndoIcon from '@mui/icons-material/Undo';
import ReplayIcon from '@mui/icons-material/Replay';
import EmailIcon from '@mui/icons-material/Email';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import type { TailorResult, ApplyTarget, MappingEntry } from '../types';

interface ResultsDisplayProps {
    result: TailorResult;
    onChange: (result: TailorResult) => void;
    applyTargets?: ApplyTarget[];
}

const editFieldSx = {
    mb: 1,
    '& .MuiInputBase-input, & .MuiInputBase-inputMultiline': { color: '#fff' },
    '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(124, 77, 255, 0.4)' },
    '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(124, 77, 255, 0.7)' },
};

function TabPanel({
    children,
    value,
    index,
}: {
    children: React.ReactNode;
    value: number;
    index: number;
}) {
    return (
        <div hidden={value !== index} style={{ padding: '16px 0' }}>
            {value === index && children}
        </div>
    );
}

function MatchScoreDisplay({ score, explanation }: { score: number; explanation: string }) {
    const getColor = (score: number) => {
        if (score >= 80) return '#4caf50';
        if (score >= 60) return '#ff9800';
        if (score >= 40) return '#f44336';
        return '#9e9e9e';
    };

    return (
        <Paper
            sx={{
                p: 3,
                mb: 3,
                background: `linear-gradient(145deg, ${getColor(score)}22 0%, #1e1e2e 100%)`,
                borderRadius: 3,
                border: `1px solid ${getColor(score)}44`,
            }}
        >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                <Box sx={{ position: 'relative', display: 'inline-flex' }}>
                    <Box
                        sx={{
                            width: 100,
                            height: 100,
                            borderRadius: '50%',
                            background: `conic-gradient(${getColor(score)} ${score * 3.6}deg, rgba(255,255,255,0.1) 0deg)`,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                        }}
                    >
                        <Box
                            sx={{
                                width: 80,
                                height: 80,
                                borderRadius: '50%',
                                backgroundColor: '#1e1e2e',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                            }}
                        >
                            <Typography variant="h4" sx={{ color: getColor(score), fontWeight: 700 }}>
                                {score}
                            </Typography>
                        </Box>
                    </Box>
                </Box>

                <Box sx={{ flex: 1 }}>
                    <Typography variant="h6" sx={{ color: '#fff', mb: 1 }}>
                        Match Score
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                        {explanation}
                    </Typography>
                </Box>
            </Box>
        </Paper>
    );
}

function ApplyBanner({ targets, applicantName, jobTitle }: {
    targets: ApplyTarget[];
    applicantName?: string;
    jobTitle?: string | null;
}) {
    if (!targets.length) return null;

    const buildHref = (t: ApplyTarget) => {
        if (t.type !== 'email') return t.href;
        const role = jobTitle?.trim();
        const subject = role
            ? `Application for ${role}${applicantName ? ` – ${applicantName}` : ''}`
            : 'Job application';
        return `mailto:${t.value}?subject=${encodeURIComponent(subject)}`;
    };

    return (
        <Paper
            sx={{
                p: 2,
                mb: 3,
                borderRadius: 3,
                background: 'linear-gradient(145deg, rgba(0, 188, 212, 0.15) 0%, #1e1e2e 100%)',
                border: '1px solid rgba(0, 188, 212, 0.35)',
            }}
        >
            <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1.5 }}>
                <Typography sx={{ color: '#fff', fontWeight: 600, mr: 1 }}>
                    Ready to apply?
                </Typography>
                {targets.map((t) => (
                    <Button
                        key={t.value}
                        component={Link}
                        href={buildHref(t)}
                        target={t.type === 'url' ? '_blank' : undefined}
                        rel={t.type === 'url' ? 'noopener noreferrer' : undefined}
                        variant="contained"
                        size="small"
                        startIcon={t.type === 'email' ? <EmailIcon /> : <OpenInNewIcon />}
                        sx={{
                            textTransform: 'none',
                            backgroundColor: 'rgba(0, 188, 212, 0.25)',
                            color: '#4dd0e1',
                            '&:hover': { backgroundColor: 'rgba(0, 188, 212, 0.4)' },
                        }}
                    >
                        {t.type === 'email' ? `Email ${t.label}` : `Apply at ${t.label}`}
                    </Button>
                ))}
            </Box>
        </Paper>
    );
}

function CVPreview({
    cv,
    editing,
    onField,
    onBullet,
}: {
    cv: TailorResult['tailored_cv'];
    editing: boolean;
    onField: (field: 'name' | 'title' | 'summary', value: string) => void;
    onBullet: (expIndex: number, bulletIndex: number, value: string) => void;
}) {
    return (
        <Box>
            {/* Header */}
            <Box sx={{ textAlign: 'center', mb: 4 }}>
                {editing ? (
                    <Box sx={{ maxWidth: 480, mx: 'auto' }}>
                        <TextField
                            value={cv.header.name}
                            onChange={(e) => onField('name', e.target.value)}
                            fullWidth
                            size="small"
                            label="Name"
                            sx={editFieldSx}
                        />
                        <TextField
                            value={cv.header.title}
                            onChange={(e) => onField('title', e.target.value)}
                            fullWidth
                            size="small"
                            label="Title"
                            sx={editFieldSx}
                        />
                    </Box>
                ) : (
                    <>
                        <Typography variant="h4" sx={{ color: '#fff', fontWeight: 700 }}>
                            {cv.header.name}
                        </Typography>
                        <Typography variant="h6" sx={{ color: 'primary.main', mb: 1 }}>
                            {cv.header.title}
                        </Typography>
                    </>
                )}
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    {Object.values(cv.header.contact).join(' | ')}
                </Typography>
            </Box>

            <Divider sx={{ borderColor: 'rgba(255,255,255,0.1)', mb: 3 }} />

            {/* Summary */}
            <Box sx={{ mb: 4 }}>
                <Typography variant="h6" sx={{ color: 'primary.main', mb: 1 }}>
                    Summary
                </Typography>
                {editing ? (
                    <TextField
                        value={cv.summary}
                        onChange={(e) => onField('summary', e.target.value)}
                        fullWidth
                        multiline
                        minRows={2}
                        sx={editFieldSx}
                    />
                ) : (
                    <Typography sx={{ color: '#fff', lineHeight: 1.7 }}>{cv.summary}</Typography>
                )}
            </Box>

            {/* Experience */}
            <Box sx={{ mb: 4 }}>
                <Typography variant="h6" sx={{ color: 'primary.main', mb: 2 }}>
                    Experience
                </Typography>
                {cv.experience.map((exp, i) => (
                    <Box key={i} sx={{ mb: 3 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                            <WorkIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
                            <Typography sx={{ color: '#fff', fontWeight: 600 }}>{exp.title}</Typography>
                        </Box>
                        <Typography variant="body2" sx={{ color: 'text.secondary', mb: 1 }}>
                            {exp.company} | {exp.dates}
                        </Typography>
                        {editing ? (
                            <Box sx={{ pl: 1 }}>
                                {exp.bullets.map((bullet, j) => (
                                    <TextField
                                        key={j}
                                        value={bullet.text}
                                        onChange={(e) => onBullet(i, j, e.target.value)}
                                        fullWidth
                                        multiline
                                        size="small"
                                        sx={editFieldSx}
                                    />
                                ))}
                            </Box>
                        ) : (
                            <List dense>
                                {exp.bullets.map((bullet, j) => (
                                    <ListItem key={j} sx={{ pl: 0 }}>
                                        <ListItemIcon sx={{ minWidth: 24 }}>
                                            <Box
                                                sx={{
                                                    width: 6,
                                                    height: 6,
                                                    borderRadius: '50%',
                                                    backgroundColor: 'primary.main',
                                                }}
                                            />
                                        </ListItemIcon>
                                        <ListItemText
                                            primary={bullet.text}
                                            sx={{ '& .MuiListItemText-primary': { color: '#fff' } }}
                                        />
                                    </ListItem>
                                ))}
                            </List>
                        )}
                        {exp.bullets.some((b) => b.keywords_used.length > 0) && (
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                                {[...new Set(exp.bullets.flatMap((b) => b.keywords_used))].map((kw) => (
                                    <Chip
                                        key={kw}
                                        label={kw}
                                        size="small"
                                        sx={{
                                            backgroundColor: 'rgba(124, 77, 255, 0.2)',
                                            color: 'primary.main',
                                            fontSize: 10,
                                        }}
                                    />
                                ))}
                            </Box>
                        )}
                    </Box>
                ))}
            </Box>

            {/* Skills */}
            <Box sx={{ mb: 4 }}>
                <Typography variant="h6" sx={{ color: 'primary.main', mb: 2 }}>
                    Skills
                </Typography>
                {cv.skills.primary.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" sx={{ color: '#fff', mb: 1 }}>
                            Core
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                            {cv.skills.primary.map((skill) => (
                                <Chip
                                    key={skill}
                                    label={skill}
                                    sx={{
                                        backgroundColor: 'rgba(76, 175, 80, 0.2)',
                                        color: 'success.main',
                                    }}
                                />
                            ))}
                        </Box>
                    </Box>
                )}
                {cv.skills.secondary.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" sx={{ color: '#fff', mb: 1 }}>
                            Additional
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                            {cv.skills.secondary.map((skill) => (
                                <Chip
                                    key={skill}
                                    label={skill}
                                    variant="outlined"
                                    sx={{
                                        borderColor: 'rgba(255,255,255,0.3)',
                                        color: '#fff',
                                    }}
                                />
                            ))}
                        </Box>
                    </Box>
                )}
            </Box>

            {/* Education */}
            {cv.education.length > 0 && (
                <Box sx={{ mb: 4 }}>
                    <Typography variant="h6" sx={{ color: 'primary.main', mb: 2 }}>
                        Education
                    </Typography>
                    {cv.education.map((edu, i) => (
                        <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                            <SchoolIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
                            <Box>
                                <Typography sx={{ color: '#fff' }}>
                                    {edu.degree} in {edu.field}
                                </Typography>
                                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                                    {edu.institution} {edu.year && `(${edu.year})`}
                                </Typography>
                            </Box>
                        </Box>
                    ))}
                </Box>
            )}
        </Box>
    );
}

function CoverLetterPreview({
    coverLetter,
    editing,
    onField,
}: {
    coverLetter: TailorResult['cover_letter'];
    editing: boolean;
    onField: (field: 'hook' | 'value_proposition' | 'fit_narrative' | 'closing', value: string) => void;
}) {
    if (!coverLetter) {
        return (
            <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography sx={{ color: 'text.secondary' }}>
                    Cover letter was not generated
                </Typography>
            </Box>
        );
    }

    const fields: Array<['hook' | 'value_proposition' | 'fit_narrative' | 'closing', string]> = [
        ['hook', coverLetter.hook],
        ['value_proposition', coverLetter.value_proposition],
        ['fit_narrative', coverLetter.fit_narrative],
        ['closing', coverLetter.closing],
    ];

    return (
        <Box sx={{ maxWidth: 600, mx: 'auto' }}>
            {fields.map(([field, value]) =>
                editing ? (
                    <TextField
                        key={field}
                        value={value}
                        onChange={(e) => onField(field, e.target.value)}
                        fullWidth
                        multiline
                        minRows={2}
                        sx={{ ...editFieldSx, mb: 2 }}
                    />
                ) : (
                    <Typography key={field} sx={{ color: '#fff', mb: 3, lineHeight: 1.8 }}>
                        {value}
                    </Typography>
                )
            )}
        </Box>
    );
}

// ---------------------------------------------------------------------------
// Analysis tab — "what is missing and from where"
// ---------------------------------------------------------------------------

const PRIORITY_LABEL: Record<string, string> = {
    must_have: 'Must-have',
    nice_to_have: 'Nice-to-have',
    inferred: 'Inferred',
};

const SEVERITY_COLOR: Record<string, 'error' | 'warning' | 'info' | 'success'> = {
    critical: 'error',
    moderate: 'warning',
    minor: 'info',
    none: 'success',
};

const MATCH_TYPE_LABEL: Record<string, string> = {
    direct: 'Direct match',
    transferable: 'Transferable',
    partial: 'Partial',
    learning: 'Learning',
};

function RequirementMet({ entry }: { entry: MappingEntry }) {
    return (
        <Paper sx={{ p: 2, mb: 1.5, backgroundColor: 'rgba(76, 175, 80, 0.08)', border: '1px solid rgba(76, 175, 80, 0.25)' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1, flexWrap: 'wrap' }}>
                <CheckCircleIcon sx={{ color: 'success.main', fontSize: 20 }} />
                <Typography sx={{ color: '#fff', fontWeight: 600, flex: 1, minWidth: 200 }}>
                    {entry.requirement.text}
                </Typography>
                <Chip label={PRIORITY_LABEL[entry.requirement.priority] ?? entry.requirement.priority} size="small" variant="outlined" />
            </Box>
            {entry.evidence.length > 0 ? (
                <Box sx={{ pl: 3.5 }}>
                    <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                        Backed by your CV:
                    </Typography>
                    {entry.evidence.slice(0, 3).map((ev, i) => (
                        <Box key={i} sx={{ display: 'flex', gap: 1, alignItems: 'flex-start', mt: 0.5 }}>
                            <Chip
                                label={`${MATCH_TYPE_LABEL[ev.match_type] ?? ev.match_type} · ${ev.relevance_score}%`}
                                size="small"
                                sx={{ backgroundColor: 'rgba(76, 175, 80, 0.2)', color: 'success.main', height: 20 }}
                            />
                            <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.85)' }}>
                                {ev.original_text} <Box component="span" sx={{ color: 'text.secondary' }}>({ev.source_type})</Box>
                            </Typography>
                        </Box>
                    ))}
                </Box>
            ) : (
                <Typography variant="body2" sx={{ color: 'text.secondary', pl: 3.5 }}>
                    Covered by your profile.
                </Typography>
            )}
        </Paper>
    );
}

function RequirementGap({ entry }: { entry: MappingEntry }) {
    const severity = entry.gap_analysis.gap_severity;
    return (
        <Paper sx={{ p: 2, mb: 1.5, backgroundColor: 'rgba(244, 67, 54, 0.07)', border: '1px solid rgba(244, 67, 54, 0.25)' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1, flexWrap: 'wrap' }}>
                <ErrorIcon sx={{ color: SEVERITY_COLOR[severity] === 'error' ? 'error.main' : 'warning.main', fontSize: 20 }} />
                <Typography sx={{ color: '#fff', fontWeight: 600, flex: 1, minWidth: 200 }}>
                    {entry.requirement.text}
                </Typography>
                <Chip label={PRIORITY_LABEL[entry.requirement.priority] ?? entry.requirement.priority} size="small" variant="outlined" />
                <Chip label={`${severity} gap`} size="small" color={SEVERITY_COLOR[severity] ?? 'warning'} />
            </Box>
            <Box sx={{ pl: 3.5 }}>
                {entry.evidence.length > 0 && (
                    <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)', mb: 1 }}>
                        Closest evidence: {entry.evidence[0].original_text}{' '}
                        <Box component="span" sx={{ color: 'text.secondary' }}>
                            ({entry.evidence[0].source_type}, {entry.evidence[0].relevance_score}%)
                        </Box>
                    </Typography>
                )}
                {entry.gap_analysis.mitigation_options.length > 0 ? (
                    <>
                        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                            How to address it:
                        </Typography>
                        <List dense sx={{ py: 0 }}>
                            {entry.gap_analysis.mitigation_options.map((opt, i) => (
                                <ListItem key={i} sx={{ pl: 0, alignItems: 'flex-start' }}>
                                    <ListItemIcon sx={{ minWidth: 26, mt: 0.5 }}>
                                        <StarIcon sx={{ color: 'warning.main', fontSize: 16 }} />
                                    </ListItemIcon>
                                    <ListItemText
                                        primary={opt.suggestion}
                                        sx={{ '& .MuiListItemText-primary': { color: '#fff', fontSize: 14 } }}
                                    />
                                </ListItem>
                            ))}
                        </List>
                    </>
                ) : (
                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                        No direct evidence found in your CV for this requirement.
                    </Typography>
                )}
            </Box>
        </Paper>
    );
}

function KeywordGroup({ title, icon, color, keywords }: {
    title: string;
    icon: React.ReactNode;
    color: string;
    keywords: string[];
}) {
    return (
        <Accordion sx={{ backgroundColor: 'rgba(0,0,0,0.2)' }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon sx={{ color: '#fff' }} />}>
                {icon}
                <Typography sx={{ color: '#fff', ml: 1 }}>
                    {title} ({keywords.length})
                </Typography>
            </AccordionSummary>
            <AccordionDetails>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {keywords.length ? (
                        keywords.map((kw) => (
                            <Chip key={kw} label={kw} size="small" sx={{ backgroundColor: `${color}33`, color }} />
                        ))
                    ) : (
                        <Typography variant="body2" sx={{ color: 'text.secondary' }}>None</Typography>
                    )}
                </Box>
            </AccordionDetails>
        </Accordion>
    );
}

function AnalysisTab({ result }: { result: TailorResult }) {
    const detail = result.mapping_detail;
    const summary = result.mapping_summary;

    const met = detail?.mapping_table.filter((e) => !e.gap_analysis.has_gap) ?? [];
    const gaps = detail?.mapping_table.filter((e) => e.gap_analysis.has_gap) ?? [];
    // Show the most severe gaps first.
    const severityRank: Record<string, number> = { critical: 0, moderate: 1, minor: 2, none: 3 };
    gaps.sort((a, b) => (severityRank[a.gap_analysis.gap_severity] ?? 9) - (severityRank[b.gap_analysis.gap_severity] ?? 9));

    return (
        <Box>
            {/* Coverage Stats */}
            {summary && (
                <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2, mb: 3 }}>
                    <Paper sx={{ p: 2, backgroundColor: 'rgba(0,0,0,0.2)' }}>
                        <Typography variant="subtitle2" sx={{ color: 'text.secondary' }}>
                            Must-Have Coverage
                        </Typography>
                        <Typography variant="h5" sx={{ color: '#fff', fontWeight: 600 }}>
                            {summary.must_have_coverage}
                        </Typography>
                    </Paper>
                    <Paper sx={{ p: 2, backgroundColor: 'rgba(0,0,0,0.2)' }}>
                        <Typography variant="subtitle2" sx={{ color: 'text.secondary' }}>
                            Nice-to-Have Coverage
                        </Typography>
                        <Typography variant="h5" sx={{ color: '#fff', fontWeight: 600 }}>
                            {summary.nice_to_have_coverage}
                        </Typography>
                    </Paper>
                </Box>
            )}

            {/* Per-requirement breakdown (detailed) */}
            {detail ? (
                <>
                    {gaps.length > 0 && (
                        <Box sx={{ mb: 3 }}>
                            <Typography variant="h6" sx={{ color: '#fff', mb: 2 }}>
                                <ErrorIcon sx={{ verticalAlign: 'middle', mr: 1, color: 'error.main' }} />
                                What's Missing & How to Address It ({gaps.length})
                            </Typography>
                            {gaps.map((entry, i) => (
                                <RequirementGap key={i} entry={entry} />
                            ))}
                        </Box>
                    )}

                    {met.length > 0 && (
                        <Box sx={{ mb: 3 }}>
                            <Typography variant="h6" sx={{ color: '#fff', mb: 2 }}>
                                <CheckCircleIcon sx={{ verticalAlign: 'middle', mr: 1, color: 'success.main' }} />
                                Requirements You Meet ({met.length})
                            </Typography>
                            {met.map((entry, i) => (
                                <RequirementMet key={i} entry={entry} />
                            ))}
                        </Box>
                    )}
                </>
            ) : (
                // Fallback for payloads without full mapping detail.
                <>
                    {summary?.strongest_matches.length ? (
                        <Box sx={{ mb: 3 }}>
                            <Typography variant="h6" sx={{ color: '#fff', mb: 2 }}>
                                <StarIcon sx={{ verticalAlign: 'middle', mr: 1, color: 'primary.main' }} />
                                Strongest Matches
                            </Typography>
                            <List>
                                {summary.strongest_matches.map((match, i) => (
                                    <ListItem key={i}>
                                        <ListItemIcon>
                                            <CheckCircleIcon sx={{ color: 'success.main' }} />
                                        </ListItemIcon>
                                        <ListItemText primary={match} sx={{ '& .MuiListItemText-primary': { color: '#fff' } }} />
                                    </ListItem>
                                ))}
                            </List>
                        </Box>
                    ) : null}

                    {summary?.critical_gaps.length ? (
                        <Box sx={{ mb: 3 }}>
                            <Typography variant="h6" sx={{ color: '#fff', mb: 2 }}>
                                <ErrorIcon sx={{ verticalAlign: 'middle', mr: 1, color: 'error.main' }} />
                                Critical Gaps
                            </Typography>
                            <List>
                                {summary.critical_gaps.map((gap, i) => (
                                    <ListItem key={i}>
                                        <ListItemIcon>
                                            <ErrorIcon sx={{ color: 'error.main' }} />
                                        </ListItemIcon>
                                        <ListItemText primary={gap} sx={{ '& .MuiListItemText-primary': { color: '#fff' } }} />
                                    </ListItem>
                                ))}
                            </List>
                        </Box>
                    ) : null}
                </>
            )}

            {/* Keyword analysis */}
            {(detail || summary) && (
                <Box>
                    <Typography variant="h6" sx={{ color: '#fff', mb: 2 }}>
                        ATS Keyword Coverage
                    </Typography>
                    <KeywordGroup
                        title="Present in your CV"
                        icon={<CheckCircleIcon sx={{ color: 'success.main' }} />}
                        color="#4caf50"
                        keywords={detail?.keyword_coverage.present_in_cv ?? summary?.keywords_present ?? []}
                    />
                    {detail && (
                        <KeywordGroup
                            title="Addable from your experience"
                            icon={<StarIcon sx={{ color: 'primary.main' }} />}
                            color="#7c4dff"
                            keywords={detail.keyword_coverage.missing_but_addressable}
                        />
                    )}
                    <KeywordGroup
                        title="Genuinely missing"
                        icon={<WarningIcon sx={{ color: 'warning.main' }} />}
                        color="#ff9800"
                        keywords={detail?.keyword_coverage.genuinely_missing ?? summary?.keywords_missing ?? []}
                    />
                </Box>
            )}
        </Box>
    );
}

// ---------------------------------------------------------------------------
// Changes tab — with per-change revert
// ---------------------------------------------------------------------------

/** Collect every editable free-text string currently in the CV. */
function currentCvTexts(cv: TailorResult['tailored_cv']): string[] {
    const texts = [cv.summary];
    for (const exp of cv.experience) {
        for (const b of exp.bullets) texts.push(b.text);
    }
    return texts;
}

/** Replace the first exact occurrence of `from` with `to` across summary/bullets. */
function replaceCvText(result: TailorResult, from: string, to: string): TailorResult | null {
    const cv = result.tailored_cv;
    if (cv.summary === from) {
        return { ...result, tailored_cv: { ...cv, summary: to } };
    }
    for (let i = 0; i < cv.experience.length; i++) {
        const exp = cv.experience[i];
        for (let j = 0; j < exp.bullets.length; j++) {
            if (exp.bullets[j].text === from) {
                const experience = cv.experience.map((e, ei) =>
                    ei !== i
                        ? e
                        : {
                              ...e,
                              bullets: e.bullets.map((b, bj) =>
                                  bj !== j ? b : { ...b, text: to }
                              ),
                          }
                );
                return { ...result, tailored_cv: { ...cv, experience } };
            }
        }
    }
    return null;
}

function ChangesTab({
    result,
    onChange,
}: {
    result: TailorResult;
    onChange: (result: TailorResult) => void;
}) {
    const { changes_log: changesLog, borderline_items: borderlineItems } = result;
    const texts = new Set(currentCvTexts(result.tailored_cv));

    return (
        <Box>
            {borderlineItems.length > 0 && (
                <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" sx={{ color: 'warning.main', mb: 2 }}>
                        ⚠️ Items Requiring Review ({borderlineItems.length})
                    </Typography>
                    {borderlineItems.map((item, i) => (
                        <Paper key={i} sx={{ p: 2, mb: 2, backgroundColor: 'rgba(255, 152, 0, 0.1)' }}>
                            <Typography sx={{ color: '#fff', mb: 1 }}>{item.content}</Typography>
                            <Typography variant="body2" sx={{ color: 'text.secondary', mb: 1 }}>
                                Original: {item.original_evidence}
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                                <Chip
                                    label={item.risk_level}
                                    size="small"
                                    color={
                                        item.risk_level === 'high' ? 'error' : item.risk_level === 'medium' ? 'warning' : 'success'
                                    }
                                />
                                <Chip label={item.category.replace(/_/g, ' ')} size="small" variant="outlined" />
                            </Box>
                        </Paper>
                    ))}
                </Box>
            )}

            <Typography variant="h6" sx={{ color: '#fff', mb: 2 }}>
                All Changes ({changesLog.length})
            </Typography>

            {changesLog.map((change, i) => {
                const hasOriginal = !!change.original;
                const newPresent = texts.has(change.new);
                const originalPresent = hasOriginal && texts.has(change.original as string);
                const canRevert = hasOriginal && newPresent;
                const canReapply = hasOriginal && !newPresent && originalPresent;

                return (
                    <Accordion key={i} sx={{ backgroundColor: 'rgba(0,0,0,0.2)', mb: 1 }}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon sx={{ color: '#fff' }} />}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                                <Chip
                                    label={change.change_type}
                                    size="small"
                                    sx={{
                                        backgroundColor:
                                            change.change_type === 'rewrite'
                                                ? 'rgba(255, 152, 0, 0.2)'
                                                : 'rgba(76, 175, 80, 0.2)',
                                        color: change.change_type === 'rewrite' ? 'warning.main' : 'success.main',
                                    }}
                                />
                                <Typography sx={{ color: 'text.secondary', flex: 1 }}>{change.section}</Typography>
                                {canReapply && (
                                    <Chip label="Reverted" size="small" variant="outlined" sx={{ height: 20, color: 'text.secondary' }} />
                                )}
                                {change.requires_review && (
                                    <Chip label="Review" size="small" color="warning" sx={{ height: 20 }} />
                                )}
                            </Box>
                        </AccordionSummary>
                        <AccordionDetails>
                            {change.original && (
                                <Box sx={{ mb: 2 }}>
                                    <Typography variant="subtitle2" sx={{ color: 'error.main' }}>
                                        Original:
                                    </Typography>
                                    <Typography variant="body2" sx={{ color: '#fff' }}>
                                        {change.original}
                                    </Typography>
                                </Box>
                            )}
                            <Box sx={{ mb: 2 }}>
                                <Typography variant="subtitle2" sx={{ color: 'success.main' }}>
                                    New:
                                </Typography>
                                <Typography variant="body2" sx={{ color: '#fff' }}>
                                    {change.new}
                                </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                                <Typography variant="caption" sx={{ color: 'text.secondary', flex: 1 }}>
                                    {change.justification}
                                </Typography>
                                {canRevert && (
                                    <Tooltip title="Restore the original wording in the CV">
                                        <Button
                                            size="small"
                                            startIcon={<UndoIcon />}
                                            onClick={() => {
                                                const updated = replaceCvText(result, change.new, change.original as string);
                                                if (updated) onChange(updated);
                                            }}
                                            sx={{ color: 'warning.main', textTransform: 'none' }}
                                        >
                                            Revert
                                        </Button>
                                    </Tooltip>
                                )}
                                {canReapply && (
                                    <Tooltip title="Re-apply the AI's tailored wording">
                                        <Button
                                            size="small"
                                            startIcon={<ReplayIcon />}
                                            onClick={() => {
                                                const updated = replaceCvText(result, change.original as string, change.new);
                                                if (updated) onChange(updated);
                                            }}
                                            sx={{ color: 'primary.main', textTransform: 'none' }}
                                        >
                                            Re-apply
                                        </Button>
                                    </Tooltip>
                                )}
                            </Box>
                        </AccordionDetails>
                    </Accordion>
                );
            })}
            {changesLog.every((c) => !c.original) && (
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                    Tip: changes that rewrote specific text can be reverted individually here.
                </Typography>
            )}
        </Box>
    );
}

export function ResultsDisplay({ result, onChange, applyTargets = [] }: ResultsDisplayProps) {
    const [tabIndex, setTabIndex] = useState(0);
    const [editing, setEditing] = useState(false);

    const updateField = (field: 'name' | 'title' | 'summary', value: string) => {
        const cv = result.tailored_cv;
        if (field === 'summary') {
            onChange({ ...result, tailored_cv: { ...cv, summary: value } });
        } else {
            onChange({
                ...result,
                tailored_cv: { ...cv, header: { ...cv.header, [field]: value } },
            });
        }
    };

    const updateBullet = (expIndex: number, bulletIndex: number, value: string) => {
        const cv = result.tailored_cv;
        const experience = cv.experience.map((e, ei) =>
            ei !== expIndex
                ? e
                : {
                      ...e,
                      bullets: e.bullets.map((b, bi) =>
                          bi !== bulletIndex ? b : { ...b, text: value }
                      ),
                  }
        );
        onChange({ ...result, tailored_cv: { ...cv, experience } });
    };

    const updateCoverLetter = (
        field: 'hook' | 'value_proposition' | 'fit_narrative' | 'closing',
        value: string
    ) => {
        if (!result.cover_letter) return;
        onChange({ ...result, cover_letter: { ...result.cover_letter, [field]: value } });
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
            <ApplyBanner
                targets={applyTargets}
                applicantName={result.tailored_cv.header.name}
                jobTitle={result.job_title}
            />

            <MatchScoreDisplay
                score={result.match_score.score}
                explanation={result.match_score.explanation}
            />

            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 1 }}>
                <Button
                    size="small"
                    variant={editing ? 'contained' : 'outlined'}
                    startIcon={editing ? <DoneIcon /> : <EditIcon />}
                    onClick={() => setEditing((e) => !e)}
                    sx={{
                        textTransform: 'none',
                        color: editing ? '#fff' : 'primary.main',
                        borderColor: 'primary.main',
                        ...(editing && { backgroundColor: 'primary.main' }),
                    }}
                >
                    {editing ? 'Done editing' : 'Edit text'}
                </Button>
            </Box>

            <Tabs
                value={tabIndex}
                onChange={(_, v) => setTabIndex(v)}
                sx={{
                    borderBottom: '1px solid rgba(255,255,255,0.1)',
                    '& .MuiTab-root': { color: 'rgba(255,255,255,0.7)' },
                    '& .Mui-selected': { color: 'primary.main' },
                }}
            >
                <Tab label="Tailored CV" />
                <Tab label="Cover Letter" />
                <Tab label="Analysis" />
                <Tab
                    label={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            Changes
                            {result.changes_log.filter((c) => c.requires_review).length > 0 && (
                                <Chip
                                    label={result.changes_log.filter((c) => c.requires_review).length}
                                    size="small"
                                    color="warning"
                                    sx={{ height: 20 }}
                                />
                            )}
                        </Box>
                    }
                />
            </Tabs>

            <TabPanel value={tabIndex} index={0}>
                <CVPreview
                    cv={result.tailored_cv}
                    editing={editing}
                    onField={updateField}
                    onBullet={updateBullet}
                />
            </TabPanel>

            <TabPanel value={tabIndex} index={1}>
                <CoverLetterPreview
                    coverLetter={result.cover_letter}
                    editing={editing}
                    onField={updateCoverLetter}
                />
            </TabPanel>

            <TabPanel value={tabIndex} index={2}>
                <AnalysisTab result={result} />
            </TabPanel>

            <TabPanel value={tabIndex} index={3}>
                <ChangesTab result={result} onChange={onChange} />
            </TabPanel>
        </Paper>
    );
}
