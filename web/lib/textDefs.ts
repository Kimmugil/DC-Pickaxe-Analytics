/**
 * 관리자 '화면 문구'에서 고칠 수 있는 문구의 목록. 기본 문구는 여기에만 적고, 화면은 T(t, '키')로 가져온다.
 * DB(settings 표)에는 사용자가 바꾼 것만 'ui.<키>'로 저장된다 (기본값으로 되돌리면 저장값이 지워진다).
 * 문구를 새로 편집 가능하게 만들려면: 아래에 한 줄 추가하고, 화면에서 T(t, '키')로 바꾸면 된다.
 */
export type TextDef = { key: string; label: string; def: string; group: string }

export const TEXT_DEFS: TextDef[] = [
  { group: '상단·공통', key: 'nav.title', label: '사이트 이름', def: '디씨곡괭이 정련소' },
  { group: '상단·공통', key: 'nav.subtitle', label: '사이트 부제', def: 'DC 갤러리 동향분석소' },
  { group: '상단·공통', key: 'nav.home', label: '메뉴: 홈', def: '홈' },
  { group: '상단·공통', key: 'nav.gallery', label: '메뉴: 갤러리', def: '갤러리' },
  { group: '상단·공통', key: 'nav.about', label: '메뉴: 점수 설명', def: '점수 설명' },
  { group: '상단·공통', key: 'nav.admin', label: '메뉴: 관리자', def: '관리자' },
  { group: '상단·공통', key: 'footer.disclaimer', label: '하단 안내문', def: '수집 데이터는 DC인사이드 공개 게시글이며, 요약은 AI가 작성해 부정확할 수 있습니다. 근거 글 링크를 함께 확인해 주세요.' },

  { group: '홈', key: 'home.calendar.title', label: '캘린더 제목', def: '이슈 캘린더' },
  { group: '홈', key: 'home.calendar.hint', label: '캘린더 안내', def: '날짜별로 어느 갤러리가 어떤 온도였는지 · 갤러리 이름을 누르면 그날 리포트로 이동' },
  { group: '홈', key: 'home.status.title', label: '갤러리 현황 제목', def: '갤러리 현황' },
  { group: '홈', key: 'home.status.hint', label: '갤러리 현황 안내', def: '오른쪽 막대는 최근 7일 게시량 (색은 그날의 온도)' },
  { group: '홈', key: 'home.rising.title', label: '급상승 단어 제목', def: '평소보다 많이 언급된 단어' },

  { group: '갤러리', key: 'gallery.list.title', label: '갤러리 목록 제목', def: '갤러리' },
  { group: '갤러리', key: 'gallery.list.sub', label: '갤러리 목록 안내 ({count}=갤러리 수)', def: '추적 중인 갤러리 {count}개 · 카드를 누르면 그 갤러리의 캘린더와 주간·월간 리포트가 열립니다' },
  { group: '갤러리', key: 'gallery.tab.daily', label: '탭: 일별', def: '일별 · 캘린더' },
  { group: '갤러리', key: 'gallery.tab.weekly', label: '탭: 주간', def: '주간 리포트' },
  { group: '갤러리', key: 'gallery.tab.monthly', label: '탭: 월간', def: '월간 리포트' },
  { group: '갤러리', key: 'gallery.empty.month', label: '이슈 없는 달 안내 ({month}=월)', def: '{month}에는 평소와 달랐던 날이 없습니다.' },

  { group: '점수 설명', key: 'about.title', label: '제목', def: '이슈는 어떻게 판정하나요' },
  { group: '점수 설명', key: 'about.sub', label: '부제', def: '점수가 아니라 ‘그 갤러리의 평소와 얼마나 다른가’를 봅니다' },
]

export const DEF_BY_KEY = Object.fromEntries(TEXT_DEFS.map(d => [d.key, d.def]))
