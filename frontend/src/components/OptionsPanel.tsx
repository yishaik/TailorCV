import {
    Box,
    Typography,
    Paper,
    FormControlLabel,
    Switch,
    ToggleButtonGroup,
    ToggleButton,
    Tooltip,
    TextField,
} from '@mui/material';
import ShieldIcon from '@mui/icons-material/Shield';
import BalanceIcon from '@mui/icons-material/Balance';
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch';
import NotesIcon from '@mui/icons-material/Notes';
import type { StrictnessLevel, OutputFormat } from '../types';

interface OptionsPanelProps {
    generateCoverLetter: boolean;
    onGenerateCoverLetterChange: (value: boolean) => void;
    strictnessLevel: StrictnessLevel;
    onStrictnessChange: (value: StrictnessLevel) => void;
    outputFormat: OutputFormat;
    onOutputFormatChange: (value: OutputFormat) => void;
    userNotes: string;
    onUserNotesChange: (value: string) => void;
    disabled?: boolean;
}

const strictnessDescriptions = {
    conservative: 'Safest option. Minimal reframing, only evidenced keywords, acknowledges gaps honestly.',
    moderate: 'Balanced approach. Natural keyword integration, allows skill inference with evidence.',
    aggressive: 'Maximum ATS optimization. Extensive reframing, creative gap positioning.',
};

export function OptionsPanel({
    generateCoverLetter,
    onGenerateCoverLetterChange,
    strictnessLevel,
    onStrictnessChange,
    outputFormat,
    onOutputFormatChange,
    userNotes,
    onUserNotesChange,
    disabled = false,
}: OptionsPanelProps) {
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
            <Typography variant="h6" sx={{ color: '#fff', fontWeight: 600, mb: 3 }}>
                ⚙️ Options
            </Typography>

            {/* Cover Letter Toggle */}
            <Box sx={{ mb: 3 }}>
                <FormControlLabel
                    control={
                        <Switch
                            checked={generateCoverLetter}
                            onChange={(e) => onGenerateCoverLetterChange(e.target.checked)}
                            disabled={disabled}
                            sx={{
                                '& .MuiSwitch-switchBase.Mui-checked': {
                                    color: 'primary.main',
                                },
                                '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                                    backgroundColor: 'primary.main',
                                },
                            }}
                        />
                    }
                    label={
                        <Box>
                            <Typography sx={{ color: '#fff' }}>Generate Cover Letter</Typography>
                            <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                                Create a tailored cover letter to complement your CV
                            </Typography>
                        </Box>
                    }
                />
            </Box>

            {/* Strictness Level */}
            <Box sx={{ mb: 3 }}>
                <Typography sx={{ color: '#fff', mb: 1, fontWeight: 500 }}>
                    Tailoring Approach
                </Typography>
                <ToggleButtonGroup
                    value={strictnessLevel}
                    exclusive
                    onChange={(_, value) => value && onStrictnessChange(value)}
                    disabled={disabled}
                    fullWidth
                    sx={{
                        '& .MuiToggleButton-root': {
                            color: 'rgba(255,255,255,0.7)',
                            borderColor: 'rgba(255,255,255,0.2)',
                            py: 1.5,
                            '&.Mui-selected': {
                                backgroundColor: 'rgba(124, 77, 255, 0.2)',
                                color: 'primary.main',
                                borderColor: 'primary.main',
                            },
                        },
                    }}
                >
                    <Tooltip title={strictnessDescriptions.conservative} arrow>
                        <ToggleButton value="conservative">
                            <ShieldIcon sx={{ mr: 1 }} />
                            Conservative
                        </ToggleButton>
                    </Tooltip>
                    <Tooltip title={strictnessDescriptions.moderate} arrow>
                        <ToggleButton value="moderate">
                            <BalanceIcon sx={{ mr: 1 }} />
                            Moderate
                        </ToggleButton>
                    </Tooltip>
                    <Tooltip title={strictnessDescriptions.aggressive} arrow>
                        <ToggleButton value="aggressive">
                            <RocketLaunchIcon sx={{ mr: 1 }} />
                            Aggressive
                        </ToggleButton>
                    </Tooltip>
                </ToggleButtonGroup>
                <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mt: 1 }}>
                    {strictnessDescriptions[strictnessLevel]}
                </Typography>
            </Box>

            {/* Output Format */}
            <Box sx={{ mb: 3 }}>
                <Typography sx={{ color: '#fff', mb: 1, fontWeight: 500 }}>
                    Export Format
                </Typography>
                <ToggleButtonGroup
                    value={outputFormat}
                    exclusive
                    onChange={(_, value) => value && onOutputFormatChange(value)}
                    disabled={disabled}
                    sx={{
                        '& .MuiToggleButton-root': {
                            color: 'rgba(255,255,255,0.7)',
                            borderColor: 'rgba(255,255,255,0.2)',
                            px: 3,
                            '&.Mui-selected': {
                                backgroundColor: 'rgba(124, 77, 255, 0.2)',
                                color: 'primary.main',
                                borderColor: 'primary.main',
                            },
                        },
                    }}
                >
                    <ToggleButton value="markdown">Markdown</ToggleButton>
                    <ToggleButton value="docx">Word</ToggleButton>
                    <ToggleButton value="pdf">PDF</ToggleButton>
                </ToggleButtonGroup>
            </Box>

            {/* User Notes */}
            <Box>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <NotesIcon sx={{ color: 'primary.main', mr: 1, fontSize: 20 }} />
                    <Typography sx={{ color: '#fff', fontWeight: 500 }}>
                        Additional Notes (Optional)
                    </Typography>
                </Box>
                <TextField
                    multiline
                    rows={4}
                    value={userNotes}
                    onChange={(e) => onUserNotesChange(e.target.value)}
                    placeholder="Add any specific instructions, preferences, or context you'd like the AI to consider when tailoring your CV and cover letter. For example:&#10;&#10;- Emphasize my leadership experience&#10;- Highlight my Python skills over Java&#10;- I'm transitioning from marketing to product management"
                    disabled={disabled}
                    fullWidth
                    sx={{
                        '& .MuiOutlinedInput-root': {
                            color: '#fff',
                            backgroundColor: 'rgba(0,0,0,0.2)',
                            '& fieldset': {
                                borderColor: 'rgba(255,255,255,0.2)',
                            },
                            '&:hover fieldset': {
                                borderColor: 'rgba(255,255,255,0.3)',
                            },
                            '&.Mui-focused fieldset': {
                                borderColor: 'primary.main',
                            },
                        },
                        '& .MuiInputBase-input::placeholder': {
                            color: 'rgba(255,255,255,0.5)',
                            opacity: 1,
                        },
                    }}
                />
                <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mt: 1 }}>
                    These notes will guide the AI when rewriting your CV summary and cover letter.
                </Typography>
            </Box>
        </Paper>
    );
}
