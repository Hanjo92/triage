# Triage Tagged Action Db Design

트리아지태그 기반 액션 DB + 추천 알고리즘 연결 설계서
텔레그램 MVP를 기준으로 액션 데이터 구조, 추천 규칙, API 연결 방식을 정의한 개발용 설계 문서
문서 목적
추천 액션을 태그 기반으로 구조화하고 사용자 상태와 연결되는 추천 엔진 설계
적용 범위
대상 채널
텔레그램 MVP 1차 구현
향후 디스코드/토스 확장 고려
1. 설계 목표
추천 액션을 단순 문장 목록이 아니라 구조화된 데이터 자산으로 전환한다.
사용자 체크인 결과(에너지, 시간, 상태, 최근 연속성)에 따라 액션을 자동 필터링한다.
회복 모드, 시작 모드, 유지 모드처럼 제품 의도에 맞는 추천 결과를 안정적으로 출력한다.
초기 MVP는 룰 기반으로 운영하고, 이후 로그가 쌓이면 점진적으로 점수 기반 추천으로 확장한다.
2. 액션 데이터 모델 개요
핵심 원칙: 액션 한 건은 ‘사용자에게 보여줄 문장’이 아니라 ‘추천 가능한 단위 데이터’여야 한다. 즉, 텍스트와 함께 난이도, 소요 시간, 추천 상황, 도메인, 회복 적합성 같은 메타데이터를 반드시 가진다.
필드
타입
예시
설명
필수
action_id
string
ACT-0001
액션 고유 식별자
Y
label
string
문서 파일 열기
사용자에게 기본 표시되는 액션명
Y
prompt_copy
string
딱 3초만, 파일만 열어볼까요?
UX용 친화 카피
Y
mode_tags
array
['start','recovery']
추천 상황 모드
Y
energy_tags
array
['low','mid']
허용 에너지 수준
Y
time_tags
array
['1','3']
추천 가능 시간 버킷(분)
Y
state_tags
array
['stressed','distracted']
감정/인지 상태 태그
N
domain_tags
array
['work']
일/공부/생활/운동/관계 등
N
difficulty
int
1~5
체감 강도 점수
Y
recovery_safe
bool
true
회복 모드에 노출 가능한지 여부
Y
success_weight
float
0.7
완료 시 스트릭 또는 추천 가중치
N
3. 태그 체계 제안
3-1. 모드 태그
start: 미루기/압박 상태에서 ‘시작하기’ 위한 액션
maintain: 이미 흐름이 있는 날, 리듬을 유지하기 위한 액션
recovery: 실패 후 다시 붙기 위한 초저강도 액션
micro_win: 오늘 최소 승리로 바로 제안 가능한 액션
3-2. 사용자 입력과 연결되는 핵심 태그
분류
태그값
입력 원천
비고
energy
low / mid / high
모닝 체크인
행동 강도와 직접 연결
time
1 / 3 / 10 / 20 / 30
가능 시간
필터링 우선순위 매우 높음
state
focused / distracted / tired / stressed
현재 상태
추천 카피와 액션 타입 모두 영향
domain
work / study / life / health / social
온보딩/설정
개인화용
streak_phase
steady / shaky / dropped
최근 행동 로그
회복 모드 판단용
4. 액션 DB 예시 스키마
권장 저장 방식: 초기에는 PostgreSQL 또는 SQLite 단일 테이블로 시작하고, 태그는 JSON 배열로 저장한다. 추천 정교화가 필요해지면 정규화 테이블로 분리한다.
컬럼
예시 정의
id
TEXT PRIMARY KEY
label
TEXT NOT NULL
prompt_copy
TEXT NOT NULL
mode_tags
JSON NOT NULL
energy_tags
JSON NOT NULL
time_tags
JSON NOT NULL
state_tags
JSON
domain_tags
JSON
difficulty
INTEGER NOT NULL
recovery_safe
BOOLEAN NOT NULL DEFAULT FALSE
is_active
BOOLEAN NOT NULL DEFAULT TRUE
5. 추천 알고리즘 연결 구조
1단계 필터링: 사용자의 현재 모드와 시간 버킷에 맞는 액션만 추린다.
2단계 안전성 필터: recovery_mode=true 인 경우 recovery_safe=false 액션은 제외한다.
3단계 점수 계산: 에너지 적합도, 상태 적합도, 최근 노출 빈도, 개인 선호 도메인을 합산한다.
4단계 다양성 보정: 직전에 보여준 액션과 유사한 항목은 가산점에서 감점한다.
5단계 출력: 상위 3개를 사용자에게 노출하고, 1개는 가장 무난한 액션으로 고정 슬롯에 둔다.
5-1. 추천 파이프라인
입력: energy, available_time, state, missed_days, domain_preference
-> 사용자 모드 판정: execute / maintain / recovery
-> 액션 DB 필터링
-> 점수 계산
-> 상위 후보 3개 선택
-> UX 카피 치환 후 응답
5-2. 추천 점수 예시
항목
가중치
계산 방식
메모
mode match
40
현재 모드와 mode_tags 일치 시 +40
가장 중요
time fit
25
available_time 버킷 일치 시 +25
불일치 시 제외 가능
energy fit
15
energy_tags 일치 시 +15
낮은 에너지 날엔 중요
state fit
10
state_tags 일치 시 +10
압박/산만 대응
domain pref
5
선호 도메인 일치 시 +5
개인화 초급 단계
novelty
5
최근 2회 미노출 시 +5
반복 피로 방지
6. 모드 판정 규칙
조건
판정 모드
추천 액션 특성
예시
missed_days >= 2 또는 최근 3일 무행동
recovery
difficulty 1~2, recovery_safe=true
물 한 잔, 1분 정리
energy=low 또는 state=tired
start
1~3분, 시작 장벽 제거형
파일 열기, 할 일 1개 적기
energy=mid/high and streak steady
maintain
10~20분 유지형
집중 10분, 문서 1페이지
7. API 연결 설계
POST /checkin: 체크인 저장 후 추천에 필요한 사용자 상태를 만든다.
GET /actions/recommend: 현재 사용자 상태를 읽고 액션 후보 3개를 반환한다.
POST /actions/complete: 선택 액션과 결과를 기록하고 추천 품질 로그를 쌓는다.
7-1. 추천 API 응답 예시
키
예시
mode
recovery
primary_action
{id:'ACT-0004', label:'물 한 잔 마시기'}
candidates
[{...}, {...}, {...}]
reason
최근 이탈 감지 + 낮은 에너지
next_prompt
오늘은 복귀만 해도 충분해요.
8. 초기 액션 레코드 예시
ID
액션명
모드
에너지/시간
회복 허용
비고
ACT-0001
문서 파일 열기
start,micro_win
low-mid / 1-3
Y
시작 장벽 제거
ACT-0002
할 일 1개 적기
start,recovery
low / 1-3
Y
생각 정리형
ACT-0003
책상 3분 정리
micro_win,maintain
mid / 3-10
Y
생활 도메인
ACT-0004
물 한 잔 마시기
recovery
low / 1
Y
초저강도
ACT-0005
집중 10분 하기
maintain
mid-high / 10
N
이미 흐름이 있는 날
9. 추천 품질 로그 설계
shown_action_ids: 사용자에게 노출한 추천 후보 목록
selected_action_id: 사용자가 실제 고른 액션
completion_status: done / partial / fail
response_time_sec: 추천 노출 후 선택까지 걸린 시간
mode_at_time: 당시 추천 모드
recommendation_reason: 어떤 규칙으로 추천됐는지 설명 문자열
10. 단계별 구현 순서
1단계 MVP: JSON 태그 저장 + 룰 기반 필터 + 상위 3개 추천
2단계: 최근 노출 빈도, 성공률 기반 가점/감점 추가
3단계: 사용자별 도메인 선호와 성공 패턴을 반영한 개인화 확장
11. 결정 포인트
초기 액션 수는 80~120개 수준이 적당하다. 너무 적으면 반복 피로가 오고, 너무 많으면 품질 관리가 어렵다.
회복 모드 액션은 일반 액션과 분리 관리하는 것이 좋다. 실패 직후 노출되는 문구 톤까지 별도 관리해야 한다.
time_tags와 recovery_safe는 실제 체감 품질에 가장 큰 영향을 준다. 이 둘은 반드시 엄격하게 입력한다.
추천 사유(reason)를 함께 저장하면 디버깅과 UX 문구 개선이 쉬워진다.
이 문서는 트리아지 MVP 설계를 위한 내부 개발용 문서입니다.
