"""Privacy protection module for sensitive data detection and masking."""

import re
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml
from pydantic import BaseModel, Field

from claude_code_tracer.utils.config import get_settings


class SensitivityLevel(str, Enum):
    """Sensitivity levels for detected patterns."""
    
    MAXIMUM = "MAXIMUM"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PatternMatch(BaseModel):
    """Model for a pattern match result."""
    
    pattern_name: str
    matched_text: str
    masked_text: str
    start_pos: int
    end_pos: int
    sensitivity_level: SensitivityLevel


class PrivacyPattern(BaseModel):
    """Model for privacy detection patterns."""
    
    name: str
    pattern: str
    description: str
    sensitivity_level: SensitivityLevel = SensitivityLevel.HIGH
    replacement: Optional[str] = None
    
    def get_replacement(self, match: str) -> str:
        """Get replacement text for matched pattern."""
        if self.replacement:
            return self.replacement
        
        # Default replacements based on pattern name
        if "key" in self.name.lower() or "token" in self.name.lower():
            return f"[{self.name.upper().replace(' ', '_')}]"
        elif "email" in self.name.lower():
            return "[EMAIL_REDACTED]"
        elif "phone" in self.name.lower():
            return "[PHONE_REDACTED]"
        elif "card" in self.name.lower():
            return "[CARD_NUMBER_REDACTED]"
        elif "ip" in self.name.lower():
            return "[IP_ADDRESS_REDACTED]"
        else:
            return f"[{self.name.upper()}_REDACTED]"


