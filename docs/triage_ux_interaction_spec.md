# Triage Ux Interaction Spec

트리아지 UX 인터랙션 명세서 & 상태 전이 설계
1. 상태 정의
idle: 시작 전 상태checked_in: 체크인 완료action_selected: 원탭 윈 선택in_progress: 실행 중completed: 완료partial: 부분 수행failed: 미수행recovery_mode: 회복 모드
2. 상태 전이 흐름
idle → checked_inchecked_in → action_selectedaction_selected → in_progressin_progress → completed / partial / failedfailed → recovery_moderecovery_mode → completed
3. 주요 인터랙션
[상태 선택 클릭]→ energy_level 저장→ 다음 질문 노출[시간 선택 클릭]→ available_time 저장[원탭 윈 선택]→ action_id 저장→ 상태: action_selected[완료 버튼 클릭]→ completion 저장→ streak 계산
4. 회복 로직
조건:- 2일 이상 미수행- 3일 이상 미접속동작:→ recovery_mode = true→ 초저강도 액션만 추천→ 완료 시 복귀 처리
5. 알림 트리거
아침: 체크인 요청점심: 실행 리마인드밤: 회복 유도이탈: 복귀 메시지
6. UX 원칙
- 선택은 빠르게- 입력은 최소- 실패는 허용- 복귀는 쉽게
