# DC-Pickaxe v2

디시인사이드 갤러리를 수집·분석하는 시스템의 새 버전. 데이터는 Supabase(PostgreSQL)에 저장한다.

## 폴더
| 위치 | 역할 |
|---|---|
| `db/` | DB 표 설계 파일. 번호 순서대로 적용 (`001_init` → `002` → `003` …). 컬럼을 바꿀 때는 새 번호 파일을 추가 |
| `collector/` | 수집 봇 (디시 접속·파싱은 `dc.py` 한 곳만 안다) |
| `core/` | 공용(설정·DB 연결) |
| `analyzer/` | 분석 봇 (이슈 점수·키워드·AI 요약) |
| `migrate/` | 예전 엑셀(구글시트) → DB 이관 스크립트 (이미 1회 실행 완료) |
| `tools/` | 점검용 도구 (`q.py "SQL"`, `run_sql.py 파일`) |
| `.env` | DB 주소·비밀번호 (내 컴퓨터에만 있음, GitHub에 올라가지 않음) |

## 수집 봇 사용법 (프로젝트 폴더에서)
```
.venv\Scripts\python.exe -m collector run                    # 정기 실행: 새 글 → 숫자 갱신 → 본문·댓글 → 완성도
.venv\Scripts\python.exe -m collector scrape --gallery gssc  # 새 글만, 특정 갤러리만
.venv\Scripts\python.exe -m collector history --gallery X --pages 30   # 과거 글 거슬러 채우기
.venv\Scripts\python.exe -m collector detect --gallery X     # 갤러리 종류(일반/마이너/미니) 판별
```
옵션: `--force` 수집 주기 무시. 차단이 의심되면 스스로 멈추고 쉰다(연속될수록 오래, 최대 6시간).

## 동작 요약
1. **새 글 수집**: 1페이지부터 훑다가 저장된 글을 5개 연속 만나면 멈춤. 정기 범위(15페이지)에서 못 끝나면 진행 위치를 저장하고 다음 실행에서 이어서 따라잡음.
2. **숫자 갱신**: 글이 12시간 지나면 1차, 36시간 지나면 최종으로 댓글·조회·추천수를 덮어씀. 이미 오래된 글을 따라잡아 가져온 경우는 처음부터 최종값으로 취급.
3. **본문·댓글**: 반응이 있는 글(댓글 3개↑ 또는 개념글)만 본문, 댓글 10개↑ 글만 댓글 내용을 가져옴.
4. **표시**: 개념글(`is_best`), 나중에 공지로 고정된 글(`is_notice`), 쿠폰·코드 교환류(`is_repetitive`, 규칙은 `noise_rules` 표).
5. **완성도**: 일별로 글번호 범위 대비 저장 비율을 `daily_coverage`에 기록.
6. 실행 결과는 `job_runs`에 남음. 설정값은 `settings` 표(`collector.*`)에서 코드 기본값을 덮어쓸 수 있음.

## 분석 봇 (analyzer)
```
.venv\Scripts\python.exe -m analyzer daily --date 2026-10-21 [--to 2026-10-25] [--gallery X] [--no-ai]
.venv\Scripts\python.exe -m analyzer weekly --week-start 2026-10-12
.venv\Scripts\python.exe -m analyzer monthly --month 2026-09
.venv\Scripts\python.exe -m analyzer calibrate --from 2026-09-28 --to 2026-10-21    # 저장·AI 없이 점수 분포만 확인
```
- 점수는 **그 갤러리의 평소(최근 28일)와 비교**한 값: 게시량 급증, 최다 댓글, 화제 글 수, 모멘텀, 개념글.
  숫자가 최종값으로 갱신된 기록(`source='live'`, `refresh_stage=2`) 7일 이상이 있어야 댓글 기반 점수가 계산된다.
