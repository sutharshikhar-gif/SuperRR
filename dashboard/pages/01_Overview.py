import streamlit as st, pandas as pd, plotly.graph_objects as go
from utils import *
f=st.session_state['global_filters']
st.markdown('<div class="hero"><div class="hero-kicker">SupeRR Selector · Season 2 · Round 1</div><h1>Who Delivers<br>When It Matters?</h1><p>Finding the batters who rescue a collapse and the bowlers who hold their nerve when the match is under pressure.</p></div>',unsafe_allow_html=True)
st.markdown('<div class="pipeline"><div class="step"><b>01</b>Define pressure</div><div class="step"><b>02</b>Compare with expectation</div><div class="step"><b>03</b>Rank and stress-test</div></div>',unsafe_allow_html=True)
d=filtered(deliveries(),f)
model=st.radio('Leaderboard view',['Final list (Model B)','Main model (Model A)','Published v3 ranks (Model C)'],horizontal=True)
model_key={'Final list (Model B)':'Model B','Main model (Model A)':'Model A','Published v3 ranks (Model C)':'Model C'}[model]
if d.empty: empty()
else:
    bflag=pressure_mask(d,'bat',f); wflag=pressure_mask(d,'bowl',f)
    cols=st.columns(5)
    legal=d.legal_ball.fillna(False).astype(bool) if 'legal_ball' in d else pd.Series(True,index=d.index)
    vals=[('Matches analysed',f"{d.match_id.nunique():,}"),('Deliveries',f"{len(d):,}"),('Batting pressure',f'{bflag[legal].mean():.1%}' if legal.any() else 'n/a'),('Bowling pressure',f'{wflag[legal].mean():.1%}' if legal.any() else 'n/a'),('Eligible players',f"{(player_tables('Batter').pressure_balls.ge(f['min_bat']).sum())} / {(player_tables('Bowler').pressure_balls.ge(f['min_bowl']).sum())}")]
    for c,(label,val) in zip(cols,vals):
        with c: metric_card(label,val,'after current filters' if label in ('Matches analysed','Deliveries','Batting pressure','Bowling pressure') else 'batters / bowlers')
    left,right=st.columns(2)
    for col,role in [(left,'Batter'),(right,'Bowler')]:
        with col:
            title_model='Model C published v3 ranks' if model_key=='Model C' else model_key
            st.subheader(f'Top 10 {role.lower()}s · {title_model}')
            tbl=leaderboard(role,model_key,f)
            if tbl.empty: empty()
            else:
                if {'model_a_rating','rating_ci_low','rating_ci_high'}.issubset(tbl.columns):
                    center=pd.to_numeric(tbl.model_a_rating,errors='coerce')
                    fig=go.Figure(go.Bar(x=center,y=tbl.name,orientation='h',marker_color=PINK,
                        error_x=dict(type='data',symmetric=False,array=(pd.to_numeric(tbl.rating_ci_high,errors='coerce')-center).fillna(0),arrayminus=(center-pd.to_numeric(tbl.rating_ci_low,errors='coerce')).fillna(0)),
                        hovertemplate='%{y}<br>Rating %{x:.2f}<extra></extra>'))
                    fig.update_layout(title=f'{role}: Model A rating · 95% CI',xaxis_title='Model A rating (standardized units)',yaxis_title='',yaxis=dict(autorange='reversed'))
                    st.plotly_chart(plot_theme(fig,300),use_container_width=True)
                for _,pr in tbl.iterrows():
                    with st.container(border=True):
                        c1,c2=st.columns([1,8])
                        rank_label=f"{int(pr['rank'])}" if pd.notna(pr.get('rank')) else 'n/a'
                        c1.markdown(f"### {rank_label}")
                        if c2.button(pr['name'],key=f"open_{role}_{model_key}_{int(pr.player_id)}",use_container_width=True): add_player_link(role,int(pr.player_id))
                        sample=pr.get('pressure_balls',float('nan'))
                        team=team_display(pr)
                        model_a=f"Model A {display_number(pr.get('model_a_rating'))} [{display_number(pr.get('rating_ci_low'))}, {display_number(pr.get('rating_ci_high'))}]"
                        if model_key=='Model B':
                            score=display_number(pr.get('model_b_score'))
                            details=f"{team} · {int(sample) if pd.notna(sample) else 'n/a'} pressure balls · Model B score {score} · {model_a}"
                        elif model_key=='Model C':
                            rank=pr.get('model_c_rank')
                            rank_text=f"#{int(rank)} of {int(pr.get('model_c_pool_size',0))}" if pd.notna(rank) else str(pr.get('model_c_status','n/a'))
                            details=f"{team} · Model C published v3 rank {rank_text} · {model_a}"
                        else:
                            details=f"{team} · {int(sample) if pd.notna(sample) else 'n/a'} pressure balls · {model_a}"
                        c2.caption(details)
footer()
