import re
from datetime import datetime, timedelta
import jaconv

class ScheduleParser:
    def __init__(self):
        self.type_keywords = {
            'ES_SUBMIT': ['ES', 'エントリーシート', '提出'],
            'SPI_TEST': ['SPI', 'テスト', '試験', 'Webテスト'],
            'INTERVIEW_1': ['一次', '1次', '初回', '面接'],
            'INTERVIEW_2': ['二次', '2次', '面接'],
            'INTERVIEW_3': ['三次', '3次', '面接'],
            'FINAL_INTERVIEW': ['最終', 'ファイナル', '面接'],
            'EXPLANATION': ['説明会', 'セミナー'],
            'INTERNSHIP': ['インターン', 'インターンシップ']
        }
    
    def parse(self, text):
        """Extract schedule info from natural language text"""
        # Extract Date
        date = self._extract_date(text)
        if not date:
            return None
        
        # Extract Type
        type_code = self._extract_type(text)
        if not type_code:
            return None
        
        # Extract Company Name
        company_name = self._extract_company_name(text, type_code)
        if not company_name:
            return None
        
        return {
            'schedule_date': date,
            'type_code': type_code,
            'company_name': company_name,
            'type_name': self._get_type_name(type_code)
        }
    
    def _extract_date(self, text):
        """Extract date information"""
        # MM/DD or MM月DD日
        patterns = [
            r'(\d{1,2})[/月](\d{1,2})[日]?',
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    # MM/DD
                    month, day = int(groups[0]), int(groups[1])
                    year = datetime.now().year
                    # If date is in the past, assume next year
                    date = datetime(year, month, day)
                    if date < datetime.now() - timedelta(days=7): # allow 7 days buffer for potential "just passed" dates, but generally assume future
                         date = datetime(year + 1, month, day)
                    return date.strftime('%Y-%m-%d')
                elif len(groups) == 3:
                    # YYYY-MM-DD
                    year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                    return datetime(year, month, day).strftime('%Y-%m-%d')
        
        # Relative dates
        if '明日' in text or 'あした' in text:
            return (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        elif '今日' in text or 'きょう' in text:
            return datetime.now().strftime('%Y-%m-%d')
        elif '来週' in text: # Simply add 7 days for "next week" as a rough estimate if no day specified
             return (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        return None
    
    def _extract_type(self, text):
        """Extract schedule type code"""
        # Check specific keywords first (longer matches first if necessary)
        # Priority: Check specific interview types before generic '面接'
        
        if any(w in text for w in ['最終', 'ファイナル']):
            return 'FINAL_INTERVIEW'
        if any(w in text for w in ['三次', '3次']):
            return 'INTERVIEW_3'
        if any(w in text for w in ['二次', '2次']):
            return 'INTERVIEW_2'
        if any(w in text for w in ['一次', '1次']):
            return 'INTERVIEW_1'
            
        for type_code, keywords in self.type_keywords.items():
            if any(keyword in text for keyword in keywords):
                return type_code
        return 'OTHER'
    
    def _extract_company_name(self, text, type_code):
        """Extract company name by removing known keywords"""
        keywords_to_remove = []
        for keywords in self.type_keywords.values():
            keywords_to_remove.extend(keywords)
            
        cleaned_text = text
        for keyword in keywords_to_remove:
            cleaned_text = cleaned_text.replace(keyword, '')
        
        # Remove date patterns
        cleaned_text = re.sub(r'\d{1,2}[/月]\d{1,2}[日]?', '', cleaned_text)
        cleaned_text = re.sub(r'\d{4}[/-]\d{1,2}[/-]\d{1,2}', '', cleaned_text)
        cleaned_text = re.sub(r'明日|今日|来週', '', cleaned_text)
        
        # Remove common particles/words often found in these messages
        cleaned_text = re.sub(r'[のがありますですね。、]', ' ', cleaned_text)

        # Trina and return
        company_name = cleaned_text.strip()
        company_name = re.sub(r'\s+', ' ', company_name)
        
        return company_name if company_name else "未定の会社"
    
    def _get_type_name(self, type_code):
        type_names = {
            'ES_SUBMIT': 'ES提出',
            'SPI_TEST': 'SPI試験',
            'INTERVIEW_1': '一次面接',
            'INTERVIEW_2': '二次面接',
            'INTERVIEW_3': '三次面接',
            'FINAL_INTERVIEW': '最終面接',
            'EXPLANATION': '会社説明会',
            'INTERNSHIP': 'インターン',
            'OTHER': 'その他'
        }
        return type_names.get(type_code, 'その他')