- 같은 제목이 하루 8번 이상이면 도배 묶음: 점수에는 묶음당 5건까지만 반영하고 리포트(`extra.floods`)에는 그대로 남긴다.
- 누락 구간 따라잡기(`crawl_cursor`)가 끝나지 않은 갤러리는 분석을 보류한다.
- AI(Gemini)는 이슈·경계 갤러리와 주간·월간 요약에만 쓴다. `.env`의 `GEMINI_API_KEY`가 없으면 점수·키워드만 계산한다.
- 공식 이벤트 후보는 `events` 표(candidate)에 쌓이고, 관리자가 confirmed로 바꾼 것만 AI 입력에 쓰인다. (빼려면 `analyzer/events.py`, `db/004_events.sql`)

## 웹 화면 (web/)
Next.js 앱. 공개 화면과 관리자 화면(`/admin`)이 한 프로젝트에 있다. DB는 서버에서만 접근한다.

화면 구조 (공개):
```
홈 (/)                        오늘의 온도 · 이슈 캘린더(갤러리별 칩) · 날짜 요약 · 갤러리 현황
└ 갤러리 (/gallery)           갤러리 카드 목록
   └ 갤러리 하나 (/gallery/ID)  탭: 일별·캘린더 / 주간 리포트 / 월간 리포트   (예전 /daily, /weekly, /monthly 는 리다이렉트)
점수 설명 (/about)
```
- 이슈 칩·날짜 요약을 누르면 `/gallery/ID?month=YYYY-MM#d-YYYY-MM-DD` 로 이동해 그 리포트 카드가 강조되어 열린다.
- 온도 단계: 평온(회색) → 주목(노랑, 이슈 직전) → 이슈(주황) → 강한 이슈(빨강). 정의는 `web/lib/level.ts`.
- 갤러리 전체를 합친 주간·월간 '종합 동향'은 만들지 않는다(갤러리마다 성향이 달라서). 리포트는 갤러리별로만 생성된다.
- 화면 문구는 `web/lib/textDefs.ts` 에 모아 두었고 관리자 '화면 문구'에서 고친다. Tailwind 가 `web/lib`도 읽도록 설정되어 있다(색 클래스를 lib에 둠).
```
cd web
npm run dev          # http://localhost:3000
npm run typecheck
```
- **관리자 비밀번호 정하기** (한 번만, 직접 실행): `.venv\Scripts\python.exe tools\set_admin_password.py` → `web/.env.local`에 해시와 세션 키가 저장된다.
- `web/.env.local` 에 필요한 값: `DATABASE_URL`, `ADMIN_PASSWORD_HASH`, `SESSION_SECRET` (+ 이 회사 PC에서만 `DB_SSL_INSECURE=1`, `NODE_TLS_REJECT_UNAUTHORIZED=0`).
  Vercel 배포 때는 앞 세 개만 환경변수로 넣는다. `DATABASE_URL`은 Supabase의 **Session pooler**(포트 5432) 주소를 쓴다. (Transaction pooler 6543 주소를 넣어도 코드가 5432로 바꿔 접속한다)
- 관리자: 갤러리 추가·수정·삭제, 이벤트 후보 확인, 이슈 맞음/틀림, 화면 문구, 반복글 규칙, 과장어 사전, 설정값. 로그인은 15분에 5회 실패하면 잠긴다.
- 알려진 함정: 서버 액션 폼에서 입력칸 이름을 `id`로 쓰면 버튼 값이 서버에 전달되지 않는다(`event_id`, `rule_id`처럼 쓸 것).
- 예전 방식(이관된) 리포트는 `extra`가 비어 있고 "예전 방식 점수" 표시가 붙는다. 점수 8점 미만이던 옛 '이슈'는 화면에서 '경계'로 보인다.

## 메모
- 이 컴퓨터는 회사망 인증서 때문에 `.env`에 `DC_INSECURE_SSL=1`이 필요. GitHub Actions에서는 쓰지 않는다.
- `refresh_stage`: 0=최초, 1=1차 갱신, 2=최종, 3=끝내 확인 못함(삭제 추정).
