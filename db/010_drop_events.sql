-- 공식 이벤트 후보·검토 기능을 제거했다: 제목만으로는 공식 여부를 판별할 수 없어서 (analyzer/events.py 삭제)
drop table if exists events;
