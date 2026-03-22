# Triage Db Sql Logic

트리아지 DB 스키마 SQL + 추천 로직 코드 명세
1. actions 테이블 (태그 기반)
CREATE TABLE actions (  id SERIAL PRIMARY KEY,  name TEXT,  energy_level TEXT,      -- low / mid / high  time_required INT,      -- minutes  action_type TEXT,       -- start / maintain / recovery  domain TEXT,            -- work / study / life  message TEXT            -- UX 카피);
2. users 테이블
CREATE TABLE users (  id SERIAL PRIMARY KEY,  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
3. checkins 테이블
CREATE TABLE checkins (  id SERIAL PRIMARY KEY,  user_id INT,  energy TEXT,  time INT,  state TEXT,  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
4. completions 테이블
CREATE TABLE completions (  id SERIAL PRIMARY KEY,  user_id INT,  action_id INT,  status TEXT,  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
5. 추천 알고리즘 (Python 의사코드)
def recommend_actions(user_state):    energy = user_state['energy']    time = user_state['time']    state = user_state['state']    query = actions.filter(energy_level=energy)    if time <= 3:        query = query.filter(time_required <= 3)    if state == 'stressed':        query = query.filter(action_type='start')    return query.limit(3)
6. 회복 모드 로직
if missed_days >= 2:    return actions.filter(action_type='recovery').limit(3)
