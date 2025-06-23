import re
from typing import Tuple, List


class TextProcessor:
    def __init__(self):
        self.excessive_whitespace = re.compile(r'\s+')
        self.control_chars = re.compile(r'[\x00-\x1f\x7f-\x9f]')
        self.special_chars = re.compile(r'[^\w\s\-.,!?()№]', re.UNICODE)
    
    def clean_description(self, description: str) -> Tuple[str, str, List[str]]:
        quality_flags = []
        if not description:
            return "", "", ['missing_required_field']
        description_raw = str(description)
        cleaned = description_raw.strip()
        if self.control_chars.search(cleaned):
            cleaned = self.control_chars.sub(' ', cleaned)
            quality_flags.append('description_contains_special_chars')
        cleaned = self.excessive_whitespace.sub(' ', cleaned)
        if self.special_chars.search(cleaned):
            problematic_chars = re.compile(r'[^\w\s\-.,!?()№/\\]', re.UNICODE)
            if problematic_chars.search(cleaned):
                quality_flags.append('description_contains_special_chars')
        cleaned = cleaned.lower().strip()
        return description_raw, cleaned, quality_flags
    
    def normalize_text(self, text: str) -> str:
        if not text:
            return ""
        normalized = self.excessive_whitespace.sub(' ', str(text).strip().lower())
        return normalized
    
    def extract_keywords(self, description: str) -> List[str]:
        if not description:
            return []
        words = re.findall(r'\b\w{3,}\b', description.lower())
        stop_words = {'для', 'при', 'без', 'над', 'под', 'про', 'как', 'что', 'где', 'когда'}
        keywords = [word for word in words if word not in stop_words]
        return list(set(keywords))
