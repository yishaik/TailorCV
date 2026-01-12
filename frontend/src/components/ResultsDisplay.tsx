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
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningIcon from '@mui/icons-material/Warning';
import ErrorIcon from '@mui/icons-material/Error';
import WorkIcon from '@mui/icons-material/Work';
import SchoolIcon from '@mui/icons-material/School';
import StarIcon from '@mui/icons-material/Star';
import type { TailorResult } from '../types';

interface ResultsDisplayProps {
    result: TailorResult;
}

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

function CVPreview({ cv }: { cv: TailorResult['tailored_cv'] }) {
    return (
        <Box>
            {/* Header */}
            <Box sx={{ textAlign: 'center', mb: 4 }}>
                <Typography variant="h4" sx={{ color: '#fff', fontWeight: 700 }}>
                    {cv.header.name}
                </Typography>
                <Typography variant="h6" sx={{ color: 'primary.main', mb: 1 }}>
                    {cv.header.title}
                </Typography>
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
                <Typography sx={{ color: '#fff', lineHeight: 1.7 }}>{cv.summary}</Typography>
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

function CoverLetterPreview({ coverLetter }: { coverLetter: TailorResult['cover_letter'] }) {
    if (!coverLetter) {
        return (
            <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography sx={{ color: 'text.secondary' }}>
                    Cover letter was not generated
                </Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ maxWidth: 600, mx: 'auto' }}>
            <Typography sx={{ color: '#fff', mb: 3, lineHeight: 1.8 }}>{coverLetter.hook}</Typography>
            <Typography sx={{ color: '#fff', mb: 3, lineHeight: 1.8 }}>
                {coverLetter.value_proposition}
            </Typography>
            <Typography sx={{ color: '#fff', mb: 3, lineHeight: 1.8 }}>
                {coverLetter.fit_narrative}
            </Typography>
            <Typography sx={{ color: '#fff', lineHeight: 1.8 }}>{coverLetter.closing}</Typography>
        </Box>
    );
}

function AnalysisTab({ result }: { result: TailorResult }) {
    const mapping = result.mapping_summary;

    return (
        <Box>
            {/* Coverage Stats */}
            {mapping && (
                <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2, mb: 3 }}>
                    <Paper sx={{ p: 2, backgroundColor: 'rgba(0,0,0,0.2)' }}>
                        <Typography variant="subtitle2" sx={{ color: 'text.secondary' }}>
                            Must-Have Coverage
                        </Typography>
                        <Typography variant="h5" sx={{ color: '#fff', fontWeight: 600 }}>
                            {mapping.must_have_coverage}
                        </Typography>
                    </Paper>
                    <Paper sx={{ p: 2, backgroundColor: 'rgba(0,0,0,0.2)' }}>
                        <Typography variant="subtitle2" sx={{ color: 'text.secondary' }}>
                            Nice-to-Have Coverage
                        </Typography>
                        <Typography variant="h5" sx={{ color: '#fff', fontWeight: 600 }}>
                            {mapping.nice_to_have_coverage}
                        </Typography>
                    </Paper>
                </Box>
            )}

            {/* Keywords */}
            {mapping && (
                <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" sx={{ color: '#fff', mb: 2 }}>
                        Keyword Analysis
                    </Typography>

                    <Accordion sx={{ backgroundColor: 'rgba(0,0,0,0.2)' }}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon sx={{ color: '#fff' }} />}>
                            <CheckCircleIcon sx={{ color: 'success.main', mr: 1 }} />
                            <Typography sx={{ color: '#fff' }}>
                                Keywords Present ({mapping.keywords_present.length})
                            </Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                {mapping.keywords_present.map((kw) => (
                                    <Chip
                                        key={kw}
                                        label={kw}
                                        size="small"
                                        sx={{ backgroundColor: 'rgba(76, 175, 80, 0.2)', color: 'success.main' }}
                                    />
                                ))}
                            </Box>
                        </AccordionDetails>
                    </Accordion>

                    <Accordion sx={{ backgroundColor: 'rgba(0,0,0,0.2)' }}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon sx={{ color: '#fff' }} />}>
                            <WarningIcon sx={{ color: 'warning.main', mr: 1 }} />
                            <Typography sx={{ color: '#fff' }}>
                                Keywords Missing ({mapping.keywords_missing.length})
                            </Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                {mapping.keywords_missing.map((kw) => (
                                    <Chip
                                        key={kw}
                                        label={kw}
                                        size="small"
                                        sx={{ backgroundColor: 'rgba(255, 152, 0, 0.2)', color: 'warning.main' }}
                                    />
                                ))}
                            </Box>
                        </AccordionDetails>
                    </Accordion>
                </Box>
            )}

            {/* Strongest Matches */}
            {mapping?.strongest_matches.length ? (
                <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" sx={{ color: '#fff', mb: 2 }}>
                        <StarIcon sx={{ verticalAlign: 'middle', mr: 1, color: 'primary.main' }} />
                        Strongest Matches
                    </Typography>
                    <List>
                        {mapping.strongest_matches.map((match, i) => (
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

            {/* Critical Gaps */}
            {mapping?.critical_gaps.length ? (
                <Box>
                    <Typography variant="h6" sx={{ color: '#fff', mb: 2 }}>
                        <ErrorIcon sx={{ verticalAlign: 'middle', mr: 1, color: 'error.main' }} />
                        Critical Gaps
                    </Typography>
                    <List>
                        {mapping.critical_gaps.map((gap, i) => (
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
        </Box>
    );
}

export function ResultsDisplay({ result }: ResultsDisplayProps) {
    const [tabIndex, setTabIndex] = useState(0);

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
            <MatchScoreDisplay
                score={result.match_score.score}
                explanation={result.match_score.explanation}
            />

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
                <CVPreview cv={result.tailored_cv} />
            </TabPanel>

            <TabPanel value={tabIndex} index={1}>
                <CoverLetterPreview coverLetter={result.cover_letter} />
            </TabPanel>

            <TabPanel value={tabIndex} index={2}>
                <AnalysisTab result={result} />
            </TabPanel>

            <TabPanel value={tabIndex} index={3}>
                <ChangesTab changesLog={result.changes_log} borderlineItems={result.borderline_items} />
            </TabPanel>
        </Paper>
    );
}

function ChangesTab({
    changesLog,
    borderlineItems,
}: {
    changesLog: TailorResult['changes_log'];
    borderlineItems: TailorResult['borderline_items'];
}) {
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

            {changesLog.map((change, i) => (
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
                        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                            {change.justification}
                        </Typography>
                    </AccordionDetails>
                </Accordion>
            ))}
        </Box>
    );
}