class PrivacyGuard:
    """Main privacy protection class."""
    
    def __init__(self):
        """Initialize privacy guard with default and custom patterns."""
        self.settings = get_settings()
        self.patterns: List[PrivacyPattern] = []
        self._load_default_patterns()
        self._load_custom_patterns()
    
    def _load_default_patterns(self) -> None:
        """Load default privacy patterns."""
        default_patterns = [
            # API Keys and Tokens
            PrivacyPattern(
                name="OpenAI API Key",
                pattern=r"sk-[a-zA-Z0-9]{48}",
                description="OpenAI API key",
                sensitivity_level=SensitivityLevel.MAXIMUM,
            ),
            PrivacyPattern(
                name="Anthropic API Key",
                pattern=r"sk-ant-[a-zA-Z0-9]{95}",
                description="Anthropic API key",
                sensitivity_level=SensitivityLevel.MAXIMUM,
            ),
            PrivacyPattern(
                name="GitHub Token",
                pattern=r"gh[ps]_[a-zA-Z0-9]{36}",
                description="GitHub personal access token",
                sensitivity_level=SensitivityLevel.MAXIMUM,
            ),
            PrivacyPattern(
                name="AWS Access Key",
                pattern=r"AKIA[0-9A-Z]{16}",
                description="AWS access key ID",
                sensitivity_level=SensitivityLevel.MAXIMUM,
            ),
            PrivacyPattern(
                name="Generic API Key",
                pattern=r"(?i)(api[_-]?key|apikey|api[_-]?token|access[_-]?token)['\"]?\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})['\"]?",
                description="Generic API key pattern",
                sensitivity_level=SensitivityLevel.HIGH,
                replacement="[API_KEY_REDACTED]",
            ),
            
            # Database Connection Strings
            PrivacyPattern(
                name="PostgreSQL Connection",
                pattern=r"postgres(?:ql)?:\/\/[^\s]+:[^\s]+@[^\s]+",
                description="PostgreSQL connection string",
                sensitivity_level=SensitivityLevel.MAXIMUM,
                replacement="postgresql://[USER]:[PASSWORD]@[HOST]/[DATABASE]",
            ),
            PrivacyPattern(
                name="MongoDB Connection",
                pattern=r"mongodb(?:\+srv)?:\/\/[^\s]+:[^\s]+@[^\s]+",
                description="MongoDB connection string",
                sensitivity_level=SensitivityLevel.MAXIMUM,
                replacement="mongodb://[USER]:[PASSWORD]@[HOST]/[DATABASE]",
            ),
            
            # Personal Information
            PrivacyPattern(
                name="Email Address",
                pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                description="Email address",
                sensitivity_level=SensitivityLevel.MEDIUM,
            ),
            PrivacyPattern(
                name="Phone Number",
                pattern=r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
                description="Phone number (US format)",
                sensitivity_level=SensitivityLevel.MEDIUM,
            ),
            PrivacyPattern(
                name="Credit Card",
                pattern=r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12})\b",
                description="Credit card number",
                sensitivity_level=SensitivityLevel.MAXIMUM,
            ),
            PrivacyPattern(
                name="SSN",
                pattern=r"\b\d{3}-\d{2}-\d{4}\b",
                description="Social Security Number",
                sensitivity_level=SensitivityLevel.MAXIMUM,
                replacement="[SSN_REDACTED]",
            ),
            
            # Network Information
            PrivacyPattern(
                name="IPv4 Address",
                pattern=r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
                description="IPv4 address",
                sensitivity_level=SensitivityLevel.LOW,
            ),
            PrivacyPattern(
                name="Private IPv4",
                pattern=r"\b(?:10\.(?:[0-9]{1,3}\.){2}[0-9]{1,3}|172\.(?:1[6-9]|2[0-9]|3[0-1])\.[0-9]{1,3}\.[0-9]{1,3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3})\b",
                description="Private IPv4 address",
                sensitivity_level=SensitivityLevel.LOW,
                replacement="[PRIVATE_IP]",
            ),
            
            # Secrets and Passwords
            PrivacyPattern(
                name="Password Field",
                pattern=r"(?i)(password|passwd|pwd)['\"]?\s*[:=]\s*['\"]?([^\s'\"]{8,})['\"]?",
                description="Password in configuration",
                sensitivity_level=SensitivityLevel.MAXIMUM,
                replacement="password=[PASSWORD_REDACTED]",
            ),
            PrivacyPattern(
                name="JWT Token",
                pattern=r"eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*",
                description="JSON Web Token",
                sensitivity_level=SensitivityLevel.HIGH,
                replacement="[JWT_TOKEN_REDACTED]",
            ),
            
            # File Paths (potentially sensitive)
            PrivacyPattern(
                name="Home Directory Path",
                pattern=r"\/(?:home|Users)\/[a-zA-Z0-9_-]+\/[^\s]*",
                description="User home directory path",
                sensitivity_level=SensitivityLevel.LOW,
                replacement="/home/[USER]/[PATH]",
            ),
        ]
        
        self.patterns.extend(default_patterns)
    
    def _load_custom_patterns(self) -> None:
        """Load custom patterns from configuration file."""
        config_path = self.settings.get_privacy_patterns_path()
        
        if not config_path.exists():
            return
        
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            
            if "custom_patterns" in config:
                for pattern_data in config["custom_patterns"]:
                    pattern = PrivacyPattern(
                        name=pattern_data["name"],
                        pattern=pattern_data["pattern"],
                        description=pattern_data.get("description", ""),
                        sensitivity_level=SensitivityLevel(
                            pattern_data.get("level", "HIGH")
                        ),
                        replacement=pattern_data.get("replacement"),
                    )
                    self.patterns.append(pattern)
        
        except Exception as e:
            print(f"Warning: Failed to load custom privacy patterns: {e}")
    
    def scan_text(self, text: str) -> List[PatternMatch]:
        """Scan text for sensitive patterns."""
        if not text:
            return []
        
        matches: List[PatternMatch] = []
        
        # Apply patterns based on privacy mode
        applicable_patterns = self._filter_patterns_by_mode()
        
        for pattern in applicable_patterns:
            try:
                regex = re.compile(pattern.pattern, re.IGNORECASE | re.MULTILINE)
                
                for match in regex.finditer(text):
                    matched_text = match.group(0)
                    masked_text = pattern.get_replacement(matched_text)
                    
                    matches.append(
                        PatternMatch(
                            pattern_name=pattern.name,
                            matched_text=matched_text,
                            masked_text=masked_text,
                            start_pos=match.start(),
                            end_pos=match.end(),
                            sensitivity_level=pattern.sensitivity_level,
                        )
                    )
            
            except re.error as e:
                print(f"Warning: Invalid regex pattern '{pattern.name}': {e}")
        
        # Sort by position to handle overlapping matches
        matches.sort(key=lambda m: (m.start_pos, -m.end_pos))
        
        # Remove overlapping matches (keep the longer one)
        filtered_matches = []
        last_end = -1
        
        for match in matches:
            if match.start_pos >= last_end:
                filtered_matches.append(match)
                last_end = match.end_pos
        
        return filtered_matches
    
    def mask_text(self, text: str) -> Tuple[str, List[PatternMatch]]:
        """Scan and mask sensitive data in text."""
        if not text:
            return text, []
        
        matches = self.scan_text(text)
        
        if not matches:
            return text, []
        
        # Apply masking from end to start to preserve positions
        masked_text = text
        for match in reversed(matches):
            masked_text = (
                masked_text[: match.start_pos]
                + match.masked_text
                + masked_text[match.end_pos :]
            )
        
        return masked_text, matches
    
    def _filter_patterns_by_mode(self) -> List[PrivacyPattern]:
        """Filter patterns based on privacy mode setting."""
        mode = self.settings.privacy_mode
        
        if mode == "minimal":
            # Only maximum sensitivity patterns
            return [
                p for p in self.patterns
                if p.sensitivity_level == SensitivityLevel.MAXIMUM
            ]
        elif mode == "moderate":
            # High and maximum sensitivity patterns
            return [
                p for p in self.patterns
                if p.sensitivity_level in [
                    SensitivityLevel.MAXIMUM,
                    SensitivityLevel.HIGH,
                ]
            ]
        else:  # strict mode
            # All patterns
            return self.patterns
    
    def get_pattern_summary(self) -> Dict[str, int]:
        """Get summary of loaded patterns by sensitivity level."""
        summary = {level.value: 0 for level in SensitivityLevel}
        
        for pattern in self.patterns:
            summary[pattern.sensitivity_level.value] += 1
        
        return summary
    
    def validate_patterns(self) -> List[str]:
        """Validate all loaded patterns and return errors."""
        errors = []
        
        for pattern in self.patterns:
            try:
                re.compile(pattern.pattern)
            except re.error as e:
                errors.append(f"{pattern.name}: {e}")
        
        return errors


# Singleton instance
_privacy_guard: Optional[PrivacyGuard] = None


def get_privacy_guard() -> PrivacyGuard:
    """Get or create privacy guard instance."""
    global _privacy_guard
    if _privacy_guard is None:
        _privacy_guard = PrivacyGuard()
    return _privacy_guard