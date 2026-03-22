# Triage Mvp Spec

트리아지 텔레그램 MVP 상세 기획서
1. 제품 흐름
모닝 체크인 → 원탭 윈 선택 → 실행 → 완료 → 스트릭 반영 → 회복 모드
2. 주요 화면
시작: 상태 선택시간 선택상태 입력원탭 윈 제안완료 체크회복 모드
3. 핵심 기능
- 체크인 시스템- 행동 추천- 완료 기록- 소프트 스트릭- 회복 시스템
4. API 설계
/checkin/action/recommend/completion
5. 데이터 구조
users / checkins / actions / completions / streaks
6. 추천 로직
에너지, 시간, 상태 기반 룰 추천
7. 알림 구조
아침 / 점심 / 밤 / 복귀 알림
8. 성공 지표
유지율, 복귀율, 완료율
