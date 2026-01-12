import React, { useState, useCallback } from 'react';
import {
    Box,
    TextField,
    Typography,
    Paper,
    Button,
    Tabs,
    Tab,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import TextFieldsIcon from '@mui/icons-material/TextFields';

interface CVUploaderProps {
    cvText: string;
    onCVTextChange: (text: string) => void;
    cvFile: File | null;
    onCVFileChange: (file: File | null) => void;
    disabled?: boolean;
}

export function CVUploader({
    cvText,
    onCVTextChange,
    cvFile,
    onCVFileChange,
    disabled = false,
}: CVUploaderProps) {
    const [tabIndex, setTabIndex] = useState(0);
    const [dragOver, setDragOver] = useState(false);

    const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
        setTabIndex(newValue);
    };

    const handleTextChange = useCallback(
        (e: React.ChangeEvent<HTMLTextAreaElement>) => {
            onCVTextChange(e.target.value);
        },
        [onCVTextChange]
    );

    const handleFileSelect = useCallback(
        (file: File) => {
            const allowedTypes = [
                'application/pdf',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'text/plain',
            ];
            const allowedExtensions = ['.pdf', '.docx', '.txt', '.md'];

            const isValidType = allowedTypes.includes(file.type);
            const isValidExtension = allowedExtensions.some((ext) =>
                file.name.toLowerCase().endsWith(ext)
            );

            if (isValidType || isValidExtension) {
                onCVFileChange(file);
            } else {
                alert('Please upload a PDF, DOCX, or TXT file');
            }
        },
        [onCVFileChange]
    );

    const handleDrop = useCallback(
        (e: React.DragEvent) => {
            e.preventDefault();
            setDragOver(false);

            const file = e.dataTransfer.files[0];
            if (file) {
                handleFileSelect(file);
            }
        },
        [handleFileSelect]
    );

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setDragOver(true);
    }, []);

    const handleDragLeave = useCallback(() => {
        setDragOver(false);
    }, []);

    const handleFileInput = useCallback(
        (e: React.ChangeEvent<HTMLInputElement>) => {
            const file = e.target.files?.[0];
            if (file) {
                handleFileSelect(file);
            }
        },
        [handleFileSelect]
    );

    const charCount = cvText.length;
    const minChars = 100;
    const isTextValid = charCount >= minChars;
    const hasContent = tabIndex === 0 ? !!cvFile : isTextValid;

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
                📄 Your CV
            </Typography>

            <Tabs
                value={tabIndex}
                onChange={handleTabChange}
                sx={{
                    mb: 2,
                    '& .MuiTab-root': { color: 'rgba(255,255,255,0.7)' },
                    '& .Mui-selected': { color: 'primary.main' },
                }}
            >
                <Tab icon={<CloudUploadIcon />} label="Upload File" iconPosition="start" />
                <Tab icon={<TextFieldsIcon />} label="Paste Text" iconPosition="start" />
            </Tabs>

            {tabIndex === 0 ? (
                <Box
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    sx={{
                        p: 4,
                        border: dragOver ? '2px dashed #7c4dff' : '2px dashed rgba(255,255,255,0.2)',
                        borderRadius: 2,
                        textAlign: 'center',
                        backgroundColor: dragOver ? 'rgba(124, 77, 255, 0.1)' : 'rgba(0,0,0,0.2)',
                        transition: 'all 0.2s ease',
                        cursor: 'pointer',
                    }}
                    onClick={() => document.getElementById('cv-file-input')?.click()}
                >
                    <input
                        id="cv-file-input"
                        type="file"
                        accept=".pdf,.docx,.txt,.md"
                        onChange={handleFileInput}
                        style={{ display: 'none' }}
                        disabled={disabled}
                    />

                    {cvFile ? (
                        <Box>
                            <Typography variant="h6" sx={{ color: 'success.main', mb: 1 }}>
                                ✓ {cvFile.name}
                            </Typography>
                            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                                {(cvFile.size / 1024).toFixed(1)} KB
                            </Typography>
                            <Button
                                variant="text"
                                color="error"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onCVFileChange(null);
                                }}
                                sx={{ mt: 1 }}
                            >
                                Remove
                            </Button>
                        </Box>
                    ) : (
                        <Box>
                            <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
                            <Typography variant="body1" sx={{ color: '#fff', mb: 1 }}>
                                Drag & drop your CV here
                            </Typography>
                            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                                Supports PDF, DOCX, TXT
                            </Typography>
                        </Box>
                    )}
                </Box>
            ) : (
                <Box>
                    <TextField
                        fullWidth
                        multiline
                        rows={10}
                        value={cvText}
                        onChange={handleTextChange}
                        disabled={disabled}
                        placeholder="Paste your CV content here..."
                        sx={{
                            '& .MuiOutlinedInput-root': {
                                backgroundColor: 'rgba(0,0,0,0.2)',
                                color: '#fff',
                                '& fieldset': {
                                    borderColor: isTextValid ? 'rgba(76, 175, 80, 0.5)' : 'rgba(255,255,255,0.2)',
                                },
                                '&:hover fieldset': {
                                    borderColor: isTextValid ? 'rgba(76, 175, 80, 0.7)' : 'rgba(255,255,255,0.3)',
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
                            sx={{ color: isTextValid ? 'success.main' : 'warning.main' }}
                        >
                            {isTextValid ? '✓ Ready' : `Minimum ${minChars} characters required`}
                        </Typography>
                        <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                            {charCount} characters
                        </Typography>
                    </Box>
                </Box>
            )}

            <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box
                    sx={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        backgroundColor: hasContent ? 'success.main' : 'warning.main',
                    }}
                />
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                    {hasContent ? 'CV ready for processing' : 'Please provide your CV'}
                </Typography>
            </Box>
        </Paper>
    );
}
