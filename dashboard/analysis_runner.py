"""
Streamlit UI에서 분석 봇을 직접 실행하는 헬퍼 모듈.
subprocess로 run_analysis.py를 호출하고 결과를 반환합니다.
"""
import subprocess
import sys
import os


def run_analysis_now(analysis_date: str) -> tuple[bool, str]:
    """
    일간 분석 봇을 실행합니다.

    Args:
        analysis_date: 'YYYY-MM-DD' 형식의 분석 기준일

    Returns:
        (success: bool, output: str)
    """
    root   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script = os.path.join(root, 'run_analysis.py')
    cmd    = [sys.executable, script, '--analysis-date', analysis_date]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=360,
            cwd=root,
        )
        output = proc.stdout
        if proc.stderr:
            output += f'\n[stderr]\n{proc.stderr}'
        return proc.returncode == 0, output

    except subprocess.TimeoutExpired:
        return False, '⏰ 분석이 6분을 초과하여 타임아웃되었습니다.\nGitHub Actions에서 실행하거나 잠시 후 다시 시도해주세요.'
    except Exception as e:
        return False, f'실행 오류: {e}'


def run_weekly_now(week_start: str) -> tuple[bool, str]:
    """
    주간 분석 봇을 실행합니다.

    Args:
        week_start: 'YYYY-MM-DD' 형식의 주 시작일 (월요일)

    Returns:
        (success: bool, output: str)
    """
    root   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script = os.path.join(root, 'run_weekly.py')
    cmd    = [sys.executable, script, '--week-start', week_start]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            cwd=root,
        )
        output = proc.stdout
        if proc.stderr:
            output += f'\n[stderr]\n{proc.stderr}'
        return proc.returncode == 0, output

    except subprocess.TimeoutExpired:
        return False, '⏰ 분석이 10분을 초과하여 타임아웃되었습니다.'
    except Exception as e:
        return False, f'실행 오류: {e}'
