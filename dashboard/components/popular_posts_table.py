"""
인기글 TOP 5 테이블 컴포넌트
"""
import json
import streamlit as st


def render_top5_table(top5_data: list | str, gallery_name: str = ''):
    """인기글 TOP 5를 카드 형태의 테이블로 렌더링합니다."""
    if isinstance(top5_data, str):
        try:
            top5_data = json.loads(top5_data)
        except Exception:
            top5_data = []

    if not top5_data:
        st.caption("인기글 데이터가 없습니다.")
        return

    for i, post in enumerate(top5_data[:5], 1):
        title   = str(post.get('제목', '(제목 없음)'))
        author  = str(post.get('작성자', ''))
        link    = str(post.get('링크', ''))
        likes   = int(post.get('추천수', 0))
        comments = int(post.get('댓글수', 0))
        views   = int(post.get('조회수', 0))
        date    = str(post.get('날짜', ''))[:10]

        rank_color = ['#FF4B4B', '#FF7676', '#FF9999', '#FFBBBB', '#FFDDDD'][i - 1]

        title_html = (
            f'<a href="{link}" target="_blank" style="color:#31333F;text-decoration:none;">{title}</a>'
            if link else title
        )

        st.markdown(
            f"""
            <div style="
                display:flex; align-items:flex-start; gap:12px;
                padding:10px 14px; margin-bottom:6px;
                background:#FAFAFA; border-radius:8px;
                border-left:4px solid {rank_color};
            ">
                <div style="
                    font-size:1.3rem; font-weight:700;
                    color:{rank_color}; min-width:24px; line-height:1.4;
                ">{i}</div>
                <div style="flex:1;">
                    <div style="font-size:0.95rem; font-weight:600; line-height:1.5;">{title_html}</div>
                    <div style="font-size:0.78rem; color:#6C757D; margin-top:3px;">
                        {author} &nbsp;|&nbsp; {date} &nbsp;|&nbsp;
                        👍 {likes:,} &nbsp; 💬 {comments:,} &nbsp; 👁️ {views:,}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
