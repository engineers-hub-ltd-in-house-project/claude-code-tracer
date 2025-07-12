"""
Privacy protection and sensitive information detection
"""

import re
import hashlib
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SensitivityLevel(Enum):
    """Sensitivity levels for detected patterns"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    MAXIMUM = 5


@dataclass
class SensitivePattern:
    """Definition of a sensitive pattern"""
    pattern: str
    description: str
    replacement: str
    level: SensitivityLevel
    enabled: bool = True


class PrivacyGuard:
    """Advanced privacy protection for Claude Code interactions"""
    
    def __init__(self, custom_patterns: Optional[List[SensitivePattern]] = None):
        self.patterns = self._load_default_patterns()
        if custom_patterns:
            self.patterns.extend(custom_patterns)
        self.user_whitelist: Set[str] = set()
        
    def _load_default_patterns(self) -> List[SensitivePattern]:
        """Load default sensitive patterns"""
        return [
            # API Keys
            SensitivePattern(
                r'sk-[a-zA-Z0-9]{48}',
                'OpenAI API Key',
                '[OPENAI_API_KEY]',
                SensitivityLevel.MAXIMUM
            ),
            SensitivePattern(
                r'ANTHROPIC_API_KEY=[a-zA-Z0-9\-_]{40,}',
                'Anthropic API Key',
                'ANTHROPIC_API_KEY=[REDACTED]',
                SensitivityLevel.MAXIMUM
            ),
            SensitivePattern(
                r'ghp_[a-zA-Z0-9]{36}',
                'GitHub Personal Access Token',
                '[GITHUB_TOKEN]',
                SensitivityLevel.MAXIMUM
            ),
            SensitivePattern(
                r'ghs_[a-zA-Z0-9]{36}',
                'GitHub Secret',
                '[GITHUB_SECRET]',
                SensitivityLevel.MAXIMUM
            ),
            
            # Database Credentials
            SensitivePattern(
                r'postgresql://[^@\s]+:[^@\s]+@[^/\s]+/\w+',
                'PostgreSQL Connection String',
                'postgresql://[USER]:[PASS]@[HOST]/[DB]',
                SensitivityLevel.CRITICAL
            ),
            SensitivePattern(
                r'mongodb\+srv://[^@\s]+:[^@\s]+@[^/\s]+',
                'MongoDB Connection String',
                'mongodb+srv://[USER]:[PASS]@[HOST]',
                SensitivityLevel.CRITICAL
            ),
            SensitivePattern(
                r'mysql://[^@\s]+:[^@\s]+@[^/\s]+/\w+',
                'MySQL Connection String',
                'mysql://[USER]:[PASS]@[HOST]/[DB]',
                SensitivityLevel.CRITICAL
            ),
            
            # Cloud Services
            SensitivePattern(
                r'https://[a-zA-Z0-9]+\.supabase\.co',
                'Supabase Project URL',
                'https://[PROJECT].supabase.co',
                SensitivityLevel.HIGH
            ),
            SensitivePattern(
                r'eyJ[a-zA-Z0-9\-_=]+\.[a-zA-Z0-9\-_=]+\.[a-zA-Z0-9\-_=]+',
                'JWT Token',
                '[JWT_TOKEN]',
                SensitivityLevel.CRITICAL
            ),
            SensitivePattern(
                r'AKIA[0-9A-Z]{16}',
                'AWS Access Key ID',
                '[AWS_ACCESS_KEY_ID]',
                SensitivityLevel.MAXIMUM
            ),
            
            # Personal Information
            SensitivePattern(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'Email Address',
                '[EMAIL]',
                SensitivityLevel.MEDIUM
            ),
            SensitivePattern(
                r'\b\d{3}-\d{4}-\d{4}\b',
                'Japanese Phone Number',
                '[PHONE_JP]',
                SensitivityLevel.HIGH
            ),
            SensitivePattern(
                r'\b\d{3}-\d{3}-\d{4}\b',
                'US Phone Number',
                '[PHONE_US]',
                SensitivityLevel.HIGH
            ),
            SensitivePattern(
                r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b',
                'Credit Card Number',
                '[CARD_NUMBER]',
                SensitivityLevel.MAXIMUM
            ),
            SensitivePattern(
                r'\b\d{3}-\d{2}-\d{4}\b',
                'SSN',
                '[SSN]',
                SensitivityLevel.MAXIMUM
            ),
            
            # File Paths
            SensitivePattern(
                r'/Users/[^/\s]+',
                'macOS User Directory',
                '/Users/[USERNAME]',
                SensitivityLevel.LOW
            ),
            SensitivePattern(
                r'/home/[^/\s]+',
                'Linux Home Directory',
                '/home/[USERNAME]',
                SensitivityLevel.LOW
            ),
            SensitivePattern(
                r'C:\\Users\\[^\\s\\]+',
                'Windows User Directory',
                'C:\\Users\\[USERNAME]',
                SensitivityLevel.LOW
            ),
            
            # IP Addresses
            SensitivePattern(
                r'\b(?:10\.|172\.(?:1[6-9]|2[0-9]|3[01])\.|192\.168\.)\d{1,3}\.\d{1,3}\b',
                'Private IP Address',
                '[PRIVATE_IP]',
                SensitivityLevel.MEDIUM
            ),
            
            # Passwords and Secrets
            SensitivePattern(
                r'(?i)password\s*[:=]\s*["\']?[^\s"\']{8,}',
                'Password Assignment',
                'password=[REDACTED]',
                SensitivityLevel.MAXIMUM
            ),
            SensitivePattern(
                r'(?i)secret\s*[:=]\s*["\']?[^\s"\']{8,}',
                'Secret Assignment',
                'secret=[REDACTED]',
                SensitivityLevel.MAXIMUM
            ),
            SensitivePattern(
                r'(?i)api_key\s*[:=]\s*["\']?[^\s"\']{16,}',
                'API Key Assignment',
                'api_key=[REDACTED]',
                SensitivityLevel.MAXIMUM
            ),
        ]
        
    def scan_and_mask(self, content: str) -> Tuple[str, List[str]]:
        """Scan content for sensitive information and mask it"""
        if not content:
            return content, []
            
        masked_content = content
        detected_patterns = []
        
        for pattern in self.patterns:
            if not pattern.enabled:
                continue
                
            matches = list(re.finditer(pattern.pattern, content, re.MULTILINE | re.IGNORECASE))
            if matches:
                detected_patterns.append(pattern.description)
                logger.debug(f"Detected {len(matches)} instances of {pattern.description}")
                
                # Mask the content
                masked_content = re.sub(
                    pattern.pattern,
                    pattern.replacement,
                    masked_content,
                    flags=re.MULTILINE | re.IGNORECASE
                )
        
        return masked_content, detected_patterns
        
    def analyze_sensitivity(self, content: str) -> Dict[str, Any]:
        """Analyze the sensitivity level of content"""
        _, detected_patterns = self.scan_and_mask(content)
        
        if not detected_patterns:
            return {
                "level": "SAFE",
                "score": 0,
                "requires_approval": False,
                "detected_patterns": []
            }
        
        # Find highest sensitivity level
        max_level = SensitivityLevel.LOW
        for pattern in self.patterns:
            if pattern.description in detected_patterns:
                if pattern.level.value > max_level.value:
                    max_level = pattern.level
        
        requires_approval = max_level.value >= SensitivityLevel.HIGH.value
        
        return {
            "level": max_level.name,
            "score": max_level.value,
            "requires_approval": requires_approval,
            "detected_patterns": detected_patterns
        }
        
    def add_custom_pattern(self, pattern: SensitivePattern):
        """Add a custom pattern"""
        self.patterns.append(pattern)
        
    def disable_pattern(self, description: str):
        """Disable a specific pattern by description"""
        for pattern in self.patterns:
            if pattern.description == description:
                pattern.enabled = False
                break
                
    def enable_pattern(self, description: str):
        """Enable a specific pattern by description"""
        for pattern in self.patterns:
            if pattern.description == description:
                pattern.enabled = True
                break
                
    def whitelist_add(self, content: str):
        """Add content hash to whitelist"""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        self.user_whitelist.add(content_hash)
        
    def is_whitelisted(self, content: str) -> bool:
        """Check if content is whitelisted"""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        return content_hash in self.user_whitelist
        
    def get_patterns_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all patterns"""
        return [
            {
                "description": p.description,
                "level": p.level.name,
                "enabled": p.enabled
            }
            for p in self.patterns
        ]