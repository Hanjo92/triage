# Triage Api Db Spec

트리아지 개발 명세서텔레그램 MVP용 API · DB 스키마 · 운영 로직
목적: 바로 개발 착수 가능한 수준으로 백엔드/봇 플로우의 핵심 명세를 정리한다.
문서 범위
텔레그램 MVP 기준 API 엔드포인트, 데이터 모델, 추천/스트릭/회복 로직, 이벤트 로그
핵심 원칙
입력 최소화 · 원탭 실행 · 소프트 스트릭 · 실패보다 회복 중심 설계
1. 제품 코어와 개발 범위
이 문서는 ‘10초 모닝 체크인 → 원탭 윈 추천 → 완료 기록 → 소프트 스트릭 반영 → 회복 모드’ 흐름을 구현하기 위한 MVP 개발 기준서다. 초기 버전은 룰 기반 추천을 사용하고, 개인화 모델은 후속 단계에서 확장한다.
플랫폼 우선순위: 텔레그램 개인 루틴형 MVP
초기 포함 기능: 체크인, 추천, 완료 기록, 스트릭, 회복 모드, 리마인드
초기 제외 기능: 장문 일기, 복잡한 통계, 다중 목표 관리, 과도한 게임화
2. 핵심 사용자 플로우
1) 체크인
2) 원탭 윈 선택
3) 완료/부분/실패 기록
4) 스트릭/회복 반영
플로우 설명: 사용자는 짧은 상태 입력 후 바로 실행 가능한 액션 3개를 받고, 하나를 선택해 진행한다. 완료 여부에 따라 점수가 누적되며, 이탈 조짐이 보이면 회복 모드가 자동 제안된다.
3. API 명세
API는 모바일/웹 미니앱과 텔레그램 봇 메시지 레이어 모두에서 재사용할 수 있도록 REST 기준으로 설계한다.
엔드포인트
설명
주요 입력
주요 출력
POST /v1/checkins
모닝 체크인 생성
user_id, energy_level, available_time, mental_state
mode, action_candidates, reminder_plan
GET /v1/actions/recommend
원탭 윈 추천 조회
user_id, optional filters
추천 액션 3개와 추천 사유
POST /v1/completions
수행 결과 기록
user_id, action_id, status
streak_score, feedback_message, recovery_flag
GET /v1/streaks/today
오늘 기준 스트릭 상태 조회
user_id
연속성 점수, 최근 7일 상태, 회복 필요 여부
POST /v1/recovery/start
회복 세션 시작
user_id, trigger_type
회복용 액션 3개
POST /v1/notifications/schedule
알림 스케줄 등록/수정
user_id, preferred_times
active schedules
3-1. API 요청/응답 예시
예시: POST /v1/checkins
Request
{  "user_id": "u_1024",  "energy_level": "low",  "available_time": "3m",  "mental_state": "stressed"}
Response
{  "mode": "recovery",  "action_candidates": ["물 한 잔 마시기", "할 일 1개 적기", "문서 열기"],  "reminder_plan": "45m_followup"}
4. 데이터 모델
초기 구현은 단순성과 추적성을 우선한다. 사용자의 상태 변화와 액션 이력을 분리 저장해 나중에 추천 고도화에 활용한다.
테이블
역할
핵심 필드
users
사용자 기본 정보 및 선호값
id (PK), telegram_id, preferred_intensity, recovery_tone, timezone, created_at
daily_checkins
일일 체크인 기록
id, user_id (FK), energy_level, available_time, mental_state, mode, created_at
actions
추천 가능한 행동 템플릿
id, title, type, difficulty, estimated_minutes, is_recovery, is_active
action_recommendations
체크인 시점 추천 결과
id, user_id, checkin_id, action_id, rank, reason_code
completions
사용자 수행 결과
id, user_id, action_id, status, score, created_at
streak_snapshots
일별 연속성 집계
id, user_id, active_date, score_sum, streak_state, recovery_needed
recovery_sessions
회복 모드 진입/종료 로그
id, user_id, trigger_type, started_at, ended_at, recovered
notification_prefs
알림 시간 및 온오프
id, user_id, morning_time, followup_time, night_time, enabled
event_logs
행동 분석용 이벤트 원장
id, user_id, event_type, payload_json, created_at
4-1. 권장 SQL 스키마 초안
CREATE TABLE users (  id UUID PRIMARY KEY,  telegram_id VARCHAR(64) UNIQUE NOT NULL,  preferred_intensity VARCHAR(16) DEFAULT 'light',  recovery_tone VARCHAR(16) DEFAULT 'gentle',  timezone VARCHAR(32) DEFAULT 'Asia/Seoul',  created_at TIMESTAMP NOT NULL DEFAULT NOW());CREATE TABLE daily_checkins (  id UUID PRIMARY KEY,  user_id UUID NOT NULL REFERENCES users(id),  energy_level VARCHAR(16) NOT NULL,  available_time VARCHAR(8) NOT NULL,  mental_state VARCHAR(16) NOT NULL,  mode VARCHAR(16) NOT NULL,  created_at TIMESTAMP NOT NULL DEFAULT NOW());CREATE TABLE completions (  id UUID PRIMARY KEY,  user_id UUID NOT NULL REFERENCES users(id),  action_id UUID NOT NULL REFERENCES actions(id),  status VARCHAR(16) NOT NULL,  score NUMERIC(3,1) NOT NULL,  created_at TIMESTAMP NOT NULL DEFAULT NOW());
5. 추천 로직과 소프트 스트릭 규칙
초기 버전은 명시적 룰 기반으로 유지한다. 사용자가 왜 이 액션을 받았는지 설명 가능해야 하며, 운영자가 쉽게 조정할 수 있어야 한다.
조건
적용 규칙
의도
에너지 낮음
difficulty=very_easy
실행 장벽이 가장 낮은 행동만 추천
가능 시간 3분
type=instant
즉시 시작 가능한 초소형 액션 우선
정신 상태 압박
type=start_action
결과보다 시작 행동 중심으로 제안
2일 연속 미수행
mode=recovery
회복 액션 3개만 노출
3일 체크인 없음
recovery_needed=true
일반 추천 대신 복귀 메시지 송출
소프트 스트릭 점수 규칙
상태
점수
설명
완료
1.0
추천 행동을 끝까지 수행
부분 수행
0.7
조금 했지만 연결감 유지
회복 수행
0.4
복귀 액션만 완료해도 인정
체크인만 함
0.2
실행은 못했지만 루틴 접속 유지
6. 텔레그램 봇 메시지 플로우
단계
메시지 예시
아침
오늘 상태 어때요? [괜찮음] [보통] [힘듦]
추천
오늘은 가볍게 시작해볼게요. [문서 열기] [할 일 1개 적기] [3분 정리]
팔로업
지금 3분만 해볼까요? [지금 할게요] [나중에]
완료 체크
완료했어요? [완료] [조금 함] [못함]
회복
괜찮아요. 회복 체크인만 해도 다시 붙어요. [회복하기]
7. 이벤트/지표 설계
분석의 초점은 ‘얼마나 오래 잘했는가’보다 ‘놓친 뒤 얼마나 잘 돌아오는가’에 둔다.
checkin_started
action_selected
action_completed
completion_partial
recovery_started
recovery_completed
notification_clicked
return_after_gap
핵심 KPI: 첫 실패 후 복귀율, 3일 이상 공백 유저 복귀율, 원탭 윈 완료율, 회복 후 7일 유지율
8. 개발 우선순위
단계
포함 범위
완료 기준
1차
체크인 · 추천 · 완료 · 스트릭
기본 루프 작동
2차
회복 모드 · 알림 스케줄링
이탈 감지와 복귀 유도
3차
통계 대시보드 · 추천 개인화
운영 최적화
9. 다음 문서화 권장 순서
이 문서 다음에는 화면 설계서, 실제 SQL 파일, 텔레그램 봇 인터랙션 스펙, 그리고 실행 가능한 MVP 코드 문서 순으로 확장하면 된다. 이후 요청 내용도 같은 방식으로 문서 파일로 만들어 첨부한다.
