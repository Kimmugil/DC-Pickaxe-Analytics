"""
키워드 트렌드 분석 모듈
- kiwipiepy(한국어 형태소 분석기)를 우선 사용
- 설치가 안 된 환경에서는 정규식 기반 단순 빈도 분석으로 자동 폴백
"""
import re
from collections import Counter
from typing import List, Tuple
import pandas as pd

# 분석에서 제외할 불용어 목록
STOPWORDS = {
    # 조사/어미
    '이', '가', '을', '를', '은', '는', '에', '의', '와', '과',
    '도', '로', '으로', '에서', '하는', '하고', '하다', '있다',
    '없다', '같다', '이다', '됩니다', '합니다', '있습니다',
    # 일반 부사/대명사
    '그리고', '하지만', '그런데', '그래서', '때문에', '아니', '진짜',
    '너무', '정말', '좀', '걍', '그냥', '뭔가', '어떤', '어떻게',
    '얼마나', '언제', '어디', '왜', '것', '거', '게', '건',
    # DC 갤러리 특유 표현
    '글', '공지', '질문', '잡담', 'ㅋㅋ', 'ㅠㅠ', 'ㅜㅜ', 'ㄷㄷ',
    '갤러리', '갤', '게시글', '이거', '저거', '그거',
}


def _simple_tokenize(text: str) -> List[str]:
    """한글 2자 이상 단어를 추출하는 단순 토크나이저 (폴백용)."""
    words = re.findall(r'[가-힣]{2,}', text)
    return [w for w in words if w not in STOPWORDS]


def extract_keywords(
    df: pd.DataFrame,
    top_n: int = 20,
    use_kiwi: bool = True,
) -> List[Tuple[str, int]]:
    """
    게시글 제목에서 상위 키워드를 추출합니다.

    Args:
        df: 게시글 DataFrame (제목 컬럼 필요)
        top_n: 반환할 키워드 수
        use_kiwi: kiwipiepy 사용 여부 (False면 단순 빈도 방식)

    Returns:
        [(키워드, 빈도수), ...] 리스트
    """
    if df.empty or '제목' not in df.columns:
        return []

    titles = ' '.join(df['제목'].fillna('').tolist())

    if use_kiwi:
        try:
            from kiwipiepy import Kiwi
            kiwi = Kiwi()
            tokens = kiwi.tokenize(titles)
            # 일반명사(NNG), 고유명사(NNP), 외래어(SL) 위주 추출
            words = [
                token.form
                for token in tokens
                if token.tag in ('NNG', 'NNP', 'SL')
                and len(token.form) >= 2
                and token.form not in STOPWORDS
            ]
        except (ImportError, Exception):
            words = _simple_tokenize(titles)
    else:
        words = _simple_tokenize(titles)

    counter = Counter(words)
    return counter.most_common(top_n)
