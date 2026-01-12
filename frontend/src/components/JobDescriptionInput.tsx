import { useState, useCallback } from 'react';
import {
    Box,
    TextField,
    Typography,
    Paper,
    Tooltip,
} from '@mui/material';
import ContentPasteIcon from '@mui/icons-material/ContentPaste';
import ClearIcon from '@mui/icons-material/Clear';
import IconButton from '@mui/material/IconButton';

interface JobDescriptionInputProps {
    value: string;
    onChange: (value: string) => void;
    disabled?: boolean;
}

export function JobDescriptionInput({
    value,
    onChange,
    disabled = false,
}: JobDescriptionInputProps) {
    const [charCount, setCharCount] = useState(value.length);

    const handleChange = useCallback(
        (e: React.ChangeEvent<HTMLTextAreaElement>) => {
            const newValue = e.target.value;
            onChange(newValue);
            setCharCount(newValue.length);
        },
        [onChange]
    );

    const handlePaste = useCallback(async () => {
        try {
            const text = await navigator.clipboard.readText();
            onChange(text);
            setCharCount(text.length);
        } catch (err) {
            console.error('Failed to paste:', err);
        }
    }, [onChange]);

    const handleClear = useCallback(() => {
        onChange('');
        setCharCount(0);
    }, [onChange]);

    const minChars = 50;
    const isValid = charCount >= minChars;

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
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ color: '#fff', fontWeight: 600 }}>
                    📋 Job Description
                </Typography>
                <Box>
                    <Tooltip title="Paste from clipboard">
                        <IconButton onClick={handlePaste} disabled={disabled} sx={{ color: 'primary.main' }}>
                            <ContentPasteIcon />
                        </IconButton>
                    </Tooltip>
                    <Tooltip title="Clear">
                        <IconButton onClick={handleClear} disabled={disabled || !value} sx={{ color: 'error.main' }}>
                            <ClearIcon />
                        </IconButton>
                    </Tooltip>
                </Box>
            </Box>

            <TextField
                fullWidth
                multiline
                rows={12}
                value={value}
                onChange={handleChange}
                disabled={disabled}
                placeholder="Paste the job description here. Include the full posting with requirements, responsibilities, and qualifications..."
                sx={{
                    '& .MuiOutlinedInput-root': {
                        backgroundColor: 'rgba(0,0,0,0.2)',
                        color: '#fff',
                        '& fieldset': {
                            borderColor: isValid ? 'rgba(76, 175, 80, 0.5)' : 'rgba(255,255,255,0.2)',
                        },
                        '&:hover fieldset': {
                            borderColor: isValid ? 'rgba(76, 175, 80, 0.7)' : 'rgba(255,255,255,0.3)',
                        },
                        '&.Mui-focused fieldset': {
                            borderColor: 'primary.main',
                        },
                    },
                }}
            />

            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                <Typography
                    variant="caption"
                    sx={{ color: isValid ? 'success.main' : 'warning.main' }}
                >
                    {isValid ? '✓ Ready' : `Minimum ${minChars} characters required`}
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                    {charCount} characters
                </Typography>
            </Box>
        </Paper>
    );
}
